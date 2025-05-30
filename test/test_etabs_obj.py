import sys
from pathlib import Path
import pytest
from unittest.mock import Mock
import tempfile

import numpy as np
import pandas as pd

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file, version, get_temp_filepath

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

@open_etabs_file('shayesteh.EDB')
def test_get_etabs_main_version():
    ver = etabs.get_etabs_main_version()
    assert ver == version

@open_etabs_file('sap2000.sdb')
def test_get_sap_main_version():
    import os
    software = os.environ.get('software_name', "ETABS")
    os.environ.setdefault('software_name', "SAP2000")
    ver = etabs.get_etabs_main_version()
    assert ver == version
    os.environ.setdefault('software_name', software)



@open_etabs_file('shayesteh.EDB')
def test_get_filename_with_suffix():
    name = etabs.get_filename_with_suffix()
    assert name == f'test{version}.EDB'

@open_etabs_file('madadi.EDB')
def test_get_filename_with_suffix_1():
    name = etabs.get_filename_with_suffix()
    assert name == f'test{version}.EDB'
    name = etabs.get_filename_with_suffix('.e2k')
    assert name == f'test{version}.e2k'
    
@open_etabs_file('shayesteh.EDB')
def test_get_from_list_table():
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

@open_etabs_file('shayesteh.EDB')
def test_get_main_periods():
    tx_drift, ty_drift = etabs.get_main_periods()
    assert pytest.approx(tx_drift, .001) == 1.291
    assert pytest.approx(ty_drift, .001) == 1.291

@open_etabs_file('shayesteh.EDB')
def test_get_drift_periods():
    Tx_drift, Ty_drift, file_name = etabs.get_drift_periods()
    assert pytest.approx(Tx_drift, .01) == 1.085
    assert pytest.approx(Ty_drift, .01) == 1.085
    assert file_name.name == f"test{version}.EDB"

@open_etabs_file('steel.EDB')
def test_get_drift_periods_steel():
    Tx_drift, Ty_drift, file_name = etabs.get_drift_periods(structure_type='steel')
    assert file_name.name == f"test{version}.EDB"
    assert pytest.approx(Tx_drift, .01) == 0.789
    assert pytest.approx(Ty_drift, .01) == 0.449
    # did not open main file after get tx, ty
    assert etabs.get_filename_with_suffix() == f'test{version}_drift.EDB'
    drift_file_path = Path(tempfile.gettempdir()) / 'periods' / f'test{version}_drift.EDB'
    assert drift_file_path.exists()

@open_etabs_file('shayesteh.EDB')
def test_apply_cfactor_to_edb():
    building = create_building()
    NumFatalErrors = etabs.apply_cfactor_to_edb(building)
    ret = etabs.SapModel.Analyze.RunAnalysis()
    assert NumFatalErrors == 0
    assert ret == 0

@open_etabs_file('shayesteh.EDB')
def test_apply_cfactors_to_edb():
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

@open_etabs_file('shayesteh.EDB')
def test_get_diaphragm_max_over_avg_drifts():
    table = etabs.get_diaphragm_max_over_avg_drifts()
    assert len(table) == 20

@open_etabs_file('shayesteh.EDB')
def test_get_magnification_coeff_aj():
    df = etabs.get_magnification_coeff_aj()
    assert len(df) == 9

@open_etabs_file('shayesteh.EDB')
def test_get_story_forces_with_percentages():
    forces, _ = etabs.get_story_forces_with_percentages()
    assert len(forces) == 10

@open_etabs_file('shayesteh.EDB')
def test_get_drifts():
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

@open_etabs_file('shayesteh.EDB')
def test_get_irregularity_of_mass():
    iom, fields = etabs.get_irregularity_of_mass()
    assert len(iom) == 5
    assert len(iom[0]) == len(fields)

@open_etabs_file('shayesteh.EDB')
def test_get_story_stiffness_modal_way():
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

