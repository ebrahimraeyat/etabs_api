import pytest
import comtypes.client
from pathlib import Path
import sys

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))
from load_combinations import generate_concrete_load_combinations

import etabs_obj

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

@pytest.mark.getmethod
def test_generate_concrete_load_combinations():
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = generate_concrete_load_combinations(equal_loads)
    assert data

@pytest.mark.getmethod
def test_generate_concrete_load_combinations_asd():
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = generate_concrete_load_combinations(equal_loads, prefix='SOIL_', design_type="ASD")
    assert data

@pytest.mark.setmethod
def test_add_load_combination(shayesteh):
    load_combinations = []
    for i in range(1, 5):
        name = f'test{i}'
        load_combinations.append(name)
        shayesteh.load_combinations.add_load_combination(name)
    shayesteh.load_combinations.add_load_combination(
        combo_name='PUSH_Grav',
        load_case_names=load_combinations,
        scale_factor=1.2,
        type_=1,
    )
    assert True

if __name__ == '__main__':
    # from pathlib import Path
    # etabs_api = Path(__file__).parent.parent
    # import sys
    # sys.path.insert(0, str(etabs_api))
    # from etabs_obj import EtabsModel
    # etabs = EtabsModel(backup=False)
    # SapModel = etabs.SapModel
    test_generate_concrete_load_combinations_asd()
