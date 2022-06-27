import math

from typing import Dict, List, Optional, Tuple, Union
from queue import SimpleQueue

from cube_hex import CubeHex
from map import Map

from constants.facility_types import FacilityTypes, BADGE_SIZES
from constants.faction_colors import FactionColors
from constants.zone_ids import ZoneID, ZoneHexSize

class Region:
    def __init__(
            self, 
            id: int = 0,
            facility_id: int = 0,
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
        self._facility_id = facility_id
        self._zone_id = zone_id
        self._facility_type = facility_type_id
        self._name = name
        self._color = color
        self.__shape = []
        self.__dirty = True
        self._location = location
        self._connections = connections
    
    def as_embeddable_json(self, regions: Dict[int, 'Region'], offsets, transform_fn=Map.world_to_map) -> Dict[str, Union[int, Tuple[float, float], List[int], Dict[str, float]]]:
        location = transform_fn(self._location, offsets)
        rounded = map(round, location, [2, 2])
        return {
            'name': self._name,
            'location': tuple(rounded),
            'badge': {
                'size': BADGE_SIZES[self._facility_type] * 2
            },
            'facility_id': self._facility_id,
            'facility_type': self._facility_type,
            'linked_facilities': [regions[region_id]._facility_id for region_id in self._connections],
            'orig_linked_facilities': [regions[region_id]._facility_id for region_id in self._connections],
        }
    
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
                    edge = hex.edge(dir, ZoneHexSize.by_id(self._zone_id))
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
