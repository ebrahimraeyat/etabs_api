import sys
from pathlib import Path
import pytest
from unittest.mock import Mock
import tempfile

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version, get_temp_filepath

Tx_drift, Ty_drift = 1.085, 1.085

# def close_etabs(ETABS):
#     SapModel = ETABS.SapModel
#     test_file_path = Path(SapModel.GetModelFilename())
#     etabs.close_etabs(ETABS)
#     test_files = test_file_path.parent.glob('test.*')
#     for f in test_files:
#         f.unlink()

def create_building():
    building = Mock()
    building.results = [True, .123, .108]
    building.kx, building.ky = 1.18, 1.15
    building.results_drift = [True, .89, .98]
    building.kx_drift, building.ky_drift = 1.15, 1.2
    return building

def test_get_etabs_main_version():
    ver = etabs.get_etabs_main_version()
    assert ver == version

def test_get_filename_with_suffix():
    open_model(etabs, 'shayesteh.EDB')
    name = etabs.get_filename_with_suffix()
    assert name == f'test{version}.EDB'
    open_model(etabs, "madadi.EDB")
    name = etabs.get_filename_with_suffix()
    assert name == f'test{version}.EDB'
    name = etabs.get_filename_with_suffix('.e2k')
    assert name == f'test{version}.e2k'
    
def test_get_from_list_table():
    open_model(etabs, 'shayesteh.EDB')
    data = [['STORY5', 'QX', 'LinStatic', None, None, None, 'Top', '0', '0'],
            ['STORY5', 'QX', 'LinStatic', None, None, None, 'Bottom', '0', '0'],
            ['STORY4', 'QX', 'LinRespSpec', 'Max', None, None, 'Bottom', '0', '25065.77']]
    columns = (1, 6)
    values = ('QX', 'Bottom')
    result = etabs.get_from_list_table(data, columns, values)
    assert list(result) == [['STORY5', 'QX', 'LinStatic', None, None, None, 'Bottom', '0', '0'],
            ['STORY4', 'QX', 'LinRespSpec', 'Max', None, None, 'Bottom', '0', '25065.77']]
    # len columns = 1
    columns = (6,)
    values = ('Bottom',)
    result = etabs.get_from_list_table(data, columns, values)
    assert list(result) == [['STORY5', 'QX', 'LinStatic', None, None, None, 'Bottom', '0', '0'],
            ['STORY4', 'QX', 'LinRespSpec', 'Max', None, None, 'Bottom', '0', '25065.77']]

def test_get_main_periods():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    tx_drift, ty_drift = etabs.get_main_periods()
    assert pytest.approx(tx_drift, .001) == 1.291
    assert pytest.approx(ty_drift, .001) == 1.291

def test_get_drift_periods():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    Tx_drift, Ty_drift, file_name = etabs.get_drift_periods()
    assert pytest.approx(Tx_drift, .01) == 1.085
    assert pytest.approx(Ty_drift, .01) == 1.085
    assert file_name.name == f"test{version}.EDB"

def test_get_drift_periods_steel():
    open_model(etabs=etabs, filename='steel.EDB')
    Tx_drift, Ty_drift, file_name = etabs.get_drift_periods(structure_type='steel')
    assert file_name.name == f"test{version}.EDB"
    assert pytest.approx(Tx_drift, .01) == 0.789
    assert pytest.approx(Ty_drift, .01) == 0.449
    # did not open main file after get tx, ty
    assert etabs.get_filename_with_suffix() == f'test{version}_drift.EDB'
    drift_file_path = Path(tempfile.gettempdir()) / 'periods' / f'test{version}_drift.EDB'
    assert drift_file_path.exists()

    
def test_apply_cfactor_to_edb():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    building = create_building()
    NumFatalErrors = etabs.apply_cfactor_to_edb(building)
    ret = etabs.SapModel.Analyze.RunAnalysis()
    assert NumFatalErrors == 0
    assert ret == 0

