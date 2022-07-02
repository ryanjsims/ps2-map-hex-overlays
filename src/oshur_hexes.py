from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
import dearpygui.dearpygui as dpg
import json

from drawing_hex import DrawingHex
from map_region import Region
from map import Map
from constants.zone_ids import ZoneHexSize
from constants.facility_types import FacilityTypes

facilities: List[dict] = []

def load_regions(sender, app_data):
    global facilities
    with open(app_data["file_path_name"]) as f:
        facilities = json.load(f)

def save_regions(sender, app_data):
    with open(app_data["file_path_name"], "w") as f:
        json.dump(facilities, f)


load_regions(None, {"file_path_name": str(Path("data") / "oshur.json")})

regions = {}
regions_by_hex = {}
selecting = False
offset = [0, 0]
drag_start = [0, 0]
scale = 1
last_hover_time = 0
hexes: List[List[DrawingHex]] = None
facility_index = 0
facility_to_link = None


def draw_hexgrid(origin: Tuple[float, float], hexes: List[List[DrawingHex]]):
    for row in hexes:
        for hex in row:
            dpg.draw_polygon(hex.vertices(ZoneHexSize.OSHUR, transform=Map.world_to_map, offset=origin), color=hex.color(), tag=str(hex))
            if hex._r == 0 and hex._s == 0:
                dpg.draw_polygon(hex.vertices(ZoneHexSize.OSHUR, transform=Map.world_to_map, offset=origin), color=hex.color(), fill=(255, 0, 0, 64))


def link_regions(sender, app_data):
    global regions_by_hex, facility_to_link
    hex = DrawingHex.from_pixel(
        Map.map_to_world(dpg.get_drawing_mouse_pos(), offsets=(-512, -512)),
        ZoneHexSize.OSHUR
    )
    if app_data[0] == 1 and str(hex) in regions_by_hex:
        if facility_to_link is None:
            facility_to_link = regions_by_hex[str(hex)]
            dpg.set_value("linking name", facility_to_link["name"])
            map_location = Map.world_to_map((float(facility_to_link["location_x"]), float(facility_to_link["location_z"])), (-4096, 4096))
            map_location = [(1 / scale) * (val - offset[i]) for i, val in enumerate(map_location)]
            dpg.configure_item("new link", p1=map_location, p2=map_location, show=True)
        else:
            regions_by_hex[str(hex)]["facility_links"].append(facility_to_link["facility_id"])
            facility_to_link["facility_links"].append(regions_by_hex[str(hex)]["facility_id"])
            dpg.configure_item("new link", p1=(0, 0), p2=(0, 0), show=False)
            dpg.set_value("linking name", f"{regions_by_hex[str(hex)]['name']} linked to {facility_to_link['name']}")
            facility_to_link = None

def move_link(sender, app_data):
    global facility_to_link
    map_location = [(1 / scale) * (val - offset[i]) for i, val in enumerate(dpg.get_drawing_mouse_pos())]
    world_location = Map.map_to_world(map_location, offsets=(-512, -512))
    dpg.set_value("mouse coords", f"x: {world_location[0]:5.2f} z: {world_location[1]:5.2f}")
    if facility_to_link is None:
        return
    dpg.configure_item("new link", p2=map_location)

