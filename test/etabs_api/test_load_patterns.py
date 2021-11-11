import pytest
import comtypes.client
from pathlib import Path
import sys

civil_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(civil_path))

from etabs_api import etabs_obj

Tx_drift, Ty_drift = 1.085, 1.085

@pytest.fixture
def shayesteh(edb="shayesteh.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                raise NameError
    except:
        helper = comtypes.client.CreateObject('ETABSv1.Helper') 
        helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
        ETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
        ETABSObject.ApplicationStart()
        SapModel = ETABSObject.SapModel
        SapModel.InitializeNewModel()
        SapModel.File.OpenFile(str(Path(__file__).parent / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.EDB"
        SapModel.File.Save(str(test_file_path))
        etabs = etabs_obj.EtabsModel(backup=False)
        return etabs

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


