from io import BytesIO
import math
import sys
sys.path.insert(0, "/home/ryan/repos/ps2alerts/map_drawing/lib/")
from DbgPack import AssetManager

from glob import glob
from pathlib import Path, PosixPath
import progressbar
from PIL import Image

test_server = r"/mnt/e/Users/Public/Daybreak Game Company/Installed Games/PlanetSide 2 Test/Resources/Assets"
packs = [Path(p) for p in (glob(test_server + "/Oshur*.pack2"))]

class LoadingBar:
    def __init__(self) -> None:
        self.loading_bar = None

    def callback(self, index, total, path: PosixPath):
        widgets = [progressbar.GranularBar(), '    ', progressbar.FormatLabel("{variables.path:35.35}", new_style=True)]
        if self.loading_bar is None:
            self.loading_bar = progressbar.ProgressBar(max_value=total, max_width=80, widgets=widgets, variables={"path": path.name})
        self.loading_bar.update(index + 1, path=str(path.name))
        return True
        
    def finish(self):
        self.loading_bar.finish()
        self.loading_bar = None


def main():
    print("Loading packs")
    bar = LoadingBar()
    manager = AssetManager(packs, callback=bar.callback)
    bar.finish()
    format = "Oshur_Tile_{:03d}_{:03d}_LOD{:d}.dds"
    saveformat = "tile_{:d}_{:d}.png"
    savepath = Path("/home/ryan/repos/ps2alerts/map_drawing/tiles/oshur/")
    savepath.mkdir(parents=True, exist_ok=True)
    print("Saving tiles...")
    total = len(range(4)) * len(range(-64, 65)) * len(range(-64, 65))
    for lod in range(4):
        for x in range(-64, 65):
            for z in range(-64, 65):
                asset = manager.get_raw(format.format(x, z, lod))
                index = lod * len(range(-64, 65)) * len(range(-64, 65)) + (x + 64) * len(range(-64, 65)) + (z + 64)
                if asset is None:
                    bar.callback(index, total, Path())
                    continue
                
                image = Image.open(BytesIO(asset.get_data()))
                path = savepath / "{}".format(5 - lod)
                path.mkdir(parents=True, exist_ok=True)
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
                image.save(path / saveformat.format(int((x + 64) / math.pow(2, 2 + lod)), int((-z + (64 - math.pow(2, 2 + lod))) / math.pow(2, 2 + lod))))
                bar.callback(index, total, path)

    bar.finish()
    print("Finished")

#
# 2 32   2^5
# 3 16   2^4
# 4 8    2^3
# 5 4    2^2            

if __name__ == "__main__":
    main()