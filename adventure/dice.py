import random

def roll_dice(sides: int, modifier: int = 0) -> int:
    return random.randint(1, sides) + modifier
