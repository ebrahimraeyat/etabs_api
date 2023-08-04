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

roof = Path(__file__).absolute().parent / 'files' / 'freecad' / 'roof.FCStd'
filename_mat = Path(__file__).absolute().parent / 'files' / 'freecad' / 'mat.FCStd'
roof_document= FreeCAD.openDocument(str(roof))

def test_get_names_of_areas_of_type():
    area_names = etabs.area.get_names_of_areas_of_type(type_='floor')
    assert len(area_names) == 232
    
def test_calculate_deck_weight_per_area():
    df = etabs.area.calculate_deck_weight_per_area()
    print(df)
    df = etabs.area.calculate_deck_weight_per_area(use_user_deck_weight=False)
    print(df)

def test_calculate_slab_weight_per_area():
    df = etabs.area.calculate_slab_weight_per_area()
    print(df)

def test_get_expanded_shell_uniform_load_sets():
    df = etabs.area.get_expanded_shell_uniform_load_sets()
    print(df)

def test_get_shell_uniform_loads():
    df = etabs.area.get_shell_uniform_loads()
    # assert len(df) == 200
    print(df)

def test_get_all_slab_types():
    d = etabs.area.get_all_slab_types()
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
        s=800, d=380, tw_top=140, tw_bot=120, hc=100, t_deck=50
    )
    assert pytest.approx(h_equal, abs=.01) == 1340.357

def test_calculate_rho():
    import area
    rho_top, rho_bot = area.calculate_rho(
        s=700, d=300, tw=120, hc=50, as_top=204, as_bot=308, fill=True
    )
    assert pytest.approx(rho_top, abs=.00001) == .00097
    assert pytest.approx(rho_bot, abs=.00001) == .001466
    rho_top, rho_bot = area.calculate_rho(
        s=800, d=380, tw=130, hc=100, as_top=204, as_bot=308, fill=False
    )
    assert pytest.approx(rho_top, abs=.00001) == .00138
    assert pytest.approx(rho_bot, abs=.00001) == .002096

def test_export_freecad_strips():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    story_name = etabs.SapModel.Story.GetStories()[1][-1]
    etabs.area.export_freecad_strips(doc=roof_document, story=story_name)
    table_key = 'Strip Object Connectivity'
    df = etabs.database.read(table_key=table_key, to_dataframe=True)
    strips = []
    for o in roof_document.Objects:
        if hasattr(o, 'Proxy') and \
            hasattr(o.Proxy, 'Type') and \
                o.Proxy.Type == 'Strip':
            strips.append(o.Label)
    assert len(df.Name.unique()) == len(strips)
    assert set(df.Name.unique()) == set(strips)

def test_reset_slab_sections_modifiers():
    etabs.area.reset_slab_sections_modifiers()
    slabs = etabs.area.get_all_slab_types()
    for slab in slabs:
        modifiers = etabs.SapModel.PropArea.GetModifiers(slab)[0]
        assert modifiers == 10 * (1,)




if __name__ == '__main__':
    test_calculate_slab_weight_per_area()