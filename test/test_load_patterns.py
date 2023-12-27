import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_get_load_patterns_in_XYdirection():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.SapModel.SetModelIsLocked(False)
    xnames, ynames = etabs.load_patterns.get_load_patterns_in_XYdirection()
    assert len(xnames) == 4
    assert len(ynames) == 4
    assert xnames == {'EXDRIFT', 'QX', 'QXN', 'QXP'}
    assert ynames == {'EYDRIFT', 'QY', 'QYN', 'QYP'}

def test_get_all_seismic_load_patterns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.SapModel.SetModelIsLocked(False)
    names = etabs.load_patterns.get_all_seismic_load_patterns()
    assert len(names) == 8
    assert names == {'EXDRIFT', 'QX', 'QXN', 'QXP', 'EYDRIFT', 'QY', 'QYN', 'QYP'}

def test_get_EX_EY_load_pattern():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    xname, yname = etabs.load_patterns.get_EX_EY_load_pattern()
    assert xname == 'QX'
    assert yname == 'QY'

def test_get_special_load_pattern_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    drift_names = etabs.load_patterns.get_special_load_pattern_names(etabs.seismic_drift_load_type)
    eq_names = etabs.load_patterns.get_special_load_pattern_names(5)
    dead_names = etabs.load_patterns.get_special_load_pattern_names(1)
    # close_etabs(shayesteh)
    assert len(drift_names) == 2
    assert len(eq_names) == 6
    assert len(dead_names) == 1

def test_get_drift_load_pattern_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.load_patterns.get_drift_load_pattern_names()
    assert len(names) == 2
    assert names == ['EXDRIFT', 'EYDRIFT']

def test_get_load_patterns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    load_pattern_names = etabs.load_patterns.get_load_patterns()
    print(load_pattern_names)
    assert len(load_pattern_names) == 17

def test_get_xy_seismic_load_patterns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.load_patterns.get_xy_seismic_load_patterns()
    assert len(names) == 6

def test_get_xy_spectral_load_patterns_with_angle():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    x_names, y_names = etabs.load_patterns.get_xy_spectral_load_patterns_with_angle(angle=0)
    assert set(x_names) == {'SPX', 'SX'}
    assert set(y_names) == {'SPY', 'SY'}

def test_select_all_load_patterns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.load_patterns.select_all_load_patterns()
    assert True

def test_get_ex_ey_earthquake_name():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ex, ey = etabs.load_patterns.get_ex_ey_earthquake_name()
    assert ex == 'QX'
    assert ey == 'QY'

def test_get_design_type():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    type_ = etabs.load_patterns.get_design_type('DEAD')
    assert type_ == 'Dead'

def test_get_seismic_load_patterns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.load_patterns.get_seismic_load_patterns()
    assert names[0] == {'QX'}
    assert names[1] == {'QXN'}
    assert names[2] == {'QXP'}
    assert names[3] == {'QY'}
    assert names[4] == {'QYN'}
    assert names[5] == {'QYP'}

def test_get_seismic_load_patterns_drifts():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.load_patterns.get_seismic_load_patterns(drifts=True)
    assert names[0] == {'EXDRIFT'}
    assert names[1] == set()
    assert names[2] == set()
    assert names[3] == {'EYDRIFT'}
    assert names[4] == set()
    assert names[5] == set()

def test_get_expanded_seismic_load_patterns():
    open_model(etabs=etabs, filename='two_earthquakes.EDB')
    df, loads, loads_type = etabs.load_patterns.get_expanded_seismic_load_patterns()
    assert len(df) == 19
    assert len(loads) == 6
    assert set(df.Name) == {'EX1', 'EX1P','EX1N', 'EY1', 'EY1P','EY1N', 'EX2', 'EX2P','EX2N', 'EY2', 'EY2P','EY2N', 'EDRIFTY', 'EDRIFTYN', 'EDRIFTYP', 'EDRIFTX'}
    assert set(loads.keys()) == {'EDRIFTX', 'EX1', 'EY1' , 'EX2', 'EY2', 'EDRIFTY'}
    assert loads_type['EDRIFTYN'] == loads_type['EDRIFTYP'] == loads_type['EDRIFTX'] == etabs.seismic_drift_load_type
    assert loads_type['EX1'] == loads_type['EY1'] == loads_type['EX2'] == 5


def test_get_expanded_seismic_load_patterns_apply():
    open_model(etabs=etabs, filename='two_earthquakes.EDB')
    df, _, _ = etabs.load_patterns.get_expanded_seismic_load_patterns()
    etabs.database.write_seismic_user_coefficient_df(df)

def test_add_load_patterns():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = ['Nx', 'Ny']
    type_ = 'Notional'
    ret = etabs.load_patterns.add_load_patterns(names, type_)
    assert ret
    all_load_patterns = etabs.load_patterns.get_load_patterns()
    for name in names:
        assert name in all_load_patterns

def test_add_notional_loads():
    open_model(etabs=etabs, filename='two_earthquakes.EDB')
    names = ['DL', 'LL', 'L2']
    etabs.load_patterns.add_notional_loads(names)
    table_key = "Load Pattern Definitions - Auto Notional Loads"
    df = etabs.database.read(table_key, to_dataframe=True)
    for name in names:
        assert f'N{name}X' in df.LoadPattern.unique()
        assert f'N{name}Y' in df.LoadPattern.unique()
    

if __name__ == '__main__':
    import etabs_obj
    two_earthquakes = etabs_obj.EtabsModel(backup=True)
    ret = test_get_expanded_seismic_load_patterns()
    print('wow')
