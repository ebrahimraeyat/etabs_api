import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh, two_earthquakes, khiabani

# from load_combinations import generate_concrete_load_combinations


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

@pytest.mark.getmethod
def test_generate_concrete_load_combinations_notional_loads(shayesteh):
    equal_loads = {'Dead' : ['Dead', 'SDead', 'Partition'],
                    'L' : ['Live', 'L-RED'],
                    }
    data = shayesteh.load_combinations.generate_concrete_load_combinations(
        equal_loads,
        prefix='COMBO',
        design_type="LRFD",
        separate_direction=True,
        sequence_numbering=True,
        add_notional_loads=True,
        )
    # print(data)
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

@pytest.mark.getmethod
def test_expand_linear_load_combinations(two_earthquakes):
    ret = two_earthquakes.load_patterns.get_expanded_seismic_load_patterns()
    two_earthquakes.database.write_seismic_user_coefficient_df(ret[0], ret[2])
    # ex_loads = {
    #     'EDRIFTX' : (('EXDRIFTX', 37)),
    #     'EX1' : (('EX1', 5), ('EX1N', 5), ('EX1P', 5)),
    #     'EX2' : (('EX2', 5), ('EX2N', 5), ('EX2P', 5)),
    #     'EY1' : (('EY1', 5), ('EY1N', 5), ('EY1P', 5)),
    #     'EY2' : (('EY2', 5), ('EY2N', 5), ('EY2P', 5)),
    #     'EDRIFTY' : (('EDRIFTY', 37), ('EDRIFTYN', 37), ('EDRIFTYP', 37)),
    #     }
    load_combos = two_earthquakes.load_combinations.get_expand_linear_load_combinations(
        expanded_loads = ret[1],
    )
    assert len(load_combos) == 32
    assert load_combos[0][2][6] == 'EX1P'
    assert load_combos[0][2][8] == 'EX2P'
    assert load_combos[1][2][6] == 'EX1N'
    assert load_combos[1][2][8] == 'EX2N'
    # assert load_combos == []

@pytest.mark.setmethod
def test_apply_linear_load_combinations(two_earthquakes):
    new_combos = [
        ('New comb 1', (0, 0, 0), ('DL', 'LL', 'EX1'), (1.4, -.3, 0.6)),
        ('New comb 2', (0, 0, 0), ('DL', 'LL', 'EY1'), (1.2, 0.5, 1)),
    ]
    two_earthquakes.load_combinations.apply_linear_load_combinations(
        new_combos,
    )
    ret = two_earthquakes.etabs.SapModel.RespCombo.GetCaseList('New comb 1')
    assert ret[1:-1] == [(0, 0, 0), ('DL', 'LL', 'EX1'), (1.4, -.3, 0.6)]
    

if __name__ == '__main__':
    import etabs_obj
    two_earthquakes = etabs_obj.EtabsModel(backup=True)
    ret = test_expand_linear_load_combinations(two_earthquakes)
    print('wow')
