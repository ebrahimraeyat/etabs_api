import sys
from pathlib import Path
import pytest

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

roof = Path(__file__).absolute().parent / 'files' / 'freecad' / 'roof.FCStd'
filename_mat = Path(__file__).absolute().parent / 'files' / 'freecad' / 'mat.FCStd'
roof_document= FreeCAD.openDocument(str(roof))

@open_etabs_file('shayesteh.EDB')
def test_get_names_of_areas_of_type():
    area_names = etabs.area.get_names_of_areas_of_type(type_='floor')
    assert len(area_names) == 232
    
@open_etabs_file('shayesteh.EDB')
def test_calculate_deck_weight_per_area():
    df = etabs.area.calculate_deck_weight_per_area()
    print(df)
    df = etabs.area.calculate_deck_weight_per_area(use_user_deck_weight=False)
    print(df)

@open_etabs_file('shayesteh.EDB')
def test_calculate_slab_weight_per_area():
    df = etabs.area.calculate_slab_weight_per_area()
    print(df)

@open_etabs_file('shayesteh.EDB')
def test_get_expanded_shell_uniform_load_sets():
    df = etabs.area.get_expanded_shell_uniform_load_sets()
    print(df)

@open_etabs_file('shayesteh.EDB')
def test_get_shell_uniform_loads():
    df = etabs.area.get_shell_uniform_loads()
    # assert len(df) == 200
    print(df)

@open_etabs_file('shayesteh.EDB')
def test_get_all_slab_types():
    d = etabs.area.get_all_slab_types()
    assert d['SLAB1'] == d['SLAB2'] == d['PLANK1']


@open_etabs_file('shayesteh.EDB')
def test_calculate_equivalent_height_according_to_volume():
    import area
    h_equal = area.calculate_equivalent_height_according_to_volume(
        s1=800, s2=800, d=380, tw1=130, tw2=130, hc=100
    )
    assert pytest.approx(h_equal, abs=.1) == 183.6

@open_etabs_file('shayesteh.EDB')
def test_deck_plate_equivalent_height_according_to_volume():
    import area
    etabs.set_current_unit('N', 'mm')
    h_equal = area.deck_plate_equivalent_height_according_to_volume(
        s=800, d=380, tw_top=140, tw_bot=120, hc=100, t_deck=50
    )
    assert pytest.approx(h_equal, abs=.01) == 83.77

@open_etabs_file('shayesteh.EDB')
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

@open_etabs_file('shayesteh.EDB')
def test_export_freecad_strips():
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

@open_etabs_file('shayesteh.EDB')
def test_reset_slab_sections_modifiers():
    etabs.area.reset_slab_sections_modifiers()
    slabs = etabs.area.get_all_slab_types()
    for slab in slabs:
        modifiers = etabs.SapModel.PropArea.GetModifiers(slab)[0]
        assert modifiers == 10 * (1,)

@open_etabs_file('shayesteh.EDB')
def test_get_slab_names():
    slabs = etabs.area.get_slab_names()
    assert len(slabs) == 193

@open_etabs_file('shayesteh.EDB')
def test_assign_slab_modifiers():
    etabs.area.assign_slab_modifiers([], * 10 * [1])
    slab_names = etabs.area.get_slab_names()
    for slab in slab_names:
        modifiers = etabs.SapModel.AreaObj.GetModifiers(slab)[0]
        assert modifiers == 10 * (1,)

@open_etabs_file('khiabany.EDB')
def test_design_slabs():
    if etabs.etabs_main_version < 20:
        with pytest.raises(NotImplementedError) as err:
            etabs.area.design_slabs(
                slab_names=['4'],
                s = 80,
                d = 30,
                tw = 13,
                hc = 5,
                as_top = 1.5,
                as_bot = 2,
                fill = True,
                two_way = True,
                design = True,
                )
    else:
        etabs.area.design_slabs(
            slab_names=['4'],
            s = 80,
            d = 30,
            tw = 13,
            hc = 5,
            as_top = 1.5,
            as_bot = 2,
            fill = True,
            two_way = True,
            design = True,
            )
    assert True
    
@open_etabs_file('shayesteh.EDB')
def test_save_as_deflection_filename():
    slab_name = '179'
    etabs.area.save_as_deflection_filename(slab_name=slab_name)
    label, story, _ = etabs.SapModel.AreaObj.GetLabelFromName(slab_name)
    filename = f'deflection_{label}_{story}.EDB'
    assert etabs.get_filename_with_suffix() == filename
    
@open_etabs_file('khiabany.EDB')
def test_get_deflection_of_slab():
    if etabs.etabs_main_version < 20:
        with pytest.raises(NotImplementedError) as err:
            etabs.area.get_deflection_of_slab(
            dead=['Dead'],
            supper_dead=['S-DEAD'],
            lives=['Live', 'Live-0.5', 'LROOF'],
            slab_name='4',
            s=800,
            d=300,
            tw=130,
            hc=50,
            as_top=130,
            as_bot=200,
            # fill=,
            two_way=True,
            lives_percentage=0.25,
            filename='',
            )
    else:
        etabs.area.get_deflection_of_slab(
        dead=['Dead'],
        supper_dead=['S-DEAD'],
        lives=['Live', 'Live-0.5', 'LROOF'],
        slab_name='4',
        s=800,
        d=300,
        tw=130,
        hc=50,
        as_top=130,
        as_bot=200,
        # fill=,
        two_way=True,
        lives_percentage=0.25,
        filename='',
        )
    assert True

@open_etabs_file('shayesteh.EDB')
def test_delete_areas():
    etabs.area.delete_areas()
    names = etabs.area.get_names_of_areas_of_type()
    assert len(names) == 0

@open_etabs_file('shayesteh.EDB')
def test_get_points_coordinate_of_all_areas():
    ret = etabs.area.get_points_coordinate_of_all_areas()
    assert len(ret) == 232

@open_etabs_file('two_earthquakes.EDB')
def test_delete_areas_1():
    etabs.area.delete_areas()
    names = etabs.area.get_names_of_areas_of_type()
    assert len(names) == 0
    names = etabs.area.get_names_of_areas_of_type(type_='wall')
    assert len(names) == 0

def test_centroid_of_polygon():
    vertices = [
        (0,0), (70,0), (70,25), (45, 45), (45, 180), (95, 188),
        (95, 200), (-25, 200), (-25,188), (25,180), (25,45), (0, 25),
    ]
    from area import centroid_of_polygon
    x, y = centroid_of_polygon(vertices=vertices)
    np.testing.assert_almost_equal(x, 35, decimal=0)
    np.testing.assert_almost_equal(y, 100.4614, decimal=4)

@open_etabs_file('two_earthquakes.EDB')
def test_set_pier():
    names = (373, 374)
    pier_name = 'P1'
    etabs.frame_obj.set_pier(names, pier_name)
    for name in names:
        p_name = etabs.SapModel.AreaObj.GetPier(str(name))[0]
        assert p_name == pier_name

@open_etabs_file('two_earthquakes.EDB')
def test_get_piers():
    n = len(etabs.area.get_names_of_areas_of_type('wall'))
    ret = etabs.area.get_piers()
    assert len(ret) == n


if __name__ == '__main__':
    test_deck_plate_equivalent_height_according_to_volume()