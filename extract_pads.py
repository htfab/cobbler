#!/usr/bin/env python3

import gdstk
import math

lib = gdstk.read_oas("caravel_2409485e.oas")
ctop = next(cell for cell in lib.cells if cell.name == "caravel_openframe")
padframe = next(cell for cell in ctop.dependencies(False) if "chip_io_openframe" in cell.name)
boundary = next(p for p in padframe.polygons if p.layer == 235 and p.datatype == 4)
(bx1, by1), (bx2, by2) = boundary.bounding_box()
r = lambda x: round(x, 9)
cx, cy, hw, hh = r((bx1+bx2)/2000), r((by1+by2)/2000), r((bx2-bx1)/2000), r((by2-by1)/2000)
padframe.flatten()
pads = [p for p in padframe.polygons if p.layer == 76 and p.datatype == 20]
pad_centers = set((r((x1+x2)/2000-cx), r(cy-(y1+y2)/2000)) for ((x1, y1), (x2, y2)) in [p.bounding_box() for p in pads])
pad_centers = sorted(pad_centers, key=lambda p: math.atan2(*p))
first_index = min(range(len(pad_centers)), key=lambda i: 10*pad_centers[i][0]+pad_centers[i][1])
pad_centers = pad_centers[first_index:] + pad_centers[:first_index]

print(f"DIE_WIDTH = {hw*2}")
print(f"DIE_HEIGHT = {hh*2}")
print("DIE_ORIGIN_X = DIE_WIDTH / 2")
print("DIE_ORIGIN_Y = DIE_HEIGHT / 2")
print("PAD_CENTERS = [")
for x, y in pad_centers:
    print(f"    ({x}, {y}),")
print("]")

