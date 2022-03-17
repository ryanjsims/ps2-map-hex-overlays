import os, shutil
import sys

z_to_lod = {
    5: "lod0",
    4: "lod1",
    3: "lod2",
    2: "lod3",
}

for z in range(2, 6):
    divisor = int(32 / (2 ** (z - 2)))
    offset = 2 ** (z - 1)

    #32 2 16 3 8 4 4 5
    
    for dir in ["oshur"]:
        coords = []
        for filename in os.listdir(f"tiles/{dir}/{z}"):
            fields = filename.split("_")
            x = fields[1]
            if len(x) != 3:
                continue
            y = fields[2].split(".")[0]
            coords.append((x, y))

        for coord in coords:
            transform = (int(int(coord[0]) / divisor) + offset, abs(int(int(coord[1]) / divisor) - (offset - 1)))
            # print(f"/home/ryan/temp/magick oshur/{lod}/tile_{coord[0]}_{coord[1]}.png -flip oshur/{lod}/tile_{transform[0]}_{transform[1]}.png")
            # sys.stdout.flush()
            os.system(f"mv tiles/{dir}/{z}/tile_{coord[0]}_{coord[1]}.png tiles/{dir}/{z}/tile_{transform[0]}_{transform[1]}.png")
        
