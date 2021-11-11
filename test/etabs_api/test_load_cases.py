import pytest
import comtypes.client
from pathlib import Path
import sys

civil_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(civil_path))
from etabs_api import etabs_obj

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
        else:
            raise FileNotFoundError
    except FileNotFoundError:
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
def test_get_load_cases(shayesteh):
    load_case_names = shayesteh.load_cases.get_load_cases()
    assert len(load_case_names) == 22

@pytest.mark.getmethod
def test_get_modal_loadcase_name(shayesteh):
    name = shayesteh.load_cases.get_modal_loadcase_name()
    assert name == 'Modal'

@pytest.mark.getmethod
def test_get_loadcase_withtype(shayesteh):
    name = shayesteh.load_cases.get_loadcase_withtype(4)
    assert name == ['SX', 'SY', 'SPX', 'SPY']

@pytest.mark.getmethod
def test_multiply_response_spectrum_scale_factor(shayesteh):
    shayesteh.load_cases.multiply_response_spectrum_scale_factor('SX', 2)
    ret = shayesteh.SapModel.LoadCases.ResponseSpectrum.GetLoads('SX')[3]
    assert ret == (3.5198 * 2,)
    shayesteh.load_cases.multiply_response_spectrum_scale_factor('SX', .5, scale_min=None)

@pytest.mark.getmethod
def test_get_spectral_with_angles(shayesteh):
    ret = shayesteh.load_cases.get_spectral_with_angles((0, 10, 15, 20, 30))
    assert ret == {15: 'SPEC15', 30: 'SPEC30', 0: 'SX'}

@pytest.mark.setmethod
def test_reset_scales_for_response_spectrums(shayesteh):
    ret = shayesteh.load_cases.reset_scales_for_response_spectrums()
    assert ret == {15: 'SPEC15', 30: 'SPEC30', 0: 'SX'}

@pytest.mark.getmethod
def test_get_response_spectrum_loadcase_name(shayesteh):
    ret = shayesteh.load_cases.get_response_spectrum_loadcase_name()
    assert ret == ['SX', 'SY', 'SPX', 'SPY']

@pytest.mark.getmethod
def test_get_response_spectrum_loadcase_with_dir_angle(shayesteh):
    ret = shayesteh.load_cases.get_response_spectrum_loadcase_with_dir_angle('U1', 0)
    assert ret == 'SX'
    ret = shayesteh.load_cases.get_response_spectrum_loadcase_with_dir_angle('U2', 0)
    assert ret == 'SY'

@pytest.mark.getmethod
def test_get_response_spectrum_xy_loadcase_name(shayesteh):
    ret = shayesteh.load_cases.get_response_spectrum_xy_loadcase_name()
    assert ret == ('SX', 'SY')

@pytest.mark.getmethod
def test_get_response_spectrum_xy_loadcases_names(shayesteh):
    x_names, y_names = shayesteh.load_cases.get_response_spectrum_xy_loadcases_names()
    assert set(x_names) == set(['SX', 'SPX'])
    assert set(y_names) == set(['SY', 'SPY'])

