from .player_state import PlayerState

class PlayerStats:
    def __init__(self, health=10, power=5, defense=5, speed=5, mana=5, max_health=None, max_mana=None):
        self.health = health
        self.power = power
        self.defense = defense
        self.speed = speed
        self.mana = mana
        self.max_health = max_health if max_health is not None else health
        self.max_mana = max_mana if max_mana is not None else mana
        # Add more stats as needed

    def to_dict(self):
        return self.__dict__

    def is_alive(self):
        return self.health > 0

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

class Player:
    def __init__(self, sid, name, role, stats=None):
        self.sid = sid
        self.name = name
        self.role = role
        self.stats = stats or PlayerStats()
        self.state = PlayerState.ALIVE
        self.inventory = []
        self.xp = 0
        self.level = 1
        self.is_dm = False
        self.last_action = None
        self.story_position = None

    def to_dict(self):
        return {
            'sid': self.sid,
            'name': self.name,
            'role': self.role,
            'stats': self.stats.to_dict(),
            'state': self.state.name,
            'inventory': self.inventory,
            'xp': self.xp,
            'level': self.level,
            'is_dm': self.is_dm,
            'last_action': self.last_action,
            'story_position': self.story_position
        }

    def gain_xp(self, amount):
        self.xp += amount
        levels = [0, 300, 900, 2700, 6500]  # Example XP thresholds
        while self.level < len(levels) and self.xp >= levels[self.level]:
            self.level_up()

    def regen_mana(self, amount):
        self.stats.mana = min(self.stats.max_mana, self.stats.mana + amount)

    def level_up(self):
        self.level += 1
        self.stats.max_health += 10
        self.stats.health = self.stats.max_health
        self.stats.power += 2
        self.stats.defense += 1
        self.stats.mana += 5
        # Notify via event or emit

    def can_act(self):
        return self.state == PlayerState.ALIVE

    def apply_action(self, action, value=None):
        if action == 'heal' and value:
            self.stats.heal(value)
        elif action == 'damage' and value:
            self.stats.take_damage(value)
            if not self.stats.is_alive():
                self.state = PlayerState.DEAD
        # Add more actions as needed
