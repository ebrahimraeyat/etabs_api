import sys
from pathlib import Path
import math

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from load_combinations import get_mabhas6_load_combinations, generate_concrete_load_combinations


def test_get_mabhas6_load_combinations():
    for way in ('LRFD', 'ASD'):
        for separate_direction in (True, False):
            for retaining_wall in (True, False):
                for code in ('ACI', 'CSA'):
                    for dynamic in ('', '100-30', 'angular'):
                        # print(f"\n{way=}, {separate_direction=}, {retaining_wall=}, {code=}, {dynamic=}")
                        d = get_mabhas6_load_combinations(way, separate_direction, retaining_wall, code, dynamic)
                        assert len(d) > 0

def test_get_mabhas6_load_combinations_1():
    ret = get_mabhas6_load_combinations(way='LRFD', separate_direction=False, retaining_wall=True, code='ACI', dynamic='100-30')
    assert math.isclose(ret['11']['Dead'], 1.4, abs_tol=.0001)

def test_generate_concrete_load_combinations_1():
    equivalent_loads= {'Dead': ['DL', 'SD'], 'L': ['LL2', 'Lpar'], 'L_5': ['LL0.5'], 'RoofLive': ['LR'], 'Snow': ['S'], 'EX': ['EX'], 'EXP': ['EXP'], 'EXN': ['EXN'], 'EY': ['EY'], 'EYP': ['EYP'], 'EYN': ['EYN'], 'SX': ['SX'], 'SXE': ['SXE'], 'SY': ['SY'], 'SYE': ['SYE'], 'EV': ['EV'], 'HXP': ['HXP'], 'HXN': ['HXN'], 'HYP': ['HYP'], 'HYN': ['HYN']}
    prefix= "DYNAMIC-"
    rho_x= 1.2
    rho_y= 1.2
    type_= "Linear Add"
    design_type= "LRFD"
    separate_direction= False
    ev_negative= True
    A= 0.3
    I= 1.2
    sequence_numbering= False
    retaining_wall= True
    dynamic= "100-30"
    data, notional_loads = generate_concrete_load_combinations(
        equivalent_loads= equivalent_loads,
        prefix= prefix,
        rho_x= rho_x,
        rho_y= rho_y,
        type_= type_,
        design_type= design_type,
        separate_direction= separate_direction,
        ev_negative= ev_negative,
        A= A,
        I= I,
        sequence_numbering= sequence_numbering,
        retaining_wall= retaining_wall,
        dynamic= dynamic,
        )

def test_generate_concrete_load_combinations():
    equal_loads = {'Dead' : ['Dead'],
                    'L' : ['Live'],
                    'L_5': ['L0.5'],
                    'RoofLive' : ['Roof'],
                    'Snow' : ['snow'],
                    'AngularDynamic': ['S0', 'S15', 'S30'],
                    'EV': ['ev'],
                    }
    mabhas6_load_combinations = {
            '2_1'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
            '2_2'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
            '3_1'   : {'Dead':0.85, 'AngularDynamic': 0.84, 'EV':-0.84},
            '81'   : {'EV':-0.84},
            }
    data, notional_loads = generate_concrete_load_combinations(
        equivalent_loads  = equal_loads,
        add_notional_loads = False,
        dynamic = 'angular',
        mabhas6_load_combinations = mabhas6_load_combinations,
        )
    print(data)
    for i in range(1, 7):
        assert data.count(f'COMBO2{i}') == 6
    for i in range(1, 4):
        assert data.count(f'COMBO3{i}') == 3
    assert data.count('COMBO81') == 1
    # Test for all conditions
    for design_type in ('LRFD', 'ASD'):
        for separate_direction in (True, False):
            for ev_negative in (True, False):
                for A in (0.3, 0.35):
                    for sequence_numbering in (True, False):
                        for add_notional_loads in (True, False):
                            for retaining_wall in (True, False):
                                for code in ("ACI", "CSA"):
                                    for dynamic in ('', '100-30', 'angular'):
                                        generate_concrete_load_combinations(
                                            equal_loads,
                                            design_type=design_type,
                                            separate_direction=separate_direction,
                                            ev_negative=ev_negative,
                                            A=A,
                                            sequence_numbering=sequence_numbering,
                                            add_notional_loads=add_notional_loads,
                                            retaining_wall=retaining_wall,
                                            code=code,
                                            dynamic=dynamic,
                                        )
        
if __name__ == "__main__":
    test_get_mabhas6_load_combinations_1()