@open_etabs_file('shayesteh.EDB')
def test_get_story_stiffness_2800_way():
    story_stiffness = etabs.get_story_stiffness_2800_way()
    assert len(story_stiffness) == 5
    desired_story_stiffness = {
         'STORY1': [6099792.60705136, 5693139.766581269],
         'STORY2': [9272997.032640949, 8692628.650904033],
         'STORY3': [6838074.398249453, 6475425.75924367],
         'STORY4': [4512024.545413528, 4195334.78771606],
         'STORY5': [975333.8079957867, 1225925.8805212637],
         }
    for story, stiff in story_stiffness.items():
        np.testing.assert_almost_equal(
            [i / 10e4 for i in stiff],
            [i / 10e4 for i in desired_story_stiffness[story]],
            decimal=0,
            )

@open_etabs_file('shayesteh.EDB')
def test_set_current_unit():
    etabs.set_current_unit('kgf', 'm')
    assert etabs.SapModel.GetPresentUnits_2()[:-1] == [5, 6, 2]
    assert etabs.SapModel.GetPresentUnits() == 8

@open_etabs_file('sap2000.sdb')
def test_set_current_unit_sap():
    etabs.set_current_unit('kgf', 'm')
    assert etabs.SapModel.GetPresentUnits() == 8

@open_etabs_file('shayesteh.EDB')
def test_add_prefix_suffix_name():
    path = etabs.add_prefix_suffix_name(prefix='asli_', suffix='_x', open=False)
    assert path.name == f'asli_test{version}_x.EDB'

@open_etabs_file('shayesteh.EDB')
def test_create_joint_shear_bcc_file():
    from shayesteh import get_temp_filepath
    filename = get_temp_filepath(filename='js_bc')
    df = etabs.create_joint_shear_bcc_file(file_name=filename.name, open_main_file=True)
    assert len(df) > 0


@open_etabs_file('shayesteh.EDB')
def test_get_type_of_structure():
    typ = etabs.get_type_of_structure()
    assert typ == 'concrete'

@open_etabs_file('steel.EDB')
def test_get_type_of_structureـ۱():
    typ = etabs.get_type_of_structure()
    assert typ == 'steel'
    etabs.frame_obj.delete_frames()
    typ = etabs.get_type_of_structure()
    assert typ == 'concrete'


@open_etabs_file('shayesteh.EDB')
def test_start_slab_design():
    if etabs.etabs_main_version < 20:
        with pytest.raises(NotImplementedError) as err:
            etabs.start_slab_design()
    else:
        etabs.start_slab_design()
    assert True

@open_etabs_file('zibaei.EDB')
def test_angles_response_spectrums_analysis():
    scales, df = etabs.angles_response_spectrums_analysis(
        ex_name='EX',
        ey_name='EY',
        specs=['SPECT0', 'SPECT105', 'SPECT120', 'SPECT135', 'SPECT15', 'SPECT150', 'SPECT165', 'SPECT30', 'SPECT45', 'SPECT60', 'SPECT75', 'SPECT90'],
        section_cuts=['SEC0', 'SEC105', 'SEC120', 'SEC135', 'SEC15', 'SEC150', 'SEC165', 'SEC30', 'SEC45', 'SEC60', 'SEC75', 'SEC90'],
        analyze=False,
    )
    for scale in scales:
        assert pytest.approx(scale, abs=.001) == 1
    print(df)

