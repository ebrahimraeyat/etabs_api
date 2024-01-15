import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_get_beams_columns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == 92
    assert len(columns) == 48
    # Remove frames
    etabs.frame_obj.delete_frames()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0
    beams, columns = etabs.frame_obj.get_beams_columns(type_=1)
    assert len(beams) == len(columns) == 0


def test_get_beams_columns_on_stories():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.frame_obj.get_beams_columns_on_stories()
    assert len(ret) == 5
    for story in etabs.SapModel.Story.GetNameList()[1]:
        assert len(ret[story]) == 2
    assert len(ret['STORY5'][1]) == 4 # Columns of Ridge

def test_get_beams_columns_in_stories():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    # frame_names = '116', '253']
    # etabs.frame_obj.set_frame_obj_selected(frame_names)
    beams, columns = etabs.frame_obj.get_beams_columns(stories=['STORY1', 'STORY2'])
    assert len(beams) == 44
    assert len(columns) == 22

def test_get_beams_columns_weakness_structure():
    if version < 20:
        assert True
        return
    open_model(etabs=etabs, filename='shayesteh.EDB')
    cols_pmm, col_fields, beams_rebars, beam_fields = etabs.frame_obj.get_beams_columns_weakness_structure('115')
    assert isinstance(cols_pmm, list)
    assert isinstance(beams_rebars, list)
    assert len(col_fields) == 5
    assert len(beam_fields) == 9
    assert len(cols_pmm) == 11
    # assert len(beams_rebars) == 217

def test_set_constant_j():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.frame_obj.set_constant_j(.15)
    js = set()
    beams, _ = etabs.frame_obj.get_beams_columns(2)
    for name in beams:
        j = etabs.SapModel.FrameObj.GetModifiers(name)[0][3]
        js.add(j)
    assert js == {.15}

def test_get_beams_sections():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beams_names = ('115',)
    beams_sections = etabs.frame_obj.get_beams_sections(beams_names)
    assert beams_sections == {'115': 'B35X50'}

def test_get_t_crack():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beams_names = ('115',)
    sec_t_crack = etabs.frame_obj.get_t_crack(beams_names=beams_names)
    assert pytest.approx(sec_t_crack, abs=.01) == {'B35X50': 2.272}

def test_get_beams_torsion_prop_modifiers():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beams_names = ('115', '120')
    beams_j = etabs.frame_obj.get_beams_torsion_prop_modifiers(beams_names)
    assert len(beams_j) == 2
    assert pytest.approx(beams_j['115'], abs=.01) == .35
    assert pytest.approx(beams_j['120'], abs=.01) == 1.0

def test_correct_torsion_stiffness_factor():
    open_model(etabs=etabs, filename='shayesteh.EDB')
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


def test_get_above_frames():
    open_model(etabs=etabs, filename='shayesteh.EDB')
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

def test_get_height_of_beam():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    h = etabs.frame_obj.get_height_of_beam('115')
    assert h == .5

def test_get_heigth_from_top_of_beam_to_buttom_of_above_beam():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    h = etabs.frame_obj.get_heigth_from_top_of_beam_to_buttom_of_above_beam('115')
    assert h == 3.02

def test_get_heigth_from_top_of_below_story_to_below_of_beam():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    h = etabs.frame_obj.get_heigth_from_top_of_below_story_to_below_of_beam('115')
    assert h == 4.72

def test_is_beam():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.frame_obj.is_beam('115')
    assert ret

def test_is_column():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.frame_obj.is_column('103')
    assert ret

def test_assign_gravity_load():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.frame_obj.assign_gravity_load('115', 'DEAD', 1000, 1000)
    assert ret == None

def test_assign_gravity_load_from_wall():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.frame_obj.assign_gravity_load_from_wall('115', 'DEAD', 220)
    assert ret == None

def test_assign_gravity_load_to_selfs_and_above_beams():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.frame_obj.assign_gravity_load_to_selfs_and_above_beams('DEAD', 220)
    assert ret == None

def test_concrete_section_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beam_names = etabs.frame_obj.concrete_section_names('Beam')
    assert len(beam_names) == 37
    beam_names = etabs.frame_obj.concrete_section_names('Column')
    assert len(beam_names) == 112

def test_all_section_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    all_names = etabs.frame_obj.all_section_names()
    assert len(all_names) == 149

def test_require_100_30():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    df = etabs.frame_obj.require_100_30('QX', 'QXN', 'QXP', 'QY', 'QYN', 'QYP', file_name=f'100_30_{version}.EDB')
    assert len(df) == 48
    assert set(df.PMMCombo.unique()) == {'QXN_100_30', 'QXP_100_30', 'QYN_100_30', 'QYP_100_30'}

def test_get_unit_weight_of_beams():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    df = etabs.frame_obj.get_unit_weight_of_beams()
    assert len(df) == 92

def test_assign_frame_modifiers():
    open_model(etabs=etabs, filename='shayesteh.EDB')
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

def test_assign_ev():
    open_model(etabs=etabs, filename='shayesteh.EDB')
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

def test_set_column_dns_overwrite():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.frame_obj.set_column_dns_overwrite(
        code='ACI 318-14',
    )
    assert True

def test_get_area():
    open_model(etabs=etabs, filename='shayesteh.EDB')
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

def test_get_length_of_frame():
    open_model(etabs=etabs, filename='shayesteh.EDB')
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

def test_set_end_length_offsets():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.frame_obj.set_end_length_offsets(0.5)
    table_key = 'Frame Assignments - End Length Offsets'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(df.RigidFact.unique()) == {'0.5'}

def test_delete_frames():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.frame_obj.delete_frames()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0
    open_model(etabs=etabs, filename='madadi.EDB')
    etabs.frame_obj.delete_frames()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0
    beams, columns = etabs.frame_obj.get_beams_columns(type_=1)
    assert len(beams) == len(columns) == 0



if __name__ == '__main__':
    test_set_end_length_offsets()





