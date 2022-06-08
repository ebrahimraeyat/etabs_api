from typing import Union
from pathlib import Path

import FreeCAD
import FreeCADGui
import Part

def rectangle_face(
    bx: Union[float, int],
    by: Union[float, int],
    center: FreeCAD.Vector = FreeCAD.Vector(0, 0, 0),
    ):

    v1, v2, v3, v4 = rectangle_vertexes(bx, by, center)
    return Part.Face(Part.makePolygon([v1, v2, v3, v4, v1]))

def rectangle_vertexes(
                       bx: Union[float, int],
                       by: Union[float, int],
                       center: FreeCAD.Vector = FreeCAD.Vector(0, 0, 0),
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
    rect = rectangle_face(width, height, center)
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

def findWidget(
        name: str,
        mw=None,
        ):

    "finds the manager widget, if present"

    import FreeCADGui
    from PySide import QtGui
    if mw is None:
        mw = FreeCADGui.getMainWindow()
    vm = mw.findChild(QtGui.QDockWidget, name)
    if vm:
        return vm
    return None

def add_dock_widget(
        widget,
        name: str,
        title: str,
        ):
    mw = FreeCADGui.getMainWindow()
    vm = findWidget(name, mw)
    if vm:
        if not vm.isVisible():
            vm.show()
    else:
        from PySide2 import QtCore, QtWidgets
        vm = QtWidgets.QDockWidget()

        # create the dialog
        # dialog = FreeCADGui.PySideUic.loadUi(ui)
        vm.setWidget(widget)
        # widget.form.show()
        vm.setObjectName(name)
        vm.setWindowTitle("civilTools")
        mw.addDockWidget(QtCore.Qt.LeftDockWidgetArea, vm)