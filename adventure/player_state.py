from enum import Enum, auto

class PlayerState(Enum):
    ALIVE = auto()
    DEAD = auto()
    CRIPPLED = auto()
    FAINTED = auto()
