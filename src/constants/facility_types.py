from enum import IntEnum

class FacilityTypes(IntEnum):
    UNKNOWN = 0
    AMP_STATION = 2
    BIO_LAB = 3
    TECHPLANT = 4
    LARGE_OUTPOST = 5
    SMALL_OUTPOST = 6
    WARPGATE = 7
    INTERLINK = 8
    CONSTRUCTION_OUTPOST = 9
    CONTAINMENT_SITE = 11,
    TRIDENT = 12

MAJOR_FACILITY_TYPES = [
    FacilityTypes.AMP_STATION, 
    FacilityTypes.BIO_LAB,
    FacilityTypes.CONTAINMENT_SITE,
    FacilityTypes.INTERLINK,
    FacilityTypes.TRIDENT, 
    FacilityTypes.TECHPLANT, 
    FacilityTypes.WARPGATE
]

BADGE_SIZES = {
    facility_type: 6 for facility_type in MAJOR_FACILITY_TYPES
}

BADGE_SIZES[FacilityTypes.LARGE_OUTPOST] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.85
BADGE_SIZES[FacilityTypes.SMALL_OUTPOST] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.7
BADGE_SIZES[FacilityTypes.CONSTRUCTION_OUTPOST] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.7
BADGE_SIZES[FacilityTypes.UNKNOWN] = 0