def test_apply_cfactors_to_edb():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    data = [
        (['QX', 'QXN'], ["STORY5", "STORY1", '0.128', '1.37']),
        (['QY', 'QYN'], ["STORY4", "STORY2", '0.228', '1.39']),
        (['QX1', 'QXN1', 'QXP1'], ["STORY5", "BASE", '0.128', '1.37']),
        (['QY1', 'QYN1', 'QYP1'], ["STORY4", "BASE", '0.228', '1.39']),
        (['QY1drift', 'QYN1drift', 'QYP1drift'], ["STORY4", "BASE", '0.208', '1.29']),
        ]
    d = {}
    d['ex_combobox'] = 'QX'
    d['exn_combobox'] = 'QXN'
    d['exp_combobox'] = 'QXP'
    d['ey_combobox'] = 'QY'
    d['eyn_combobox'] = 'QYN'
    d['eyp_combobox'] = 'QYP'
    d['ex1_combobox'] = 'QX1'
    d['exn1_combobox'] = 'QXN1'
    d['exp1_combobox'] = 'QXP1'
    d['ey1_combobox'] = 'QY1'
    d['eyn1_combobox'] = 'QYN1'
    d['eyp1_combobox'] = 'QYP1'
    d['ey1_drift_combobox'] = 'QY1drift'
    d['eyn1_drift_combobox'] = 'QYN1drift'
    d['eyp1_drift_combobox'] = 'QYP1drift'
    d['activate_second_system'] = True
    errors = etabs.apply_cfactors_to_edb(data, d)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    for earthquake, new_data in data:
        assert len(df.loc[df.Name.isin(earthquake)]) == len(earthquake)
        ret = df.loc[df.Name.isin(earthquake), ['TopStory', 'BotStory', 'C', 'K']] == new_data
        assert ret.all().all()
    for lp in ('QX', 'QXN', 'QXP', 'QY', 'QYN', 'QYP', 'QX1', 'QXN1', 'QXP1', 'QY1', 'QYN1', 'QYP1'):
        assert etabs.SapModel.LoadPatterns.GetLoadType(lp)[0] == 5
    for lp in ('QY1drift', 'QYN1drift', 'QYP1drift'):
        assert etabs.SapModel.LoadPatterns.GetLoadType(lp)[0] == etabs.seismic_drift_load_type
    assert errors == 0

def test_get_diaphragm_max_over_avg_drifts():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    table = etabs.get_diaphragm_max_over_avg_drifts()
    assert len(table) == 20

def test_get_magnification_coeff_aj():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    df = etabs.get_magnification_coeff_aj()
    assert len(df) == 9

def test_get_story_forces_with_percentages():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    forces, _ = etabs.get_story_forces_with_percentages()
    assert len(forces) == 10

def test_get_drifts():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    no_story, cdx, cdy = 4, 4.5, 4.5
    drifts, headers = etabs.get_drifts(no_story, cdx, cdy)
    assert len(drifts[0]) == len(headers)
    assert len(drifts) == 10
    print(drifts)
    # drifts is look like this
    # [['STORY5', 'EX_DRIFT', 'LinStatic', None, None, None, 'Diaph D1 X', '0.001227',
    # None, '0.001152', '1.065', '7', '11.81', '5', '18.68', '0.0056'], [...]]
    ret_drifts = [.0012, .0025, .0043, .0038, .0057, .0049, .0056, .0049, .0038, .0034]
    for i, dr in enumerate(ret_drifts):
        assert pytest.approx(dr, abs=0.0001) == float(drifts[i][5])

def test_get_irregularity_of_mass():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    iom, fields = etabs.get_irregularity_of_mass()
    assert len(iom) == 5
    assert len(iom[0]) == len(fields)

def test_get_story_stiffness_modal_way():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    # dx = dy = {
    #             'STORY5' : 5,
    #             'STORY4' : 4,
    #             'STORY3' : 3,
    #             'STORY2' : 2,
    #             'STORY1' : 1,
    #         }
    # wx = wy = 1
    # mocker.patch(
    #     'etabs_api.database.DataBaseTables.get_stories_displacement_in_xy_modes',
    #     return_value = (dx, dy, wx, wy))
    # mocker.patch(
    #     'etabs_api.etabs_obj.EtabsModel.get_story_stiffness_modal_way',
    #     return_value = (
    #         ('STORY1', '1'),
    #         ('STORY2', '1'),
    #         ('STORY3', '1'),
    #         ('STORY4', '1'),
    #         ('STORY5', '1'),
    #         ))
    story_stiffness = etabs.get_story_stiffness_modal_way()
    assert len(story_stiffness) == 5
    desired_story_stiffness = {
        'STORY1': [3981106.61, 4123839.81],
        'STORY2': [3907090.56, 3828170.06],
        'STORY3': [2941770.48, 2917066.37],
        'STORY4': [2199361.67, 2148767.10],
        'STORY5': [741428.62, 426294.86],
    }
    for story, stiff in story_stiffness.items():
        np.testing.assert_almost_equal(
            [i / 10e4 for i in stiff],
            [i / 10e4 for i in desired_story_stiffness[story]],
            decimal=0,
            )

