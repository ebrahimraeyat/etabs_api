import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh


# @pytest.mark.getmethod
def test_get_beams_columns(shayesteh):
    beams, columns = shayesteh.frame_obj.get_beams_columns()
    assert len(beams) == 92
    assert len(columns) == 48

def test_get_beams_columns_weakness_structure(shayesteh):
    cols_pmm, col_fields, beams_rebars, beam_fields = shayesteh.frame_obj.get_beams_columns_weakness_structure('115')
    assert len(col_fields) == 5
    assert len(beam_fields) == 9
    assert len(cols_pmm) == 11
    assert len(beams_rebars) == 217

# @pytest.mark.modify
def test_set_constant_j(shayesteh):
    shayesteh.frame_obj.set_constant_j(.15)
    js = set()
    beams, _ = shayesteh.frame_obj.get_beams_columns(2)
    for name in beams:
        j = shayesteh.SapModel.FrameObj.GetModifiers(name)[0][3]
        js.add(j)
    assert js == {.15}

# @pytest.mark.getmethod
def test_get_beams_sections(shayesteh):
    beams_names = ('115',)
    beams_sections = shayesteh.frame_obj.get_beams_sections(beams_names)
    assert beams_sections == {'115': 'B35X50'}

# @pytest.mark.getmethod
def test_get_t_crack(shayesteh):
    beams_names = ('115',)
    sec_t_crack = shayesteh.frame_obj.get_t_crack(beams_names=beams_names)
    assert pytest.approx(sec_t_crack, abs=.01) == {'B35X50': 2.272}

# @pytest.mark.getmethod
def test_get_beams_torsion_prop_modifiers(shayesteh):
    beams_names = ('115', '120')
    beams_j = shayesteh.frame_obj.get_beams_torsion_prop_modifiers(beams_names)
    assert len(beams_j) == 2
    assert pytest.approx(beams_j['115'], abs=.01) == .35
    assert pytest.approx(beams_j['120'], abs=.01) == 1.0

# @pytest.mark.getmethod
def test_get_above_frames(shayesteh):
    beams = shayesteh.frame_obj.get_above_frames('115')
    assert len(beams) == 5
    assert set(beams) == set(['253', '207', '161', '291', '115'])
    beams = shayesteh.frame_obj.get_above_frames('115', stories=['STORY1', 'STORY2'])
    assert len(beams) == 2
    beams = shayesteh.frame_obj.get_above_frames('115', stories=['STORY2'])
    assert len(beams) == 1
    assert set(beams) == set(['253'])
    shayesteh.view.show_frame('115')
    beams = shayesteh.frame_obj.get_above_frames()
    assert len(beams) == 5
    assert set(beams) == set(['253', '207', '161', '291', '115'])

# @pytest.mark.getmethod
def test_get_height_of_beam(shayesteh):
    h = shayesteh.frame_obj.get_height_of_beam('115')
    assert h == .5

# @pytest.mark.getmethod
def test_get_heigth_from_top_of_beam_to_buttom_of_above_beam(shayesteh):
    h = shayesteh.frame_obj.get_heigth_from_top_of_beam_to_buttom_of_above_beam('115')
    assert h == 3.02

# @pytest.mark.getmethod
def test_get_heigth_from_top_of_below_story_to_below_of_beam(shayesteh):
    h = shayesteh.frame_obj.get_heigth_from_top_of_below_story_to_below_of_beam('115')
    assert h == 4.72

# @pytest.mark.getmethod
def test_is_beam(shayesteh):
    ret = shayesteh.frame_obj.is_beam('115')
    assert ret

# @pytest.mark.getmethod
def test_is_column(shayesteh):
    ret = shayesteh.frame_obj.is_column('103')
    assert ret

# @pytest.mark.setmethod
def test_assign_gravity_load(shayesteh):
    ret = shayesteh.frame_obj.assign_gravity_load('115', 'DEAD', 1000, 1000)
    assert ret == None

# @pytest.mark.setmethod
def test_assign_gravity_load_from_wall(shayesteh):
    ret = shayesteh.frame_obj.assign_gravity_load_from_wall('115', 'DEAD', 220)
    assert ret == None

# @pytest.mark.setmethod
def test_assign_gravity_load_to_selfs_and_above_beams(shayesteh):
    ret = shayesteh.frame_obj.assign_gravity_load_to_selfs_and_above_beams('DEAD', 220)
    assert ret == None

# @pytest.mark.setmethod
def test_concrete_section_names(shayesteh):
    beam_names = shayesteh.frame_obj.concrete_section_names('Beam')
    assert len(beam_names) == 37
    beam_names = shayesteh.frame_obj.concrete_section_names('Column')
    assert len(beam_names) == 112

# @pytest.mark.setmethod
def test_all_section_names(shayesteh):
    all_names = shayesteh.frame_obj.all_section_names()
    assert len(all_names) == 149

# @pytest.mark.getmethod
def test_require_100_30(shayesteh):
    df = shayesteh.frame_obj.require_100_30()
    assert len(df) == 48

# @pytest.mark.getmethod
def test_get_unit_weight_of_beams(shayesteh):
    df = shayesteh.frame_obj.get_unit_weight_of_beams()
    assert len(df) == 92

# @pytest.mark.setmethod
def test_assign_ev(shayesteh):
    shayesteh.frame_obj.assign_ev(
        frames=['129', '267'],
        load_patterns=['DEAD'],
        acc = 0.3,
        ev = 'QZ',
        self_weight=True,
    )
    self_multiple = shayesteh.SapModel.LoadPatterns.GetSelfWTMultiplier('QZ')[0]
    assert self_multiple == 0.18
    ret = shayesteh.SapModel.FrameObj.GetLoadDistributed('129')[10:12]
    assert ret[0][1] == ret[1][1] == -121

# @pytest.mark.modify
def test_set_column_dns_overwrite(shayesteh):
    shayesteh.frame_obj.set_column_dns_overwrite(
        code='ACI 318-19',
    )
    assert True



