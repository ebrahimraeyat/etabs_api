import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh, shayesteh_safe

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

def test_calculate_deck_weight_per_area(shayesteh):
    df = shayesteh.area.calculate_deck_weight_per_area()
    print(df)
    df = shayesteh.area.calculate_deck_weight_per_area(use_user_deck_weight=False)
    print(df)

def test_calculate_slab_weight_per_area(shayesteh):
    df = shayesteh.area.calculate_slab_weight_per_area()
    print(df)

def test_get_expanded_shell_uniform_load_sets(shayesteh):
    df = shayesteh.area.get_expanded_shell_uniform_load_sets()
    print(df)

def test_get_shell_uniform_loads(shayesteh):
    df = shayesteh.area.get_shell_uniform_loads()
    assert len(df) == 200
    print(df)

def test_get_all_slab_types(shayesteh):
    d = shayesteh.area.get_all_slab_types()
    assert d['SLAB1'] == d['SLAB2'] == d['PLANK1']


def test_calculate_equivalent_height_according_to_volume():
    import area
    h_equal = area.calculate_equivalent_height_according_to_volume(
        s1=800, s2=800, d=380, tw1=130, tw2=130, hc=100
    )
    assert pytest.approx(h_equal, abs=.1) == 183.6

def test_deck_plate_equivalent_height_according_to_volume():
    import area
    h_equal = area.deck_plate_equivalent_height_according_to_volume(
        s=800, d=380, tw_top=140, tw_bot=120, hc=100
    )
    assert pytest.approx(h_equal, abs=.01) == 1340.357

if __name__ == '__main__':
    test_calculate_slab_weight_per_area(shayesteh)