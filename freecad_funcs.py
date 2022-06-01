from typing import Union

import FreeCAD
import Part

def rectangle_face(
    center: FreeCAD.Vector,
    bx: Union[float, int],
    by: Union[float, int],
    ):

    v1, v2, v3, v4 = rectangle_vertexes(center, bx, by)
    return Part.Face(Part.makePolygon([v1, v2, v3, v4, v1]))

def rectangle_vertexes(
                       center: FreeCAD.Vector,
                       bx: Union[float, int],
                       by: Union[float, int],
                       ):
    dx = bx / 2
    dy = by / 2
    v1 = center.add(FreeCAD.Vector(-dx, -dy, 0))
    v2 = center.add(FreeCAD.Vector(dx, -dy, 0))
    v3 = center.add(FreeCAD.Vector(dx, dy, 0))
    v4 = center.add(FreeCAD.Vector(-dx, dy, 0))
    return [v1, v2, v3, v4]

def column_shape(
    width: float,
    height: float,
    N: int,
    M: int,
    main_diameter: int,
    tie_diameter: int = 10,
    cover: int = 40,
    center: FreeCAD.Vector = FreeCAD.Vector(0, 0, 0),
):
    rect = rectangle_face(center, width, height)
    c = cover + tie_diameter + main_diameter / 2
    b = width - 2 * (cover + tie_diameter) - main_diameter
    dx = b / (N - 1)
    h = height - 2 * (cover + tie_diameter) - main_diameter
    dy = h / (M - 1)
    x1 = -width / 2 + c
    y1 = -height / 2 + c
    x2 = width / 2 - c
    y2 = height / 2 - c
    circles = []
    radius = main_diameter / 2
    for i in range(N):
        for j in range(M):
            x = -width / 2 + (c + i * dx)
            y = -height / 2 + (c + j * dy)
            if x1 < x < x2 and y1 < y < y2:
                continue
            center = FreeCAD.Vector(x, y, 0)
            circle = Part.makeCircle(radius, center)
            circles.append(circle)
    return Part.makeCompound([rect] + circles)


