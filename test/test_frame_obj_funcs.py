import sys
from pathlib import Path

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
