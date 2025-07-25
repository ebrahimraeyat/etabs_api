import sys
from pathlib import Path
import pytest

import numpy as np
import pandas as pd

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file, version

@open_etabs_file('madadi.EDB')
def test_get_start_end_releases():
    ret = etabs.frame_obj.get_start_end_releases(['215', '157', '152', '150', '123'])
    assert ret == ['Fixed', 'Fixed']
    ret = etabs.frame_obj.get_start_end_releases(['15', '16', '19', '20'])
    assert ret == ['Pinned', 'Pinned']
    ret = etabs.frame_obj.get_start_end_releases(['15', '157', '152', '150', '123'])
    assert ret == ['Pinned', 'Pinned']

@open_etabs_file('shayesteh.EDB')
def test_get_beams_columns():
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == 92
    assert len(columns) == 48
    # Remove frames
    etabs.frame_obj.delete_frames()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0
    beams, columns = etabs.frame_obj.get_beams_columns(type_=1)
    assert len(beams) == len(columns) == 0

@open_etabs_file('shayesteh.EDB')
def test_get_columns_type_names():
    col_type_names = etabs.frame_obj.get_columns_type_names()
    assert len(col_type_names) == 11
    assert col_type_names['C5'] == ['107', '245', '199', '153', None]
    assert col_type_names['C3'] == ['105', '243', '197', '151', '288']

def test_get_columns_type_sections():
    col_type_section, _ = etabs.frame_obj.get_columns_type_sections()
    assert len(col_type_section) == 11
    assert col_type_section['C5'] == ['C5016F20', 'C4512F18', 'C4012F16', 'C3510F16', None]

@open_etabs_file('shayesteh.EDB')
def test_get_section_area():
    etabs.set_current_unit('kgf', 'cm')
    areas = etabs.frame_obj.get_section_area()
    assert isinstance(areas, dict)
    assert len(areas) == 149
    assert areas['B25X40'] == 1000

@open_etabs_file('shayesteh.EDB')
def test_set_pier():
    names = (103, 104)
    pier_name = 'P1'
    etabs.frame_obj.set_pier(names, pier_name)
    for name in names:
        p_name = etabs.SapModel.FrameObj.GetPier(str(name))[0]
        assert p_name == pier_name 
    



@open_etabs_file('shayesteh.EDB')
def test_get_beams_columns_on_stories():
    ret = etabs.frame_obj.get_beams_columns_on_stories()
    assert len(ret) == 5
    for story in etabs.SapModel.Story.GetNameList()[1]:
        assert len(ret[story]) == 2
    assert len(ret['STORY5'][1]) == 4 # Columns of Ridge

@open_etabs_file('shayesteh.EDB')
def test_get_beams_columns_in_stories():
    # frame_names = '116', '253']
    # etabs.frame_obj.set_frame_obj_selected(frame_names)
    beams, columns = etabs.frame_obj.get_beams_columns(stories=['STORY1', 'STORY2'])
    assert len(beams) == 44
    assert len(columns) == 22

@open_etabs_file('shayesteh.EDB')
def test_get_beams_columns_weakness_structure():
    if version < 20:
        assert True
        return
    cols_pmm, col_fields, beams_rebars, beam_fields = etabs.frame_obj.get_beams_columns_weakness_structure('115')
    assert isinstance(cols_pmm, list)
    assert isinstance(beams_rebars, list)
    assert len(col_fields) == 5
    assert len(beam_fields) == 9
    assert len(cols_pmm) == 11

@open_etabs_file('zibaei.EDB')
def test_get_beams_columns_weakness_structure_dynamic_angular():
    if version < 20:
        assert True
        return
    d = {}
    d["ex_combobox"] = 'EX'
    d["ey_combobox"] = 'EY'
    d["x_scalefactor_combobox"] = "1"
    d["y_scalefactor_combobox"] = "1"
    d["combination_response_spectrum_checkbox"] = False
    d["angular_response_spectrum_checkbox"] = True
    d_angles = {}
    for angle in range(0, 180, 15):
        d_angles[angle] = [ f"SEC{angle}", f"SPECT{angle}"]
    d["angular_tableview"] = d_angles
    cols_pmm, col_fields, beams_rebars, beam_fields = etabs.frame_obj.get_beams_columns_weakness_structure(
        '67',
        dynamic=True,
        d = d,
        )
    assert isinstance(cols_pmm, list)
    assert isinstance(beams_rebars, list)
    assert len(col_fields) == 5
    assert len(beam_fields) == 9
    assert len(cols_pmm) == 16

