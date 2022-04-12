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
    RELIC = 10
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
    facility_type: 10 for facility_type in MAJOR_FACILITY_TYPES
}

BADGE_SIZES[FacilityTypes.LARGE_OUTPOST] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.85
BADGE_SIZES[FacilityTypes.SMALL_OUTPOST] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.7
BADGE_SIZES[FacilityTypes.CONSTRUCTION_OUTPOST] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.7
BADGE_SIZES[FacilityTypes.RELIC] = BADGE_SIZES[FacilityTypes.WARPGATE] * 0.7
BADGE_SIZES[FacilityTypes.UNKNOWN] = 0

BADGE_HREFS = {
    FacilityTypes.AMP_STATION: "#amp-fg",
    FacilityTypes.BIO_LAB: "#bio-fg",
    FacilityTypes.TECHPLANT: "#tech-fg",
    FacilityTypes.LARGE_OUTPOST: "#lg-outpost-fg",
    FacilityTypes.SMALL_OUTPOST: "#sm-outpost-fg",
    FacilityTypes.WARPGATE: "#warpgate-fg",
    FacilityTypes.INTERLINK: "#interlink-fg",
    FacilityTypes.CONSTRUCTION_OUTPOST: "#const-outpost-fg",
    FacilityTypes.RELIC: "#relic-fg",
    FacilityTypes.CONTAINMENT_SITE: "#containment-fg",
    FacilityTypes.TRIDENT: "#trident-fg",
    FacilityTypes.UNKNOWN: "",
}