@open_etabs_file('akhondzadeh.EDB')
def test_angles_response_spectrums_analysis_two_systems():
    scales, df = etabs.angles_response_spectrums_analysis(
        ex_name=['EX', 'EXb'],
        ey_name=['EY', 'EYb'],
        specs=['SPEC0', 'SPEC10', 'SPEC20', 'SPEC30', 'SPEC40', 'SPEC50', 'SPEC60', 'SPEC70', 'SPEC80', 'SPEC90', 'SPEC100', 'SPEC110', 'SPEC120', 'SPEC130', 'SPEC140', 'SPEC150', 'SPEC160', 'SPEC170'],
        section_cuts=['SEC0', 'SEC10', 'SEC20', 'SEC30', 'SEC40', 'SEC50', 'SEC60', 'SEC70', 'SEC80', 'SEC90', 'SEC100', 'SEC110', 'SEC120', 'SEC130', 'SEC140', 'SEC150', 'SEC160', 'SEC170'],
        analyze=False,
    )
    for scale in scales:
        assert pytest.approx(scale, abs=.001) == 1
    print(df)

@open_etabs_file('shayesteh.EDB')
def test_scale_response_spectrums():
    for force in ('kgf',): #, 'N', 'KN'):
        for length in ('m',): #, 'mm', 'cm'):
            etabs.set_current_unit(force, length)
            print(f'Units: {force=}, {length=}')
            ex_name='QX'
            ey_name='QY'
            x_specs=['SX']
            y_specs=['SY']
            x_scales, y_scales, df = etabs.scale_response_spectrums(
                ex_name=ex_name,
                ey_name=ey_name,
                x_specs=x_specs,
                y_specs=y_specs,
                analyze=False,
            )
            for scale in x_scales + y_scales:
                assert pytest.approx(scale, abs=.001) == 1
            # Test base reactions
            vex, vey = etabs.results.get_base_react(
                    loadcases=[ex_name, ey_name],
                    directions=['x', 'y'],
                    absolute=True,
                    )
            vsx = etabs.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = etabs.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
            )
            for v in vsx:
                np.testing.assert_almost_equal(v / vex, 0.9, decimal=2)
            for v in vsy:
                np.testing.assert_almost_equal(v / vey, 0.9, decimal=2)
            force = etabs.get_current_unit()[0]
            load_cases = [ex_name, ey_name] + x_specs + y_specs
            base_shear = [vex, vey] + vsx + vsy
            ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
            final_scales = [1, 1] # Get final scales that applied in etabs model
            for name in x_specs + y_specs:
                ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
                final_scales.append(ret[3][0])
            df1 = pd.DataFrame({
                'Case': load_cases,
                f'V ({force})': base_shear,
                'Ratio': ratios,
                'Scale': final_scales,
                })
            # Assert equality between the two DataFrames
            cols = [f'V ({force})', 'Ratio', 'Scale']
            np.testing.assert_allclose(df1[cols].values, df[cols].values, rtol=1e-3, atol=1e-3)

@open_etabs_file('two_earthquakes.EDB')
def test_scale_response_spectrums_two_earthquakes():
    for force in ('kgf',): #, 'N', 'KN'):
        for length in ('m',): #, 'mm', 'cm'):
            etabs.set_current_unit(force, length)
            print(f'Units: {force=}, {length=}')
            ex_name=['EX1', 'EX2']
            ey_name=['EY1', 'EY2']
            x_specs=['SPECX']
            y_specs=['SPECY']
            x_scales, y_scales, df = etabs.scale_response_spectrums(
                ex_name=ex_name,
                ey_name=ey_name,
                x_specs=x_specs,
                y_specs=y_specs,
                analyze=False,
            )
            for scale in x_scales + y_scales:
                assert pytest.approx(scale, abs=.001) == 1
            # Test base reactions
            V = etabs.results.get_base_react(
                    loadcases=ex_name + ey_name,
                    directions=['x'] * len(ex_name) + ['y'] * len(ey_name),
                    absolute=True,
                    )
            vex = sum(V[0: len(ex_name)])
            vey = sum(V[len(ex_name):])
            vsx = etabs.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = etabs.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
            )
            for v in vsx:
                np.testing.assert_almost_equal(v / vex, 0.9, decimal=2)
            for v in vsy:
                np.testing.assert_almost_equal(v / vey, 0.9, decimal=2)
            force = etabs.get_current_unit()[0]
            load_cases = ['&'.join(ex_name),  '&'.join(ey_name)] + x_specs + y_specs
            base_shear = [vex, vey] + vsx + vsy
            ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
            final_scales = [1, 1] # Get final scales that applied in etabs model
            for name in x_specs + y_specs:
                ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
                final_scales.append(ret[3][0])
            df1 = pd.DataFrame({
                'Case': load_cases,
                f'V ({force})': base_shear,
                'Ratio': ratios,
                'Scale': final_scales,
                })
            # Assert equality between the two DataFrames
            cols = [f'V ({force})', 'Ratio', 'Scale']
            np.testing.assert_allclose(df1[cols].values, df[cols].values, rtol=1e-3, atol=1e-3)

