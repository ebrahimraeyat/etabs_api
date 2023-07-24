import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import *

# @pytest.mark.getmethod
def test_get_beams_columns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == 92
    assert len(columns) == 48

def test_get_beams_columns_in_stories():
    # frame_names = '116', '253']
    # etabs.frame_obj.set_frame_obj_selected(frame_names)
    beams, columns = etabs.frame_obj.get_beams_columns(stories=['STORY1', 'STORY2'])
    assert len(beams) == 44
    assert len(columns) == 22

def test_get_beams_columns_weakness_structure():
    cols_pmm, col_fields, beams_rebars, beam_fields = etabs.frame_obj.get_beams_columns_weakness_structure('115')
    assert len(col_fields) == 5
    assert len(beam_fields) == 9
    assert len(cols_pmm) == 11
    assert len(beams_rebars) == 217

# @pytest.mark.modify
def test_set_constant_j():
    etabs.frame_obj.set_constant_j(.15)
    js = set()
    beams, _ = etabs.frame_obj.get_beams_columns(2)
    for name in beams:
        j = etabs.SapModel.FrameObj.GetModifiers(name)[0][3]
        js.add(j)
    assert js == {.15}

# @pytest.mark.getmethod
def test_get_beams_sections():
    beams_names = ('115',)
    beams_sections = etabs.frame_obj.get_beams_sections(beams_names)
    assert beams_sections == {'115': 'B35X50'}

# @pytest.mark.getmethod
def test_get_t_crack():
    beams_names = ('115',)
    sec_t_crack = etabs.frame_obj.get_t_crack(beams_names=beams_names)
    assert pytest.approx(sec_t_crack, abs=.01) == {'B35X50': 2.272}

# @pytest.mark.getmethod
def test_get_beams_torsion_prop_modifiers():
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


# @pytest.mark.getmethod
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

# @pytest.mark.getmethod
def test_get_height_of_beam():
    h = etabs.frame_obj.get_height_of_beam('115')
    assert h == .5

# @pytest.mark.getmethod
def test_get_heigth_from_top_of_beam_to_buttom_of_above_beam():
    h = etabs.frame_obj.get_heigth_from_top_of_beam_to_buttom_of_above_beam('115')
    assert h == 3.02

# @pytest.mark.getmethod
def test_get_heigth_from_top_of_below_story_to_below_of_beam():
    h = etabs.frame_obj.get_heigth_from_top_of_below_story_to_below_of_beam('115')
    assert h == 4.72

# @pytest.mark.getmethod
def test_is_beam():
    ret = etabs.frame_obj.is_beam('115')
    assert ret

# @pytest.mark.getmethod
def test_is_column():
    ret = etabs.frame_obj.is_column('103')
    assert ret

# @pytest.mark.setmethod
def test_assign_gravity_load():
    ret = etabs.frame_obj.assign_gravity_load('115', 'DEAD', 1000, 1000)
    assert ret == None

# @pytest.mark.setmethod
def test_assign_gravity_load_from_wall():
    ret = etabs.frame_obj.assign_gravity_load_from_wall('115', 'DEAD', 220)
    assert ret == None

# @pytest.mark.setmethod
def test_assign_gravity_load_to_selfs_and_above_beams():
    ret = etabs.frame_obj.assign_gravity_load_to_selfs_and_above_beams('DEAD', 220)
    assert ret == None

# @pytest.mark.setmethod
def test_concrete_section_names():
    beam_names = etabs.frame_obj.concrete_section_names('Beam')
    assert len(beam_names) == 37
    beam_names = etabs.frame_obj.concrete_section_names('Column')
    assert len(beam_names) == 112

# @pytest.mark.setmethod
def test_all_section_names():
    all_names = etabs.frame_obj.all_section_names()
    assert len(all_names) == 149

# @pytest.mark.getmethod
def test_require_100_30():
    df = etabs.frame_obj.require_100_30()
    assert len(df) == 48

# @pytest.mark.getmethod
def test_get_unit_weight_of_beams():
    df = etabs.frame_obj.get_unit_weight_of_beams()
    assert len(df) == 92

def test_assign_frame_modifires():
    beams, _ = etabs.frame_obj.get_beams_columns()
    etabs.frame_obj.assign_frame_modifires(beams, i33=0.5)
    for beam in beams:
        modifiers = etabs.SapModel.FrameObj.GetModifiers(beam)[0]
        assert modifiers[5] == 0.5

# @pytest.mark.setmethod
def test_assign_ev():
    etabs.frame_obj.assign_ev(
        frames=['129', '267'],
        load_patterns=['DEAD'],
        acc = 0.3,
        ev = 'QZ',
        self_weight=True,
    )
    self_multiple = etabs.SapModel.LoadPatterns.GetSelfWTMultiplier('QZ')[0]
    assert self_multiple == 0.18
    ret = etabs.SapModel.FrameObj.GetLoadDistributed('129')[10:12]
    assert ret[0][1] == ret[1][1] == -121

# @pytest.mark.modify
def test_set_column_dns_overwrite():
    etabs.frame_obj.set_column_dns_overwrite(
        code='ACI 318-19',
    )
    assert True

def test_get_area():
    area = etabs.frame_obj.get_area(
        '130',
    )
    assert area == 40 * 44
    cover = 6.5
    area = etabs.frame_obj.get_area(
        '130',
        cover = cover,
    )
    assert area == 40 * (50 - cover)

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