def test_set_current_unit():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.set_current_unit('kgf', 'm')
    assert etabs.SapModel.GetPresentUnits_2()[:-1] == [5, 6, 2]
    assert etabs.SapModel.GetPresentUnits() == 8

def test_add_prefix_suffix_name():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    path = etabs.add_prefix_suffix_name(prefix='asli_', suffix='_x', open=False)
    assert path.name == f'asli_test{version}_x.EDB'

def test_create_joint_shear_bcc_file():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    from shayesteh import get_temp_filepath
    filename = get_temp_filepath(filename='js_bc')
    df = etabs.create_joint_shear_bcc_file(file_name=filename.name, open_main_file=True)
    assert len(df) > 0


def test_get_type_of_structure():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    typ = etabs.get_type_of_structure()
    assert typ == 'concrete'
    open_model(etabs=etabs, filename='steel.EDB')
    typ = etabs.get_type_of_structure()
    assert typ == 'steel'
    etabs.frame_obj.delete_frames()
    typ = etabs.get_type_of_structure()
    assert typ == 'concrete'


def test_start_slab_design():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    with pytest.raises(NotImplementedError) as err:
        etabs.start_slab_design()
    assert True

def test_angles_response_spectrums_analysis():
    open_model(etabs=etabs, filename='zibaei.EDB')
    scales = etabs.angles_response_spectrums_analysis(
        ex_name='EX',
        ey_name='EY',
        specs=['SPECT0', 'SPECT105', 'SPECT120', 'SPECT135', 'SPECT15', 'SPECT150', 'SPECT165', 'SPECT30', 'SPECT45', 'SPECT60', 'SPECT75', 'SPECT90'],
        section_cuts=['SEC0', 'SEC105', 'SEC120', 'SEC135', 'SEC15', 'SEC150', 'SEC165', 'SEC30', 'SEC45', 'SEC60', 'SEC75', 'SEC90'],
        analyze=False,
    )
    for scale in scales:
        assert pytest.approx(scale, abs=.001) == 1

def test_check_seismic_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    n1 = len(etabs.load_patterns.get_load_patterns())
    d = {}
    d['ex_combobox'] = 'QX'
    d['exn_combobox'] = 'QXN'
    d['exp_combobox'] = 'QXP'
    d['ey_combobox'] = 'QY'
    d['eyn_combobox'] = 'QYN'
    d['eyp_combobox'] = 'QYP'
    d['ex1_combobox'] = 'QX1'
    d['exn1_combobox'] = 'QXN1'
    d['exp1_combobox'] = 'QXP1'
    d['ey1_combobox'] = 'QY1'
    d['eyn1_combobox'] = 'QYN1'
    d['eyp1_combobox'] = 'QYP1'
    d['activate_second_system'] = True
    df = etabs.check_seismic_names(d)
    assert set(df.Name) == set(({
        'EXDRIFT',
        'QX',
        'QXN',
        'QXP',
        'EYDRIFT',
        'QY',
        'QYN',
        'QYP',
        'QX1',
        'QXN1',
        'QXP1',
        'QY1',
        'QYN1',
        'QYP1',
        'EX(Drift)',
        'EXN(Drift)',
        'EXP(Drift)',
        'EY(Drift)',
        'EYN(Drift)',
        'EYP(Drift)',
        'EX1(Drift)',
        'EXN1(Drift)',
        'EXP1(Drift)',
        'EY1(Drift)',
        'EYN1(Drift)',
        'EYP1(Drift)',
        }))
    filt = df.Name.isin(('QYN1', 'QXN1', 'QXP1', 'EXN(Drift)', 'EXP(Drift)', 'EYN(Drift)', 'EYP(Drift)'))
    ecc = df.loc[filt]['EccRatio']
    assert float(ecc.min()) == float(ecc.max()) == 0.05
    assert len(df) == 26
    n2 = len(etabs.load_patterns.get_load_patterns())
    assert (n2 - n1) == 18
    assert n1 == 17
    assert n2 == 35



if __name__ == '__main__':
    test_start_slab_design()


