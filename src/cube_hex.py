import math

class CubeHex:
    DIRECTION_VECTORS: tuple = tuple()

    def __init__(self, q:int, r:int, s:int):
        self._q = q
        self._r = r
        self._s = s
    
    def __add__(self, other):
        assert type(other) == CubeHex, "Cannot add " + str(type(other)) + " to CubeHex"
        return CubeHex(self._q + other._q, self._r + other._r, self._s + other._s)

    def __sub__(self, other):
        assert type(other) == CubeHex, "Cannot subtract " + str(type(other)) + " from CubeHex"
        return CubeHex(self._q - other._q, self._r - other._r, self._s - other._s)

    def __hash__(self):
        return hash(str(self._q) + str(self._r) + str(self._s))
    
    def __eq__(self, other):
        return self._q == other._q and self._r == other._r and self._s == other._s
    
    def __str__(self):
        return f"CubeHex({self._q} {self._r} {self._s})"
    
    def __repr__(self):
        return str(self)

    def distance(self, other):
        vec = self - other
        return max(abs(vec._q), abs(vec._r), abs(vec._s))
    
    def neighbor(self, direction: int):
        direction = direction % 6
        return self + CubeHex.DIRECTION_VECTORS[direction]

    def to_pixel(self, hex_size: float):
        z = hex_size * math.sqrt(3) * (self._q + 0.5 * self._r - 0.5)
        x = hex_size * (self._r * -(3 / 2) - 1 / 2)
        return x, z
    
    def corner(self, i: int, hex_size: float):
        angle = math.radians(60 * i - 30)
        center = self.to_pixel(hex_size)
        return round(center[0] + hex_size * math.sin(angle), 2), round(center[1] + hex_size * math.cos(angle))
    
    def edge(self, i, hex_size: float):
        indices = [(0, 1), (1, 2), (2, 3),
                   (3, 4), (4, 5), (5, 0),]
        return (self.corner(indices[(i) % len(indices)][0], hex_size), self.corner(indices[(i) % len(indices)][1], hex_size))

    def vertices(self, hex_size: float):
        return [self.corner(i, hex_size) for i in range(6)]
    
    @classmethod
    def from_axial_rs(cls, r: int, s: int):
        return cls(-r-s, r, s)
   
    @classmethod
    def from_axial_qs(cls, q: int, s: int):
        return cls(q, -q-s, s)
    
    @classmethod
    def from_axial_qr(cls, q: int, r: int):
        return cls(q, r, -q-r)
    
    @classmethod
    def from_pixel(cls, point: tuple, size: float):
        q = (math.sqrt(3) / 3 * point[0] - 1./3 * point[1]) / size
        r = (                              2./3 * point[1]) / size
        s = -q-r
        def hex_round(qf, rf, sf):
            q = round(qf)
            r = round(rf)
            s = round(sf)

            q_diff = abs(q - qf)
            r_diff = abs(r - rf)
            s_diff = abs(s - sf)

            if q_diff > r_diff and q_diff > s_diff:
                q = -r-s
            elif r_diff > s_diff:
                r = -q-s
            else:
                s = -q-r
            
            return cls(q, r, s)
        return hex_round(q, r, s)

CubeHex.DIRECTION_VECTORS = (CubeHex(+1, 0, -1), CubeHex(+1, -1, 0), CubeHex(0, -1, +1),
                             CubeHex(-1, 0, +1), CubeHex(-1, +1, 0), CubeHex(0, +1, -1),)
