from enum import Flag
from io import FileIO
import sys
import cairo
import math
from typing import Tuple, List

import xml.etree.ElementTree as ET

class LineBase:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def __str__(self):
        return f"{self._x} {self._y}"

class Move(LineBase):
    def __init__(self, x, y):
        super().__init__(x, y)
    
    def __str__(self):
        return f"M {super().__str__()}"

class MoveRel(LineBase):
    def __init__(self, dx, dy):
        super().__init__(dx, dy)
    
    def __str__(self):
        return f"m {super().__str__()}"

class Line(LineBase):
    def __init__(self, x, y):
        super().__init__(x, y)
    
    def __str__(self):
        return f"L {super().__str__()}"

class LineRel(LineBase):
    def __init__(self, dx, dy):
        super().__init__(dx, dy)
    
    def __str__(self):
        return f"l {super().__str__()}"

class Horizontal:
    def __init__(self, x):
        self._x = x
    
    def __str__(self):
        return f"H {self._x}"

class HorizontalRel:
    def __init__(self, dx):
        self._x = dx
    
    def __str__(self):
        return f"h {self._x}"

class Vertical:
    def __init__(self, y):
        self._y = y
    
    def __str__(self):
        return f"V {self._y}"

class VerticalRel:
    def __init__(self, dy):
        self._y = dy
    
    def __str__(self):
        return f"v {self._y}"

class ClosePath:
    def __init__(self):
        pass

    def __str__(self):
        return "Z"

class CubicCurve:
    def __init__(self, x1, y1, x2, y2, x, y):
        self._x1 = x1
        self._y1 = y1
        self._x2 = x2
        self._y2 = y2
        self._x = x
        self._y = y
    
    def __str__(self):
        return f"C {self._x1} {self._y1} {self._x2} {self._y2} {self._x} {self._y}"

class CubicCurveRel:
    def __init__(self, dx1, dy1, dx2, dy2, dx, dy):
        self._x1 = dx1
        self._y1 = dy1
        self._x2 = dx2
        self._y2 = dy2
        self._x = dx
        self._y = dy
    
    def __str__(self):
        return f"c {self._x1} {self._y1} {self._x2} {self._y2} {self._x} {self._y}"

class ContinuedCubicCurve:
    def __init__(self, x2, y2, x, y):
        self._x2 = x2
        self._y2 = y2
        self._x = x
        self._y = y
    
    def __str__(self):
        return f"S {self._x2} {self._y2} {self._x} {self._y}"

class ContinuedCubicCurveRel:
    def __init__(self, dx2, dy2, dx, dy):
        self._x2 = dx2
        self._y2 = dy2
        self._x = dx
        self._y = dy
    
    def __str__(self):
        return f"s {self._x2} {self._y2} {self._x} {self._y}"

class QuadraticCurve:
    def __init__(self, x1, y1, x, y):
        self._x1 = x1
        self._y1 = y1
        self._x = x
        self._y = y
    
    def __str__(self):
        return f"Q {self._x1} {self._y1} {self._x} {self._y}"

class QuadraticCurveRel:
    def __init__(self, dx1, dy1, dx, dy):
        self._x1 = dx1
        self._y1 = dy1
        self._x = dx
        self._y = dy
    
    def __str__(self):
        return f"q {self._x1} {self._y1} {self._x} {self._y}"

class ContinuedQuadraticCurve:
    def __init__(self, x, y):
        self._x = x
        self._y = y
    
    def __str__(self):
        return f"T {self._x} {self._y}"

class ContinuedQuadraticCurveRel:
    def __init__(self, dx, dy):
        self._x = dx
        self._y = dy
    
    def __str__(self):
        return f"t {self._x} {self._y}"

class Arc:
    def __init__(self, rx, ry, xrot, largearc, sweep, x, y):
        self._rx = rx
        self._ry = ry
        self._xrot = xrot
        self._largearc = largearc
        self._sweep = sweep
        self._x = x
        self._y = y
    
    def __str__(self):
        return f"A {self._rx} { self._ry} {self._xrot} {self._largearc} {self._sweep} {self._x} {self._y}"

class ArcRel:
    def __init__(self, rx, ry, xrot, largearc, sweep, dx, dy):
        self._rx = rx
        self._ry = ry
        self._xrot = xrot
        self._largearc = largearc
        self._sweep = sweep
        self._x = dx
        self._y = dy
    
    def __str__(self):
        return f"a {self._rx} { self._ry} {self._xrot} {self._largearc} {self._sweep} {self._x} {self._y}"

