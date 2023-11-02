import enum

from dataclasses import dataclass
from pathlib import Path

class Importance(enum.IntEnum):

    DONE = -20

    WAITING_C = -6
    WAITING_B = -5
    WAITING_A = -4

    TODO_C = 4
    TODO_B = 5
    TODO_A = 6

    DOING_C = 14
    DOING_B = 15
    DOING_A = 16

    DEFAULT = TODO_B

    @staticmethod
    def to_text(importance):
        match importance//10:
            case -2:
                return "DONE"
            case -1:
                return "WAITING"
            case 0:
                return "TODO"
            case 1:
                return "DOING"

@dataclass
class TaskOrigin:
    file: Path
    block_start_line: int
    block_first_line_text: str
