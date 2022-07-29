import json
import math

with open("../data/NexusRegions_locs.json") as f:
    zone_data = json.load(f)

with open("../data/NexusHexes.json") as f:
    zone_hexes = json.load(f)

facility_id_map = {
    region["facility_id"]: region["map_region_id"] 
    for region in zone_data
}

for region in zone_data:
    if "zone_id" in region:
        del region["zone_id"]
    if "location_y" in region:
        del region["location_y"]
    if "region_boundaries" in region:
        del region["region_boundaries"]
    if "region_boundaries_overflow" in region:
        del region["region_boundaries_overflow"]
    region["facility_links"] = [
        {
            "facility_id_b": facility_id,
            "map_region": {
                "map_region_id": facility_id_map[facility_id]
            }
        } for facility_id in region["facility_links"]
    ]
    region["map_hexes"] = [
        {
            "x": str(-cubehex[2]), 
            "y": str(-cubehex[1] - 1)
        } for cubehex in zone_hexes[region["map_region_id"]]["hexes"]
    ]


zone_cache = {}
zone_cache["map_region_list"] = zone_data
zone_cache["returned"] = len(zone_data)

with open("../cache/nexus_cache.json", "w") as f:
    json.dump(zone_cache, f, separators=(',', ':'))
