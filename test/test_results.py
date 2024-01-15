import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_get_xy_period():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    Tx, Ty, i_x, i_y = etabs.results.get_xy_period()
    assert pytest.approx(Tx, abs=.01) == 1.291
    assert pytest.approx(Ty, abs=.01) == 1.291
    assert i_x == 2
    assert i_y == 2

def test_get_base_react():
    units = etabs.get_current_unit()
    etabs.set_current_unit('kgf', 'm')
    open_model(etabs=etabs, filename='shayesteh.EDB')
    vx, vy = etabs.results.get_base_react()
    assert vx == pytest.approx(-110709.5, .1)
    assert vy == pytest.approx(-110709.5, .1)
    etabs.set_current_unit(*units)

def test_get_base_react_loadcases():
    units = etabs.get_current_unit()
    etabs.set_current_unit('kgf', 'm')
    open_model(etabs=etabs, filename='shayesteh.EDB')
    V = etabs.results.get_base_react(
        loadcases=['QX', 'QY', 'SPX'],
        directions=['x', 'y', 'x'],
        absolute=True,
        )
    assert V[0] == pytest.approx(110709.5, .1)
    assert V[1] == pytest.approx(110709.5, .1)
    assert V[2] == pytest.approx(58251.6, .1)
    etabs.set_current_unit(*units)

def test_get_point_xy_displacement():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    units = etabs.get_current_unit()
    etabs.set_current_unit('N', 'cm')
    point = '116'
    case = 'DEAD'
    disps = etabs.results.get_point_xy_displacement(point, case, 'Case')
    if etabs.etabs_main_version < 20:
        assert set(disps) == {-0.0508, 0.1243}
    else:
        assert set(disps) == {-0.0499, 0.1241}
    etabs.set_current_unit(*units)

def test_get_points_min_max_displacements():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    units = etabs.get_current_unit()
    etabs.set_current_unit('N', 'cm')
    point = '116'
    case = 'DEAD'
    disps = etabs.results.get_points_min_max_displacements(points=[point],load_cases=[case])
    if etabs.etabs_main_version < 20:
        assert set(disps.loc[(point, case)].values) == {-0.0508, 0.1243, -0.0199}
    else:
        assert set(disps.loc[(point, case)].values) == {-0.0499, 0.1241, -0.0199}
    etabs.set_current_unit(*units)

# def test_get_points_min_max_displacements_nonlinear_cases():
#     # create nonlinear cases
#     open_model(etabs, 'khiabany.EDB')
#     units = etabs.get_current_unit()
#     dead = ['Dead']
#     sd = ['S-DEAD']
#     lives = ['Live', 'Live-0.5', 'L-RED']
#     ret = etabs.database.create_nonlinear_loadcases(dead, sd, lives)
#     # nonlinear load combinations
#     print("Create deflection load combinations ...")
#     etabs.SapModel.RespCombo.Add('deflection1', 0)
#     etabs.SapModel.RespCombo.SetCaseList('deflection1', 0, ret[1], 1)
#     etabs.SapModel.RespCombo.SetCaseList('deflection1', 0, ret[0], -1)
#     etabs.set_current_unit('N', 'cm')
#     etabs.run_analysis()
#     etabs.load_cases.select_load_cases(ret)
#     point = '~215'
#     case = 'Dead+S-DEAD+0.25Live'
#     disps = etabs.results.get_points_min_max_displacements(
#         [point],
#         [case],
#         )
#     assert set(disps.loc[(point, case)].values) == {0, -0.0378, -0.2262}
#     combo = 'deflection1'
#     disps = etabs.results.get_points_min_max_displacements(
#         [point],
#         [combo],
#         type_='Combo',
#         )
#     assert set(disps.loc[(point, combo)].values) == {0.0077, 0.0039, -0.0073}
#     etabs.set_current_unit(*units)


if __name__ == '__main__':
    test_get_point_xy_displacement()