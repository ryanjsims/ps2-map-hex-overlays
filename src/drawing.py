import math
import os
import sys
import asyncio
import json
import cairo
import gi
gi.require_foreign("cairo")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango as pango, PangoCairo as pangocairo

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from queue import SimpleQueue
from argparse import ArgumentParser

import auraxium
from auraxium import ps2

from constants.zone_ids import ZoneID
from constants.faction_colors import FactionColors
from constants.facility_types import BADGE_SIZES, FacilityTypes, MAJOR_FACILITY_TYPES

class Map:
    WORLD_SIZE = 8192
    MAP_SIZE = 1024

    @classmethod
    def world_to_map(cls, point: Tuple[float, float], offsets: Tuple[float, float] = (0, 0)):
        ratio = cls.MAP_SIZE / cls.WORLD_SIZE
        return (ratio * (point[1] + offsets[1]), ratio * -(point[0] + offsets[0]))
    
    @classmethod
    def world_to_map_outline(cls, point: Tuple[float, float]):
        ratio = cls.MAP_SIZE / cls.WORLD_SIZE
        return (ratio * point[1], ratio * point[0])

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

    HEX_SPACING_X = 52
    HEX_SPACING_Y = 45

    def to_pixel_qr(self, size: float):
        z = size * math.sqrt(3) * (self._q + 0.5 * self._r)
        x = size * (3. / 2 * self._r)
        return x, z
    
    def to_pixel(self, size: float):
        z = self.HEX_SPACING_X * (self._q + 0.5 * self._r)
        x = self.HEX_SPACING_Y * (self._r * -1 - 2 / 3)
        return x, z

    def to_world(self, oshur: bool = False):
        hex_size = 115.5 if not oshur else 57.75
        z = hex_size * math.sqrt(3) * (self._q + 0.5 * self._r - 0.5)
        x = hex_size * (self._r * -(3 / 2) - 1 / 2)
        return x, z
    
    def corner_size(self, size: float, i: int):
        angle = math.radians(60 * i - 30)
        center = self.to_pixel(size)
        return center[0] + size * math.cos(angle), center[1] + size * math.sin(angle)

    def corner(self, size: float, i: int):
        angle = math.radians(60 * i - 30)
        center = self.to_pixel(size)
        return center[0] + self.HEX_SPACING_X * math.cos(angle), center[1] + self.HEX_SPACING_Y * math.sin(angle)
    
    def world_corner(self, i: int, oshur: bool = False):
        hex_size = 115.5 if not oshur else 57.75
        angle = math.radians(60 * i - 30)
        center = self.to_world(oshur)
        return round(center[0] + hex_size * math.sin(angle), 2), round(center[1] + hex_size * math.cos(angle))

    def edge(self, size, i):
        indices = [(0, 1), (1, 2), (2, 3),
                   (3, 4), (4, 5), (5, 0),]
        return (self.corner(size, indices[(i) % len(indices)][0]), self.corner(size, indices[(i) % len(indices)][1]))
    
    def world_edge(self, i, oshur: bool = False):
        indices = [(0, 1), (1, 2), (2, 3),
                   (3, 4), (4, 5), (5, 0),]
        return (self.world_corner(indices[(i) % len(indices)][0], oshur), self.world_corner(indices[(i) % len(indices)][1], oshur))

    def vertices(self, size: float):
        return [self.corner(size, i) for i in range(6)]

    def world_vertices(self, oshur: bool = False):
        return [self.world_corner(i, oshur) for i in range(6)]
    
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


