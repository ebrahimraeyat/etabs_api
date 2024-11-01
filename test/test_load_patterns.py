import sys
from pathlib import Path
import pytest

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_get_load_patterns_in_XYdirection():
    etabs.SapModel.SetModelIsLocked(False)
    xnames, ynames = etabs.load_patterns.get_load_patterns_in_XYdirection()
    assert len(xnames) == 4
    assert len(ynames) == 4
    assert xnames == {'EXDRIFT', 'QX', 'QXN', 'QXP'}
    assert ynames == {'EYDRIFT', 'QY', 'QYN', 'QYP'}

@open_etabs_file('shayesteh.EDB')
def test_get_all_seismic_load_patterns():
    etabs.SapModel.SetModelIsLocked(False)
    names = etabs.load_patterns.get_all_seismic_load_patterns()
    assert len(names) == 8
    assert names == {'EXDRIFT', 'QX', 'QXN', 'QXP', 'EYDRIFT', 'QY', 'QYN', 'QYP'}

@open_etabs_file('shayesteh.EDB')
def test_get_EX_EY_load_pattern():
    xname, yname = etabs.load_patterns.get_EX_EY_load_pattern()
    assert xname == 'QX'
    assert yname == 'QY'

@open_etabs_file('shayesteh.EDB')
def test_get_special_load_pattern_names():
    drift_names = etabs.load_patterns.get_special_load_pattern_names(etabs.seismic_drift_load_type)
    eq_names = etabs.load_patterns.get_special_load_pattern_names(5)
    dead_names = etabs.load_patterns.get_special_load_pattern_names(1)
    # close_etabs(shayesteh)
    assert len(drift_names) == 2
    assert len(eq_names) == 6
    assert len(dead_names) == 1

@open_etabs_file('shayesteh.EDB')
def test_get_drift_load_pattern_names():
    names = etabs.load_patterns.get_drift_load_pattern_names()
    assert len(names) == 2
    assert names == ['EXDRIFT', 'EYDRIFT']

@open_etabs_file('steel.EDB')
def test_get_notional_load_pattern_names():
    names = etabs.load_patterns.get_notional_load_pattern_names()
    assert len(names) == 12

@open_etabs_file('shayesteh.EDB')
def test_get_load_patterns():
    load_pattern_names = etabs.load_patterns.get_load_patterns()
    assert len(load_pattern_names) == 17

@open_etabs_file('shayesteh.EDB')
def test_get_xy_seismic_load_patterns():
    names = etabs.load_patterns.get_xy_seismic_load_patterns()
    assert len(names) == 6

@open_etabs_file('shayesteh.EDB')
def test_get_xy_spectral_load_patterns_with_angle():
    x_names, y_names = etabs.load_patterns.get_xy_spectral_load_patterns_with_angle(angle=0)
    assert set(x_names) == {'SPX', 'SX'}
    assert set(y_names) == {'SPY', 'SY'}

@open_etabs_file('shayesteh.EDB')
def test_select_all_load_patterns():
    etabs.load_patterns.select_all_load_patterns()
    assert True

@open_etabs_file('shayesteh.EDB')
def test_get_ex_ey_earthquake_name():
    ex, ey = etabs.load_patterns.get_ex_ey_earthquake_name()
    assert ex == 'QX'
    assert ey == 'QY'

@open_etabs_file('shayesteh.EDB')
def test_get_design_type():
    type_ = etabs.load_patterns.get_design_type('DEAD')
    assert type_ == 'Dead'

@open_etabs_file('shayesteh.EDB')
def test_get_seismic_load_patterns():
    names = etabs.load_patterns.get_seismic_load_patterns()
    assert names[0] == {'QX'}
    assert names[1] == {'QXN'}
    assert names[2] == {'QXP'}
    assert names[3] == {'QY'}
    assert names[4] == {'QYN'}
    assert names[5] == {'QYP'}

@open_etabs_file('shayesteh.EDB')
def test_get_seismic_load_patterns_drifts():
    names = etabs.load_patterns.get_seismic_load_patterns(drifts=True)
    assert names[0] == {'EXDRIFT'}
    assert names[1] == set()
    assert names[2] == set()
    assert names[3] == {'EYDRIFT'}
    assert names[4] == set()
    assert names[5] == set()

@open_etabs_file('two_earthquakes.EDB')
def test_get_expanded_seismic_load_patterns():
    df, loads, loads_type = etabs.load_patterns.get_expanded_seismic_load_patterns()
    assert len(df) == 19
    assert len(loads) == 6
    assert set(df.Name) == {'EX1', 'EX1P','EX1N', 'EY1', 'EY1P','EY1N', 'EX2', 'EX2P','EX2N', 'EY2', 'EY2P','EY2N', 'EDRIFTY', 'EDRIFTYN', 'EDRIFTYP', 'EDRIFTX'}
    assert set(loads.keys()) == {'EDRIFTX', 'EX1', 'EY1' , 'EX2', 'EY2', 'EDRIFTY'}
    assert loads_type['EDRIFTYN'] == loads_type['EDRIFTYP'] == loads_type['EDRIFTX'] == etabs.seismic_drift_load_type
    assert loads_type['EX1'] == loads_type['EY1'] == loads_type['EX2'] == 5


@open_etabs_file('two_earthquakes.EDB')
def test_get_expanded_seismic_load_patterns_apply():
    df, _, _ = etabs.load_patterns.get_expanded_seismic_load_patterns()
    etabs.database.write_seismic_user_coefficient_df(df)

@open_etabs_file('shayesteh.EDB')
def test_add_load_patterns():
    names = ['Nx', 'Ny']
    type_ = 'Notional'
    ret = etabs.load_patterns.add_load_patterns(names, type_)
    assert ret
    all_load_patterns = etabs.load_patterns.get_load_patterns()
    for name in names:
        assert name in all_load_patterns
        cases = etabs.SapModel.LoadCases.StaticLinear.GetLoads(name)
        assert cases[2][0] == name

@open_etabs_file('two_earthquakes.EDB')
def test_add_notional_loads():
    names = ['DL', 'LL', 'L2']
    etabs.load_patterns.add_notional_loads(names)
    table_key = "Load Pattern Definitions - Auto Notional Loads"
    df = etabs.database.read(table_key, to_dataframe=True)
    for name in names:
        assert f'N{name}X' in df.LoadPattern.unique()
        assert f'N{name}Y' in df.LoadPattern.unique()
    
@open_etabs_file('two_earthquakes.EDB')
def test_get_earthquake_values():
    names = ["EX1", "EY1", "EX2"]
    ret = etabs.load_patterns.get_earthquake_values(names)
    np.testing.assert_allclose(ret, [0.072, .072, 0.15], rtol=0.001)
    names = ["EX2", "EY1", "EX1"]
    ret = etabs.load_patterns.get_earthquake_values(names)
    np.testing.assert_allclose(ret, [0.15, 0.072, .072], rtol=0.001)

if __name__ == '__main__':
    import etabs_obj
    two_earthquakes = etabs_obj.EtabsModel(backup=True)
    ret = test_get_expanded_seismic_load_patterns()
    print('wow')
