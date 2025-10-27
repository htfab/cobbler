#!/usr/bin/env python3

import itertools
from math import pi, cos, sin, tan, atan
from svgpathtools import Path, Line, CubicBezier, Arc

# Description of Caravel die & pads
# Warning: pad numbers don't correspond to QFN pin numbering
DIE_WIDTH = 3.6
DIE_HEIGHT = 5.2
DIE_ORIGIN_X = DIE_WIDTH / 2
DIE_ORIGIN_Y = DIE_HEIGHT / 2
PAD_CENTERS = [
    (-1.729785, -2.2195), (-1.7294, -2.0035), (-1.7294, -1.7925), (-1.7294, -1.5815), (-1.729785, -1.3705), (-1.729785, -1.1545),
    (-1.729785, -0.9385), (-1.729785, -0.7225), (-1.729785, -0.5065), (-1.729785, -0.2905), (-1.729785, -0.0745), (-1.7294, 0.1415),
    (-1.7294, 0.3525), (-1.729785, 0.5635), (-1.729785, 0.7795), (-1.729785, 0.9955), (-1.729785, 1.2115), (-1.729785, 1.4275),
    (-1.729785, 1.6435), (-1.7294, 2.0055), (-1.7294, 2.2165), (-1.3625, 2.5294), (-1.0935, 2.5294), (-0.8245, 2.529785),
    (-0.5505, 2.5294), (-0.2815, 2.529785), (-0.0075, 2.529785), (0.2665, 2.529785), (0.5405, 2.529785), (0.8145, 2.529785),
    (1.0885, 2.5294), (1.3575, 2.5294), (1.729785, 2.0565), (1.729785, 1.8305), (1.729785, 1.6055), (1.729785, 1.3795),
    (1.729785, 1.1545), (1.729785, 0.9295), (1.729785, 0.7035), (1.7294, 0.4785), (1.7294, 0.2575), (1.7294, 0.0375),
    (1.729785, -0.1825), (1.729785, -0.4085), (1.729785, -0.6335), (1.729785, -0.8595), (1.729785, -1.0845), (1.729785, -1.3095),
    (1.7294, -1.5355), (1.729785, -1.7555), (1.7294, -1.9815), (1.729785, -2.2015), (1.3785, -2.529785), (1.1215, -2.5294),
    (0.8695, -2.529785), (0.6125, -2.529785), (0.1675, -2.529785), (-0.0895, -2.5294), (-0.3415, -2.529785), (-0.5995, -2.529785),
    (-0.8565, -2.529785), (-1.1135, -2.529785), (-1.3705, -2.529785),
]
GROUND_PADS = [3, 12, 21, 24, 30, 39, 40, 53, 57]
PAD_SIZE = 0.06

# Description of footprint to generate
FP_WIDTH = 15
FP_HEIGHT = 17
FP_ORIGIN_X = FP_WIDTH / 2
FP_ORIGIN_Y = FP_HEIGHT / 2

# Description of pattern to generate
LANDING_PADS = 72
LP_PHI1 = 0.07 * pi
LP_PHI2 = 0.09 * pi

# Bond wires
BOND_MAP = [
    *range(26, 47),
    *range(49, 60),
    *(*range(63, 72), *range(0, 11)),
    *range(13, 24),
]

# Wires to footprint edge
EDGE_RASTER = 1
LEFT_PAD_COUNT = 16
BOTTOM_PAD_COUNT=16
RIGHT_PAD_COUNT = 16
TOP_PAD_COUNT = 16

LEFT_PADS = [(-FP_ORIGIN_X, ((LEFT_PAD_COUNT-1)/2-i)*EDGE_RASTER) for i in range(LEFT_PAD_COUNT)]
BOTTOM_PADS = [((i-(BOTTOM_PAD_COUNT-1)/2)*EDGE_RASTER, -FP_ORIGIN_Y) for i in range(BOTTOM_PAD_COUNT)]
RIGHT_PADS = [(FP_ORIGIN_X, (i-(RIGHT_PAD_COUNT-1)/2)*EDGE_RASTER) for i in range(RIGHT_PAD_COUNT)]
TOP_PADS = [(((TOP_PAD_COUNT-1)/2-i)*EDGE_RASTER, FP_ORIGIN_Y) for i in range(TOP_PAD_COUNT)]
EDGE_PADS = [
    *LEFT_PADS,
    *BOTTOM_PADS,
    *RIGHT_PADS,
    *TOP_PADS,
]

EDGE_MAP = [
    *range(61, 64), *range(0, 18), *range(19, 61),
]

