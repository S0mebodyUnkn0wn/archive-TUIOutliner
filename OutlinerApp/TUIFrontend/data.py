from dataclasses import dataclass
from typing import overload


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Bounds:
    top: int = 0
    left: int = 0
    bottom: int = 0
    right: int = 0

    @overload
    def collide(self, point: Point = Point(0, 0)):
        ...

    @overload
    def collide(self, x: int = 0, y: int = 0):
        ...

    def collide(self, *args):
        """ Returns true if point (x,y) is contained in bounds"""
        if len(args)==1 and isinstance(args[0],Point):
            x = args[0].x
            y = args[0].y
        elif len(args)==2 and isinstance(args[0],int) and isinstance(args[1],int):
            x = args[0]
            y = args[1]
        else:
            raise TypeError

        return (self.left <= x <= self.right) and (self.top <= y <= self.bottom)
