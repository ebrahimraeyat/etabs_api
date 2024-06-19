import sys
from pathlib import Path
import pytest

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_get_load_cases():
    load_case_names = etabs.load_cases.get_load_cases()
    assert len(load_case_names) == 22

@open_etabs_file('shayesteh.EDB')
def test_add_response_spectrum_loadcases():
    names = ['XX', 'YY']
    etabs.load_cases.add_response_spectrum_loadcases(names, .05)
    for name in names:
        np.testing.assert_almost_equal(
        [etabs.SapModel.LoadCases.ResponseSpectrum.GetEccentricity(name)[0]],
        [.05], decimal=3)

@open_etabs_file('shayesteh.EDB')
def test_get_modal_loadcase_name():
    name = etabs.load_cases.get_modal_loadcase_name()
    assert name == 'Modal'

@open_etabs_file('shayesteh.EDB')
def test_get_loadcase_withtype():
    name = etabs.load_cases.get_loadcase_withtype(4)
    assert name == ['SX', 'SY', 'SPX', 'SPY']

@open_etabs_file('shayesteh.EDB')
def test_multiply_response_spectrum_scale_factor():
    current_scale = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads('SX')[3][0]
    scales = etabs.load_cases.multiply_response_spectrum_scale_factor('SX', 2)
    ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads('SX')[3]
    assert ret == (current_scale * 2,)
    etabs.load_cases.multiply_response_spectrum_scale_factor('SX', .5, scale_min=None)

@open_etabs_file('shayesteh.EDB')
def test_get_spectral_with_angles():
    ret = etabs.load_cases.get_spectral_with_angles((0, 10, 15, 20, 30))
    assert ret == {0: 'SX'}

@open_etabs_file('shayesteh.EDB')
def test_reset_scales_for_response_spectrums():
    etabs.load_cases.reset_scales_for_response_spectrums()

@open_etabs_file('shayesteh.EDB')
def test_get_response_spectrum_loadcase_name():
    ret = etabs.load_cases.get_response_spectrum_loadcase_name()
    assert ret == ['SX', 'SY', 'SPX', 'SPY']

@open_etabs_file('shayesteh.EDB')
def test_get_response_spectrum_loadcase_with_dir_angle():
    ret = etabs.load_cases.get_response_spectrum_loadcase_with_dir_angle('U1', 0)
    assert ret == 'SX'
    ret = etabs.load_cases.get_response_spectrum_loadcase_with_dir_angle('U2', 0)
    assert ret == 'SY'

@open_etabs_file('shayesteh.EDB')
def test_get_response_spectrum_xy_loadcase_name():
    ret = etabs.load_cases.get_response_spectrum_xy_loadcase_name()
    assert ret == ('SX', 'SY')

@open_etabs_file('shayesteh.EDB')
def test_get_response_spectrum_xy_loadcases_names():
    x_names, y_names = etabs.load_cases.get_response_spectrum_xy_loadcases_names()
    assert set(x_names) == set(['SX', 'SPX'])
    assert set(y_names) == set(['SY', 'SPY'])

@open_etabs_file('shayesteh.EDB')
def test_get_response_spectrum_sxye_loadcases_names():
    sx, sxe, sy, sye = etabs.load_cases.get_response_spectrum_sxye_loadcases_names()
    assert sx == {'SX'}
    assert sxe == {'SPX'}
    assert sy == {'SY'}
    assert sye == {'SPY'}

@open_etabs_file('khiabany.EDB')
def test_get_response_spectrum_sxye_loadcases_names_1():
    sx, sxe, sy, sye = etabs.load_cases.get_response_spectrum_sxye_loadcases_names()
    assert sx == {'SPX'}
    assert sxe == {'SPXE'}
    assert sy == {'SPY'}
    assert sye == {'SPYE'}

@open_etabs_file('madadi.EDB')
def test_get_response_spectrum_sxye_loadcases_names_2():
    sx, sxe, sy, sye = etabs.load_cases.get_response_spectrum_sxye_loadcases_names()
    assert sx == {'SX', 'SX-drift'}
    assert sxe == {'SXE', 'SXE-drift'}
    assert sy == {'SY', 'SY-drift'}
    assert sye == {'SYE', 'SYE-drift'}

@open_etabs_file('steel.EDB')
def test_get_response_spectrum_sxye_loadcases_names_3():
    sx, sxe, sy, sye = etabs.load_cases.get_response_spectrum_sxye_loadcases_names()
    assert sx == {'0.3.SX', 'SX-Base Shear'}
    assert sxe == {'SXPN', 'SXPN-Drift'}
    assert sy == {'0.3.SY', 'SY-Base Shear'}
    assert sye == {'SYPN', 'SYPN-Drift'}

@open_etabs_file('shayesteh.EDB')
def test_get_seismic_load_cases():
    seismic_load_cases = etabs.load_cases.get_seismic_load_cases()
    assert True

@open_etabs_file('shayesteh.EDB')
def test_get_seismic_drift_load_cases():
    seismic_drift_load_cases = etabs.load_cases.get_seismic_drift_load_cases()
    assert len(seismic_drift_load_cases) == 2
    assert seismic_drift_load_cases == ['EX_DRIFT', 'EYDRIFT']


@open_etabs_file('shayesteh.EDB')
def test_get_xy_seismic_load_cases():
    x_seismic_load_cases, y_seismic_load_cases = etabs.load_cases.get_xy_seismic_load_cases()

@open_etabs_file('zibaei.EDB')
def test_get_angular_response_spectrum_with_section_cuts():
    angles, section_cuts, specs, _ = etabs.load_cases.get_angular_response_spectrum_with_section_cuts()
    assert len(angles) == len(section_cuts) == len(specs) == 12

@open_etabs_file('zibaei.EDB')
def test_add_angular_load_cases():
    prefix = 'spec'
    angles = range(0, 180, 10)
    etabs.load_cases.add_angular_load_cases(func="SOIL-III", prefix=prefix, angles=angles)
    angles_spectral = etabs.load_cases.get_spectral_with_angles(angles)
    for angle in angles:
        assert angles_spectral[angle]



if __name__ == "__main__":
    test_get_spectral_with_angles()