BOND_MAP_REVERSE = {j: i for i, j in enumerate(BOND_MAP)}
GROUND_FINGERS = {i for i in range(LANDING_PADS) if BOND_MAP_REVERSE.get(i) in GROUND_PADS + [None]}


def line_segment(dx, dy):
    return Line(start=0j, end=complex(dx, dy))

def bezier_segment(dx, dy, phi):
    theta = atan(tan(phi)*2/3)
    return CubicBezier(
        start=0j,
        control1=complex(dx/3*cos(theta)-dy/2*sin(theta), dy/3*cos(theta)+dx/2*sin(theta)),
        control2=complex(dx-dx/3*cos(theta)-dy/2*sin(theta), dy-dy/3*cos(theta)+dx/2*sin(theta)),
        end=complex(dx, dy))

def join_segments(*segments):
    pos = 0j
    path = Path()
    for segment in segments:
        segment = segment.translated(pos)
        pos = segment.end
        path.append(segment)
    return path

def rectangle(cx, cy, w, h):
    return join_segments(
        line_segment(-w, 0),
        line_segment(0, h),
        line_segment(w, 0),
        line_segment(0, -h)
    ).translated(complex(cx+w/2, cy-h/2))

def bezier_rectangle(cx, cy, w, h, r, phi1, phi2):
    return join_segments(
        bezier_segment(r*(sin(phi2)-cos(phi1)), r*(-cos(phi2)+sin(phi1)), (pi/2-phi1-phi2)/2),
        bezier_segment(-w-2*r*sin(phi2), 0, phi2),
        bezier_segment(r*(-cos(phi1)+sin(phi2)), r*(-sin(phi1)+cos(phi2)), (pi/2-phi1-phi2)/2),
        bezier_segment(0, h+2*r*sin(phi1), phi1),
        bezier_segment(r*(-sin(phi2)+cos(phi1)), r*(cos(phi2)-sin(phi1)), (pi/2-phi1-phi2)/2),
        bezier_segment(w+2*r*sin(phi2), 0, phi2),
        bezier_segment(r*(cos(phi1)-sin(phi2)), r*(sin(phi1)-cos(phi2)), (pi/2-phi1-phi2)/2),
        bezier_segment(0, -h-2*r*sin(phi1), phi1)
    ).translated(complex(cx+w/2+r*cos(phi1), cy-h/2-r*sin(phi1)))

def rounded_rectangle(cx, cy, w, h, r):
    # r is added to the rectangle size
    return bezier_rectangle(cx, cy, w, h, r, 0, 0)

def polygon(*points):
    path = Path()
    for p, q in itertools.pairwise(points):
        path.append(Line(start=p, end=q))
    return path

def circle(cx, cy, r):
    return Path(
        Arc(start=complex(cx+r, cy), radius=complex(r, r), rotation=0, large_arc=0, sweep=0, end=complex(cx, cy-r)),
        Arc(start=complex(cx, cy-r), radius=complex(r, r), rotation=0, large_arc=0, sweep=0, end=complex(cx-r, cy)),
        Arc(start=complex(cx-r, cy), radius=complex(r, r), rotation=0, large_arc=0, sweep=0, end=complex(cx, cy+r)),
        Arc(start=complex(cx, cy+r), radius=complex(r, r), rotation=0, large_arc=0, sweep=0, end=complex(cx+r, cy))
    )


die_rect = rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT)
ground_pad = rounded_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 0.15)
thermal_bridges_masked = [rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH+1.7, 0.3),
                          rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, 0.3, DIE_HEIGHT+1.7)]
thermal_bridges = [rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH+0.6, 0.3),
                   rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, 0.3, DIE_HEIGHT+0.6)]
mask_ring_inner = rounded_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 0.3)
ground_ring_inner = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 0.5, LP_PHI1, LP_PHI2)
ground_ring_mid = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 0.65, LP_PHI1, LP_PHI2)
ground_ring_outer = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 0.8, LP_PHI1, LP_PHI2)
finger_ring_inner = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 1.0, LP_PHI1, LP_PHI2) 
mask_ring_outer = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 1.1, LP_PHI1, LP_PHI2)
finger_ring_bond = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 1.4, LP_PHI1, LP_PHI2)
finger_ring_outer = bezier_rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, DIE_WIDTH, DIE_HEIGHT, 1.7, LP_PHI1, LP_PHI2)
finger_circle = circle(FP_ORIGIN_X, FP_ORIGIN_Y, 5.4)
trace_width = 5.4 * 2*pi / (2*LANDING_PADS)
footprint_rect = rectangle(FP_ORIGIN_X, FP_ORIGIN_Y, FP_WIDTH, FP_HEIGHT)