# two systems
@open_etabs_file('akhonzadeh.EDB')
def test_scale_response_spectrums_two_systems():
    for force in ('kgf',): #, 'N', 'KN'):
        for length in ('m',): #, 'mm', 'cm'):
            etabs.set_current_unit(force, length)
            print(f'Units: {force=}, {length=}')
            ex_name=['EXb', 'EX']
            ey_name=['EYb', 'EY']
            x_specs=['SX', 'SXE']
            y_specs=['SY', 'SYE']
            x_scales, y_scales, df = etabs.scale_response_spectrums(
                ex_name=ex_name,
                ey_name=ey_name,
                x_specs=x_specs,
                y_specs=y_specs,
                analyze=False,
            )
            for scale in x_scales + y_scales:
                assert pytest.approx(scale, abs=.001) == 1
            # Test base reactions
            V = etabs.results.get_base_react(
                    loadcases=ex_name + ey_name,
                    directions=['x'] * len(ex_name) + ['y'] * len(ey_name),
                    absolute=True,
                    )
            vex = sum(V[0: len(ex_name)])
            vey = sum(V[len(ex_name):])
            vsx = etabs.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = etabs.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
            )
            for v in vsx:
                np.testing.assert_almost_equal(v / vex, 0.9, decimal=2)
            for v in vsy:
                np.testing.assert_almost_equal(v / vey, 0.9, decimal=2)
            force = etabs.get_current_unit()[0]
            load_cases = ['&'.join(ex_name),  '&'.join(ey_name)] + x_specs + y_specs
            base_shear = [vex, vey] + vsx + vsy
            ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
            final_scales = [1, 1] # Get final scales that applied in etabs model
            for name in x_specs + y_specs:
                ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
                final_scales.append(ret[3][0])
            df1 = pd.DataFrame({
                'Case': load_cases,
                f'V ({force})': base_shear,
                'Ratio': ratios,
                'Scale': final_scales,
                })
            # Assert equality between the two DataFrames
            cols = [f'V ({force})', 'Ratio', 'Scale']
            np.testing.assert_allclose(df1[cols].values, df[cols].values, rtol=1e-3, atol=1e-3)

