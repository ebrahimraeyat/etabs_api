import sys
from pathlib import Path

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

import frame_obj_funcs as fof


def test_get_beam_continuity():
    # first
    col_dim = [50, 50, 300]
    beams_in_axis_plus_dimensions = [(40, 50, 964)] 
    beams_in_axis_minus_dimensions = [] 
    ret = fof.get_beam_continuity(
        beams_in_axis_plus_dimensions,
        beams_in_axis_minus_dimensions,
        col_dim,
        axis=2,
        )
    assert not ret
    beams_in_axis_plus_dimensions = [(40, 50, 964)]
    beams_in_axis_minus_dimensions = [(40, 50, 964)]
    ret = fof.get_beam_continuity(
        beams_in_axis_plus_dimensions,
        beams_in_axis_minus_dimensions,
        col_dim,
        axis=3,
        )
    assert ret
    # Second
    col_dim = [70, 80, 300]
    beams_in_axis_plus_dimensions = [(60, 80, 456)] 
    beams_in_axis_minus_dimensions = [(60, 80, 926)] 
    ret = fof.get_beam_continuity(
        beams_in_axis_plus_dimensions,
        beams_in_axis_minus_dimensions,
        col_dim,
        axis=2,
        )
    assert ret
    beams_in_axis_plus_dimensions = [(60, 80, 568)]
    beams_in_axis_minus_dimensions = [(60, 80, 95)]
    ret = fof.get_beam_continuity(
        beams_in_axis_plus_dimensions,
        beams_in_axis_minus_dimensions,
        col_dim,
        axis=3,
        )
    assert not ret
    # Third
    col_dim = [50, 50, 300]
    beams_in_axis_plus_dimensions = [(50, 70, 926)] 
    beams_in_axis_minus_dimensions = [] 
    ret = fof.get_beam_continuity(
        beams_in_axis_plus_dimensions,
        beams_in_axis_minus_dimensions,
        col_dim,
        axis=2,
        )
    assert not ret
    beams_in_axis_plus_dimensions = [(40, 50, 582)]
    beams_in_axis_minus_dimensions = []
    ret = fof.get_beam_continuity(
        beams_in_axis_plus_dimensions,
        beams_in_axis_minus_dimensions,
        col_dim,
        axis=3,
        )
    assert not ret

def test_get_column_continuity():
    # first
    bot_col_dim = [50, 50, 300]
    top_col_dim = [40, 40, 300]
    axis_2, axis_3 = fof.get_column_continuity(
        bot_col_dim,
        top_col_dim,
        )
    assert axis_2
    assert axis_3
    # Second
    bot_col_dim = [70, 80, 300]
    top_col_dim = [70, 80, 70]
    axis_2, axis_3 = fof.get_column_continuity(
        bot_col_dim,
        top_col_dim,
        )
    assert axis_2
    assert not axis_3

def test_get_joint_shear_vu_due_to_beams_mn_or_mpr():
    axis_plus_as_top = 2000
    axis_plus_as_bot = 2000
    axis_minus_as_top = 2500
    axis_minus_as_bot = 2000
    ductility = 'Intermediate'
    fy = 400
    vu1 = fof.get_joint_shear_vu_due_to_beams_mn_or_mpr(axis_plus_as_top, axis_plus_as_bot, axis_minus_as_top, axis_minus_as_bot, ductility, fy)
    assert vu1 == (2000 + 2500) * 400
    ductility = 'high'
    vu1 = fof.get_joint_shear_vu_due_to_beams_mn_or_mpr(axis_plus_as_top, axis_plus_as_bot, axis_minus_as_top, axis_minus_as_bot, ductility, fy)
    np.testing.assert_allclose(vu1, (2000 + 2500) * 1.25 * 400, atol=.01)

def test_get_beam_section_mn():
    ass = [5.9, 18.1, 9.1, 23.8]
    widths = [25, 25, 30, 30]
    mns = [950871, 2393806, 1429014, 3049363]
    fy = 4000
    d = 35
    fc = 250
    ductility = 'High'
    for as_, mn, width in zip(ass, mns, widths):
        ret = fof.get_beam_section_mn(as_, d, fy, fc, width, ductility)
        np.testing.assert_allclose(ret, mn, atol=10000)

def test_get_vu_column_due_to_beams_mn_or_mpr():
    axis_plus_mn_top = 1429014
    axis_plus_mn_bot = 3049363
    axis_minus_mn_top = 950871
    axis_minus_mn_bot = 2393806
    h_column_bot = 300
    h_column_top = 300
    ret = fof.get_vu_column_due_to_beams_mn_or_mpr(axis_plus_mn_top, axis_plus_mn_bot, axis_minus_mn_top, axis_minus_mn_bot, h_column_bot, h_column_top)
    np.testing.assert_allclose(ret, 13334, atol=1)


