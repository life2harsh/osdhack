from typing import Dict, List, Optional
from .player import Player, PlayerStats
from .player_state import PlayerState
from .characters import PremadeCharacter, PREMADE_CHARACTERS
from .dice import roll_dice
from .ai_dm import AIDungeonMaster

adm=AIDungeonMaster()

class AdventureHandler:
    def __init__(self, sio, connected_clients):
        self.sio = sio
        self.connected_clients = connected_clients
        self.adventure_rooms = {}
        self.room_counter = 1
        self.ai_dms = {}

    async def handle_next_turn(self, room_id):
        ai_dm = self.ai_dms.get(room_id)
        if not ai_dm:
            return

        current_player_sid = ai_dm.manage_turn_order()
        if not current_player_sid:
            return

        # Notify all players whose turn it is
        current_player = ai_dm.players.get(current_player_sid)
        if current_player:
            await self.sio.emit("turn_notification", {
                "player_name": current_player.name,
                "message": f"It's {current_player.name}'s turn!"
            }, room=room_id)

        # suggested_actions = ai_dm._generate_potential_actions()
#         await self.sio.emit("suggested_actions", {"actions": suggested_actions.split("\n")}, to=current_player_sid)

    async def start_encounter(self, sid, data):
        room_id = data.get("room_id")
        enemies = data.get("enemies", {})  # Should be a dict of enemies
        ai_dm = self.ai_dms.get(room_id)
        if ai_dm:
            ai_dm.start_encounter(enemies)
            summary = ai_dm.generate_turn_summary()
            await self.sio.emit("encounter_started", {"enemies": enemies, "turn_summary": summary}, room=room_id)

    async def start_adventure(self, sid, data):

        room_id = f"adventure_{self.room_counter}"
        self.room_counter += 1

        theme = data.get("theme") or "High Fantasy"
        tonality = data.get("tonality") or "Whimsical & Heroic"

        self.ai_dms[room_id] = AIDungeonMaster(theme=theme, tonality=tonality, room_id=room_id)

        story = data.get("story", "").strip()
        users_to_add = data.get("users", [])
        if not story:
            story= await adm.generate_story(theme,tonality)
        if not users_to_add:
            await self.sio.emit("server_message", {"text from server": "Please specify users to invite to the adventure!"}, to=sid)
            return

        self.adventure_rooms[room_id] = {
            "story": story,
            "dm": sid,
            "players": {},
            "invited_users": users_to_add
        }

        await self.sio.enter_room(sid, room_id)
        await self.sio.emit("server_message", {
            "text from server": f"Adventure room '{room_id}' created! Story: {story}. Invited users: {', '.join(users_to_add)}"
        }, to=sid)
        await self._notify_invited_users(room_id, users_to_add, sid)

    async def join_adventure(self, sid, data):
        room_id = data.get("room_id", "").strip()
        player_role = data.get("role", "").strip()
        if not room_id or not player_role:
            await self.sio.emit("server_message", {"text from server": "Usage: /joinadventure <room_id> <player_role>"}, to=sid)
            return
        if room_id not in self.adventure_rooms:
            await self.sio.emit("server_message", {"text from server": f"Adventure room '{room_id}' not found!"}, to=sid)
            return
        adventure = self.adventure_rooms[room_id]
        username = self.connected_clients[sid]
        if username not in adventure["invited_users"]:
            await self.sio.emit("server_message", {"text from server": f"You are not invited to adventure '{room_id}'!"}, to=sid)
            return
        if sid in adventure["players"]:
            await self.sio.emit("server_message", {"text from server": f"You are already in adventure '{room_id}' as {adventure['players'][sid]}!"}, to=sid)
            return
        await self.sio.enter_room(sid, room_id)
        
        # Create Player object and add to AI DM
        username = self.connected_clients[sid]
        player = Player(sid, username, player_role)
        adventure["players"][sid] = player
        self.ai_dms[room_id].add_player(player)
        
        await self.sio.emit("server_message", {
            "text from server": f"You joined adventure '{room_id}' as {player_role}!"
        }, to=sid)
        await self.sio.emit("adventure_message", {
            "room_id": room_id,
            "message": f"{username} joined the adventure as {player_role}!",
            "timestamp": data.get("timestamp", ""),
            "type": "join"
        }, room=room_id, skip_sid=sid)

    async def send_adventure_message(self, sid, data):
        room_id = data.get("room_id", "").strip()
        message = data.get("message", "")
        if not room_id or not message:
            await self.sio.emit("server_message", {"text from server": "Room ID and message are required!"}, to=sid)
            return
        if room_id not in self.adventure_rooms:
            await self.sio.emit("server_message", {"text from server": f"Adventure room '{room_id}' not found!"}, to=sid)
            return
        adventure = self.adventure_rooms[room_id]
        user_rooms = self.sio.rooms(sid)
        if room_id not in user_rooms:
            await self.sio.emit("server_message", {"text from server": f"You are not in adventure '{room_id}'!"}, to=sid)
            return
        
        # Get AI DM for this room
        ai_dm = self.ai_dms.get(room_id)
        if not ai_dm:
            await self.sio.emit("server_message", {"text from server": "AI DM not found for this room!"}, to=sid)
            return
        
        # Check if player can act (not dead/fainted)
        player = ai_dm.players.get(sid)
        if player and not player.can_act():
            await self.sio.emit("server_message", {"text from server": "You cannot act while incapacitated!"}, to=sid)
            return
        
        # Parse player intent and process action
        if player and sid != adventure["dm"]:  # Only process for players, not DM
            intent = await ai_dm.parse_player_intent(message)
            action_result = await ai_dm.process_action(player, intent)
            
            # Generate AI narration
            narration = await ai_dm.narrate("Player action", intent, action_result)
            
            # Send action result and narration
            await self.sio.emit("adventure_message", {
                "room_id": room_id,
                "sender_name": self.connected_clients[sid],
                "sender_role": player.role,
                "message": message,
                "action_result": action_result,
                "ai_narration": narration,
                "timestamp": data.get("timestamp", ""),
                "type": "action"
            }, room=room_id)
           
            await self.handle_next_turn(room_id)
            # Send turn summary
            turn_summary = ai_dm.generate_turn_summary()
            await self.sio.emit("turn_summary", turn_summary, room=room_id)
          
        else:
            # DM message - no action processing
            sender_role = "DM" if sid == adventure["dm"] else "Unknown"
            await self.sio.emit("adventure_message", {
                "room_id": room_id,
                "sender_name": self.connected_clients[sid],
                "sender_role": sender_role,
                "message": message,
                "timestamp": data.get("timestamp", ""),
                "type": "message"
            }, room=room_id, skip_sid=sid)

    async def get_adventure_info(self, sid, data):
        room_id = data.get("room_id", "").strip()
        ai_dm = self.ai_dms.get(room_id)
        if not room_id:
            await self.sio.emit("server_message", {"text from server": "Room ID is required!"}, to=sid)
            return
        if room_id not in self.adventure_rooms:
            await self.sio.emit("server_message", {"text from server": f"Adventure room '{room_id}' not found!"}, to=sid)
            return
        adventure = self.adventure_rooms[room_id]
        user_rooms = self.sio.rooms(sid)
        if room_id not in user_rooms:
            await self.sio.emit("server_message", {"text from server": f"You are not in adventure '{room_id}'!"}, to=sidadventure_5)
            return
        players_info = []
        for player_sid, player in adventure["players"].items():
            player_name = self.connected_clients.get(player_sid, "Unknown")
            players_info.append(f"{player_name} ({player.role})")

        dm_name = self.connected_clients.get(adventure["dm"], "Unknown")
        await self.sio.emit("adventure_info", {
            "room_id": room_id,
            "story": ai_dm.current_story() or adventure["story"],
            "dm": dm_name,
            "players": players_info,
            "invited_users": adventure["invited_users"]
        }, to=sid)

    async def cleanup_on_disconnect(self, sid):
        for room_id, adventure in list(self.adventure_rooms.items()):
            if adventure["dm"] == sid:
                await self.sio.emit("adventure_message", {
                    "room_id": room_id,
                    "message": f"DM {self.connected_clients[sid]} has disconnected. Adventure ended.",
                    "timestamp": "",
                    "type": "dm_disconnect"
                }, room=room_id)
                # Clean up AI DM
                if room_id in self.ai_dms:
                    del self.ai_dms[room_id]
                del self.adventure_rooms[room_id]
            elif sid in adventure["players"]:
                player = adventure["players"][sid]
                # Remove from AI DM
                if room_id in self.ai_dms:
                    self.ai_dms[room_id].remove_player(sid)
                del adventure["players"][sid]
                await self.sio.emit("adventure_message", {
                    "room_id": room_id,
                    "message": f"{self.connected_clients[sid]} ({player.role if hasattr(player, 'role') else 'Unknown'}) has disconnected.",
                    "timestamp": "",
                    "type": "player_disconnect"
                }, room=room_id)

    async def _notify_invited_users(self, room_id, users_to_add, dm_sid):
        adventure = self.adventure_rooms[room_id]
        ai_dm = self.ai_dms.get(room_id)
        for username in users_to_add:
            target_sid = None
            for user_sid, user_name in self.connected_clients.items():
                if user_name == username:
                    target_sid = user_sid
                    break
            if target_sid:
                await self.sio.emit("adventure_invitation", {
                    "room_id": room_id,
                    "story": ai_dm.current_story(),
                    "dm": self.connected_clients[dm_sid],
                    "message": f"You've been invited to join D&D adventure '{room_id}' by {self.connected_clients[dm_sid]}. Story: {adventure['story']}. Use /joinadventure {room_id} <role> to join!"
                }, to=target_sid)

    def get_player(self, sid) -> Optional[Player]:
        for room in self.adventure_rooms.values():
            if sid in room.get("players", {}):
                return room["players"][sid]
        return None

    def get_room_players(self, room_id) -> List[Player]:
        room = self.adventure_rooms.get(room_id, {})
        return list(room.get("players", {}).values())

    async def handle_action(self, sid, data):
        """Handle explicit action commands"""
        room_id = data.get("room_id")
        action = data.get("action")
        
        if not room_id or room_id not in self.adventure_rooms:
            await self.sio.emit("server_message", {"text from server": "Invalid room!"}, to=sid)
            return
            
        ai_dm = self.ai_dms.get(room_id)
        if not ai_dm:
            await self.sio.emit("server_message", {"text from server": "AI DM not found!"}, to=sid)
            return
            
        player = ai_dm.players.get(sid)
        if not player or not player.can_act():
            await self.sio.emit("server_message", {"text from server": "Cannot perform action!"}, to=sid)
            return
            
        action_result = ai_dm.process_action(player, data)
        narration = ai_dm.narrate("Explicit action", data, action_result)
        
        await self.sio.emit("adventure_message", {
            "room_id": room_id,
            "sender_name": self.connected_clients[sid],
            "sender_role": player.role,
            "message": f"Performs {action}",
            "action_result": action_result,
            "ai_narration": narration,
            "timestamp": data.get("timestamp", ""),
            "type": "action"
        }, room=room_id)

    async def handle_dice_roll(self, sid, data):
        """Handle /dice command"""
        try:
            sides = int(data.get("sides", 20))
            modifier = int(data.get("modifier", 0))
        except Exception:
            sides, modifier = 20, 0
        result = roll_dice(sides, modifier)
        
        room_id = data.get("room_id")
        if room_id and room_id in self.adventure_rooms:
            # Send to room if in adventure
            await self.sio.emit("adventure_message", {
                "room_id": room_id,
                "sender_name": self.connected_clients[sid],
                "message": f"🎲 Rolled {result} (d{sides}{'+' if modifier >= 0 else ''}{modifier if modifier != 0 else ''})",
                "dice_result": {"result": result, "sides": sides, "modifier": modifier},
                "type": "dice"
            }, room=room_id)
        else:
            # Send to individual if not in room
            await self.sio.emit("dice_result", {"result": result, "sides": sides, "modifier": modifier}, to=sid)

    async def handle_stats(self, sid, room_id):
        """Send player stats to the user"""

        # Ensure room_id is hashable and the correct type
        if isinstance(room_id, list):
            if len(room_id) > 0:
                room_id = room_id[0]  # Use the first element if it's a list
            else:
                room_id = None

        if isinstance(room_id, str) and room_id in self.ai_dms:
            ai_dm = self.ai_dms[room_id]
            player = ai_dm.players.get(sid)
            if player:
                await self.sio.emit("player_stats", player.stats.to_dict(), to=sid)
                return

        # Fallback for non-adventure rooms
        player = self.get_player(sid)
        if player:
            await self.sio.emit("player_stats", player.stats.to_dict(), to=sid)
        else:
            await self.sio.emit("server_message", {"text from server": "Player not found."}, to=sid)

    async def handle_inventory(self, sid, data):
        """Send player inventory to the user"""
        room_id = data.get("room_id")
        
        if room_id and room_id in self.ai_dms:
            ai_dm = self.ai_dms[room_id]
            player = ai_dm.players.get(sid)
            if player:
                await self.sio.emit("player_inventory", {"inventory": player.inventory}, to=sid)
                return
        
        # Fallback for non-adventure rooms
        player = self.get_player(sid)
        if player:
            await self.sio.emit("player_inventory", {"inventory": player.inventory}, to=sid)
        else:
            await self.sio.emit("server_message", {"text from server": "Player not found."}, to=sid)

    def parse_story_file(self, story_file_path: str):
        pass

#     def generate_turn_summary(self, room_id):
#         """Generate turn summary using AI DM"""
#         if room_id in self.ai_dms:
#             return self.ai_dms[room_id].generate_turn_summary()
#         return {}

    def update_player_state(self, player: Player, new_state: PlayerState):
        player.state = new_state