@open_etabs_file('shayesteh.EDB')
def test_get_beams_columns_weakness_structure_dynamic_combination():
    if version < 20:
        assert True
        return
    d = {}
    d["ex_combobox"] = 'QX'
    d["ey_combobox"] = 'QY'
    d["sx_combobox"] = "SX"
    d["sxe_combobox"] = "SX"
    d["sy_combobox"] = "SY"
    d["sye_combobox"] = "SY"
    d["x_scalefactor_combobox"] = "1"
    d["y_scalefactor_combobox"] = "1"
    d["combination_response_spectrum_checkbox"] = True
    cols_pmm, col_fields, beams_rebars, beam_fields = etabs.frame_obj.get_beams_columns_weakness_structure(
        '115',
        dynamic=True,
        d = d,
        )
    assert isinstance(cols_pmm, list)
    assert isinstance(beams_rebars, list)
    assert len(col_fields) == 5
    assert len(beam_fields) == 9
    assert len(cols_pmm) == 11

@open_etabs_file('shayesteh.EDB')
def test_set_constant_j():
    etabs.frame_obj.set_constant_j(.15)
    js = set()
    beams, _ = etabs.frame_obj.get_beams_columns(2)
    for name in beams:
        j = etabs.SapModel.FrameObj.GetModifiers(name)[0][3]
        js.add(j)
    assert js == {.15}

@open_etabs_file('shayesteh.EDB')
def test_get_beams_sections():
    beams_names = ('115',)
    beams_sections = etabs.frame_obj.get_beams_sections(beams_names)
    assert beams_sections == {'115': 'B35X50'}

@open_etabs_file('shayesteh.EDB')
def test_get_t_crack():
    beams_names = ('115',)
    sec_t_crack = etabs.frame_obj.get_t_crack(beams_names=beams_names)
    assert pytest.approx(sec_t_crack, abs=.01) == {'B35X50': 2.272}

@open_etabs_file('shayesteh.EDB')
def test_get_beams_torsion_prop_modifiers():
    beams_names = ('115', '120')
    beams_j = etabs.frame_obj.get_beams_torsion_prop_modifiers(beams_names)
    assert len(beams_j) == 2
    assert pytest.approx(beams_j['115'], abs=.01) == .35
    assert pytest.approx(beams_j['120'], abs=.01) == 1.0

@open_etabs_file('shayesteh.EDB')
def test_correct_torsion_stiffness_factor():
    num_iteration = 1
    g = etabs.frame_obj.correct_torsion_stiffness_factor(
        num_iteration = num_iteration,
        )
    i = 0
    try:
        while True:
            ret = g.__next__()
            if isinstance(ret, int):
                print(f'{ret=}, {i=}')
                assert ret == i
            else:
                print('Return df')
                import pandas as pd
                assert isinstance(ret, pd.DataFrame)
                assert len(ret) == 92
            i += 1
    except StopIteration:
        return


@open_etabs_file('shayesteh.EDB')
def test_get_above_frames():
    beams = etabs.frame_obj.get_above_frames('115')
    assert len(beams) == 5
    assert set(beams) == set(['253', '207', '161', '291', '115'])
    beams = etabs.frame_obj.get_above_frames('115', stories=['STORY1', 'STORY2'])
    assert len(beams) == 2
    beams = etabs.frame_obj.get_above_frames('115', stories=['STORY2'])
    assert len(beams) == 1
    assert set(beams) == set(['253'])
    etabs.view.show_frame('115')
    beams = etabs.frame_obj.get_above_frames()
    assert len(beams) == 5
    assert set(beams) == set(['253', '207', '161', '291', '115'])

@open_etabs_file('shayesteh.EDB')
def test_get_height_of_beam():
    h = etabs.frame_obj.get_height_of_beam('115')
    assert h == .5

@open_etabs_file('shayesteh.EDB')
def test_get_heigth_from_top_of_beam_to_buttom_of_above_beam():
    h = etabs.frame_obj.get_heigth_from_top_of_beam_to_buttom_of_above_beam('115')
    assert h == 3.02

@open_etabs_file('shayesteh.EDB')
def test_get_heigth_from_top_of_below_story_to_below_of_beam():
    h = etabs.frame_obj.get_heigth_from_top_of_below_story_to_below_of_beam('115')
    assert h == 4.72

