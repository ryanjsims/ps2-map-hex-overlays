import cairo, json
from drawing import CubeHex, Map

with open("../data/hvar.json") as f:
    hvar = [CubeHex(q, r, s) for q, r, s in json.load(f)]

with cairo.SVGSurface("../svg/hvar.svg", 2000, 2000) as surface:
    context = cairo.Context(surface)
    for hex in hvar:
        for dir in range(6):
            if hex.neighbor(dir) not in hvar:
                edge = hex.world_edge(dir)
                offsets = Map.world_to_map((1039.5, 3401))
                context.move_to(Map.world_to_map(edge[0])[0] + offsets[0], Map.world_to_map(edge[0])[1] - offsets[1])
                context.line_to(Map.world_to_map(edge[1])[0] + offsets[0], Map.world_to_map(edge[1])[1] - offsets[1])
                context.stroke()