from .player import PlayerStats

class PremadeCharacter:
    def __init__(self, name, stats, traits):
        self.name = name
        self.stats = stats
        self.traits = traits

# Example premade characters (expand as needed)
PREMADE_CHARACTERS = [
    PremadeCharacter("Sabrina", PlayerStats(health=12, power=7, defense=4, speed=6, mana=10), ["Mage", "Funny pet"]),
    PremadeCharacter("Throg", PlayerStats(health=16, power=9, defense=8, speed=3, mana=2), ["Barbarian", "Strong"]),
]