@open_etabs_file('khalkhali.EDB')
def test_scale_response_spectrums2():
    for force in ('kgf',): #, 'N', 'KN'):
        for length in ('m',): #, 'mm', 'cm'):
            etabs.set_current_unit(force, length)
            print(f'Units: {force=}, {length=}')
            ex_name='EX'
            ey_name='EY'
            x_specs=['SX', 'SXPN']
            y_specs=['SY', 'SYPN']
            x_scale_factor=.85
            y_scale_factor=1
            x_scales, y_scales, df = etabs.scale_response_spectrums(
                ex_name=ex_name,
                ey_name=ey_name,
                x_specs=x_specs,
                y_specs=y_specs,
                x_scale_factor=x_scale_factor,
                y_scale_factor=y_scale_factor,
                tolerance=.02,
                analyze=False,
            )
            for scale in x_scales + y_scales:
                assert pytest.approx(scale, abs=.001) == 1
            # Test base reactions
            vex, vey = etabs.results.get_base_react(
                    loadcases=[ex_name, ey_name],
                    directions=['x', 'y'],
                    absolute=True,
                    )
            vsx = etabs.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = etabs.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
            )
            for v in vsx:
                np.testing.assert_almost_equal(v / vex, x_scale_factor, decimal=2)
            for v in vsy:
                np.testing.assert_almost_equal(v / vey, y_scale_factor, decimal=2)
            force = etabs.get_current_unit()[0]
            load_cases = [ex_name, ey_name] + x_specs + y_specs
            base_shear = [vex, vey] + vsx + vsy
            ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
            final_scales = [1, 1] # Get final scales that applied in etabs model
            for name in x_specs + y_specs:
                ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
                final_scales.append(ret[3][0])
            df1 = pd.DataFrame({
                'Case': load_cases,
                f'V ({force})': base_shear,
                'Ratio': ratios,
                'Scale': final_scales,
                })
            # Assert equality between the two DataFrames
            cols = [f'V ({force})', 'Ratio', 'Scale', ]
            np.testing.assert_allclose(df1[cols].values, df[cols].values, rtol=1e-3, atol=1e-3)

@open_etabs_file('khalkhali.EDB')
def test_scale_response_spectrums_min_base_shear():
    for force in ('kgf',): #, 'N', 'KN'):
        for length in ('m',): #, 'mm', 'cm'):
            etabs.set_current_unit(force, length)
            print(f'Units: {force=}, {length=}')
            ex_name='EX'
            ey_name='EY'
            x_specs=['SX', 'SXPN']
            y_specs=['SY', 'SYPN']
            x_scale_factor=.85
            y_scale_factor=1
            table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
            df = etabs.database.read(table_key, to_dataframe=True)
            df['C'] = '.036'
            etabs.database.write_seismic_user_coefficient_df(df)
            d = {"risk_level": "زیاد", "importance_factor": 1}
            x_scales, y_scales, df = etabs.scale_response_spectrums(
                ex_name=ex_name,
                ey_name=ey_name,
                x_specs=x_specs,
                y_specs=y_specs,
                x_scale_factor=x_scale_factor,
                y_scale_factor=y_scale_factor,
                tolerance=.02,
                analyze=False,
                consider_min_static_base_shear=True,
                d=d,
            )
            for scale in x_scales + y_scales:
                assert pytest.approx(scale, abs=.001) == 1
            # Test base reactions
            vex, vey = etabs.results.get_base_react(
                    loadcases=[ex_name, ey_name],
                    directions=['x', 'y'],
                    absolute=True,
                    )
            vsx = etabs.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = etabs.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
            )
            for v in vsx:
                np.testing.assert_almost_equal(v / vex, 1.0, decimal=2)
            for v in vsy:
                np.testing.assert_almost_equal(v / vey, 1.0, decimal=2)
            force = etabs.get_current_unit()[0]
            load_cases = [ex_name, ey_name] + x_specs + y_specs
            base_shear = [vex, vey] + vsx + vsy
            ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
            final_scales = [1, 1] # Get final scales that applied in etabs model
            for name in x_specs + y_specs:
                ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
                final_scales.append(ret[3][0])
            df1 = pd.DataFrame({
                'Case': load_cases,
                f'V ({force})': base_shear,
                'Ratio': ratios,
                'Scale': final_scales,
                })
            # Assert equality between the two DataFrames
            cols = [f'V ({force})', 'Ratio', 'Scale']
            np.testing.assert_allclose(df1[cols].values, df[cols].values, rtol=1e-3, atol=1e-3)

