from typing import Tuple

class Map:
    WORLD_SIZE = 8192
    MAP_SIZE = 1024

    @classmethod
    def world_to_map(cls, point: Tuple[float, float], offsets: Tuple[float, float] = (0, 0)):
        ratio = cls.MAP_SIZE / cls.WORLD_SIZE
        return (ratio * (point[1] + offsets[1]), ratio * -(point[0] + offsets[0]))
    
    @classmethod
    def world_to_map_outline(cls, point: Tuple[float, float], offsets: Tuple[float, float] = (0, 0)):
        ratio = cls.MAP_SIZE / cls.WORLD_SIZE
        return (ratio * (point[1] + offsets[1]), ratio * (point[0] + offsets[0]))
    
    @classmethod
    def map_to_world(cls, point: Tuple[float, float], offsets: Tuple[float, float] = (0, 0)):
        ratio = cls.WORLD_SIZE / cls.MAP_SIZE
        return (ratio * -(point[1] + offsets[1]), ratio * (point[0] + offsets[0]))
