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

def test_get_beam_section_mpr():
    ass = [5.9, 18.1, 9.1, 23.8]
    widths = [25, 25, 30, 30]
    mprs = [950871, 2393806, 1429014, 3049363]
    fy = 4000
    d = 35
    fc = 250
    ductility = 'High'
    for as_, mpr, width in zip(ass, mprs, widths):
        ret = fof.get_beam_section_mpr(as_, d, fy, fc, width, ductility)
        np.testing.assert_allclose(ret, mpr, atol=10000)

def test_get_vu_column_due_to_beams_mn_or_mpr():
    axis_plus_mn_top = 1429014
    axis_plus_mn_bot = 3049363
    axis_minus_mn_top = 950871
    axis_minus_mn_bot = 2393806
    h_column_bot = 300
    h_column_top = 300
    ret = fof.get_vu_column_due_to_beams_mn_or_mpr(axis_plus_mn_top, axis_plus_mn_bot, axis_minus_mn_top, axis_minus_mn_bot, h_column_bot, h_column_top)
    np.testing.assert_allclose(ret, 13334, atol=1)

def test_get_max_allowed_rebar_distance_due_to_crack_control():
    transver_rebar_sizes=(10,10,10,10,12,12)
    all_fy = (400,400,400,400,420,420)
    cover = 40
    allows = (274, 274, 274, 274, 250, 250)

    for transver_rebar_size, fy, allow in zip(
        transver_rebar_sizes, all_fy, allows
    ):
        ret = fof.get_max_allowed_rebar_distance_due_to_crack_control(
            transver_rebar_size=transver_rebar_size,
            fy=fy,
            cover=cover,
        )
        np.testing.assert_allclose(ret, allow, atol=1)

def test_get_rebar_distance_in_section_width():
    widths=(500,500,400,400,900,900)
    transver_rebar_sizes=(10,10,10,10,12,12)
    cover = 40
    all_rebar_size = (12,12,16,26,25,25)
    all_number_of_rebars = (3,2,2,2,4,5)
    dists = (194, 388, 284, 274, 257, 192.75)
    for beam_width, transver_rebar_size, rebar_size, number_of_rebars, dist in zip(
        widths, transver_rebar_sizes, all_rebar_size, all_number_of_rebars, dists
    ):
        ret = fof.get_rebar_distance_in_section_width(
            section_width=beam_width,
            transver_rebar_size=transver_rebar_size,
            cover=cover,
            rebar_size=rebar_size,
            number_of_rebars=number_of_rebars,
        )
        np.testing.assert_allclose(ret, dist, atol=1)

def test_check_max_allowed_rebar_distance_due_to_crack_control():
    beam_widths=(500,500,400,400,900,900)
    transver_rebar_sizes=(10,10,10,10,12,12)
    all_fy = (400,400,400,400,420,420)
    cover = 40
    all_rebar_size = (12,12,16,26,25,25)
    all_number_of_rebars = (3,2,2,2,4,5)
    results = (True, False, False, False, False, True)
    dists = (194, 388, 284, 274, 257, 192.75)
    allows = (274, 274, 274, 274, 250, 250)

    for beam_width, transver_rebar_size, fy, rebar_size, number_of_rebars, result, dist, allow in zip(
        beam_widths, transver_rebar_sizes, all_fy, all_rebar_size, all_number_of_rebars, results, dists, allows
    ):
        ret = fof.check_max_allowed_rebar_distance_due_to_crack_control(
            beam_width=beam_width,
            transver_rebar_size=transver_rebar_size,
            fy=fy,
            cover=cover,
            rebar_size=rebar_size,
            number_of_rebars=number_of_rebars,
        )
        # print(f"{beam_width=}, {fy=}, {number_of_rebars=}, {rebar_size=}, {ret}, {dist=}, {allow=}")
        np.testing.assert_allclose(ret[1], dist, atol=1)
        np.testing.assert_allclose(ret[2], allow, atol=1)
        assert ret[0] == result

def test_control_mn_end_in_beam():
    as_tops = (1700, 2500, 1800, 2500)
    as_bots = (1600, 2000, 1900, 3000)
    ds = (440, 440, 540, 540)
    fy = 400
    fc = 30
    section_width = 400
    mns = ((276465333.3, 261461333.3), (390833333.3, 320533333.3), (363312000.0, 382001333.3), (490833333.3, 577200000))
    ductility = "high"
    for d, mn, as_top, as_bot in zip(ds, mns, as_tops, as_bots):
        ret, mn_top, mn_bot = fof.control_mn_end_in_beam(
            as_top=as_top,
            as_bot=as_bot,
            fy=fy,
            fc=fc,
            section_width=section_width,
            d_top=d,
            ductility=ductility,
        )
        assert ret
        np.testing.assert_allclose(mn_top, mn[0], atol=1000)
        np.testing.assert_allclose(mn_bot, mn[1], atol=1000)

def test_get_b_joint_shear_of_column():
    column_len_in_direction_of_investigate = 600
    column_len_perpendicular_of_investigate = 400
    beams_width = [200, 300]
    beams_c = [100, 50]
    b = fof.get_b_joint_shear_of_column(
        column_len_in_direction_of_investigate=column_len_in_direction_of_investigate,
        column_len_perpendicular_of_investigate=column_len_perpendicular_of_investigate,
        beams_width=beams_width,
        beams_c=beams_c,
    )
    np.testing.assert_allclose(b, 400, atol=.01)
    beams_c = [0, 0]
    b = fof.get_b_joint_shear_of_column(
        column_len_in_direction_of_investigate=column_len_in_direction_of_investigate,
        column_len_perpendicular_of_investigate=column_len_perpendicular_of_investigate,
        beams_width=beams_width,
        beams_c=beams_c,
    )
    np.testing.assert_allclose(b, 250, atol=.01)
