from cube_hex import CubeHex
from typing import Tuple

class DrawingHex(CubeHex):
    def __init__(self, q:int, r:int, s:int):
        super().__init__(q, r, s)
        self._color = (128, 128, 128, 128)
        self._selected_color = (0, 255, 0, 128)
        self._fill = (0, 0, 0, 0)
        self._selected_fill = (0, 255, 0, 64)
        self._selected = False
    
    def color(self, new_color: Tuple[int, int, int, int]=None):
        if new_color is not None:
            self._color = new_color
        return self._color if not self._selected else self._selected_color

    def fill(self, new_fill: Tuple[int, int, int, int]=None):
        if new_fill is not None:
            self._fill = new_fill
        return self._fill if not self._selected else self._selected_fill
    
    def toggle_select(self):
        self._selected = not self._selected