@open_etabs_file('shayesteh.EDB')
def test_is_beam():
    ret = etabs.frame_obj.is_beam('115')
    assert ret

@open_etabs_file('shayesteh.EDB')
def test_is_column():
    ret = etabs.frame_obj.is_column('103')
    assert ret

@open_etabs_file('shayesteh.EDB')
def test_assign_gravity_load():
    ret = etabs.frame_obj.assign_gravity_load('115', 'DEAD', 1000, 1000)
    assert ret == None

@open_etabs_file('shayesteh.EDB')
def test_assign_gravity_load_from_wall():
    ret = etabs.frame_obj.assign_gravity_load_from_wall('115', 'DEAD', 220)
    assert ret == None

@open_etabs_file('shayesteh.EDB')
def test_assign_gravity_load_to_selfs_and_above_beams():
    ret = etabs.frame_obj.assign_gravity_load_to_selfs_and_above_beams('DEAD', 220)
    assert ret == None

@open_etabs_file('shayesteh.EDB')
def test_update_gravity_loads_from_wall():
    frame_1 = "115"
    frame_2 = "114"
    load = 200
    wall_loads_dict = {'beams_wall_loads': {
                'wall_loadpat': {frame_1: 'DEAD', frame_2: "QZ"},
                'wall_weight_per_area': {frame_1: load, frame_2: load},
                'wall_opening_ratio': {frame_1: 0.3, frame_2: 0},
                'wall_dist1': {frame_1: .1, frame_2: 0},
                'wall_dist2': {frame_1: .9, frame_2: 1},
                'height_from_below': {frame_1: False, frame_2: True},
                'parapet': {frame_1: 0, frame_2: 0},
                'none_beam_h': {frame_1: 0, frame_2: 0},
                }}
    etabs.set_settings_to_model(wall_loads_dict)
    etabs.frame_obj.update_gravity_loads_from_wall([frame_1])
    ret = etabs.SapModel.FrameObj.GetLoadDistributed(frame_1)
    assert ret[1][0] == frame_1
    assert ret[2][0] == 'DEAD'
    assert ret[10][0] == ret[11][0] == 423

@open_etabs_file('shayesteh.EDB')
def test_concrete_section_names():
    beam_names = etabs.frame_obj.concrete_section_names('Beam')
    assert len(beam_names) == 37
    beam_names = etabs.frame_obj.concrete_section_names('Column')
    assert len(beam_names) == 112

@open_etabs_file('shayesteh.EDB')
def test_all_section_names():
    all_names = etabs.frame_obj.all_section_names()
    assert len(all_names) == 149

@open_etabs_file('shayesteh.EDB')
def test_require_100_30():
    loads = ['QX', 'QXN', 'QXP', 'QY', 'QYN', 'QYP']
    df = etabs.frame_obj.require_100_30(loads, file_name=f'100_30_{version}.EDB')
    assert len(df) == 48
    assert set(df.PMMCombo.unique()) == {'QXN_100_30', 'QXP_100_30', 'QYN_100_30', 'QYP_100_30'}

@open_etabs_file('shayesteh.EDB')
def test_get_unit_weight_of_beams():
    df = etabs.frame_obj.get_unit_weight_of_beams()
    assert len(df) == 92

@open_etabs_file('shayesteh.EDB')
def test_assign_frame_modifiers_mass():
    mod = 10
    beams, _ = etabs.frame_obj.get_beams_columns(type_=2)
    etabs.frame_obj.assign_frame_modifiers(beams, mass=mod)
    modifier = etabs.SapModel.FrameObj.GetModifiers('115')[0][-2]
    assert modifier == 0.8
    modifier = etabs.SapModel.FrameObj.GetModifiers('253')[0][-2]
    assert modifier == 0.75

