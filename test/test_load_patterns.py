import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_get_load_patterns_in_XYdirection(shayesteh):
    shayesteh.SapModel.SetModelIsLocked(False)
    xnames, ynames = shayesteh.load_patterns.get_load_patterns_in_XYdirection()
    assert len(xnames) == 4
    assert len(ynames) == 4
    assert xnames == {'EXDRIFT', 'QX', 'QXN', 'QXP'}
    assert ynames == {'EYDRIFT', 'QY', 'QYN', 'QYP'}

@pytest.mark.getmethod
def test_get_EX_EY_load_pattern(shayesteh):
    xname, yname = shayesteh.load_patterns.get_EX_EY_load_pattern()
    assert xname == 'QX'
    assert yname == 'QY'

@pytest.mark.getmethod
def test_get_special_load_pattern_names(shayesteh):
    drift_names = shayesteh.load_patterns.get_special_load_pattern_names(37)
    eq_names = shayesteh.load_patterns.get_special_load_pattern_names(5)
    dead_names = shayesteh.load_patterns.get_special_load_pattern_names(1)
    # close_etabs(shayesteh)
    assert len(drift_names) == 2
    assert len(eq_names) == 6
    assert len(dead_names) == 1

@pytest.mark.getmethod
def test_get_drift_load_pattern_names(shayesteh):
    names = shayesteh.load_patterns.get_drift_load_pattern_names()
    assert len(names) == 2
    assert names == ['EXDRIFT', 'EYDRIFT']

@pytest.mark.getmethod
def test_get_load_patterns(shayesteh):
    load_pattern_names = shayesteh.load_patterns.get_load_patterns()
    assert len(load_pattern_names) == 17

@pytest.mark.getmethod
def test_get_xy_seismic_load_patterns(shayesteh):
    names = shayesteh.load_patterns.get_xy_seismic_load_patterns()
    assert len(names) == 6

@pytest.mark.getmethod
def test_get_xy_spectral_load_patterns_with_angle(shayesteh):
    x_names, y_names = shayesteh.load_patterns.get_xy_spectral_load_patterns_with_angle(angle=0)
    assert x_names == ['SPX', 'SX']
    assert y_names == ['SPY', 'SY']

@pytest.mark.selectmethod
def test_select_all_load_patterns(shayesteh):
    shayesteh.load_patterns.select_all_load_patterns()
    assert True

def test_get_ex_ey_earthquake_name(shayesteh):
    ex, ey = shayesteh.load_patterns.get_ex_ey_earthquake_name()
    assert ex == 'QX'
    assert ey == 'QY'

def test_get_design_type(shayesteh):
    type_ = shayesteh.load_patterns.get_design_type('DEAD')
    assert type_ == 'Dead'

@pytest.mark.getmethod
def test_get_seismic_load_patterns(shayesteh):
    names = shayesteh.load_patterns.get_seismic_load_patterns()
    assert names[0] == {'QX'}
    assert names[1] == {'QXN'}
    assert names[2] == {'QXP'}
    assert names[3] == {'QY'}
    assert names[4] == {'QYN'}
    assert names[5] == {'QYP'}
