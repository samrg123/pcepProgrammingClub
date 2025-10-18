from enum import Enum


class Direction(Enum):
    Up    = 0
    Down  = 1
    Left  = 2
    Right = 3

class Position:
    x:int
    y:int

    def __init__(self, x:int, y:int):
        self.x = x
        self.y = y

    def __hash__(self):
        return hash(self.x) + hash(self.y)

    def __eq__(self, position:"Position"):
        return self.x == position.x and self.y == position.y

class ControlCodes:
    ClearScreen = "\x1b[2J\x1b[1;1H"
    Blink       = "\x1b[5m"
    Reset       = "\x1b[0m"

    FG_Red       = "\x1b[91m"
    FG_Green     = "\x1b[92m"
    FG_Yellow    = "\x1b[93m"
    FG_Blue      = "\x1b[94m"
    FG_Magenta   = "\x1b[95m"
    FG_Cyan      = "\x1b[96m"
    FG_White     = "\x1b[97m"

    BG_Red       = "\x1b[100m"
    BG_Green     = "\x1b[101m"
    BG_Yellow    = "\x1b[102m"
    BG_Blue      = "\x1b[103m"
    BG_Magenta   = "\x1b[104m"
    BG_Cyan      = "\x1b[105m"
    BG_White     = "\x1b[106m"    
