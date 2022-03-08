from enum import Enum
from string import hexdigits
from typing import Tuple

class color:
    def __init__(self, r: int, g: int, b: int, a: int = 255):
        self.__r = r
        self.__g = g
        self.__b = b
        self.__a = a

    def as_percents(self, alpha=False) -> Tuple[float, ...]:
        if alpha:
            return (self.__r / 255, self.__g / 255, self.__b / 255, self.__a / 255)
        return (self.__r / 255, self.__g / 255, self.__b / 255)
    
    def as_hex(self, alpha=False) -> str:
        return f"#{hexdigits[self.__r >> 4]}{hexdigits[self.__r & 0xF]}{hexdigits[self.__g >> 4]}{hexdigits[self.__g & 0xF]}{hexdigits[self.__b >> 4]}{hexdigits[self.__b & 0xF]}{hexdigits[self.__a >> 4]}{hexdigits[self.__a & 0xF]} "[:-1 if alpha else -3].upper()

    def as_ints(self) -> Tuple[int, int, int, int]:
        return (self.__r, self.__g, self.__b, self.__a)

class FactionColors(color, Enum):
    VS = (68, 14, 98)
    NC = (0, 75, 128)
    TR = (158, 11, 15)