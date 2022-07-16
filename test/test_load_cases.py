import pytest
import comtypes.client
from pathlib import Path
import sys
import shutil
import tempfile

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

import etabs_obj


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
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 19\ETABS.exe'
            )
        temp_path = Path(tempfile.gettempdir())
        test_file_path = temp_path / "test.EDB"
        etabs.SapModel.File.Save(str(test_file_path))
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

@pytest.mark.getmethod
def test_get_seismic_load_cases(shayesteh):
    seismic_load_cases = shayesteh.load_cases.get_seismic_load_cases()
    assert True

@pytest.mark.getmethod
def test_get_seismic_drift_load_cases(shayesteh):
    seismic_drift_load_cases = shayesteh.load_cases.get_seismic_drift_load_cases()
    assert len(seismic_drift_load_cases) == 6

@pytest.mark.getmethod
def test_get_xy_seismic_load_cases(shayesteh):
    x_seismic_load_cases, y_seismic_load_cases = shayesteh.load_cases.get_xy_seismic_load_cases()
    assert len(x_seismic_load_cases) == 6
    assert len(y_seismic_load_cases) == 6