class Region:
    def __init__(
            self, 
            id: int = 0,
            zone_id: int = ZoneID.INDAR,
            facility_type_id: int = FacilityTypes.UNKNOWN,
            name: str = None, 
            hex_tuples: Optional[List[tuple]] = None, 
            hexes: List[CubeHex] = [], 
            location: Tuple[float, float] = (0, 0), 
            connections: List[int] = [],
            color: FactionColors = FactionColors.VS
            ):
        self._hexes = {CubeHex(q, r, s) for q, r, s in hex_tuples} if hex_tuples is not None else set(hexes)
        self._id = id
        self._zone_id = zone_id
        self._facility_type = facility_type_id
        self._name = name
        self._color = color
        self.__shape = []
        self.__dirty = True
        self._location = location
        self._connections = connections
    
    def add_hexes(self, hexes: List[CubeHex]) -> None:
        self._hexes = self._hexes.union(set(hexes))
        self.__dirty = True
    
    def add_hex(self, hex: CubeHex) -> None:
        self._hexes.add(hex)
        self.__dirty = True

    def get_connections(self) -> List[int]:
        return self._connections
    
    def get_facility_type(self) -> FacilityTypes:
        return self._facility_type
    
    def get_name(self) -> str:
        return self._name

    def get_location(self) -> Tuple[float, float]:
        return self._location
    
    def get_zone_id(self) -> ZoneID:
        return ZoneID(self._zone_id)

    def get_outline(self) -> List[tuple]:
        if not self.__dirty and len(self.__shape) > 0 or len(self._hexes) == 0:
            return self.__shape
        
        pile = SimpleQueue()
        for hex in self._hexes:            
            for dir in range(6):
                if hex.neighbor(dir) not in self._hexes:
                    edge = hex.world_edge(dir, self._zone_id == ZoneID.OSHUR)
                    pile.put(edge)
        
        edge = pile.get()
        self.__shape.extend(edge)
        while not pile.empty():
            edge = pile.get()
            index0, index1 = -1, -1
            for i in range(len(self.__shape)):
                if abs(self.__shape[i][0] - edge[0][0]) < 1 and abs(self.__shape[i][1] - edge[0][1]) < 1:
                    index0 = i
                if abs(self.__shape[i][0] - edge[1][0]) < 1 and abs(self.__shape[i][1] - edge[1][1]) < 1:
                    index1 = i
                if index0 != -1 and index1 != -1:
                    break
            if index0 != -1 and index1 != -1:
                continue
            if index0 != -1:
                self.__shape.insert(index0 + 1, edge[1])
            elif index1 != -1:
                self.__shape.insert(index1, edge[0])
            else:
                pile.put(edge)
        
        self.__dirty = False
        return self.__shape
    
    def draw_outline(self, context: cairo.Context, offset_x = 0, offset_y = 0, transform_fn = Map.world_to_map):
        context.save()
        context.set_line_width(1.2)
        context.set_line_cap(cairo.LINE_CAP_BUTT)
        context.set_line_join(cairo.LINE_JOIN_MITER)
        context.set_source_rgba(*self._color.as_percents(), 0.4)
        outline = self.get_outline()
        if len(outline) == 0:
            return
        point = transform_fn(outline[0], (-offset_x, offset_y))
        context.move_to(point[0], point[1])
        for point in outline[1:]:
            point = transform_fn(point, (-offset_x, offset_y))
            context.line_to(point[0], point[1])
        context.close_path()
        context.fill_preserve()
        context.set_source_rgba(0, 0, 0, 0.8)
        context.stroke()
        context.restore()
    
    def draw_lattice(self, context: cairo.Context, offset_x, offset_y, connections: List['Region'], transform_fn=Map.world_to_map):
        offsets = Map.world_to_map((offset_x, offset_y))
        if len(self.get_location()) != 2:
            return
        if None in self.get_location():
            return
        context.save()
        x, y = Map.world_to_map(self.get_location())
        for connection in connections:
            conn_x, conn_y = transform_fn(connection.get_location())
            context.set_miter_limit(3)
            context.set_source_rgba(*self._color.as_percents(), 1)
            context.move_to(x + offsets[0], y - offsets[1])
            context.line_to(conn_x + offsets[0], conn_y - offsets[1])
            context.stroke()
            context.set_source_rgba(1, 1, 1, 0.75)
            context.save()
            context.set_line_width(context.get_line_width() * 0.66)
            context.move_to(x + offsets[0], y - offsets[1])
            context.line_to(conn_x + offsets[0], conn_y - offsets[1])
            context.stroke()
            context.restore()
        context.restore()
    
    def draw_name(self, context: cairo.Context, offset_x: int, offset_y: int, transform_fn = Map.world_to_map):
        if len(self.get_location()) != 2:
            return
        if None in self.get_location():
            return
        x, y = Map.world_to_map(self.get_location(), (-offset_x, offset_y))
        if self.get_facility_type() == FacilityTypes.CONSTRUCTION_OUTPOST:
            return
        if self.get_facility_type() not in MAJOR_FACILITY_TYPES:
            font_size = 5
        else:
            font_size = 10
        context.save()
        context.set_source_rgba(1, 1, 1, 1)
        layout = pangocairo.create_layout(context)

        font_desc = pango.font_description_from_string(f"Geogrotesque Medium, {font_size}px")
        layout.set_font_description(font_desc)

        layout.set_text(self._name)
        extents = layout.get_extents()
        context.move_to(x - extents.logical_rect.width / (2 * pango.SCALE), y + BADGE_SIZES[self._facility_type])
        pangocairo.show_layout(context, layout)
        context.restore()
    
    def draw_facility_indicator(self, context: cairo.Context, offset_x: float, offset_y: float, transform_fn = Map.world_to_map):
        if self._facility_type == FacilityTypes.UNKNOWN:
            return
        center = transform_fn(self.get_location(), (-offset_x, offset_y))
        badge_radius = BADGE_SIZES[self._facility_type]
        
        context.save()
        context.arc(center[0], center[1], badge_radius * 1.05, 0, 360)
        context.set_source_rgb(1, 1, 1)
        context.fill()

        context.set_source_rgba(*self._color.as_percents(), 0.75)
        context.arc(center[0], center[1], badge_radius * 0.95, 0, 360)
        context.fill()
        context.restore()

        if self._facility_type == FacilityTypes.INTERLINK:
            self.draw_interlink_dish(context, offset_x, offset_y, transform_fn)
        if self._facility_type == FacilityTypes.TECHPLANT:
            self.draw_tech_icon(context, offset_x, offset_y, transform_fn)
        if self._facility_type == FacilityTypes.AMP_STATION:
            self.draw_lightning(context, offset_x, offset_y, transform_fn)
        if self._facility_type == FacilityTypes.BIO_LAB:
            self.draw_flask(context, offset_x, offset_y, transform_fn)

    def draw_interlink_dish(self, context: cairo.Context, offset_x: float, offset_y: float, transform_fn = Map.world_to_map):
        center = transform_fn(self.get_location(), (-offset_x, offset_y))
        badge_radius = BADGE_SIZES[self._facility_type]
        
        start_angle, end_angle = -30, 120
        radius_dish = badge_radius * 0.7
        radius_ant = radius_dish / 10
        width_ant = radius_dish / 9
        length_ant = 2 / 3 * radius_dish

        chord_len = 2 * radius_dish * math.sin(math.radians(end_angle - start_angle) / 2)
        dist = math.sqrt(radius_dish ** 2 - ((chord_len ** 2) / 4))
        vec = (dist * math.cos(math.radians(135)), -dist * math.sin(math.radians(135)))
        arc_center = (center[0] + vec[0], center[1] + vec[1])

        context.save()
        context.set_source_rgb(1, 1, 1)
        context.set_line_width(width_ant)
        context.arc(arc_center[0], arc_center[1], radius_dish, math.radians(start_angle), math.radians(end_angle))
        context.fill()
        context.move_to(*center)
        context.line_to(center[0] + length_ant * math.cos(math.radians(135)), center[1] - length_ant * math.sin(math.radians(135)))
        context.stroke()
        context.arc(center[0] + length_ant * math.cos(math.radians(135)), center[1] - length_ant * math.sin(math.radians(135)), radius_ant, math.radians(0), math.radians(360))
        context.fill()
        context.restore()

    def draw_tech_icon(self, context: cairo.Context, offset_x: float, offset_y: float, transform_fn = Map.world_to_map):
        center = transform_fn(self.get_location(), (-offset_x, offset_y))
        badge_radius = BADGE_SIZES[self._facility_type]
        width = badge_radius / 10

        context.save()
        context.set_source_rgb(1, 1, 1)
        context.set_line_width(width)

        context.move_to(center[0] - badge_radius * 1/6, center[1] - badge_radius / 3)
        context.line_to(center[0] + badge_radius * 1/6, center[1] - badge_radius / 3)
        context.stroke()

        context.move_to(center[0] - badge_radius * 1/6, center[1] + badge_radius / 3)
        context.line_to(center[0] + badge_radius * 1/6, center[1] + badge_radius / 3)
        context.stroke()

        context.rectangle(center[0] - badge_radius / 2, center[1] - badge_radius / 2, badge_radius / 3, badge_radius / 3)
        context.stroke()

        context.arc(center[0] + badge_radius / 3, center[1] - badge_radius / 3, badge_radius / 6, math.radians(0), math.radians(360))
        context.stroke()

        context.arc(center[0] - badge_radius / 3, center[1] + badge_radius / 3, badge_radius / 6, math.radians(0), math.radians(360))
        context.stroke()

        context.arc(center[0] + badge_radius / 3, center[1] + badge_radius / 3, badge_radius / 6, math.radians(0), math.radians(360))

        context.stroke()

        context.restore()
    
    def draw_lightning(self, context: cairo.Context, offset_x: float, offset_y: float, transform_fn = Map.world_to_map):
        center = transform_fn(self.get_location(), (-offset_x, offset_y))
        badge_radius = BADGE_SIZES[self._facility_type]

        context.save()
        context.set_source_rgb(1, 1, 1)
        context.move_to(center[0] + badge_radius / 10, center[1] - badge_radius * 5 / 8)
        context.line_to(center[0] - badge_radius * 3 / 8, center[1] + badge_radius / 10)
        context.line_to(center[0], center[1] + badge_radius / 10)
        context.line_to(center[0] - badge_radius / 10, center[1] + badge_radius * 5 / 8)
        context.line_to(center[0] + badge_radius * 3 / 8, center[1] - badge_radius / 10)
        context.line_to(center[0], center[1] - badge_radius / 10)
        context.fill()
        context.restore()

    def draw_flask(self, context: cairo.Context, offset_x: float, offset_y: float, transform_fn = Map.world_to_map):
        center = transform_fn(self.get_location(), (-offset_x, offset_y))
        badge_radius = BADGE_SIZES[self._facility_type]
        width = badge_radius / 6

        context.save()
        context.set_source_rgb(1, 1, 1)
        context.set_line_width(width)
        context.set_line_join(cairo.LINE_JOIN_BEVEL)
        context.move_to(center[0] - badge_radius * (3/8), center[1] + badge_radius * (7/16))
        context.line_to(center[0] + badge_radius * (3/8), center[1] + badge_radius * (7/16))
        context.line_to(center[0], center[1] - badge_radius * (5/16))
        context.close_path()
        
        context.stroke()
        context.move_to(center[0], center[1] - badge_radius * (5/16))
        context.line_to(center[0] - badge_radius * (5/16), center[1] - badge_radius * (9/16))
        context.line_to(center[0] + badge_radius * (5/16), center[1] - badge_radius * (9/16))
        context.fill()
        context.restore()

