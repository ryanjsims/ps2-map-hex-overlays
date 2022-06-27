import math

from typing import List, Optional, Tuple

import cairo
import gi
gi.require_foreign("cairo")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango as pango, PangoCairo as pangocairo

from map_region import Region

from cube_hex import CubeHex
from map import Map

from constants.facility_types import FacilityTypes, MAJOR_FACILITY_TYPES, BADGE_SIZES
from constants.faction_colors import FactionColors
from constants.zone_ids import ZoneID

class CairoRegion(Region):
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
        super().__init__(id, zone_id, facility_type_id, name, hex_tuples, hexes, location, connections, color)
    
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
        #if self.get_facility_type() == FacilityTypes.CONSTRUCTION_OUTPOST:
        #    return
        if self.get_facility_type() not in MAJOR_FACILITY_TYPES:
            font_size = 8
        else:
            font_size = 10
        context.save()
        context.set_source_rgba(1, 1, 1, 1)
        layout = pangocairo.create_layout(context)

        font_desc = pango.font_description_from_string(f"Geogrotesque Medium, {font_size}px")
        layout.set_font_description(font_desc)
        layout.set_alignment(pango.Alignment.CENTER)
        if self._name == "Southpeak Meadows" or self._name == "Emerald Research Co." or self._name == "Hopeswell Beachhead":
            self._name = "\n".join(self._name.split())
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
        context.move_to(center[0], center[1])
        context.line_to(center[0] + self._facility_type, center[1] + badge_radius)
        context.set_source_rgb(1, 1, 1)
        context.stroke()
        return
        context.set_source_rgba(*self._color.as_percents(), 0.75)
        context.arc(center[0], center[1], badge_radius * 0.95, 0, 360)
        context.fill()
        context.restore()
        return

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