@open_etabs_file('shayesteh.EDB')
def test_assign_frame_modifiers():
    i33_beam = 0.5
    i33_column = 0.7
    beams, columns = etabs.frame_obj.get_beams_columns(type_=2)
    etabs.frame_obj.assign_frame_modifiers(beams, i33=i33_beam)
    etabs.frame_obj.assign_frame_modifiers(columns, i33=i33_column)
    for beam in beams:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(beam)[0]
        assert modifiers[5] == i33_beam
    for column in columns:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(column)[0]
        assert modifiers[5] == i33_column
    # filter design_procedure
    etabs.frame_obj.assign_frame_modifiers(beams, i33=0.8, design_procedure='steel')
    etabs.frame_obj.assign_frame_modifiers(columns, i33=0.9, design_procedure='steel')
    for beam in beams:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(beam)[0]
        assert modifiers[5] == i33_beam
    for column in columns:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(column)[0]
        assert modifiers[5] == i33_column
    # filter design orientation
    etabs.frame_obj.assign_frame_modifiers(beams, i33=0.8, design_orientation='column')
    etabs.frame_obj.assign_frame_modifiers(columns, i33=0.9, design_orientation='beam')
    for beam in beams:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(beam)[0]
        assert modifiers[5] == i33_beam
    for column in columns:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(column)[0]
        assert modifiers[5] == i33_column

@open_etabs_file('shayesteh.EDB')
def test_assign_ev():
    etabs.frame_obj.assign_ev(
        frames=['129', '267'],
        load_patterns=['DEAD'],
        acc = 0.3,
        ev = 'QZ',
        self_weight=True,
    )
    self_multiple = etabs.SapModel.LoadPatterns.GetSelfWTMultiplier('QZ')[0]
    assert self_multiple == 0
    ret = etabs.SapModel.FrameObj.GetLoadDistributed('129')[10:12]
    assert ret[0][1] == ret[1][1] == -121

@open_etabs_file('shayesteh.EDB')
def test_set_column_dns_overwrite():
    etabs.frame_obj.set_column_dns_overwrite(
        code='ACI 318-14',
    )
    assert True

@open_etabs_file('shayesteh.EDB')
def test_get_area():
    etabs.set_current_unit('N', 'cm')
    area = etabs.frame_obj.get_area(
        '130',
    )
    assert area == 40 * (50 - 6)
    cover = 6.5
    area = etabs.frame_obj.get_area(
        '130',
        cover = cover,
    )
    assert area == 40 * (50 - cover)
    # change unit
    etabs.set_current_unit('N', 'm')
    area = etabs.frame_obj.get_area(
        '130',
    )
    assert pytest.approx(area, abs=.0001) == .40 * (.50 - 0.06)

@open_etabs_file('shayesteh.EDB')
def test_get_length_of_frame():
    length = etabs.frame_obj.get_length_of_frame(
        '126',
        'cm'
        )
    assert pytest.approx(length, abs=0.01) == 599.715
    length = etabs.frame_obj.get_length_of_frame(
        '126',
        'm'
        )
    assert pytest.approx(length, abs=.01) == 5.997

@open_etabs_file('shayesteh.EDB')
def test_get_offset_coordinate_of_beam_in_plan():
    etabs.set_current_unit('kgf', 'cm')
    dist = 20
    x1, y1, z1, x2, y2, z2 = etabs.frame_obj.get_offset_coordinate_of_beam_in_plan(
        '115',
        dist,
        )
    assert y1 == y2 == 20
    assert pytest.approx(z1, abs=.01) == z2

@open_etabs_file('shayesteh.EDB')
def test_set_end_length_offsets():
    etabs.frame_obj.set_end_length_offsets(0.5)
    table_key = 'Frame Assignments - End Length Offsets'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(df.RigidFact.unique()) == {'0.5'}

@open_etabs_file('shayesteh.EDB')
def test_delete_frames():
    etabs.frame_obj.delete_frames()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0

@open_etabs_file('madadi.EDB')
def test_delete_frames_1():
    etabs.frame_obj.delete_frames()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0
    beams, columns = etabs.frame_obj.get_beams_columns(type_=1)
    assert len(beams) == len(columns) == 0

@open_etabs_file('shayesteh.EDB')
def test_assign_wall_loads_to_etabs():
    FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
    sys.path.append(FREECADPATH)
    import FreeCAD
    freecad_model = etabs_api_path / 'test' / 'files' / 'freecad' / 'shayesteh.FCStd'
    FreeCAD.openDocument(str(freecad_model))
    etabs.frame_obj.assign_wall_loads_to_etabs()
    ret = etabs.SapModel.FrameObj.GetLoadDistributed('124')
    np.testing.assert_allclose(ret[10], -665)
    np.testing.assert_allclose(ret[11], -665)

@open_etabs_file('steel.EDB')
def test_set_lateral_bracing():
    names = ['94', '95', '96']
    ret = etabs.frame_obj.set_lateral_bracing(names)
    assert set(ret) == {0}

