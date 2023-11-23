import enum

from dataclasses import dataclass
from pathlib import Path


class Importance(enum.IntEnum):
    DONE = -20

    WAITING_C = 4
    WAITING_B = 5
    WAITING_A = 6

    TODO_C = 14
    TODO_B = 15
    TODO_A = 16

    DOING_C = 24
    DOING_B = 25
    DOING_A = 26

    DEFAULT = TODO_B

    @staticmethod
    def to_text(importance):
        match importance//10:
            case 0:
                return "WAITING"
            case 1:
                return "TODO"
            case 2:
                return "DOING"


@dataclass
class TaskOrigin:
    file: Path
    block_start_line: int
    block_first_line_text: str
