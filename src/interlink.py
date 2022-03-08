import cairo
import math

radius = 30
start_angle, end_angle = -25, 115
length = 20
center = (50, 50)
antenna_rad = 3.5
width = 3

# length of chord = 2 × r × sine (C/2)

with cairo.SVGSurface("../svg/Interlink.svg", 100, 100) as surface:
    context = cairo.Context(surface)
    context.set_source_rgb(1, 1, 1)
    context.set_line_width(width)
    chord_len = 2 * radius * math.sin(math.radians(end_angle - start_angle) / 2)
    dist = math.sqrt(radius ** 2 - ((chord_len ** 2) / 4))
    vec = (dist * math.cos(math.radians(135)), -dist * math.sin(math.radians(135)))
    arc_center = (center[0] + vec[0], center[1] + vec[1])
    context.arc(arc_center[0], arc_center[1], radius, math.radians(start_angle), math.radians(end_angle))
    context.fill()
    context.move_to(*center)
    context.line_to(center[0] + length * math.cos(math.radians(135)), center[1] - length * math.sin(math.radians(135)))
    context.stroke()
    context.arc(center[0] + length * math.cos(math.radians(135)), center[1] - length * math.sin(math.radians(135)), antenna_rad, math.radians(0), math.radians(360))
    context.fill()

with cairo.SVGSurface("icon_bg.svg", 100, 100) as surface:
    context = cairo.Context(surface)
    context.set_source_rgb(0, 0, 0)
    context.arc(center[0], center[1], 47.5, 0, 360)
    context.set_line_width(5)
    context.fill()
    
    context.arc(center[0], center[1], 47.5, 0, 360)
    context.set_source_rgb(1, 1, 1)
    context.stroke()