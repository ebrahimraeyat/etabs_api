import pytest
from pathlib import Path
import sys

import numpy as np

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

filename = Path(__file__).absolute().parent / 'files' / 'freecad' / 'roof.FCStd'
filename_mat = Path(__file__).absolute().parent / 'files' / 'freecad' / 'mat.FCStd'
document= FreeCAD.openDocument(str(filename))

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file


@open_etabs_file('shayesteh.EDB')
def test_table_names_that_containe():
    s = "Concrete Joint Design Summary"
    names = etabs.database.table_names_that_containe(s)
    assert len(names) == 0

@open_etabs_file('shayesteh.EDB')
def test_get_story_mass():
    story_mass = etabs.database.get_story_mass()
    assert len(story_mass) == 5
    assert pytest.approx(float(story_mass[2][1]), abs=1) == 17696

@open_etabs_file('shayesteh.EDB')
def test_get_story_mass_as_dict():
    story_mass = etabs.database.get_story_mass_as_dict()
    assert len(story_mass) == 5
    assert pytest.approx(story_mass.get('STORY3'), abs=1) == 17696
    assert pytest.approx(story_mass.get('STORY2'), abs=1) == 18032

@open_etabs_file('shayesteh.EDB')
def test_get_cumulative_story_mass():
    story_mass = etabs.database.get_cumulative_story_mass()
    assert len(story_mass) == 5
    assert pytest.approx(story_mass.get('STORY3'), abs=1) == 17696
    assert pytest.approx(story_mass.get('STORY2'), abs=1) == 18032

@open_etabs_file('shayesteh.EDB')
def test_get_center_of_rigidity():
    cor = etabs.database.get_center_of_rigidity()
    assert len(cor) == 5
    assert cor['STORY1'] == ('9.3844', '3.7778')


@open_etabs_file('shayesteh.EDB')
def test_get_stories_displacement_in_xy_modes():
    dx, dy, wx, wy = etabs.database.get_stories_displacement_in_xy_modes()
    assert len(dx) == 5
    assert len(dy) == 5
    assert pytest.approx(wx, abs=.01) == 4.868
    assert pytest.approx(wy, abs=.01) == 4.868

@open_etabs_file('shayesteh.EDB')
def test_get_story_forces():
    forces, loadcases, _ = etabs.database.get_story_forces()
    assert len(forces) == 10
    assert loadcases == ('QX', 'QY')

@open_etabs_file('shayesteh.EDB')
def test_get_story_forces_of_loadcases():
    story_forces = etabs.database.get_story_forces_of_loadcases(loadcases=('QX', 'QY'))
    assert len(story_forces) == 2
    assert story_forces['QX']['STORY5'] == [0, 0]
    assert story_forces['QX']['STORY4'] == [-40601.68, 0]
    # assert np.testing.assert_allclose(story_forces['QX']['STORY4'], [-40601.68, 0])

@open_etabs_file('shayesteh.EDB')
def test_multiply_seismic_loads():
    NumFatalErrors, ret = etabs.database.multiply_seismic_loads(.67)
    assert NumFatalErrors == ret == 0
    ret = etabs.SapModel.Analyze.RunAnalysis()
    assert ret == 0

@open_etabs_file('shayesteh.EDB')
def test_write_aj_user_coefficient():
    etabs.load_patterns.select_all_load_patterns()
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    input_df = etabs.database.read(table_key, to_dataframe=True)
    import pandas as pd
    df = pd.DataFrame({'OutputCase': 'QXP',
                        'Story': 'Story1',
                        'Diaph': 'D1',
                        'Ecc. Length (Cm)': 82,
                        }, index=range(1))
    etabs.database.write_aj_user_coefficient(table_key, input_df, df)
    ret = etabs.SapModel.Analyze.RunAnalysis()
    assert ret == 0

@open_etabs_file('shayesteh.EDB')
def test_select_load_cases_combinations():
    load_cases = ['DEAD']
    load_combinations=['COMB1', 'COMB2', 'COMB3']
    etabs.database.select_load_cases_combinations(load_cases=load_cases, load_combinations=load_combinations)
    ret = etabs.SapModel.DatabaseTables.GetLoadCasesSelectedForDisplay()
    assert ret[0] == 1
    assert set(ret[1]).intersection(load_cases) == set(load_cases)
    ret = etabs.SapModel.DatabaseTables.GetLoadCombinationsSelectedForDisplay()
    assert ret[0] == 3
    assert set(ret[1]).intersection(load_combinations) == set(load_combinations)

