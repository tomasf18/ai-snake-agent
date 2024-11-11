from enum import Enum

class DIRECTION(Enum):
    UP = "w", (0, -1)
    DOWN = "s", (0, 1)
    LEFT = "a", (-1, 0)
    RIGHT = "d", (1, 0)
    
    def __init__(self, key: str, dir: tuple[int, int]):
        self.__key = key
        self.__dir = dir

    @property
    def key(self):
        return self.__key

    @property
    def dir(self):
        return self.__dir

    def __add__(self, other):
        return [self.dir[0] + other[0], self.dir[1] + other[1]]