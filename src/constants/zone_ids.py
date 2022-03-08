from enum import IntEnum, Enum

class ZoneID(IntEnum):
    INDAR = 2
    SEARHUS = 3
    HOSSIN = 4
    AMERISH = 6
    ESAMIR = 8
    OSHUR = 344
    NEXUS = 10
    TUTORIAL = 95
    TUTORIAL_ISLAND = 14
    TUTORIAL_2 = 364
    VR_NC = 96
    VR_TR = 97
    VR_VS = 98
    SANCTUARY = 339
    DESOLATION = 338

class ZoneHexSize(float, Enum):
    OSHUR = 57.75
    INDAR = 115.5
    HOSSIN = INDAR
    AMERISH = INDAR
    ESAMIR = INDAR

    def by_id(zone_id: ZoneID):
        if zone_id == ZoneID.OSHUR:
            return ZoneHexSize.OSHUR
        if zone_id == ZoneID.INDAR:
            return ZoneHexSize.INDAR
        if zone_id == ZoneID.AMERISH:
            return ZoneHexSize.AMERISH
        if zone_id == ZoneID.HOSSIN:
            return ZoneHexSize.HOSSIN
        if zone_id == ZoneID.ESAMIR:
            return ZoneHexSize.ESAMIR
        raise IndexError(f"ZoneHexSize: {zone_id}'s hex size is unknown/not implemented")