@open_etabs_file('two_earthquakes.EDB')
def test_write_daynamic_aj_user_coefficient():
    etabs.database.write_daynamic_aj_user_coefficient()
    assert set(etabs.load_cases.get_response_spectrum_loadcase_name()) == {'SPECX', 'SPECY', 'SPECXD', 'SPECYD'}
    assert len(etabs.load_cases.get_load_cases()) == 19
    assert True


@open_etabs_file('two_earthquakes.EDB')
def test_write_seismic_user_coefficient_df():
    import pandas as pd
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'auto_seismic.csv'
    df = pd.read_csv(filename)
    df = df.astype(str)
    etabs.database.write_seismic_user_coefficient_df(df)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 14

@open_etabs_file('yadeganeh.EDB')
def test_write_seismic_user_coefficient_df_yadeganeh():
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    etabs.check_seismic_names(apply=True)
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 14

@open_etabs_file('steel.EDB')
def test_write_seismic_user_coefficient_df_with_ecc():
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    etabs.database.write_seismic_user_coefficient_df(df)
    x, xn, xp, y, yn, yp = etabs.load_patterns.get_seismic_load_patterns()
    assert 'EXP' in xp
    assert 'EXN' in xn

@open_etabs_file('two_earthquakes.EDB')
def test_write_seismic_user_coefficient_df01():
    import pandas as pd
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'auto_seismic'
    df = pd.read_pickle(filename)
    df['C'] = "0.1"
    etabs.database.write_seismic_user_coefficient_df(df)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 14
    for _, row in df.iterrows():
        assert row['C'] == '0.1'

@open_etabs_file('two_earthquakes.EDB')
def test_write_seismic_user_coefficient_df_overwrite():
    import pandas as pd
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'auto_seismic_overwrite'
    df = pd.read_pickle(filename)
    seismic_drift_type = etabs.seismic_drift_load_type
    loads_type = {
        'EX1' : 5,
        'EX1P' : 5,
        'EX1N' : 5,
        'EY1' : 5,
        'EY1P' : 5,
        'EY1N' : 5,
        'EX2' : 5,
        'EX2P' : 5,
        'EX2N' : 5,
        'EY2' : 5,
        'EY2P' : 5,
        'EY2N' : 5,
        'EDRIFTY' : seismic_drift_type,
        'EDRIFTYN' : seismic_drift_type,
        'EDRIFTYP' : seismic_drift_type,
        'EDRIFTX' : seismic_drift_type,
        }
    etabs.database.write_seismic_user_coefficient_df(df, loads_type)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 19
    for lp, n in loads_type.items():
        assert etabs.SapModel.LoadPatterns.GetLoadType(lp)[0] == n

@open_etabs_file('shayesteh.EDB')
def test_get_beams_forces():
    df = etabs.database.get_beams_forces()
    assert len(df) == 37625
    df = etabs.database.get_beams_forces(beams = ['114', '115'])
    assert len(df) == 910
    df = etabs.database.get_beams_forces(
        beams = ['114', '115'],
        cols = ['Story', 'Beam', 'UniqueName', 'T'])
    assert len(df) == 910
    assert len(df.columns) == 4

@open_etabs_file('shayesteh.EDB')
def test_get_beams_torsion():
    df = etabs.database.get_beams_torsion()
    assert len(df) == 92
    assert len(df.columns) == 4

@open_etabs_file('shayesteh.EDB')
def test_get_beams_torsion_2():
    df = etabs.database.get_beams_torsion(beams=['115'])
    assert len(df) == 1
    assert len(df.columns) == 4
    assert pytest.approx(df.iat[0, 3], abs=.01) == 3.926

@open_etabs_file('shayesteh.EDB')
def test_get_beams_torsion_dict():
    cols=['UniqueName', 'T']
    df = etabs.database.get_beams_torsion(beams=['115'], cols=cols)
    assert len(df) == 1
    assert type(df) == dict


@open_etabs_file('shayesteh.EDB')
def test_get_concrete_frame_design_load_combinations():
    combos = etabs.database.get_concrete_frame_design_load_combinations()
    assert len(combos) == 35
    combinations = [f'COMB{i}' for i in range(1, 36)]
    assert combos == combinations


@open_etabs_file('shayesteh.EDB')
def test_get_section_cuts_base_shear():
    df = etabs.database.get_section_cuts_base_shear(loadcases=['DEAD'], section_cuts=['SEC15'])
    assert len(df) == 1
    df = etabs.database.get_section_cuts_base_shear(loadcases=['DEAD', 'QXP'], section_cuts=['SEC15'])
    assert len(df) == 2