@open_etabs_file('khalkhali.EDB')
def test_scale_response_spectrums_min_base_shear_2():
    for force in ('kgf',): #, 'N', 'KN'):
        for length in ('m',): #, 'mm', 'cm'):
            etabs.set_current_unit(force, length)
            print(f'Units: {force=}, {length=}')
            ex_name='EX'
            ey_name='EY'
            x_specs=['SX', 'SXPN']
            y_specs=['SY', 'SYPN']
            x_scale_factor=.85
            y_scale_factor=1
            d = {"risk_level": "زیاد", "importance_factor": 1}
            x_scales, y_scales, df = etabs.scale_response_spectrums(
                ex_name=ex_name,
                ey_name=ey_name,
                x_specs=x_specs,
                y_specs=y_specs,
                x_scale_factor=x_scale_factor,
                y_scale_factor=y_scale_factor,
                tolerance=.02,
                analyze=False,
                consider_min_static_base_shear=True,
                d=d,
            )
            for scale in x_scales + y_scales:
                assert pytest.approx(scale, abs=.001) == 1
            # Test base reactions
            vex, vey = etabs.results.get_base_react(
                    loadcases=[ex_name, ey_name],
                    directions=['x', 'y'],
                    absolute=True,
                    )
            vsx = etabs.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = etabs.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
            )
            for v in vsx:
                np.testing.assert_almost_equal(v / vex, x_scale_factor, decimal=2)
            for v in vsy:
                np.testing.assert_almost_equal(v / vey, y_scale_factor, decimal=2)
            force = etabs.get_current_unit()[0]
            load_cases = [ex_name, ey_name] + x_specs + y_specs
            base_shear = [vex, vey] + vsx + vsy
            ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
            final_scales = [1, 1] # Get final scales that applied in etabs model
            for name in x_specs + y_specs:
                ret = etabs.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
                final_scales.append(ret[3][0])
            df1 = pd.DataFrame({
                'Case': load_cases,
                f'V ({force})': base_shear,
                'Ratio': ratios,
                'Scale': final_scales,
                })
            # Assert equality between the two DataFrames
            cols = [f'V ({force})', 'Ratio', 'Scale']
            np.testing.assert_allclose(df1[cols].values, df[cols].values, rtol=1e-3, atol=1e-3)

@open_etabs_file('shayesteh.EDB')
def test_check_seismic_names():
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

@open_etabs_file('two_earthquakes.EDB')
def test_purge_model():
    etabs.purge_model()
    beams, columns = etabs.frame_obj.get_beams_columns()
    assert len(beams) == len(columns) == 0
    beams, columns = etabs.frame_obj.get_beams_columns(type_=1)
    assert len(beams) == len(columns) == 0
    names = etabs.area.get_names_of_areas_of_type()
    assert len(names) == 0
    names = etabs.area.get_names_of_areas_of_type(type_='wall')
    assert len(names) == 0

@open_etabs_file('shayesteh.EDB')
def test_get_json_file_path_for_table_results():
    json_filename = "test.json"
    filename = etabs.get_json_file_path_for_table_results(json_filename=json_filename)
    table_result_path = etabs.get_filepath() / "shayesteh_table_results"
    assert filename == table_result_path / json_filename

@open_etabs_file('shayesteh.EDB')
def test_get_new_filename_in_folder_and_add_name():
    folder_name = 'TEST'
    _, new = etabs.get_new_filename_in_folder_and_add_name(folder_name=folder_name, name='alaki')
    assert new.parent.exists()
    assert new.parent.name == folder_name

@open_etabs_file('shayesteh.EDB')
def test_save_in_folder_and_add_name():
    folder_name = 'TEST'
    _, new = etabs.save_in_folder_and_add_name(folder_name=folder_name, name='alaki')
    assert new.parent.exists()
    assert new.exists()

@open_etabs_file('shayesteh.EDB')
def test_get_x_and_y_system_ductility():
    d = {'x_system': [2, 1], 'y_system': [3, 1]}
    ret = etabs.get_x_and_y_system_ductility(d=d)
    assert ret == ['M', None]


if __name__ == '__main__':
    test_get_sap_main_version()


