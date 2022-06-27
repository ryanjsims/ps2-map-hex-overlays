from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
import dearpygui.dearpygui as dpg
import json

from cube_hex import CubeHex
from map import Map
from constants.zone_ids import ZoneHexSize


def get_numeric(prompt):
    sign = 1
    val = input(prompt)
    if val.lower().startswith("d"):
        return None
    if val.startswith("-"):
        sign = -1
        val = val[1:]
    while not val.isnumeric():
        sign = 1
        val = input(prompt)
        if val.lower().startswith("d"):
            return None
        if val.startswith("-"):
            sign = -1
            val = val[1:]
    return sign * int(val)
        

def get_hexes():
    r = get_numeric("R? (Blue) ")
    if r is None:
        return []
    s_range = input("S range? (Red)")
    if(s_range.lower().startswith("d")):
        return []
    s_strvals = s_range.split(",")
    s_vals = []
    for val in s_strvals:
        if ":" in val:
            val_range = val.split(":")
            s_vals.extend(range(int(val_range[0]), int(val_range[1]) + 1))
        else:
            s_vals.append(int(val))
    return [(-r-s, r, s) for s in s_vals]
    

with open(Path("data") / "oshur.json") as f:
    facilities: List[dict] = json.load(f)

regions = {}

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

hexes: List[List[DrawingHex]] = None

def draw_hexgrid(origin: Tuple[float, float], hexes: List[List[DrawingHex]]):
    for row in hexes:
        for hex in row:
            dpg.draw_polygon(hex.vertices(ZoneHexSize.OSHUR, transform=Map.world_to_map, offset=origin), color=hex.color(), tag=str(hex))
            if hex._r == 0 and hex._s == 0:
                dpg.draw_polygon(hex.vertices(ZoneHexSize.OSHUR, transform=Map.world_to_map, offset=origin), color=hex.color(), fill=(255, 0, 0, 64))

