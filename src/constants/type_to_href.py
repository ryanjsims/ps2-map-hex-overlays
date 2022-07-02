from facility_types import *
import xml.etree.ElementTree as ET

def type_to_href(type: FacilityTypes):
    if type == FacilityTypes.AMP_STATION:
        return "#amp-fg"
    if type == FacilityTypes.BIO_LAB:
        return "#bio-fg"
    if type == FacilityTypes.TECHPLANT:
        return "#tech-fg"
    if type == FacilityTypes.LARGE_OUTPOST:
        return "#lg-outpost-fg"
    if type == FacilityTypes.SMALL_OUTPOST:
        return "#sm-outpost-fg"
    if type == FacilityTypes.WARPGATE:
        return "#warpgate-fg"
    if type == FacilityTypes.INTERLINK:
        return "#interlink-fg"
    if type == FacilityTypes.CONSTRUCTION_OUTPOST:
        return "#const-outpost-fg"
    if type == FacilityTypes.CONTAINMENT_SITE:
        return "#containment-fg"
    if type == FacilityTypes.TRIDENT:
        return "#trident-fg"
    if type == FacilityTypes.UNDERWATER:
        return "#seapost-fg"

def create_badge(badge: ET.Element):
    if badge:
        for elem in badge:
            badge.remove(elem)
    badge.tag = '{http://www.w3.org/2000/svg}g'
    path = [float(el) for el in badge.attrib['d'].split() if len(el) > 1]
    cx, cy = path[0], path[1]
    type = FacilityTypes(int(path[2] - cx))
    radius = path[3] - cy
    bg = ET.SubElement(badge, '{http://www.w3.org/2000/svg}use')
    fg = ET.SubElement(badge, '{http://www.w3.org/2000/svg}use')
    bg.set("x", str(cx))
    bg.set("y", str(cy))
    bg.set("transform-origin", str(cx) + " " + str(cy))
    bg.set("transform", "translate({0} {0}) scale({1})".format(-radius, abs(2 * radius / 100)))
    for item in bg.attrib:
        fg.set(item, bg.get(item))
    bg.set("href", "#facility-bg")
    bg.set("fill", "rgb(61.960784%,4.313725%,5.882353%)")
    fg.set("href", type_to_href(type))
    badge.attrib = {}

def convert():
    tree = ET.parse("../../svg/oshur copy.svg")
    root = tree.getroot()
    badges = []
    for elem in root[1]:
        if elem.attrib["style"] == "fill:none;stroke-width:1.2;stroke-linecap:butt;stroke-linejoin:miter;stroke:rgb(100%,100%,100%);stroke-opacity:1;stroke-miterlimit:10;":
            badges.append(elem)
    
    for badge in badges:
        create_badge(badge)
    
    tree.write("oshur_badges.svg")

if __name__ == "__main__":
    convert()