@open_etabs_file('shayesteh.EDB')
def test_get_section_cuts_angle():
    d = etabs.database.get_section_cuts_angle()
    assert len(d) == 12

@open_etabs_file('khiabany.EDB')
def test_create_section_cuts():
    # etabs.database.create_section_cuts(group='All')
    # df = etabs.database.get_section_cuts()
    # assert len(df) == 12
    etabs.database.create_section_cuts(group='All', angles=range(0, 180, 2))
    df = etabs.database.get_section_cuts()
    assert len(df) == 90

@open_etabs_file('sap2000.sdb')
def test_create_section_cuts_sap():
    angles=range(0, 180, 10)
    etabs.database.create_section_cuts_sap(group='All', angles=angles)
    sects = etabs.database.get_section_cuts_sap()
    assert len(sects) == len(angles)

@open_etabs_file('sap2000.sdb')
def test_get_section_cuts_sap():
    sects = etabs.database.get_section_cuts_sap()
    assert sects == []

@open_etabs_file('khiabany.EDB')
def test_expand_seismic_load_patterns():
    df, loads = etabs.database.expand_seismic_load_patterns()
    assert len(loads) == 4
    assert len(df) == 12
    assert set(df.Name) == {'EY', 'EX', 'EY_DRIFT', 'EYN_DRIFT', 'EYP_DRIFT', 'EXP', 'EYN', 'EXN', 'EXN_DRIFT', 'EXP_DRIFT', 'EX_DRIFT', 'EYP'}
    assert set(loads.keys()) == {'EYDRIFT', 'EXALL', 'EYALL', 'EXDRIFT'}


@open_etabs_file('khiabany.EDB')
def test_expand_table():
    d1 = {
        'EXALL' : ['EX', 'EPX', 'ENX'],
        'EYALL' : ['EY', 'EPY', 'ENY'],
        'EXDRIFT' : ['EPXDRIFT'],
        }
    d2 = {'Name': ['EXALL', 'EX', 'Dead', 'EYALL', 'EXDRIFT'],
            'SF' : [1, 2, 3, 4, 5],
            }
    import pandas as pd
    df = pd.DataFrame(d2)
    df = etabs.database.expand_table(df, d1,'Name')
    assert len(df) == 9


@open_etabs_file('khiabany.EDB')
def test_expand_design_combos():
    d1 = {
        'EXALL' : ['EX', 'EPX', 'ENX'],
        'EYALL' : ['EY', 'EPY', 'ENY'],
        'EXDRIFT' : ['EPXDRIFT'],
        }
    dfs = etabs.database.expand_design_combos(d1)
    assert len(dfs) == 1
    assert list(dfs.keys())[0] == 'Concrete Frame Design Load Combination Data'

@open_etabs_file('khiabany.EDB')
def test_area_mesh_joints():
    ret = etabs.database.area_mesh_joints(areas=['4'])
    assert len(ret) == 3
    if version < 20:
        assert len(ret[0]) == 0
        assert len(ret[1]['4'].keys()) == 13
        assert set(ret[1]['4']['4-1']) == set(['99', '~199', '~200', '~201'])
        for value in ret[1]['4'].values():
            assert len(value) == 4
    # else:
    #     assert len(ret['4']) == 16
    #     assert set(ret['4']['~208']) == set([5750, -1700, 15840])
    # # multi shells
    areas = ['4', '15', '29']
    ret = etabs.database.area_mesh_joints(areas=areas)
    assert len(ret) == 3
    if version < 20:
        assert len(ret[0]) == 0
        assert len(ret[1]['4'].keys()) == 13
        assert set(ret[1]['4']['4-1']) == set(['99', '~199', '~200', '~201'])
        for area in areas:
            for value in ret[1][area].values():
                assert len(value) == 4
    #     assert len(ret['4']) == 15
    #     assert set(ret['4']['~199']) == set([5750, -1700, 15840])
    # else:
    #     assert len(ret['4']) == 16
    #     assert set(ret['4']['~208']) == set([5750, -1700, 15840])
    # Get map points
    map_dict = etabs.database.get_map_mesh_points()
    ret = etabs.database.area_mesh_joints(areas=['4'], map_dict=map_dict)
    assert len(ret) == 3
    if version < 20:
        assert len(ret[0]) == 0
        assert len(ret[1]['4'].keys()) == 13
        for value in ret[1]['4'].values():
            assert len(value) == 4
        assert set(ret[1]['4'][1]) == set([99, 220, 221, 219])


