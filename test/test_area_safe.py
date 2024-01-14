import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

filename = Path(__file__).absolute().parent / 'files' / 'freecad' / 'strip.FCStd'
filename_mat = Path(__file__).absolute().parent / 'files' / 'freecad' / 'mat.FCStd'
document= FreeCAD.openDocument(str(filename))


def test_export_freecad_slabs(shayesteh_safe):
    slabs = shayesteh_safe.area.export_freecad_slabs(document)
    assert shayesteh_safe.SapModel.AreaObj.GetNameList()[0] == 7
    shayesteh_safe.SapModel.View.RefreshView()

def test_export_freecad_slabs_mat(shayesteh_safe):
    document_mat= FreeCAD.openDocument(str(filename_mat))
    slabs = shayesteh_safe.area.export_freecad_slabs(
        document_mat,
        )
    shayesteh_safe.SapModel.View.RefreshView()
    assert shayesteh_safe.SapModel.AreaObj.GetNameList()[0] == len(slabs)

def test_export_freecad_strips(shayesteh_safe):
    shayesteh_safe.area.export_freecad_strips(document)
    shayesteh_safe.SapModel.View.RefreshView()

def test_export_freecad_stiff_elements(shayesteh_safe):
    shayesteh_safe.area.export_freecad_stiff_elements(document)

def test_set_uniform_gravity_load(shayesteh_safe):
    shayesteh_safe.area.set_uniform_gravity_load(
        ['1'], 'DEAD', 350
    )
    ret = shayesteh_safe.SapModel.AreaObj.GetLoadUniform('1')
    assert ret[2][0] == 'DEAD'
    assert ret[4][0] == 6
    assert ret[5][0] == -350

def test_export_freecad_wall_loads(shayesteh_safe):
    shayesteh_safe.area.export_freecad_wall_loads(document)
