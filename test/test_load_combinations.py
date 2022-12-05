import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

from load_combinations import generate_concrete_load_combinations


@pytest.mark.getmethod
def test_generate_concrete_load_combinations():
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = generate_concrete_load_combinations(equal_loads)
    assert data

@pytest.mark.getmethod
def test_generate_concrete_load_combinations_separate_direction():
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = generate_concrete_load_combinations(equal_loads, separate_direction=True)
    assert data

@pytest.mark.getmethod
def test_generate_concrete_load_combinations_asd():
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = generate_concrete_load_combinations(equal_loads, prefix='SOIL_', design_type="ASD")
    assert data

@pytest.mark.getmethod
def test_generate_concrete_load_combinations_separate_direction_asd():
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = generate_concrete_load_combinations(equal_loads, prefix='SOIL_', design_type="ASD", separate_direction=True)
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

@pytest.mark.getmethod
def test_get_load_combinations_of_type(shayesteh):
    load_combos = shayesteh.load_combinations.get_load_combinations_of_type(type_='ALL')
    assert len(load_combos) == 59
    load_combos = shayesteh.load_combinations.get_load_combinations_of_type(type_='SEISMIC')
    assert len(load_combos) == 48
    load_combos = shayesteh.load_combinations.get_load_combinations_of_type(type_='GRAVITY')
    assert len(load_combos) == 11

if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
    test_add_load_combination(etabs)