def build_zone_request(service_id: str, zone_id: int) -> auraxium.census.Query:
    query = auraxium.census.Query(ps2.MapRegion.collection, service_id=service_id, zone_id=zone_id)
    query.show("map_region_id", "facility_id", "facility_name", "facility_type_id", "location_x", "location_z")
    join = query.create_join(ps2.MapHex.collection)
    join.set_fields("map_region_id", "map_region_id")
    join.set_list(True)
    join.set_inject_at("map_hexes")
    join.show("x", "y")
    join2 = query.create_join("facility_link")
    join2.set_fields("facility_id", "facility_id_a")
    join2.set_list(True)
    join2.set_inject_at("facility_links")
    join2.show("facility_id_b")
    join3 = join2.create_join(ps2.MapRegion.collection)
    join3.set_fields("facility_id_b", "facility_id")
    join3.set_inject_at("map_region")
    join3.show("map_region_id")
    query.limit(10000)

    return query

async def main():
    parser = ArgumentParser(description="Planetside 2 Map Drawing Utility")
    parser.add_argument("service-id", help="PS2 census service ID: https://census.daybreakgames.com/#devSignup")
    args = parser.parse_args()
    if not args.service_id.starts_with("s:"):
        service_id = "s:" + args.service_id
    else:
        service_id = args.service_id
        
    async with auraxium.Client(service_id=service_id) as client:
        zones: Dict[int, Dict[int, Region]] = {}
        for name, id in [("indar", 2), ("hossin", 4), ("amerish", 6), ("esamir", 8), ("oshur", 344)]:
            #print(f"Looking up {name} map hex data...")
            query = build_zone_request(client.service_id, id)

            try:
                with open(f"..{os.path.sep}cache{os.path.sep}{name}_cache.json") as f:
                    data = json.load(f)
            except FileNotFoundError:
                if id != ZoneID.OSHUR:
                    data = await client.request(query)
                    Path(f"..{os.path.sep}cache").mkdir(exist_ok=True)
                    with open(f"..{os.path.sep}cache{os.path.sep}{name}_cache.json", "w") as f:
                        json.dump(data, f, separators=(',', ':'))
                else:
                    print("Could not find Oshur data in cache and Oshur is not implemented in Census ¯\\_(ツ)_/¯", file=sys.stderr)
                    continue
    
            facilities: Dict[int, Region] = {}
            for map_region in data["map_region_list"]:
                map_region_id = int(map_region["map_region_id"])
                if "location_x" in map_region:
                    location = (float(map_region["location_x"]), float(map_region["location_z"]))
                elif map_region["facility_name"] == "Berjess Overlook":
                    location = (-2032.33, -92.78)
                elif map_region["facility_name"] == "Sunken Relay Station":
                    location = (1423.7, 2631.84)
                elif map_region["facility_name"] == "Lowland Trading Post":
                    location = (601.596, -2408.15)
                else:
                    location = tuple()
                
                if "facility_links" in map_region:
                    connections = [int(link["map_region"]["map_region_id"]) for link in map_region["facility_links"]]
                else:
                    connections = []
                
                if "facility_type_id" not in map_region:
                    map_region["facility_type_id"] = FacilityTypes.UNKNOWN

                facilities[map_region_id] = Region(
                    map_region_id,
                    zone_id=id,
                    facility_type_id=int(map_region["facility_type_id"]),
                    name = map_region["facility_name"],
                    location = location,
                    connections = connections,
                    hexes = [CubeHex.from_axial_rs(-int(hex["y"]) - 1, -int(hex["x"])) for hex in map_region["map_hexes"]],
                    color=FactionColors.TR
                )

            
            zones[name] = facilities

        Path(f"..{os.path.sep}svg").mkdir(exist_ok=True)
        for zone in zones:
            with cairo.SVGSurface(f"..{os.path.sep}svg{os.path.sep}{zone}.svg", 1024, 1024) as surface:
                surface.set_document_unit(cairo.SVG_UNIT_PX)
                print("Drawing " + f"..{os.path.sep}svg{os.path.sep}{zone}.svg")
                context = cairo.Context(surface)
                
                offsets = (4096, 4096)
                for region_id, region in zones[zone].items():
                    if region_id != region._id:
                        continue
                    region.draw_outline(context, *offsets, transform_fn=Map.world_to_map)
                
                context.set_source_rgba(1, 1, 1, 0.5)
                for region_id, region in zones[zone].items():
                    if region_id != region._id:
                        continue
                    region.draw_lattice(context, *offsets, [zones[zone][link_id] for link_id in region.get_connections()])
                
                for region_id, region in zones[zone].items():
                    if region_id != region._id:
                        continue
                    try:
                        region.draw_facility_indicator(context, *offsets)
                    except IndexError as e:
                        print(region.get_name())
                        raise e

                for region_id, region in zones[zone].items():
                    if region_id != region._id:
                        continue
                    region.draw_name(context, *offsets)            


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())