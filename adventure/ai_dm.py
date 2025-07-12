import json
import asyncio
import os
from typing import Dict, List, Optional, Any
from openai import OpenAI
from .dice import roll_dice

aimodel="qwen/qwen3-235b-a22b"

class StoryState:
    def __init__(self):
        self.current_scene = ""
        self.npcs = {}
        self.enemies = {}
        self.environment = {}
        self.time = "day"
        self.weather = "clear"
        self.turn_order = []
        self.turn_order_sid = []
        self.current_turn = 0
        self.encounter_active = False

class AIDungeonMaster:
    """
    AI Dungeon Master for handling narration, rules, and player actions.
    Fully integrated system for D&D gameplay using OpenAI LLM.
    """
    def __init__(self, theme="High Fantasy", tonality="Whimsical & Heroic", room_id=None):
        self.theme = theme
        self.tonality = tonality
        self.room_id = room_id
        self.story_state = StoryState()
        self.players = {}
        self.client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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"
        )
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self):
        return f"""You are an expert Dungeon Master for Dungeons & Dragons 5th Edition. You control a {self.theme} adventure with a {self.tonality} tone.

CORE RESPONSIBILITIES:
- Narrate immersive stories and describe vivid scenes
- Interpret player actions and determine realistic outcomes
- Control NPCs, enemies, and environmental interactions
- Manage combat, dice rolls, and game mechanics
- Award XP, handle leveling, and track character progression
- Create branching storylines with meaningful choices

RESPONSE FORMAT:
Always respond with valid JSON in this exact format:
{{
    "narration": "Your storytelling response (1000-3000 characters)",
    "action_result": {{
        "success": true/false,
        "roll": null or dice roll result,
        "damage": 0,
        "healing": 0,
        "effects": {{}},
        "description": "Mechanical result description"
    }},
    "story_updates": {{
        "scene_change": null or "new scene description",
        "environment_changes": {{}},
        "npcs_affected": [],
        "enemies_affected": []
    }},
    "suggested_actions": [
        "Action 1 description",
        "Action 2 description", 
        "Action 3 description",
        "Action 4 description",
        "Action 5 description (make this one creative/dangerous/funny)"
    ]
}}

GAME RULES:
- Use D&D 5e mechanics for all actions
- Base AC is 12, modify based on context
- Attack rolls: d20 + ability modifier
- Damage varies by weapon/spell type
- Healing spells cost mana
- Award 50-100 XP for successful encounters
- Dead players cannot act until revived

Current game state will be provided with each request."""

    def add_player(self, player):
        self.players[player.sid] = player
        if player.name not in self.story_state.turn_order:
            self.story_state.turn_order.append(player.name)
            self.story_state.turn_order_sid.append(player.sid)


    def remove_player(self, player_sid):
        """Remove a player from DM tracking"""
    # Pop the player object (if any) so we can grab its name
        player = self.players.pop(player_sid, None)
        if not player:
            return  # nothing to do

        # If we ever added them into the turn order, remove both SID and name at the same index
        if player_sid in self.story_state.turn_order_sid:
            idx = self.story_state.turn_order_sid.index(player_sid)
            # remove the sid
            self.story_state.turn_order_sid.pop(idx)
            # remove the matching name
            # guard against any mismatch in list‐length, though they should always line up
            if idx < len(self.story_state.turn_order):
                self.story_state.turn_order.pop(idx)

    async def parse_player_intent(self, message: str) -> str:
        return await asyncio.to_thread(self._parse_player_intent, message)

    def _parse_player_intent(self, message: str) -> Dict[str, Any]:
        """Use LLM to parse player intent from natural language input"""
        prompt = (
            "You are a parser that interprets player actions in a D&D game. "
            "Classify the player's intent into one of these categories:\n"
            "- Attack\n"
            "- Defend\n"
            "- Heal\n"
            "- Move\n"
            "- Stealth\n"
            "- Communicate\n"
            "- Intimidate\n"
            "- Investigate\n"
            "- Perception\n"
            "- CastSpell\n"
            "- Unknown\n"
            "Provide your response in one word strings.\n"
            f"Player Message: {message}"
        )

        try:
            response = self.client.chat.completions.create(
                model=aimodel,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            return "Unknown"

    async def process_action(self, player, action: str) -> str:
        return await asyncio.to_thread(self._process_action, player, action)

    def _process_action(self, player, action: str) -> Dict[str, Any]:
        """Process a player's action and return results"""
        player_stats = player.stats
        
        result = {
            "success": False,
            "roll": None,
            "description": "",
            "effects": {},
            "damage": 0,
            "healing": 0
        }
        
        if action.lower() == "attack":
            # Roll for attack
            attack_roll = roll_dice(20) + (player_stats.power // 2)
            result["roll"] = attack_roll
            
            if attack_roll >= 12:  # Basic AC
                damage = roll_dice(6) + (player_stats.power // 3)
                result["success"] = True
                result["damage"] = damage
                result["description"] = f"Attack hits for {damage} damage! (Rolled {attack_roll})"
            else:
                result["description"] = f"Attack misses! (Rolled {attack_roll})"
                
        elif action.lower() == "defend":
            defense_bonus = player_stats.defense
            result["success"] = True
            result["effects"]["defense_bonus"] = defense_bonus
            result["description"] = f"Defensive stance taken! (+{defense_bonus} to defense)"
            
        elif action.lower() == "heal":
            if player_stats.mana >= 2:
                healing = roll_dice(4) + 2
                player.stats.heal(healing)
                player.stats.mana -= 2
                result["success"] = True
                result["healing"] = healing
                result["description"] = f"Heals for {healing} HP! (Cost: 2 mana)"
            else:
                result["description"] = "Not enough mana to heal!"
                
        elif action.lower() == "castspell":
            if player_stats.mana >= 3:
                spell_roll = roll_dice(20) + (player_stats.mana // 2)
                result["roll"] = spell_roll
                
                if spell_roll >= 15:
                    damage = roll_dice(8) + 2
                    player.stats.mana -= 3
                    result["success"] = True
                    result["damage"] = damage
                    result["description"] = f"Spell hits for {damage} magical damage! (Rolled {spell_roll})"
                else:
                    result["description"] = f"Spell fizzles! (Rolled {spell_roll})"
            else:
                result["description"] = "Not enough mana to cast spell!"
        
        else:
            # For roleplay actions, just acknowledge
            result["success"] = True
            result["description"] = f"Player attempts to {action}"

        story_update= f"""
        This is a game of Dungeons and Dragons and With respect to the story {self.story_state.current_scene} and the current action taken {result}, make description of the current scenario in a interative and captivating way.
        """
        try:
            response = self.client.chat.completions.create(
                model=aimodel,
                messages=[
                    {"role": "user", "content": story_update}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            updated_story= response.choices[0].message.content.strip()
            self.update_story_state(updated_story) 
        except:
            pass

        return result 
       
    async def narrate(self, context: str, player_action: Optional[Dict] = None, action_result: Optional[Dict] = None) -> str:
        return await asyncio.to_thread(self._narrate, context, player_action, action_result)

    def _narrate(self, context: str, player_action: Optional[Dict] = None, action_result: Optional[Dict] = None) -> str:
        """Generate AI narration using LLM based on context and actions"""
        # Prepare prompt for the LLM
        prompt = self._build_prompt(context, player_action, action_result)

        try:
            response = self.client.chat.completions.create(
                model=aimodel,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating narration: {e}"



    def _build_prompt(self, context: str, player_action: str, action_result: Optional[Dict]) -> str:
        """Construct a prompt for the LLM based on game state and player actions"""
        scene_description = self._generate_scene_description()
        action_narration = ""

        if player_action and action_result:
            action_narration = self._describe_action(player_action, action_result)

        prompt = (
            f"Current Scene: {scene_description}\n"
            f"{action_narration}\n"
            f"Context: {context}\n"
            "Narrate the next part of the story and suggest possible actions."
        )
        return prompt

    def _describe_action(self, player_action: str, result: Dict) -> str:
        """Describe the player's action in natural language for the LLM"""
        base_description = result.get("description", "")
        return f"The player attempted to '{player_action}' and {base_description.lower()}."

    def _generate_scene_description(self) -> str:
        """Generate description of current scene"""
        if not self.story_state.current_scene:
            return f"You find yourself in a mysterious {self.theme.lower()} realm. The air is thick with magic and adventure awaits around every corner."
        return self.story_state.current_scene

    def _narrate_action(self, player_action: Dict, result: Dict) -> str:
        """Narrate the result of a player action"""
        base_description = result.get("description", "")
        
        if result.get("success"):
            if result.get("damage", 0) > 0:
                return f"{base_description} The enemy staggers from the blow!"
            elif result.get("healing", 0) > 0:
                return f"{base_description} You feel renewed vitality!"
            else:
                return f"{base_description}"
        else:
            return f"{base_description}"

#     def _generate_potential_actions(self) -> str:
#         """Generate 5 potential actions for players"""
#         actions = [
#             "1. {Attack the nearest threat with your weapon}",
#             "2. {Cast a spell to aid your party}",
#             "3. {Search the area for hidden secrets}",
#             "4. {Attempt to negotiate with any present creatures}",
#             "5. {Use the environment to your tactical advantage}"
#         ]
#         return "\n".join(actions)
# 
    async def generate_story(self, theme: str, tonality: str) -> str:
        return await asyncio.to_thread(self._generate_story_sync, theme, tonality)

    def _generate_story_sync(self, theme: str, tonality: str) -> str:
        if not theme.strip():
            theme = "High Fantasy"
        if not tonality.strip():
            tonality = "Whimsical & Heroic"

        prompt = f"""
        Write a short story set in a Dungeons & Dragons-inspired world. 
        The theme is **{theme}**, and the tonality should be **{tonality}**.

        Create a vivid, imaginative narrative featuring a party of unique adventurers suited to this theme and tone. 
        The party should face a challenge or quest that reflects the world and emotional atmosphere you've set.

        Include:
        - Descriptions of the setting, magic, and fantastical elements.
        - Characters with distinct personalities, motivations, and classes/races.
        - Along with story components that require different strenght tests.
        - Dialogue and moments that highlight the tone (**{tonality}**).
        - A clear sense of adventure, conflict, or mystery aligned with the **{theme}**.
        """

        try:
            response = self.client.chat.completions.create(
                model=aimodel,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1000
            )
            self.story_state.current_scene=response.choices[0].message.content.strip()
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {e}"

    def decide_enemy_action(self, encounter_context: Dict) -> Dict[str, Any]:
        """Let the LLM determine enemy behavior based on the game state"""
        prompt = (
            "You are controlling enemies in a D&D game. Based on the current situation, choose one of the following actions:\n"
            "- Attack\n"
            "- Defend\n"
            "- Use Special Ability\n"
            "- Retreat\n"
            "- Trickery\n"
            f"Encounter Context: {encounter_context}\n"
            "Respond with your chosen action in JSON format."
        )

        try:
            response = self.client.chat.completions.create(
                model=aimodel,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            return {"action": "attack", "target": "random_player", "description": "The enemy attacks recklessly!"}

    def manage_turn_order(self) -> Optional[str]:
    # Advance to next player's turn FIRST
        self.story_state.current_turn = (self.story_state.current_turn + 1) % len(self.story_state.turn_order_sid)
        
        # Now get the player whose turn it is
        current_player_sid = self.story_state.turn_order_sid[self.story_state.current_turn]

        return current_player_sid
            

    def _generate_potential_actions(self) -> str:
        """Ask the LLM to generate creative suggested actions"""
        prompt = (
            "You are a creative Dungeon Master. Suggest five interesting and varied actions players could take in the current scene. "
            "Make sure one of them is unusual or risky.\n"
            f"Current Scene: {self.story_state.current_scene}"
        )

        try:
            response = self.client.chat.completions.create(
                model=aimodel,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.9
            )
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            return "Default actions:\n1. Attack the nearest threat\n2. Cast a defensive spell\n3. Search for hidden items\n4. Negotiate with enemies\n5. Try something risky or creative"

    def generate_turn_summary(self) -> Dict[str, Any]:
        """Generate JSON summary of the current turn state"""
        return {
            "room_id": self.room_id,
            "current_turn": self.story_state.current_turn,
            "turn_order": self.story_state.turn_order,
            "players": {sid: player.to_dict() for sid, player in self.players.items()},
            "story_state": {
                "current_scene": self.story_state.current_scene,
                "environment": self.story_state.environment,
                "time": self.story_state.time,
                "weather": self.story_state.weather,
                "encounter_active": self.story_state.encounter_active
            },
            "npcs": self.story_state.npcs,
            "enemies": self.story_state.enemies
        }

    def current_story(self) -> str:
        return self.story_state.current_scene

    def update_story_state(self, new_scene: Optional[str] = None, environment_changes: Optional[Dict] = None):
        """Update the story state"""
        if new_scene:
            self.story_state.current_scene = new_scene
        if environment_changes:
            self.story_state.environment.update(environment_changes)

    def start_encounter(self, enemies: Dict):
        """Start a combat encounter"""
        self.story_state.encounter_active = True
        self.story_state.enemies = enemies

    def end_encounter(self):
        """End the current encounter"""
        self.story_state.encounter_active = False
        self.story_state.enemies = {}
        
        # Award XP to surviving players
        for player in self.players.values():
            if player.can_act():
                player.xp += 50  # Base XP reward