def hex_grid_click(sender, app_data):
    hex = CubeHex.from_pixel(
        Map.map_to_world(dpg.get_drawing_mouse_pos(), offsets=(-512, -512)),
        ZoneHexSize.OSHUR
    )
    drawhex = hexes[hex._r + len(hexes) // 2][hex._s + len(hexes[0]) // 2]
    drawhex.toggle_select()
    dpg.configure_item(str(drawhex), color=drawhex.color())

selecting = False
offset = [0, 0]
drag_start = [0, 0]
scale = 1
last_hover_time = 0

def hex_grid_drag(sender, app_data):
    global last_hover_time
    if datetime.now() - last_hover_time > timedelta(milliseconds=50):
        return
    if app_data[0] == 0:
        global selecting, offset, scale
        raw_pos = dpg.get_drawing_mouse_pos()
        transformed_pos = [(1 / scale) * (val - offset[i]) for i, val in enumerate(raw_pos)]
        hex = CubeHex.from_pixel(
            Map.map_to_world(transformed_pos, offsets=(-512, -512)),
            ZoneHexSize.OSHUR
        )
        drawhex = hexes[hex._r + len(hexes) // 2][hex._s + len(hexes[0]) // 2]
        if app_data[1] == 0:
            selecting = not drawhex._selected
        
        if selecting != drawhex._selected:
            drawhex.toggle_select()
            dpg.configure_item(str(drawhex), color=drawhex.color(), fill=drawhex.fill())
    elif app_data[0] == 2:
        global drag_start, offset, scale
        if app_data[1] == 0:
            drag_start = dpg.get_drawing_mouse_pos()
            return
        x, y = dpg.get_drawing_mouse_pos()
        if x - drag_start[0] != 0 or y - drag_start[1] != 0:
            offset[0] += x - drag_start[0]
            offset[1] += y - drag_start[1]
            drag_start = [x, y]
            dpg.apply_transform("root node", dpg.create_translation_matrix(offset) * dpg.create_scale_matrix([scale, scale]))

def hex_grid_hovered(sender, app_data):
    global last_hover_time
    last_hover_time = datetime.now()


def zoom(sender, app_data):
    global offset, scale
    if scale <= 0.5:
        return
    if scale > 3:
        return
    scale += 0.05 * scale * app_data
    dpg.apply_transform("root node", dpg.create_translation_matrix(offset) * dpg.create_scale_matrix([scale, scale]))

def clear(sender=None, app_data=None, user_data=None, keep_fill=False):
    global hexes
    for row in hexes:
        for hex in row:
            if hex._selected:
                hex.toggle_select()
                dpg.configure_item(str(hex), color=hex.color())
                if not keep_fill:
                    dpg.configure_item(str(hex), fill=hex.fill())

facility_index = 0

def prev_region(sender, app_data):
    global facilities, regions, hexes, facility_index
    region = {"name": facilities[facility_index]["facility_name"], "hexes": []}
    for row in hexes:
        for hex in row:
            if hex._selected:
                region["hexes"].append([hex._q, hex._r, hex._s])
    regions[facilities[facility_index]["map_region_id"]] = region
    clear()
    facility_index -= 1
    region = regions[facilities[facility_index]["map_region_id"]]
    for _, r, s in region["hexes"]:
        hex = hexes[r + len(hexes) // 2][s + len(hexes[0]) // 2]
        hex._selected = True
        dpg.configure_item(str(hex), color=hex.color(), fill=hex.fill())
    dpg.set_value("region name", facilities[facility_index]["facility_name"])

def next_region(sender, app_data):
    global facilities, regions, hexes, facility_index
    region = {"name": facilities[facility_index]["facility_name"], "hexes": []}
    for row in hexes:
        for hex in row:
            if hex._selected:
                region["hexes"].append([hex._q, hex._r, hex._s])
    regions[facilities[facility_index]["map_region_id"]] = region
    facility_index += 1
    dpg.set_value("region name", facilities[facility_index]["facility_name"])
    clear(keep_fill=True)
    if facilities[facility_index]["map_region_id"] in regions:
        region = regions[facilities[facility_index]["map_region_id"]]
        for _, r, s in region["hexes"]:
            hex = hexes[r + len(hexes) // 2][s + len(hexes[0]) // 2]
            hex._selected = True
            dpg.configure_item(str(hex), color=hex.color(), fill=hex.fill())

def save(sender, app_data):
    global regions
    with open("new_oshur.json") as f:
        json.dump(regions, f)
    
def main():
    dpg.create_context()
    dpg.create_viewport(title="Oshur Hex Editor", width=1280, height=1280)
    width, height, channels, data = dpg.load_image('new_oshur.png')
    global hexes, facilities, facility_index
    hexes = [[DrawingHex.from_axial_rs(r, s) for s in range(-50, 51)] for r in range(-50, 51)]
    hexes[len(hexes) // 2][len(hexes[0]) // 2].fill((255, 0, 0, 255))

    with dpg.texture_registry():
        dpg.add_static_texture(width, height, data, tag="image_id")
    
    with dpg.item_handler_registry(tag="clear handler"):
        dpg.add_item_clicked_handler(callback=clear)
    
    with dpg.item_handler_registry(tag="next handler"):
        dpg.add_item_clicked_handler(callback=next_region)
    
    with dpg.item_handler_registry(tag="prev handler"):
        dpg.add_item_clicked_handler(callback=prev_region)
    
    with dpg.item_handler_registry(tag="save handler"):
        dpg.add_item_clicked_handler(callback=save)

    with dpg.handler_registry():
        dpg.add_mouse_down_handler(callback=hex_grid_drag)
        dpg.add_mouse_wheel_handler(callback=zoom)

    with dpg.item_handler_registry(tag="hex grid handler"):
        dpg.add_item_hover_handler(callback=hex_grid_hovered)
        
    with dpg.value_registry():
        dpg.add_string_value(default_value="", tag="region name")

    with dpg.window(label="Oshur Hex Editor", tag="Primary Window"):
        with dpg.drawlist(width=1024, height=1024, tag="hex grid"):
            with dpg.draw_node(tag="root node"):
                dpg.draw_image("image_id", (1, 2), (1024, 1025), uv_min=(0.03, 0.03), uv_max=(0.97, 0.97))
                dpg.draw_line((0, 0), (0, 1023))
                dpg.draw_line((0, 1023), (1023, 1023))
                dpg.draw_line((1023, 1023), (1023, 0))
                dpg.draw_line((1023, 0), (0, 0))
                draw_hexgrid((-4096, 4096), hexes)
        dpg.add_text(label="Current Region Name", source="region name", show_label=True)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Next Region", width=256, height=64, tag="next")
            dpg.add_button(label="Previous Region", width=256, height=64, tag="prev")
            dpg.add_button(label="Clear Selection", width=256, height=64, tag="clear")
            dpg.add_button(label="Save", width=256, height=64, tag="save")
    
    dpg.bind_item_handler_registry("next", "next handler")
    dpg.bind_item_handler_registry("prev", "prev handler")
    dpg.bind_item_handler_registry("clear", "clear handler")
    dpg.bind_item_handler_registry("save", "save handler")
    dpg.bind_item_handler_registry("hex grid", "hex grid handler")

    dpg.set_value("region name", facilities[facility_index]["facility_name"])
    
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()
    
    return
    for i, facility in enumerate(facilities.values()):
        if len(facility["hexes"]) != 0:
            continue
        print(facility["name"], len(facilities) - i)
        hexes = get_hexes()
        while len(hexes) != 0:
            facility["hexes"].extend(hexes)
            hexes = get_hexes()

    with open("oshur_hexes.json", "w") as f:
        json.dump(facilities, f, indent=4)


if __name__ == "__main__":
    main()
