import os
import sys
import asyncio
import json
import xml.etree.ElementTree as ET
import cairo
import gi
gi.require_foreign("cairo")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango as pango, PangoCairo as pangocairo

from pathlib import Path
from typing import Dict
from argparse import ArgumentParser

import auraxium
from auraxium import ps2

from cube_hex import CubeHex
from map_region import Region
from map import Map
from path_drawer import pathContext

from constants.zone_ids import ZoneID
from constants.faction_colors import FactionColors
from constants.facility_types import BADGE_SIZES, FacilityTypes, BADGE_HREFS


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
    parser.add_argument("--defs", help="Only output definitions block, no graphics", action="store_true")
    args = parser.parse_args()
    
    service_id = ""
    if not vars(args)["service-id"].startswith("s:"):
        service_id += "s:"
    service_id += vars(args)["service-id"]
        
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
                if "facility_id" not in map_region:
                    facility_id = map_region_id
                    print(map_region["facility_name"])
                    print(map_region_id)
                else:
                    facility_id = int(map_region["facility_id"])
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
                    facility_id=facility_id,
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

        facility_icons = ET.ElementTree(file=f"..{os.path.sep}svg{os.path.sep}facility-icon.svg").getroot()[0]
        embedded_css = open("../css/map_embedded.min.css")
        style = ET.Element("style")
        style.text = embedded_css.read()
        embedded_css.close()
        offsets = (4096, 4096)

        for zone in zones:
            regions = ET.Element("regionJson")
            regionData = {
                "byFacilityIds": {region._facility_id: region.as_embeddable_json(zones[zone], (-offsets[0], offsets[1])) for region in zones[zone].values() if region.get_facility_type() != FacilityTypes.UNKNOWN},
                "regionIdsToFacilityIds": {reg_id: region._facility_id for reg_id, region in zones[zone].items() if region.get_facility_type() != FacilityTypes.UNKNOWN}
            }
            for regionJson in regionData["byFacilityIds"].values():
                for connection_id in regionJson["linked_facilities"]:
                    if regionJson["facility_id"] in regionData["byFacilityIds"][connection_id]["linked_facilities"]:
                        continue
                    regionData["byFacilityIds"][connection_id]["linked_facilities"].append(regionJson["facility_id"])
            regions.text = json.dumps(regionData, separators=(',', ':'))
            with open(f"..{os.path.sep}svg{os.path.sep}{zone}_base.svg", "wb") as surface:
                print("Drawing " + f"..{os.path.sep}svg{os.path.sep}{zone}_base.svg")
                context = pathContext(surface, 2048, 2048)
                context.embed(regions)
                context.embed(style)

                context.enter_defs()
                for icon in facility_icons:
                    context.embed(icon)
                
                for region_id, region in zones[zone].items():
                    if region_id != region._id or region.get_facility_type() == FacilityTypes.UNKNOWN:
                        continue
                    context.id(f"hex-{region._facility_id}")
                    region.draw_outline(context, *offsets)
                    region.draw_lattice_defs(context, *offsets, [zones[zone][link_id] for link_id in region.get_connections()])
                    context.id(f"name-{region._facility_id}")
                    region.draw_name(context, *offsets)

                context.exit_defs()

                if not args.defs:
                    context.enter_group("hex-layer")
                    for region_id, region in zones[zone].items():
                        if region_id != region._id or region.get_facility_type() == FacilityTypes.UNKNOWN:
                            continue
                        context._class("region-TR")
                        context.use(f"#hex-{region._facility_id}")
                        context._finalize()
                    context.exit_group()

                    context.enter_group("lattice-layer")
                    context.set_source_rgba(1, 1, 1, 0.5)
                    for region_id, region in zones[zone].items():
                        if region_id != region._id or region.get_facility_type() == FacilityTypes.UNKNOWN:
                            continue
                        for link_id in region.get_connections():
                            connection = zones[zone][link_id]
                            context._class("bglink-TR")
                            context.use(f"#link-{region._facility_id}-{connection._facility_id}")
                            context._finalize()
                            context._class("link link-TR")
                            context.use(f"#link-{region._facility_id}-{connection._facility_id}")
                            context._finalize()
                    context.exit_group()

                    context.enter_group("badge-layer")
                    for region_id, region in zones[zone].items():
                        if region_id != region._id or region.get_facility_type() == FacilityTypes.UNKNOWN:
                            continue
                        location = Map.world_to_map(region.get_location(), (-offsets[0], offsets[1]))
                        context.id(f"badge-{region._facility_id}")
                        context._class(f"badge-TR")
                        context.use(
                            "#facility-bg",
                            location[0],
                            location[1],
                            BADGE_SIZES[region.get_facility_type()] * 2,
                            BADGE_SIZES[region.get_facility_type()] * 2
                        )
                        context._finalize()
                        context.use(
                            f"{BADGE_HREFS[region.get_facility_type()]}", 
                            location[0],
                            location[1],
                            BADGE_SIZES[region.get_facility_type()] * 2,
                            BADGE_SIZES[region.get_facility_type()] * 2
                        )
                        context._finalize()
                    context.exit_group()

                    context.enter_group("name-layer")
                    for region_id, region in zones[zone].items():
                        if region_id != region._id:
                            continue
                        context._class(f"bgtext bgtext-TR")
                        context.use(f"#name-{region._facility_id}")
                        context._class(f"fgtext")
                        context.use(f"#name-{region._facility_id}")
                    context.exit_group()

                context.write()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())