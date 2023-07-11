import pytest
from pathlib import Path
import sys

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

filename = Path(__file__).absolute().parent / 'files' / 'freecad' / 'strip.FCStd'
filename_mat = Path(__file__).absolute().parent / 'files' / 'freecad' / 'mat.FCStd'
document= FreeCAD.openDocument(str(filename))

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import *


def test_get_strip_connectivity(shayesteh_safe):
    df = shayesteh_safe.database.get_strip_connectivity()
    assert len(df) == shayesteh_safe.SapModel.DesignConcreteSlab.DesignStrip.GetNameList()[0]

@pytest.mark.applymethod
def test_create_area_spring_table(shayesteh_safe):
    names_props = [('SOIL', '2'), ('SOIL_1.5', '3'), ('SOIL_2', '4')]
    df = shayesteh_safe.database.create_area_spring_table(names_props)

@pytest.mark.applymethod
def test_create_punching_shear_general_table(shayesteh_safe):
    punches = []
    for o in document.Objects:
        if hasattr(o, "Proxy") and \
            hasattr(o.Proxy, "Type") and \
            o.Proxy.Type == "Punch":
            punches.append(o)
    shayesteh_safe.database.create_punching_shear_general_table(punches)

@pytest.mark.applymethod
def test_create_punching_shear_perimeter_table(shayesteh_safe):
    punches = []
    for o in document.Objects:
        if hasattr(o, "Proxy") and \
            hasattr(o.Proxy, "Type") and \
            o.Proxy.Type == "Punch":
            punches.append(o)
    shayesteh_safe.database.create_punching_shear_perimeter_table(punches)