def hex_grid_drag(sender, app_data):
    global last_hover_time
    if datetime.now() - last_hover_time > timedelta(milliseconds=50):
        return
    if app_data[0] == 0:
        global selecting, offset, scale
        raw_pos = dpg.get_drawing_mouse_pos()
        transformed_pos = [(1 / scale) * (val - offset[i]) for i, val in enumerate(raw_pos)]
        hex = DrawingHex.from_pixel(
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

def create_region(index):
    global facilities
    return {
        "name": facilities[index]["facility_name"], 
        "hexes": [], 
        "facility_id": facilities[index]["facility_id"], 
        "facility_links": facilities[index]["facility_links"], 
        "location_x": facilities[index]["location_x"],
        "location_z": facilities[index]["location_z"]
    }

def update_region_with_current_selection(index: int):
    global regions, regions_by_hex, facilities
    region_name = facilities[index]["facility_name"]
    map_region_id = facilities[index]["map_region_id"]
    if map_region_id not in regions:
        region = create_region(index)
    else:
        region = regions[map_region_id]
        region["hexes"] = []
    for row in hexes:
        for hex in row:
            if hex._selected:
                region["hexes"].append([hex._q, hex._r, hex._s])
                regions_by_hex[str(hex)] = region
    regions[map_region_id] = region


def load_region(map_region_id: str):
    global facilities, facility_index, regions, hexes
    if map_region_id in regions:
        region = regions[map_region_id]
        for _, r, s in region["hexes"]:
            hex = hexes[r + len(hexes) // 2][s + len(hexes[0]) // 2]
            hex._selected = True
            dpg.configure_item(str(hex), color=hex.color(), fill=hex.fill())
    dpg.set_value("region name", facilities[facility_index]["facility_name"])

def prev_region(sender, app_data):
    global facilities, regions, hexes, facility_index
    update_region_with_current_selection(facility_index)
    clear()
    facility_index = max(0, facility_index - 1)
    load_region(facilities[facility_index]["map_region_id"])

def next_region(sender, app_data):
    global facilities, regions, hexes, facility_index
    update_region_with_current_selection(facility_index)
    clear(keep_fill=True)
    facility_index = min(len(facilities) - 1, facility_index + 1)
    load_region(facilities[facility_index]["map_region_id"])

def save_hexes(sender, app_data):
    global regions
    with open(app_data["file_path_name"], "w") as f:
        json.dump(regions, f)

def load_hexes(sender, app_data):
    global regions, facility_index
    with open(app_data["file_path_name"]) as f:
        new_regions = json.load(f)
        for map_region_id in new_regions:
            if map_region_id not in regions:
                for i, facility in enumerate(facilities):
                    if facility["map_region_id"] == map_region_id:
                        regions[map_region_id] = create_region(i)
                        break
            regions[map_region_id]["hexes"] = new_regions[map_region_id]["hexes"]
    load_region(facilities[facility_index]["map_region_id"])
    while facility_index < len(facilities) - 1:
        next_region(None, None)

def add_or_edit_region(sender, app_data):
    global facilities
    name = dpg.get_value("facility name input")
    ftype = dpg.get_value("facility type input")
    to_edit = {}
    edit_index = None
    max_facility_id = 0
    max_map_region_id = 0
    #{
    #    "zone_id": "334", 
    #    "facility_type_id": str(FacilityTypes[ftype].value),
    #    "facility_name": name,
    #}
    for i, facility in enumerate(facilities):
        if name == facility["facility_name"]:
            to_edit = facility
            edit_index = i
        max_facility_id = max(max_facility_id, int(facility["facility_id"]))
        max_map_region_id = max(max_map_region_id, int(facility["map_region_id"]))
    
    if edit_index is None:
        to_edit["map_region_id"] = str(max_map_region_id + 1)
        to_edit["zone_id"] = "334"
        to_edit["facility_id"] = str(max_facility_id + 1)
        to_edit["facility_name"] = name
        to_edit["facility_links"] = []
    
    to_edit["facility_type_id"] = str(FacilityTypes[ftype].value)
    to_edit["location_x"] = str(dpg.get_value("facility x input"))
    to_edit["location_z"] = str(dpg.get_value("facility z input"))

    if edit_index is None:
        facilities.append(to_edit)
    dpg.set_value("facility name input", "")
    dpg.hide_item("region editor")


def main():
    dpg.create_context()
    dpg.create_viewport(title="Oshur Hex Editor", width=1280, height=1408)
    width, height, channels, data = dpg.load_image('new_oshur.png')
    global hexes, facilities, facility_index
    hexes = [[DrawingHex.from_axial_rs(r, s) for s in range(-50, 51)] for r in range(-50, 51)]
    hexes[len(hexes) // 2][len(hexes[0]) // 2].fill((255, 0, 0, 255))

    with dpg.file_dialog(directory_selector=False, show=False, callback=load_hexes, tag="load hexes file picker", height=512):
        dpg.add_file_extension(".json")
    
    with dpg.file_dialog(directory_selector=False, show=False, callback=save_hexes, tag="save hexes file picker", height=512):
        dpg.add_file_extension(".json")
    
    with dpg.file_dialog(directory_selector=False, show=False, callback=load_regions, tag="load regions file picker", height=512):
        dpg.add_file_extension(".json")
    
    with dpg.file_dialog(directory_selector=False, show=False, callback=save_regions, tag="save regions file picker", height=512):
        dpg.add_file_extension(".json")

    with dpg.texture_registry():
        dpg.add_static_texture(width, height, data, tag="image_id")
    
    with dpg.item_handler_registry(tag="clear handler"):
        dpg.add_item_clicked_handler(callback=clear)
    
    with dpg.item_handler_registry(tag="next handler"):
        dpg.add_item_clicked_handler(callback=next_region)
    
    with dpg.item_handler_registry(tag="prev handler"):
        dpg.add_item_clicked_handler(callback=prev_region)
    
    with dpg.item_handler_registry(tag="hex grid handler"):
        dpg.add_item_hover_handler(callback=hex_grid_hovered)
        dpg.add_item_clicked_handler(callback=link_regions)
        
    with dpg.value_registry():
        dpg.add_string_value(default_value="", tag="region name")
        dpg.add_string_value(default_value="", tag="linking name")
        dpg.add_string_value(default_value="", tag="mouse coords")

    with dpg.handler_registry():
        dpg.add_mouse_down_handler(callback=hex_grid_drag)
        dpg.add_mouse_wheel_handler(callback=zoom)
        dpg.add_mouse_move_handler(callback=move_link)

    with dpg.window(label="Oshur Hex Editor", tag="Primary Window"):
        with dpg.drawlist(width=1024, height=1024, tag="hex grid"):
            with dpg.draw_node(tag="root node"):
                dpg.draw_image("image_id", (1, 2), (1024, 1025), uv_min=(0.03, 0.03), uv_max=(0.97, 0.97))
                dpg.draw_line((0, 0), (0, 1023))
                dpg.draw_line((0, 1023), (1023, 1023))
                dpg.draw_line((1023, 1023), (1023, 0))
                dpg.draw_line((1023, 0), (0, 0))
                draw_hexgrid((-4096, 4096), hexes)
                dpg.draw_line((0, 0), (0, 0), show=False, color=(0, 0, 255, 255), tag="new link")
        
        dpg.add_text(label="Current Region Name", source="region name", show_label=True)
        dpg.add_text(label="Linking Region Name", source="linking name", show_label=True)
        dpg.add_text(label="Mouse World Coordinates", source="mouse coords", show_label=True)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Previous Region", width=256, height=64, tag="prev")
            dpg.add_button(label="Next Region", width=256, height=64, tag="next")
            dpg.add_button(label="Clear Selection", width=256, height=64, tag="clear")
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="Save Hexes...", width=256, height=64, callback=lambda: dpg.show_item("save hexes file picker"))
            dpg.add_button(label="Load Hexes...", width=256, height=64, callback=lambda: dpg.show_item("load hexes file picker"))
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="Save Regions...", width=256, height=64, callback=lambda: dpg.show_item("save regions file picker"))
            dpg.add_button(label="Load Regions...", width=256, height=64, callback=lambda: dpg.show_item("load regions file picker"))
            dpg.add_button(label="Add/Edit Region...", width=256, height=64, callback=lambda: dpg.show_item("region editor"))
    
    with dpg.window(label="Add/Edit Region", show=False, tag="region editor"):
        with dpg.group(horizontal=True):
            dpg.add_text("facility_name")
            dpg.add_input_text(tag="facility name input")
        
        with dpg.group(horizontal=True):
            dpg.add_text("location_x (vertical location)")
            dpg.add_input_float(tag="facility x input")
        
        with dpg.group(horizontal=True):
            dpg.add_text("location_z (horizontal location)")
            dpg.add_input_float(tag="facility z input")
        
        with dpg.group(horizontal=True):
            dpg.add_text("facility type")
            dpg.add_listbox(list((ftype.name for ftype in FacilityTypes)), tag="facility type input")
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="Done", width=256, height=64, callback=add_or_edit_region)
            dpg.add_button(label="Cancel", width=256, height=64, callback=lambda: dpg.hide_item("region editor"))
        
        
    
    dpg.bind_item_handler_registry("next", "next handler")
    dpg.bind_item_handler_registry("prev", "prev handler")
    dpg.bind_item_handler_registry("clear", "clear handler")
    dpg.bind_item_handler_registry("hex grid", "hex grid handler")

    dpg.set_value("region name", facilities[facility_index]["facility_name"])
    
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
