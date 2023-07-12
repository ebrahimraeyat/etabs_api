import pytest
from pathlib import Path
import sys

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

filename = Path(__file__).absolute().parent / 'files' / 'freecad' / 'strip.FCStd'
filename_mat = Path(__file__).absolute().parent / 'files' / 'freecad' / 'mat.FCStd'
document= FreeCAD.openDocument(str(filename))

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import *

def test_get_story_mass():
    story_mass = etabs.database.get_story_mass()
    assert len(story_mass) == 5
    assert pytest.approx(float(story_mass[2][1]), abs=1) == 17696

def test_get_center_of_rigidity():
    cor = etabs.database.get_center_of_rigidity()
    assert len(cor) == 5
    assert cor['STORY1'] == ('9.3844', '3.7778')


def test_get_stories_displacement_in_xy_modes():
    dx, dy, wx, wy = etabs.database.get_stories_displacement_in_xy_modes()
    assert len(dx) == 5
    assert len(dy) == 5
    assert pytest.approx(wx, abs=.01) == 4.868
    assert pytest.approx(wy, abs=.01) == 4.868

def test_get_story_forces():
    forces, loadcases, _ = etabs.database.get_story_forces()
    assert len(forces) == 10
    assert loadcases == ('QX', 'QY')

def test_multiply_seismic_loads():
    NumFatalErrors, ret = etabs.database.multiply_seismic_loads(.67)
    assert NumFatalErrors == ret == 0
    ret = etabs.SapModel.Analyze.RunAnalysis()
    assert ret == 0

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

def test_write_seismic_user_coefficient_df():
    import pandas as pd
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'auto_seismic'
    df = pd.read_pickle(filename)
    open_model(etabs=etabs, filename="two_earthquakes.EDB")
    etabs.database.write_seismic_user_coefficient_df(df)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 14

def test_write_seismic_user_coefficient_df01():
    import pandas as pd
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'auto_seismic'
    df = pd.read_pickle(filename)
    df['C'] = "0.1"
    open_model(etabs=etabs, filename="two_earthquakes.EDB")
    etabs.database.write_seismic_user_coefficient_df(df)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 14
    for _, row in df.iterrows():
        assert row['C'] == '0.1'

def test_write_seismic_user_coefficient_df_overwrite():
    import pandas as pd
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'auto_seismic_overwrite'
    df = pd.read_pickle(filename)
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
        'EDRIFTY' : 37,
        'EDRIFTYN' : 37,
        'EDRIFTYP' : 37,
        'EDRIFTX' : 37,
        }
    open_model(etabs=etabs, filename="two_earthquakes.EDB")
    etabs.database.write_seismic_user_coefficient_df(df, loads_type)
    table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert len(df) == 19
    for lp, n in loads_type.items():
        assert etabs.SapModel.LoadPatterns.GetLoadType(lp)[0] == n

def test_get_beams_forces():
    open_model(etabs=etabs, filename="shayesteh.EDB")
    df = etabs.database.get_beams_forces()
    assert len(df) == 37625
    df = etabs.database.get_beams_forces(beams = ['114', '115'])
    assert len(df) == 910
    df = etabs.database.get_beams_forces(
        beams = ['114', '115'],
        cols = ['Story', 'Beam', 'UniqueName', 'T'])
    assert len(df) == 910
    assert len(df.columns) == 4

def test_get_beams_torsion():
    df = etabs.database.get_beams_torsion()
    assert len(df) == 92
    assert len(df.columns) == 4

def test_get_beams_torsion_2():
    df = etabs.database.get_beams_torsion(beams=['115'])
    assert len(df) == 1
    assert len(df.columns) == 4
    assert pytest.approx(df.iat[0, 3], abs=.01) == 3.926

def test_get_beams_torsion_dict():
    cols=['UniqueName', 'T']
    df = etabs.database.get_beams_torsion(beams=['115'], cols=cols)
    assert len(df) == 1
    assert type(df) == dict


def test_get_concrete_frame_design_load_combinations():
    combos = etabs.database.get_concrete_frame_design_load_combinations()
    assert len(combos) == 35
    combinations = [f'COMB{i}' for i in range(1, 36)]
    assert combos == combinations