@open_etabs_file('steel.EDB')
def test_get_section_type_and_geometry():
    names = ['94', '95', '96']
    ret = etabs.frame_obj.get_section_type_and_geometry(names)
    assert set(ret.keys()) == set(names)
    for name in names:
        assert ret[name]['sec_type'] == "WB"
    assert len(ret) == len(names)

@open_etabs_file('steel.EDB')
def test_get_lateral_bracing():
    etabs.set_current_unit('N', 'm')
    name = '94'
    ret = etabs.frame_obj.get_lateral_bracing(name)
    assert ret[0] == []
    assert ret[1] == []
    etabs.frame_obj.set_lateral_bracing([name], 1, 3, 3, relative=False)
    ret = etabs.frame_obj.set_lateral_bracing([name], 2, 1, 1, 2, relative=False)
    assert set(ret) == {0}
    ret = etabs.frame_obj.get_lateral_bracing(name)
    assert set(ret[1]) == set([3])
    assert [1,2] in ret[0]
    assert 3 in ret[0]

@open_etabs_file('steel.EDB')
def test_group_stacked_columns_by_points_working():
    etabs.frame_obj.group_stacked_columns_by_points()
    assert True  # If no exception is raised, the test passes

@open_etabs_file('steel.EDB')
def test_stacked_columns_dataframe_by_points_working():
    etabs.frame_obj.stacked_columns_dataframe_by_points()
    assert True  # If no exception is raised, the test passes


def test_group_stacked_columns_by_points():
    # Points: Z values are floats
    points_df = pd.DataFrame([
        {'UniqueName': 1, 'X': 0, 'Y': 0, 'Z': 0.0},
        {'UniqueName': 2, 'X': 0, 'Y': 0, 'Z': 3.0},
        {'UniqueName': 3, 'X': 0, 'Y': 0, 'Z': 6.0},
        {'UniqueName': 4, 'X': 0, 'Y': 0, 'Z': 9.0},
        {'UniqueName': 5, 'X': 1, 'Y': 0, 'Z': 0.0},
        {'UniqueName': 6, 'X': 1, 'Y': 0, 'Z': 3.0},
    ])
    # Columns: one stack of 3, one stack of 2
    columns_df = pd.DataFrame([
        {'UniqueName': 101, 'UniquePtI': 1, 'UniquePtJ': 2},
        {'UniqueName': 102, 'UniquePtI': 2, 'UniquePtJ': 3},
        {'UniqueName': 103, 'UniquePtI': 3, 'UniquePtJ': 4},
        {'UniqueName': 201, 'UniquePtI': 5, 'UniquePtJ': 6},
    ])
    from frame_obj import FrameObj
    frame_obj = FrameObj(etabs=None)
    groups = frame_obj.group_stacked_columns_by_points(points_df=points_df, columns_df=columns_df)
    # Should be two groups, one with 3 columns, one with 1
    assert isinstance(groups, list)
    assert any(len(g) == 3 for g in groups)
    assert any(len(g) == 1 for g in groups)

@open_etabs_file('shayesteh.EDB')
def test_stacked_columns_dataframe_by_points():
    points_df = pd.DataFrame([
        {'UniqueName': 1, 'X': 0, 'Y': 0, 'Z': 0.0},
        {'UniqueName': 2, 'X': 0, 'Y': 0, 'Z': 3.0},
        {'UniqueName': 3, 'X': 0, 'Y': 0, 'Z': 6.0},
        {'UniqueName': 4, 'X': 0, 'Y': 0, 'Z': 9.0},
        {'UniqueName': 5, 'X': 1, 'Y': 0, 'Z': 0.0},
        {'UniqueName': 6, 'X': 1, 'Y': 0, 'Z': 3.0},
    ])
    columns_df = pd.DataFrame([
        {'UniqueName': 101, 'UniquePtI': 1, 'UniquePtJ': 2},
        {'UniqueName': 102, 'UniquePtI': 2, 'UniquePtJ': 3},
        {'UniqueName': 103, 'UniquePtI': 3, 'UniquePtJ': 4},
        {'UniqueName': 201, 'UniquePtI': 5, 'UniquePtJ': 6},
    ])
    df = etabs.frame_obj.stacked_columns_dataframe_by_points(points_df=points_df, columns_df=columns_df)
    # Should have 3 rows (excluding lowest Z=0.0), and 2 columns (2 stacks)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 3
    assert df.shape[1] == 2
    print(df)


if __name__ == '__main__':
    test_stacked_columns_dataframe_by_points()