class Point:
    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y
    
    def __eq__(self, other: "Point"):
        return abs(self._x - other._x) < 0.01 and abs(self._y - other._y) < 0.01
    
    def __ne__(self, other: "Point"):
        return not (self == other)
    
    def __add__(self, other: "Point") -> "Point":
        return Point(self._x + other._x, self._y + other._y)
    
    def __sub__(self, other: "Point") -> "Point":
        return Point(self._x - other._x, self._y - other._y)
    
    def as_tuple(self):
        return self._x, self._y

class pathContext:
    def __init__(self, target: FileIO, width: float, height: float) -> None:
        self.target = target
        self.__line_cap = 0
        self.__line_join = 0
        self.__line_width = 1
        self.__miter_limit = 4
        self.__color = None
        self.__saved = []
        self.__root = ET.Element("svg", {
            "xmlns": "http://www.w3.org/2000/svg", 
            "version": "1.1", 
            "viewBox": "0 0 1024 1024",
            "width": f"{width}px",
            "height": f"{height}px"
        })
        self.__tree = ET.ElementTree(self.__root)
        self.__parents = []
        self.__path = []
        self.__location = Point(0, 0)
        self.__elem = None
        self.__ids_required = False
        self.__id = None
        self.__class = None

    def embed(self, elem: ET.Element):
        self.__root.append(elem)
    
    def enter_defs(self):
        self.__parents.append(self.__root)
        self.__root = ET.SubElement(self.__root, "defs")
        self.__ids_required = True

    def exit_defs(self):
        assert self.__root.tag == "defs", "Not in defs!"
        self.__root = self.__parents.pop()
        self.__ids_required = False
    
    def enter_group(self, name: str=None):
        self.__parents.append(self.__root)
        self.__root = ET.SubElement(self.__root, "g")
        if name is not None:
            self.__root.set("id", name)
        if self.__class is not None:
            self.__root.set("class", self.__class)
            self.__class = None
    
    def exit_group(self):
        assert self.__root.tag == "g", "Not in group!"
        self.__root = self.__parents.pop()

    def arc(self, xc: float, yc: float, radius: float, angle1: float, angle2: float) -> None:
        if abs(angle2 - angle1 - math.radians(360)) < 0.01:
            self.circle(xc, yc, radius)
            return
        start = Point(xc, yc) - Point(radius * math.cos(angle1), radius * math.sin(angle1))
        if start != self.__location:
            self.__path.append(Move(*start.as_tuple()))
        end = Point(xc, yc) + Point(radius * math.cos(angle2), radius * math.sin(angle2))
        largearc = int(abs(angle2 - angle1) > math.pi)
        sweep = int(angle2 - angle1 < 0)
        self.__path.append(Arc(radius, radius, 0, largearc, sweep, *end.as_tuple()))
        self.__location = end
    
    def circle(self, xc, yc, radius) -> None:
        assert not self.__ids_required or self.__id is not None, "An ID was required but was not provided!"
        self.__elem = ET.SubElement(self.__root, "circle", {
            "cx": str(xc),
            "cy": str(yc),
            "r": str(radius),
        })
        if self.__id is not None:
            self.__elem.attrib["id"] = self.__id
        if self.__class is not None:
            self.__elem.attrib["class"] = self.__class
        else:
            self.__elem.attrib["fill"] = "none"
            self.__elem.attrib["stroke"] = "none"
    
    def _class(self, classname: str):
        self.__class = classname

    def close_path(self) -> None:
        self.__path.append(ClosePath())
        self.__location = Point(0, 0)

    def curve_to(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> None:
        self.__path.append(CubicCurve(x1, y1, x2, y2, x3, y3))
        self.__location = Point(x3, y3)

    def _finalize(self):
        self.__elem = None
        self.__path = []
        self.__id = None
        self.__class = None

    def fill(self) -> None:
        self.fill_preserve()
        self._finalize()

    def fill_preserve(self) -> None:
        assert not self.__ids_required or self.__id is not None, "An ID was required but was not provided!"
        if self.__elem is None:
            if len(self.__path) > 0 and type(self.__path[-1]) != ClosePath:
                self.close_path()
            self.__elem = ET.SubElement(self.__root, "path", {
                "d": " ".join([str(elem) for elem in self.__path]),
            })
            if self.__id is not None:
                self.__elem.attrib["id"] = self.__id
            if self.__class is not None:
                self.__elem.attrib["class"] = self.__class
        if self.__class is None:
            self.__elem.attrib["fill"] = f"rgb({self.__color[0] * 100:.2f}%,{self.__color[1] * 100:.2f}%,{self.__color[2] * 100:.2f}%)"
            self.__elem.attrib["fill-opacity"] = f"{self.__color[3]}"
        self.__elem.attrib["fill-rule"] = "nonzero"
    
    def id(self, _id: str):
        self.__id = _id

    def move_to(self, x: float, y: float) -> None:
        self.__path.append(Move(x, y))
        self.__location = Point(x, y)

    def line_to(self, x: float, y: float) -> None:
        self.__path.append(Line(x, y))
        self.__location = Point(x, y)
    
    def save(self) -> None:
        self.__saved.append(
            (
                self.__color,
                self.__line_cap,
                self.__line_join,
                self.__line_width,
                self.__miter_limit
            )
        )
    
    def restore(self) -> None:
        if len(self.__saved) == 0:
            return
        values = self.__saved.pop()
        self.__color = values[0]
        self.__line_cap = values[1]
        self.__line_join = values[2]
        self.__line_width = values[3]
        self.__miter_limit = values[4]

    def set_miter_limit(self, m: float) -> None:
        self.__miter_limit = m

    def set_line_width(self, w: float) -> None:
        self.__line_width = w

    def get_line_width(self) -> float:
        return self.__line_width

    def set_line_cap(self, linecap: cairo.LineCap) -> None:
        self.__line_cap = linecap

    def set_line_join(self, linejoin: cairo.LineJoin) -> None:
        self.__line_join = linejoin

    def set_source_rgba(self, r: float, g: float, b: float, a: float) -> None:
        self.__color = (r, g, b, a)

    def set_source_rgb(self, r: float, g: float, b: float) -> None:
        self.__color = (r, g, b, 1)

    def stroke(self) -> None:
        self.stroke_preserve()
        self._finalize()

    def stroke_preserve(self) -> None:
        assert not self.__ids_required or self.__id is not None, "An ID was required but was not provided!"
        if self.__elem is None:
            self.__elem = ET.SubElement(self.__root, "path", {
                "d": " ".join([str(elem) for elem in self.__path]),
            })
            if self.__id is not None:
                self.__elem.attrib["id"] = self.__id
            if self.__class is not None:
                self.__elem.attrib["class"] = self.__class
            else:
                self.__elem.attrib["fill"] = "none"
        if self.__class is None:
            self.__elem.attrib["stroke"] = f"rgb({self.__color[0] * 100:.2f}%,{self.__color[1] * 100:.2f}%,{self.__color[2] * 100:.2f}%)"
            self.__elem.attrib["stroke-opacity"] = f"{self.__color[3]}"
        linecaps = ["butt", "round", "square"]
        linejoins = ["miter", "round", "bevel"]
        self.__elem.attrib["stroke-linejoin"] = linejoins[self.__line_join]
        self.__elem.attrib["stroke-linecap"] = linecaps[self.__line_cap]
        self.__elem.attrib["stroke-width"] = str(self.__line_width)
        self.__elem.attrib["stroke-miterlimit"] = str(self.__miter_limit)

    def rectangle(self, x, y, w, h):
        self.__path.append(Move(x, y))
        self.__path.append(HorizontalRel(w))
        self.__path.append(VerticalRel(h))
        self.__path.append(HorizontalRel(-w))
        self.close_path()
        self.__location = Point(x, y)
    
    def text(self, x: float, y: float, font_size: float, text: str, background: bool = False):
        self.__elem = ET.SubElement(self.__root, "text", {
            "x": str(x),
            "y": str(y),
            "font-size": str(font_size),
        })
        if self.__id is not None:
            self.__elem.attrib["id"] = self.__id
        if self.__class is not None:
            self.__elem.attrib["class"] = self.__class
        if background:
            self.__elem.attrib["stroke-width"] = f"{font_size / 6:.1f}"
            self.__elem.attrib["filter"] = f"blur({font_size / 10:.1f}px)"
        for i, line in enumerate(text.split("\n")):
            attribs = {"text-anchor": "middle"}
            if i != 0:
                attribs["dy"] = "110%"
            tspan = ET.SubElement(self.__elem, "tspan", attribs)
            tspan.text = line

    def use(self, href: str, x: float, y: float, width: float = 0, height: float = 0):
        self.__elem = ET.SubElement(self.__root, "use", {
            "href": href,
            "x": str(x),
            "y": str(y),
            "transform": f"translate({-50 * width / 100}, {-50 * height / 100}) scale({width / 100} {height / 100})",
            "transform-origin": f"{x} {y}"
        })
        if self.__id is not None:
            self.__elem.attrib["id"] = self.__id
        if self.__class is not None:
            self.__elem.attrib["class"] = self.__class

    def write(self):
        ET.indent(self.__tree)
        self.__tree.write(self.target, "UTF-8", True)