def stripe_coord(ring, index):
    phi = index/(4*LANDING_PADS)*2*pi
    r = 10
    seg = line_segment(r*cos(phi), -r*sin(phi)).translated(complex(FP_ORIGIN_X, FP_ORIGIN_Y))
    isc = ring.intersect(seg)
    assert len(isc) == 1
    return seg.point(isc[0][1][0])
    
def fingers(ring_inner, ring_outer):
    f = []
    for i in range(LANDING_PADS):
        f.append(polygon(
            stripe_coord(ring_inner, 4*i-1),
            stripe_coord(ring_outer, 4*i-1),
            stripe_coord(ring_outer, 4*i+1),
            stripe_coord(ring_inner, 4*i+1),
        ))
    return f


landing_pads = []
for i in range(LANDING_PADS):
    landing_pads.append(stripe_coord(finger_ring_bond, 4*i))

fingers_no_mask = fingers(mask_ring_outer, finger_ring_outer)
fingers_ground_no_mask = fingers(ground_ring_mid, finger_ring_outer)
fingers_mask = fingers(finger_ring_inner, finger_circle)
fingers_ground_mask = fingers(ground_ring_mid, finger_circle)
fingers_ground_mask2 = fingers(ground_ring_mid, mask_ring_outer)

pad_centers = [complex(FP_ORIGIN_X+x, FP_ORIGIN_Y+y) for x, y in PAD_CENTERS]
finger_caps = [complex(FP_ORIGIN_X+5.4*cos(i/LANDING_PADS*2*pi), FP_ORIGIN_Y-5.4*sin(i/LANDING_PADS*2*pi)) for i in range(LANDING_PADS)]
edge_pads = [complex(FP_ORIGIN_X+x, FP_ORIGIN_Y-y) for x, y in EDGE_PADS]

edge_lines = []
center = complex(FP_ORIGIN_X, FP_ORIGIN_Y)
for i in range(len(PAD_CENTERS)):
    start = finger_caps[BOND_MAP[i]]
    end = edge_pads[EDGE_MAP[i]]
    control1 = (start-center) * 1.2 + center
    control2 = (end-center) * 1 + center
    line = Path(CubicBezier(start=start, control1=control1, control2=control2, end=end))
    edge_lines.append(line)


with open("preview.svg", "w") as f:
    print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FP_WIDTH} {FP_HEIGHT}" width="{FP_WIDTH}mm" height="{FP_HEIGHT}mm">', file=f)
    print(f'<path d="{footprint_rect.d()}" fill="#008000" />', file=f)
    print(f'<path d="{finger_ring_outer.d()}" fill="#aa8800" />', file=f)
    print(f'<path d="{mask_ring_outer.d()}" fill="#008000" />', file=f)
    for i in range(LANDING_PADS):
        if i in GROUND_FINGERS:
            print(f'<path d="{fingers_ground_mask[i].d()}" fill="#55d400" />', file=f)
            print(f'<path d="{fingers_ground_no_mask[i].d()}" fill="#ffff00" />', file=f)
            print(f'<path d="{fingers_ground_mask2[i].d()}" fill="#55d400" />', file=f)
        else:
            print(f'<path d="{fingers_mask[i].d()}" fill="#55d400" />', file=f)
            print(f'<path d="{fingers_no_mask[i].d()}" fill="#ffff00" />', file=f)
    print(f'<path d="{ground_ring_outer.d()}" fill="#55d400" />', file=f)
    print(f'<path d="{ground_ring_inner.d()}" fill="#008000" />', file=f)
    print(f'<path d="{mask_ring_inner.d()}" fill="#aa8800" />', file=f)
    for r in thermal_bridges_masked:
        print(f'<path d="{r.d()}" fill="#55d400" />', file=f)
    for r in thermal_bridges:
        print(f'<path d="{r.d()}" fill="#ffff00" />', file=f)
    print(f'<path d="{ground_pad.d()}" fill="#ffff00" />', file=f)
    print(f'<path d="{die_rect.d()}" fill="#999999" />', file=f)
    for i, j in enumerate(BOND_MAP):
        if j is not None:
            print(f'<circle cx="{pad_centers[i].real}" cy="{pad_centers[i].imag}" r="{PAD_SIZE/2}" fill="#333333" />', file=f)
            print(f'<circle cx="{landing_pads[j].real}" cy="{landing_pads[j].imag}" r="{PAD_SIZE/2}" fill="#333333" />', file=f)
            print(f'<line x1="{pad_centers[i].real}" y1="{pad_centers[i].imag}" x2="{landing_pads[j].real}" y2="{landing_pads[j].imag}" stroke="#333333" stroke-width="0.02" />', file=f)
    for pt in finger_caps:
        print(f'<circle cx="{pt.real}" cy="{pt.imag}" r="{trace_width/2}" fill="#55d400" />', file=f)
    for pt in edge_pads:
        print(f'<circle cx="{pt.real}" cy="{pt.imag}" r="{trace_width/2}" fill="#55d400" />', file=f)
    for line in edge_lines:
        print(f'<path d="{line.d()}" stroke="#55d400" fill="none" stroke-width="{trace_width}" />', file=f)
    print(f'<path d="{finger_circle.d()}" stroke="#ffffff" fill="none" stroke-width="0.05" />', file=f)
    print('</svg>', file=f)

