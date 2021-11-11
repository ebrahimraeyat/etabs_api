import pytest
import comtypes.client
from pathlib import Path
import sys

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

filename = Path(__file__).absolute().parent.parent / 'etabs_api' / 'test_files' / 'freecad' / 'strip.FCStd'
filename_mat = Path(__file__).absolute().parent.parent / 'etabs_api' / 'test_files' / 'freecad' / 'mat.FCStd'
document= FreeCAD.openDocument(str(filename))
etabs_api_path = Path(__file__).parent.parent.parent
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
        helper = comtypes.client.CreateObject('ETABSv1.Helper') 
        helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
        ETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
        ETABSObject.ApplicationStart()
        SapModel = ETABSObject.SapModel
        # SapModel.InitializeNewModel()
        SapModel.File.OpenFile(str(Path(__file__).parent / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.EDB"
        SapModel.File.Save(str(test_file_path))
        etabs = etabs_obj.EtabsModel(backup=False)
        return etabs

@pytest.fixture
def shayesteh_safe(edb="shayesteh.FDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False, software='SAFE')
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                raise NameError
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        helper = comtypes.client.CreateObject('SAFEv1.Helper') 
        helper = helper.QueryInterface(comtypes.gen.SAFEv1.cHelper)
        SAFEObject = helper.CreateObjectProgID("CSI.SAFE.API.ETABSObject")
        SAFEObject.ApplicationStart()
        SapModel = SAFEObject.SapModel
        SapModel.InitializeNewModel()
        SapModel.File.OpenFile(str(Path(__file__).parent / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.EDB"
        SapModel.File.Save(str(test_file_path))
        etabs = etabs_obj.EtabsModel(backup=False)
        return etabs

@pytest.fixture
def khiabany(edb="khiabany.EDB"):
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
        SapModel.File.OpenFile(str(Path(__file__).parent / 'files' / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.EDB"
        SapModel.File.Save(str(test_file_path))
        etabs = etabs_obj.EtabsModel(backup=False)
        return etabs

def test_get_story_mass(shayesteh):
    story_mass = shayesteh.database.get_story_mass()
    assert len(story_mass) == 5
    assert pytest.approx(float(story_mass[2][1]), abs=1) == 17696

def test_get_center_of_rigidity(shayesteh):
    cor = shayesteh.database.get_center_of_rigidity()
    assert len(cor) == 5
    assert cor['STORY1'] == ('9.3844', '3.7778')

@pytest.mark.getmethod
def test_get_stories_displacement_in_xy_modes(shayesteh):
    dx, dy, wx, wy = shayesteh.database.get_stories_displacement_in_xy_modes()
    assert len(dx) == 5
    assert len(dy) == 5
    assert pytest.approx(wx, abs=.01) == 4.868
    assert pytest.approx(wy, abs=.01) == 4.868

def test_get_story_forces(shayesteh):
    forces, loadcases, _ = shayesteh.database.get_story_forces()
    assert len(forces) == 10
    assert loadcases == ('QX', 'QY')

def test_multiply_seismic_loads(shayesteh):
    NumFatalErrors, ret = shayesteh.database.multiply_seismic_loads(.67)
    assert NumFatalErrors == ret == 0
    ret = shayesteh.SapModel.Analyze.RunAnalysis()
    assert ret == 0

def test_write_aj_user_coefficient(shayesteh):
    shayesteh.load_patterns.select_all_load_patterns()
    TableKey = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
    [_, _, FieldsKeysIncluded, _, TableData, _] = shayesteh.database.read_table(TableKey)
    import pandas as pd
    df = pd.DataFrame({'OutputCase': 'QXP',
                        'Story': 'Story1',
                        'Diaph': 'D1',
                        'Ecc. Length (Cm)': 82,
                        }, index=range(1))
    NumFatalErrors, ret = shayesteh.database.write_aj_user_coefficient(TableKey, FieldsKeysIncluded, TableData, df)
    assert NumFatalErrors == ret == 0
    ret = shayesteh.SapModel.Analyze.RunAnalysis()
    assert ret == 0

def test_get_beams_forces(shayesteh):
    df = shayesteh.database.get_beams_forces()
    assert len(df) == 37625
    df = shayesteh.database.get_beams_forces(beams = ['114', '115'])
    assert len(df) == 910
    df = shayesteh.database.get_beams_forces(
        beams = ['114', '115'],
        cols = ['Story', 'Beam', 'UniqueName', 'T'])
    assert len(df) == 910
    assert len(df.columns) == 4

def test_get_beams_torsion(shayesteh):
    df = shayesteh.database.get_beams_torsion()
    assert len(df) == 92
    assert len(df.columns) == 4

def test_get_beams_torsion_2(shayesteh):
    df = shayesteh.database.get_beams_torsion(beams=['115'])
    assert len(df) == 1
    assert len(df.columns) == 4
    assert pytest.approx(df.iat[0, 3], abs=.01) == 3.926

def test_get_beams_torsion_dict(shayesteh):
    cols=['UniqueName', 'T']
    df = shayesteh.database.get_beams_torsion(beams=['115'], cols=cols)
    assert len(df) == 1
    assert type(df) == dict

@pytest.mark.getmethod
def test_get_concrete_frame_design_load_combinations(shayesteh):
    combos = shayesteh.database.get_concrete_frame_design_load_combinations()
    assert len(combos) == 35
    combinations = [f'COMB{i}' for i in range(1, 36)]
    assert combos == combinations

@pytest.mark.getmethod
def test_get_section_cuts_base_shears(shayesteh):
    df = shayesteh.database.get_section_cuts_base_shear(specs=['D'], section_cuts=['SCut1'])
    assert len(df) == 1
    df = shayesteh.database.get_section_cuts_base_shear(specs=['D', 'DCon11'], section_cuts=['SCut1'])
    assert len(df) == 3

@pytest.mark.getmethod
def test_get_section_cuts_angle(shayesteh):
    d = shayesteh.database.get_section_cuts_angle()
    assert len(d) == 13

@pytest.mark.getmethod
def test_expand_seismic_load_patterns(khiabany):
    df, loads = khiabany.database.expand_seismic_load_patterns()
    assert len(loads) == 4
    assert len(df) == 12
    assert set(df.Name) == {'EY', 'EX', 'EY_DRIFT', 'ENY_DRIFT', 'EPY_DRIFT', 'EPX', 'ENY', 'ENX', 'ENX_DRIFT', 'EPX_DRIFT', 'EX_DRIFT', 'EPY'}
    assert set(loads.keys()) == {'EYDRIFT', 'EXALL', 'EYALL', 'EXDRIFT'}

@pytest.mark.getmethod
def test_expand_table(khiabany):
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
    df = khiabany.database.expand_table(df, d1,'Name')
    assert len(df) == 9

@pytest.mark.getmethod
def test_expand_design_combos(khiabany):
    d1 = {
        'EXALL' : ['EX', 'EPX', 'ENX'],
        'EYALL' : ['EY', 'EPY', 'ENY'],
        'EXDRIFT' : ['EPXDRIFT'],
        }
    dfs = khiabany.database.expand_design_combos(d1)
    assert len(dfs) == 1
    assert list(dfs.keys())[0] == 'Concrete Frame Design Load Combination Data'

@pytest.mark.getmethod
def test_apply_expand_design_combos(khiabany):
    import pandas as pd
    table_key = 'Concrete Frame Design Load Combination Data'
    d = {'Strength' : 'UDCon-DYN1'}
    d1 = {table_key: pd.DataFrame(d, index=range(len(d)))}
    khiabany.database.apply_expand_design_combos(d1)
    d = khiabany.database.get_design_load_combinations()
    assert d is not None
    assert list(d.keys())[0] == table_key
    
@pytest.mark.getmethod
def test_get_basepoints_coord_and_dims(shayesteh):
    d = shayesteh.database.get_basepoints_coord_and_dims()
    assert len(d) == 11

@pytest.mark.getmethod
def test_get_frame_points_xyz(shayesteh):
    d = shayesteh.database.get_frame_points_xyz(frames=('114', '115'))
    assert len(d) == 2

@pytest.mark.getmethod
def test_get_strip_connectivity(shayesteh_safe):
    df = shayesteh_safe.database.get_strip_connectivity()
    assert len(df) == shayesteh_safe.SapModel.DesignConcreteSlab.DesignStrip.GetNameList()[0]

@pytest.mark.applymethod
def test_create_area_spring_table(shayesteh_safe):
    names_props = [('SOIL', '2'), ('SOIL_1.5', '3'), ('SOIL_2', '4')]
    df = shayesteh_safe.database.create_area_spring_table(names_props)

@pytest.mark.applymethod
def test_create_punching_shear_general_table(shayesteh_safe):
    punches = []
    for o in document.Objects:
        if hasattr(o, "Proxy") and \
            hasattr(o.Proxy, "Type") and \
            o.Proxy.Type == "Punch":
            punches.append(o)
    shayesteh_safe.database.create_punching_shear_general_table(punches)

@pytest.mark.applymethod
def test_create_punching_shear_perimeter_table(shayesteh_safe):
    punches = []
    for o in document.Objects:
        if hasattr(o, "Proxy") and \
            hasattr(o.Proxy, "Type") and \
            o.Proxy.Type == "Punch":
            punches.append(o)
    shayesteh_safe.database.create_punching_shear_perimeter_table(punches)



if __name__ == '__main__':
    sh = shayesteh()