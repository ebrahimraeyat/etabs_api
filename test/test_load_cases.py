import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_get_load_cases():
    load_case_names = etabs.load_cases.get_load_cases()
    assert len(load_case_names) == 22

@pytest.mark.getmethod
def test_get_modal_loadcase_name():
    name = etabs.load_cases.get_modal_loadcase_name()
    assert name == 'Modal'

@pytest.mark.getmethod
def test_get_loadcase_withtype():
    name = etabs.load_cases.get_loadcase_withtype(4)
    assert name == ['SX', 'SY', 'SPX', 'SPY']

@pytest.mark.getmethod
def test_multiply_response_spectrum_scale_factor():
    etabs.load_cases.multiply_response_spectrum_scale_factor('SX', 2)
    ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads('SX')[3]
    assert ret == (3.5198 * 2,)
    etabs.load_cases.multiply_response_spectrum_scale_factor('SX', .5, scale_min=None)

@pytest.mark.getmethod
def test_get_spectral_with_angles():
    ret = etabs.load_cases.get_spectral_with_angles((0, 10, 15, 20, 30))
    assert ret == {15: 'SPEC15', 30: 'SPEC30', 0: 'SX'}

@pytest.mark.setmethod
def test_reset_scales_for_response_spectrums():
    ret = etabs.load_cases.reset_scales_for_response_spectrums()
    assert ret == {15: 'SPEC15', 30: 'SPEC30', 0: 'SX'}

@pytest.mark.getmethod
def test_get_response_spectrum_loadcase_name():
    ret = etabs.load_cases.get_response_spectrum_loadcase_name()
    assert ret == ['SX', 'SY', 'SPX', 'SPY']

@pytest.mark.getmethod
def test_get_response_spectrum_loadcase_with_dir_angle():
    ret = etabs.load_cases.get_response_spectrum_loadcase_with_dir_angle('U1', 0)
    assert ret == 'SX'
    ret = etabs.load_cases.get_response_spectrum_loadcase_with_dir_angle('U2', 0)
    assert ret == 'SY'

@pytest.mark.getmethod
def test_get_response_spectrum_xy_loadcase_name():
    ret = etabs.load_cases.get_response_spectrum_xy_loadcase_name()
    assert ret == ('SX', 'SY')

@pytest.mark.getmethod
def test_get_response_spectrum_xy_loadcases_names():
    x_names, y_names = etabs.load_cases.get_response_spectrum_xy_loadcases_names()
    assert set(x_names) == set(['SX', 'SPX'])
    assert set(y_names) == set(['SY', 'SPY'])

@pytest.mark.getmethod
def test_get_seismic_load_cases():
    seismic_load_cases = etabs.load_cases.get_seismic_load_cases()
    assert True

@pytest.mark.getmethod
def test_get_seismic_drift_load_cases():
    seismic_drift_load_cases = etabs.load_cases.get_seismic_drift_load_cases()
    assert len(seismic_drift_load_cases) == 2
    assert seismic_drift_load_cases == ['EXDRIFT', 'EYDRIFT']


@pytest.mark.getmethod
def test_get_xy_seismic_load_cases():
    x_seismic_load_cases, y_seismic_load_cases = etabs.load_cases.get_xy_seismic_load_cases()
    assert len(x_seismic_load_cases) == 6
    assert len(y_seismic_load_cases) == 6