with open("copper.svg", "w") as f:
    print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FP_WIDTH} {FP_HEIGHT}" width="{FP_WIDTH}mm" height="{FP_HEIGHT}mm">', file=f)
    print(f'<path d="{footprint_rect.d()}" fill="#e0e0ff" />', file=f)
    for i in range(LANDING_PADS):
        if i in GROUND_FINGERS:
            print(f'<path d="{fingers_ground_mask[i].d()}" fill="#000000" />', file=f)
            print(f'<path d="{fingers_ground_mask2[i].d()}" fill="#000000" />', file=f)
        else:
            print(f'<path d="{fingers_mask[i].d()}" fill="#000000" />', file=f)
    print(f'<path d="{ground_ring_outer.d()}" fill="#000000" />', file=f)
    print(f'<path d="{ground_ring_inner.d()}" fill="#ffc0c0" />', file=f)
    print(f'<path d="{ground_pad.d()}" fill="#000000" />', file=f)
    for r in thermal_bridges_masked:
        print(f'<path d="{r.d()}" fill="#000000" />', file=f)
    for r in thermal_bridges:
        print(f'<path d="{r.d()}" fill="#000000" />', file=f)
    for pt in finger_caps:
        print(f'<circle cx="{pt.real}" cy="{pt.imag}" r="{trace_width/2}" fill="#000000" />', file=f)
    for pt in edge_pads:
        print(f'<circle cx="{pt.real}" cy="{pt.imag}" r="{trace_width/2}" fill="#000000" />', file=f)
    for line in edge_lines:
        print(f'<path d="{line.d()}" stroke="#000000" fill="none" stroke-width="{trace_width}" />', file=f)
    print('</svg>', file=f)

with open("mask.svg", "w") as f:
    print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FP_WIDTH} {FP_HEIGHT}" width="{FP_WIDTH}mm" height="{FP_HEIGHT}mm">', file=f)
    print(f'<path d="{footprint_rect.d()}" fill="#e0e0ff" />', file=f)
    print(f'<path d="{finger_ring_outer.d()}" fill="#000000" />', file=f)
    print(f'<path d="{mask_ring_outer.d()}" fill="#ffc0c0" />', file=f)
    print(f'<path d="{mask_ring_inner.d()}" fill="#000000" />', file=f)
    print('</svg>', file=f)

with open("silkscreen.svg", "w") as f:
    print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FP_WIDTH} {FP_HEIGHT}" width="{FP_WIDTH}mm" height="{FP_HEIGHT}mm">', file=f)
    print(f'<path d="{footprint_rect.d()}" fill="#e0e0ff" />', file=f)
    print(f'<path d="{finger_circle.d()}" stroke="#000000" fill="none" stroke-width="0.05" />', file=f)
    print('</svg>', file=f)

with open("user.svg", "w") as f:
    print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FP_WIDTH} {FP_HEIGHT}" width="{FP_WIDTH}mm" height="{FP_HEIGHT}mm">', file=f)
    print(f'<path d="{footprint_rect.d()}" fill="#e0e0ff" />', file=f)
    print(f'<path d="{die_rect.d()}" stroke="#000000" fill="none" stroke-width="0.02" stroke-linecap="round" stroke-linejoin="round" />', file=f)
    for i, j in enumerate(BOND_MAP):
        if j is not None:
            print(f'<circle cx="{pad_centers[i].real}" cy="{pad_centers[i].imag}" r="{PAD_SIZE/2}" fill="#000000" />', file=f)
            print(f'<circle cx="{landing_pads[j].real}" cy="{landing_pads[j].imag}" r="{PAD_SIZE/2}" fill="#000000" />', file=f)
            print(f'<line x1="{pad_centers[i].real}" y1="{pad_centers[i].imag}" x2="{landing_pads[j].real}" y2="{landing_pads[j].imag}" stroke="#000000" stroke-width="0.02" />', file=f)
    print('</svg>', file=f)