@open_etabs_file('shayesteh.EDB')
def test_apply_expand_design_combos():
    import pandas as pd
    table_key = 'Concrete Frame Design Load Combination Data'
    l1 = [['Strength', 'COMB1']]
    d1 = {table_key: pd.DataFrame(l1, columns=['ComboType', 'ComboName'], index=range(len(l1)))}
    etabs.database.apply_expand_design_combos(d1)
    l2 = etabs.database.get_design_load_combinations()
    assert l2 == ['COMB1']
    
@open_etabs_file('shayesteh.EDB')
def test_get_basepoints_coord_and_dims():
    d = etabs.database.get_basepoints_coord_and_dims()
    assert len(d) == 11


@open_etabs_file('shayesteh.EDB')
def test_get_frame_points_xyz():
    d = etabs.database.get_frame_points_xyz(frames=('114', '115'))
    assert len(d) == 2

@open_etabs_file('shayesteh.EDB')
def test_set_floor_cracking_for_floor():
    type_ = 'Area'
    etabs.database.set_floor_cracking(type_=type_)
    names = etabs.area.get_names_of_areas_of_type(type_='floor')
    table_key = f"{type_} Assignments - Floor Cracking"
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(names) == set(df['UniqueName'].unique())

@open_etabs_file('shayesteh.EDB')
def test_set_floor_cracking_for_beams():
    type_ = 'Frame'
    etabs.database.set_floor_cracking(type_=type_)
    names, _ = etabs.frame_obj.get_beams_columns()
    table_key = f"{type_} Assignments - Floor Cracking"
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(names) == set(df['UniqueName'].unique())

@open_etabs_file('shayesteh.EDB')
def test_get_design_load_combinations_steel():
    etabs.database.get_design_load_combinations('steel')

@open_etabs_file('shayesteh.EDB')
def test_create_nonlinear_loadcases():
    dead = ['Dead']
    sd = ['S-DEAD']
    lives = ['Live', 'Live-0.5', 'L-RED']
    ret = etabs.database.create_nonlinear_loadcases(dead, sd, lives)
    load_cases = etabs.load_cases.get_load_cases()
    for name in ret:
        assert name in load_cases
    assert ret[0] == 'Dead+S-DEAD+0.25Live'

@open_etabs_file('shayesteh.EDB')
def test_add_grid_lines():
    data = [
    'G1', 'X (Cartesian)', '1', '140.0', 'End', 'Yes',
    'G1', 'X (Cartesian)', '2', '250.0', 'End', 'Yes',
    'G1', 'Y (Cartesian)', 'BF', '6130.0', 'Start', 'Yes',
    'G1', 'Y (Cartesian)', 'BG', '290.0', 'Start', 'Yes',
    ]
    etabs.database.add_grid_lines(data)
    table_key = 'Grid Definitions - Grid Lines'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 4
    assert set(df.Ordinate) == {'140', '250', '6130', '290'}

@open_etabs_file('shayesteh.EDB')
def test_set_cracking_analysis_option():
    min_tension_ratio = .1
    min_compression_ratio = .2
    etabs.database.set_cracking_analysis_option(
        min_tension_ratio=min_tension_ratio,
        min_compression_ratio=min_compression_ratio,
        )
    table_key = 'Analysis Options - Cracking Analysis Options'
    df = etabs.database.read(table_key, to_dataframe=True)
    data = ['User and Designed',
            str(min_tension_ratio),
            str(min_compression_ratio)
            ]
    assert list(df.iloc[0]) == data

@open_etabs_file('khiabany.EDB')
def test_get_map_mesh_points():
    maped = etabs.database.get_map_mesh_points()
    assert isinstance(maped, dict)
    table_key = 'Objects and Elements - Joints'
    df = etabs.database.read(table_key=table_key, to_dataframe=True)
    df = df[df['ObjType'] == 'Shell']
    assert len(df) == len(maped)

@open_etabs_file('shayesteh.EDB')
def test_get_axial_pressure_columns():
    df = etabs.database.get_axial_pressure_columns()
    limit_ag_fc = 'limit*Ag*fc'
    fields = set(['Story', 'Column', 'OutputCase', 'UniqueName', 'P', 'section',  't2', 't3', 'fc', limit_ag_fc, 'Result'])
    assert set(df.columns) == fields




if __name__ == '__main__':
    test_write_seismic_user_coefficient_df_yadeganeh()