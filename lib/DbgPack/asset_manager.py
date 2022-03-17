import os
from sys import path
from DbgPack.asset2 import Asset2
from DbgPack.hash import crc64
from collections import ChainMap
from dataclasses import dataclass, field
from pathlib import Path, PosixPath
from typing import List, ChainMap as ChainMapType, Callable, Optional

from .abc import AbstractPack, AbstractAsset
from .loose_pack import LoosePack
from .pack1 import Pack1
from .pack2 import Pack2


@dataclass
class AssetManager:
    packs: List[AbstractPack]
    assets: ChainMapType[str, AbstractAsset] = field(repr=False)

    @staticmethod
    def load_pack(path: Path, namelist: List[str] = None):
        if path.is_file():
            if path.suffix == '.pack':
                return Pack1(path)
            elif path.suffix == '.pack2':
                return Pack2(path, namelist=namelist)
        else:
            return LoosePack(path)

    def export_pack2(self, name: str, outdir: Path, raw=False):
        Pack2.export(list(self.assets.values()), name, outdir, raw)

    def __init__(self, paths: List[Path], namelist: List[str] = None, callback: Callable = lambda x, y, z: True):
        self.packs = [AssetManager.load_pack(path, namelist=namelist) for i, path in enumerate(paths) if callback(i, len(paths), path)]
        self.assets = ChainMap(*[p.assets for p in self.packs])

    def __len__(self):
        return len(self.assets)

    def __getitem__(self, item):
        return self.assets[item]

    def __contains__(self, item):
        return item in self.assets

    def __iter__(self):
        return iter(self.assets.values())
    
    def search(self, term: str, suffix: str = ""):
        names = []
        for key in self.assets.values():
            if term.lower() in key.name.lower() and key.name.endswith(suffix):
                names.append(key.name)
        names.sort()
        return names
    
    def get_raw(self, name: str) -> Optional[Asset2]:
        name_hash = crc64(name.encode("ascii"))
        for pack in self.packs:
            assert type(pack) == Pack2
            if name_hash in pack.raw_assets:
                return pack.raw_assets[name_hash]
        return None
    
    def save_raw(self, name: str, dest_dir: str="./") -> bool:
        to_save = self.get_raw(name)
        if to_save is not None:
            try:
                with open(dest_dir + name, "wb") as f:
                    f.write(to_save.get_data())
            except Exception as e:
                print(e)
                return False
            return True
        return False
    
    def export_all_of_magic(self, magic: bytes, callback: Callable = lambda x, y, z: None, suffix: str = None):
        assert len(magic) == 4
        i = 0
        total = 0
        for pack in self.packs:
            total += len(pack.raw_assets)
        for pack in self.packs:
            for namehash, asset in pack.raw_assets.items():
                name = str(namehash) + "." + (suffix if suffix is not None else str(magic, encoding="utf-8").strip().lower())
                if asset.name != '':
                    name = asset.name
                callback(i, total, PosixPath(name))
                i += 1
                data = asset.get_data()
                if data[:4] == magic:
                    if not os.path.exists(pack.name):
                        os.makedirs(pack.name, exist_ok=True)
                    if os.path.exists(pack.name + os.sep + name):
                        continue
                    with open(pack.name + os.sep + name, "wb") as f:
                        f.write(data)
                    
    
    def save(self, key: str):
        with open(key, "wb") as f:
            f.write(self.assets[key].get_data())

    def save_raw_as(self, key: str, dest: str):
        to_save = self.get_raw(key)
        if to_save is not None:
            try:
                with open(dest, "wb") as f:
                    f.write(to_save.get_data())
            except Exception as e:
                print(e)
                return False
            return True
        return False