def test_get_section_cuts_base_shear():
    df = etabs.database.get_section_cuts_base_shear(loadcases=['DEAD'], section_cuts=['SEC15'])
    assert len(df) == 1
    df = etabs.database.get_section_cuts_base_shear(loadcases=['DEAD', 'QXP'], section_cuts=['SEC15'])
    assert len(df) == 2


def test_get_section_cuts_angle():
    d = etabs.database.get_section_cuts_angle()
    assert len(d) == 12


def test_expand_seismic_load_patterns():
    open_model(etabs=etabs, filename="khiabany.EDB")
    df, loads = etabs.database.expand_seismic_load_patterns()
    assert len(loads) == 4
    assert len(df) == 12
    assert set(df.Name) == {'EY', 'EX', 'EY_DRIFT', 'EYN_DRIFT', 'EYP_DRIFT', 'EXP', 'EYN', 'EXN', 'EXN_DRIFT', 'EXP_DRIFT', 'EX_DRIFT', 'EYP'}
    assert set(loads.keys()) == {'EYDRIFT', 'EXALL', 'EYALL', 'EXDRIFT'}


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


def test_expand_design_combos():
    d1 = {
        'EXALL' : ['EX', 'EPX', 'ENX'],
        'EYALL' : ['EY', 'EPY', 'ENY'],
        'EXDRIFT' : ['EPXDRIFT'],
        }
    dfs = etabs.database.expand_design_combos(d1)
    assert len(dfs) == 1
    assert list(dfs.keys())[0] == 'Concrete Frame Design Load Combination Data'


def test_apply_expand_design_combos():
    open_model(etabs=etabs, filename="shayesteh.EDB")
    import pandas as pd
    table_key = 'Concrete Frame Design Load Combination Data'
    l1 = [['Strength', 'COMB1']]
    d1 = {table_key: pd.DataFrame(l1, columns=['ComboType', 'ComboName'], index=range(len(l1)))}
    etabs.database.apply_expand_design_combos(d1)
    l2 = etabs.database.get_design_load_combinations()
    assert l2 == ['COMB1']
    
def test_get_basepoints_coord_and_dims():
    d = etabs.database.get_basepoints_coord_and_dims()
    assert len(d) == 11


def test_get_frame_points_xyz():
    d = etabs.database.get_frame_points_xyz(frames=('114', '115'))
    assert len(d) == 2

def test_set_floor_cracking_for_floor():
    type_ = 'Area'
    etabs.database.set_floor_cracking(type_=type_)
    names = etabs.area.get_names_of_areas_of_type(type_='floor')
    table_key = f"{type_} Assignments - Floor Cracking"
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(names) == set(df['UniqueName'].unique())

def test_set_floor_cracking_for_beams():
    type_ = 'Frame'
    etabs.database.set_floor_cracking(type_=type_)
    names, _ = etabs.frame_obj.get_beams_columns()
    table_key = f"{type_} Assignments - Floor Cracking"
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(names) == set(df['UniqueName'].unique())

def test_get_design_load_combinations_steel():
    etabs.database.get_design_load_combinations('steel')

def test_create_nonlinear_loadcases():
    dead = ['Dead']
    sd = ['S-DEAD']
    lives = ['Live', 'Live-0.5', 'L-RED']
    ret = etabs.database.create_nonlinear_loadcases(dead, sd, lives)
    load_cases = etabs.load_cases.get_load_cases()
    for name in ret:
        assert name in load_cases
    assert ret[0] == 'Dead+S-DEAD+0.25Live'

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

def test_set_cracking_analysis_option():
    min_tension_ratio = .1
    min_compression_ratio = .2
    etabs.database.set_cracking_analysis_option(
        min_tension_ratio=min_tension_ratio,
        min_compression_ratio=min_compression_ratio,
        )
    table_key = 'Analysis Options - Cracking Analysis Options'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert list(df.iloc[0]) == ['User and Designed', str(min_tension_ratio), str(min_compression_ratio)]





if __name__ == '__main__':
    test_set_floor_cracking_for_floor(shayesteh)