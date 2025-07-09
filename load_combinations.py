
from typing import Union
import python_functions
import enum

import pandas as pd

@enum.unique
class COMBOTYPE(enum.IntEnum):
    Linear_Add = 0
    Envelope = 1
    Absolute_Add = 2
    Srss = 3
    Range_Add = 4

class LoadCombination:
    combotyp = COMBOTYPE
    
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def select_load_combinations(self,
        load_combinations : Union[bool, list] = None,
        deselect_load_cases : bool = True,
        ) -> None:
        if load_combinations is None:
            load_combinations = self.get_load_combination_names()
        if deselect_load_cases:
            self.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay('')
        self.SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay(load_combinations)
    
    def get_load_combination_names(self):
        try:
            load_combinations = self.SapModel.RespCombo.GetNameList()[1]
        except IndexError:
            print("There is no load combinations in this model")
            load_combinations = []
        return load_combinations
    
    def delete_load_combinations(self, combo_names):
        rets = set()
        for combo_name in combo_names:
            ret = self.etabs.SapModel.RespCombo.Delete(combo_name)
            rets.add(ret)
        return rets
    
    def add_load_combination(
        self,
        combo_name: str,
        load_case_names: list = [],
        scale_factor: float = 1,
        type_: int = 0, # envelop: 1
        ):
        '''
        Add Envelop Load combination
        '''
        self.etabs.SapModel.RespCombo.add(combo_name, type_)
        for case_name in load_case_names:
            self.etabs.SapModel.RespCombo.SetCaseList(
                combo_name,
                type_, # loadcase=0, loadcombo=1
                case_name,    # cname
                scale_factor,    # sf
                )

    def get_load_combinations_of_type(
        self,
        type_: str = 'ALL', # 'GRAVITY' , 'SEISMIC
        all_load_combos: Union[list, bool] = None,
        ):
        '''
        return load combinations with respect to type_
        '''
        if all_load_combos is None:
            all_load_combos = self.SapModel.RespCombo.GetNameList()[1]
        if type_ == 'ALL':
            return all_load_combos
        seismic_load_cases = self.etabs.load_cases.get_seismic_load_cases()
        seismic_load_combos = []
        for combo in all_load_combos:
            if self.is_seismic(
                        combo,
                        seismic_load_cases=seismic_load_cases,
                        ):
                seismic_load_combos.append(combo)
        if type_ == 'SEISMIC':
            return seismic_load_combos
        elif type_ == "GRAVITY":
            return set(all_load_combos).difference(seismic_load_combos)
        
    def is_seismic(
        self,
        combo: str,
        seismic_load_cases: Union[list, bool] = None,
        ):
        if seismic_load_cases is None:
            seismic_load_cases = self.etabs.load_cases.get_seismic_load_cases()
        load_cases = self.SapModel.RespCombo.GetCaseList(combo)[2]
        for lc in load_cases:
            if lc in seismic_load_cases:
                return True
        return False
    
    def get_table_of_load_combinations(self,
                                       cols: Union[list, None]=['Name', 'LoadName', 'Type', 'SF'],
                                       ) -> pd.DataFrame:
        table_key = "Load Combination Definitions"
        if self.etabs.database.table_name_that_containe(table_key):
            df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        else:
            load_combinations = self.get_load_combinations_of_type()
            ret = []
            for combo in load_combinations:
                type_ = self.get_type_of_combo(combo)
                type_ = self.combotyp(type_).name.replace('_', ' ').title()
                _, cases, scale_factores = self.SapModel.RespCombo.GetCaseList(combo)[1:4]
                for case, sf in zip(cases, scale_factores):
                    ret.append([combo, case, type_, sf])
            df = pd.DataFrame(ret, columns=cols)
        return df


    def get_type_of_combo(self,
        name : str,
        ):
        return self.etabs.SapModel.RespCombo.GetTypeOAPI(name)[0]
        
    def get_expand_linear_load_combinations(self,
        expanded_loads : dict,
        ):
        combo_names = self.etabs.SapModel.RespCombo.GetNameList()[1]
        seismic_load_cases = self.etabs.load_cases.get_seismic_load_cases()
        new_combos = []
        EX, EXN, EXP, EY, EYN, EYP = self.etabs.load_patterns.get_seismic_load_patterns()
        for combo in combo_names:
            type_ = self.get_type_of_combo(combo)
            if type_ == self.combotyp.Linear_Add:
                number_items, cases, scale_factores = self.etabs.SapModel.RespCombo.GetCaseList(combo)[1:4]
                max_sf = 0
                # for models that has
                max_sf_cases = []
                for case, sf in zip(cases, scale_factores):
                    if case in seismic_load_cases and abs(sf) > max_sf:
                        max_sf = abs(sf)
                if max_sf == 0:
                    continue
                for case, sf in zip(cases, scale_factores):
                    if case in seismic_load_cases and abs(sf) == max_sf:
                        max_sf_cases.append(case)

                equal_cases = expanded_loads[max_sf_cases[0]]
                # don't get existance load case, only load case that generated with expand 
                # load pattern or expand load case
                index = cases.index(max_sf_cases[0])
                load_pats = [i[0] for i in equal_cases if i[0] != max_sf_cases[0]]
                n = len(load_pats)
                for i, load in enumerate(load_pats, start=1):
                    name = f'{combo}({i}/{n}'
                    new_cases = list(cases)
                    new_cases[index] = load
                    # search for other compact load pattern in case of multi earthquake
                    # applied to structure for example EX1 and EX2
                    if len(max_sf_cases) > 1:
                        dir_ = None
                        for e in (EX, EXN, EXP, EY, EYN, EYP):
                            if load in e:
                                dir_ = e
                        for case in max_sf_cases:
                            equal_cases = expanded_loads[case]
                            index = cases.index(case)
                            load_pats = [pats[0] for pats in equal_cases if pats[0] != case]
                            for load in load_pats:
                                if load in dir_:
                                    new_cases[index] = load
                    new_combos.append(
                        (name, number_items, new_cases, scale_factores)
                    )
            # elif type_ == 'Envelope':
            #     pass
        return new_combos

    def apply_linear_load_combinations(self,
        new_combos : list,
        ):
        for combo in new_combos:
            name = combo[0]
            self.etabs.SapModel.RespCombo.Add(name, 0)
            for number_item, case, scale_factore in zip(*combo[1:]):
                self.etabs.SapModel.RespCombo.SetCaseList(
                    name,
                    number_item,
                    case,
                    scale_factore,
                )
        return True

    def generate_concrete_load_combinations(self,
        equivalent_loads : dict,
        prefix : str = 'COMBO',
        suffix : str = '',
        rho_x : float = 1,
        rho_y : float = 1,
        type_ : str = 'Linear Add',
        design_type: str = 'LRFD',
        separate_direction: bool = False,
        ev_negative: bool = True,
        A: float = 0.3,
        I: float = 1,
        sequence_numbering: bool = False,
        add_notional_loads: bool = False,
        retaining_wall: bool = False,
        omega_x: float=0,
        omega_y: float=0,
        rho_x1 : float = 1,
        rho_y1 : float = 1,
        omega_x1: float=0,
        omega_y1: float=0,
        code: str="ACI",
        dynamic: str="", # '100-30' , 'angular'
        ):
        data, notional_loads = generate_concrete_load_combinations(
            equivalent_loads=equivalent_loads,
            prefix=prefix,
            suffix=suffix,
            rho_x=rho_x,
            rho_y=rho_y,
            type_=type_,
            design_type=design_type,
            separate_direction=separate_direction,
            ev_negative=ev_negative,
            A=A,
            I=I,
            sequence_numbering=sequence_numbering,
            add_notional_loads=add_notional_loads,
            retaining_wall=retaining_wall,
            omega_x=omega_x,
            omega_y=omega_y,
            rho_x1=rho_x1,
            rho_y1=rho_y1,
            omega_x1=omega_x1,
            omega_y1=omega_y1,
            code=code,
            dynamic=dynamic,
            )
        if notional_loads:
            etabs_notional_loads = self.etabs.load_patterns.get_notional_load_pattern_names()
            current_notional_loads = set()
            for nl in etabs_notional_loads:
                current_notional_loads.add(nl[1:-1])
            diff = set(notional_loads).difference(current_notional_loads)
            if len(diff) > 0:
                self.etabs.load_patterns.add_notional_loads(diff)
        return data
    
    def create_load_combinations_from_loads(self,
                                            load_names: list,
                                            suffix: str='',
                                            prefix: str='',
                                            type_: str = 'Concrete', # 'Steel'
                                            code : Union[str, None] = None,
                                            ):
        combos = []
        load_cases = []
        for load in load_names:
            if load:
                self.SapModel.RespCombo.Add(f'{prefix}{load}{suffix}', 0)
                self.SapModel.RespCombo.SetCaseList(f'{prefix}{load}{suffix}', 0, load, 1)
                combos.append(['Strength', f'{prefix}{load}{suffix}'])
                load_cases.append(load)
        # set overwrite for columns
        if code is None:
            code = self.etabs.design.get_code(type_)
        code_string = self.etabs.design.get_code_string(type_, code)
        # set design combo
        if self.etabs.etabs_main_version < 20:
            cols = ['Combo Type', 'Combo Name']
            cols1 = ['Design Type']
        else:
            cols = ['ComboType', 'ComboName']
            cols1 = ['DesignType']
        if type_ == 'Concrete':
            columns = self.etabs.frame_obj.set_column_dns_overwrite(code=code_string, type_=type_)
            df = pd.DataFrame(combos,columns=cols)
            table_key = 'Concrete Frame Design Load Combination Data'
        elif type_ == 'Steel':
            for c in combos:
                c.insert(0, 'Steel Frame')
            # self.etabs.set_infinite_bending_capacity_for_steel_columns(code_string)
            df = pd.DataFrame(combos,
                                columns=cols1 + cols
                                )
            table_key = 'Steel Design Load Combination Data'
            columns = self.etabs.frame_obj.get_beams_columns(type_=1)[1]
        self.etabs.database.apply_data(table_key, df)
        return load_cases, columns, code
            
def get_mabhas6_load_combinations(
    way='LRFD', # 'ASD'
    separate_direction: bool = False,
    retaining_wall: bool = False,
    code: str = 'ACI',
    dynamic: str= '',
    ):
    '''
    separate_direction: For 100-30 earthquake
    '''
    if separate_direction:
        if retaining_wall:
            if way == "LRFD":
                if code.lower() == "aci":
                    if dynamic:
                        gravity = {
                            '11'   : {'Dead':1.4, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '21'   : {'Dead':1.2, 'L':1.6, 'L_5':1.6, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '22'   : {'Dead':1.2, 'L':1.6, 'L_5':1.6, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        }
                        if dynamic == '100-30':
                            seismic =  {
                                '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                                '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                                '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                                '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                                '71'   : {'Dead':0.9, 'SXE': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                                '72'   : {'Dead':0.9, 'SXE': 1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                                '73'   : {'Dead':0.9, 'SYE': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                                '74'   : {'Dead':0.9, 'SYE': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                                '81'   : {'EV':-1},
                            }
                        elif dynamic == 'angular':
                            seismic =  {
                                '5_1'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                                '5_2'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                                '5_3'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                                '5_4'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                                '7_1'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                                '7_2'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                                '7_3'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                                '7_4'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                                '81'   : {'EV':-1},

                            }
                        gravity.update(seismic)
                        return gravity
                    else:
                        return {
                            '11'   : {'Dead':1.4, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '21'   : {'Dead':1.2, 'L':1.6, 'L_5':1.6, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '22'   : {'Dead':1.2, 'L':1.6, 'L_5':1.6, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP': 1, 'EXP1': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                            '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN': 1, 'EXN1': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                            '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP':-1, 'EXP1':-1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN':-1, 'EXN1':-1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP': 1, 'EYP1': 1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '56'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN': 1, 'EYN1': 1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '57'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP':-1, 'EYP1':-1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '58'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN':-1, 'EYN1':-1, 'EV':1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '71'   : {'Dead':0.9, 'EXP': 1, 'EXP1': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                            '72'   : {'Dead':0.9, 'EXN': 1, 'EXN1': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 1.6},
                            '73'   : {'Dead':0.9, 'EXP':-1, 'EXP1':-1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '74'   : {'Dead':0.9, 'EXN':-1, 'EXN1':-1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                            '75'   : {'Dead':0.9, 'EYP': 1, 'EYP1': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '76'   : {'Dead':0.9, 'EYN': 1, 'EYN1': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '77'   : {'Dead':0.9, 'EYP':-1, 'EYP1':-1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '78'   : {'Dead':0.9, 'EYN':-1, 'EYN1':-1, 'EV':-1, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '81'   : {'EV':-1},
                        }
                elif code.lower() == "csa":
                    if dynamic:
                        gravity = {
                            '11'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'RoofLive':1.5},
                            '12'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'Snow':1.5},
                            '41'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                            '42'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                            '51'  : {'Dead':0.85, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        }
                        if dynamic == '100-30':
                            seismic =  {
                            '21'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SXE': 0.84, 'EV':0.84},
                            '22'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SXE': 0.84, 'EV':0.84},
                            '23'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SYE': 0.84, 'EV':0.84},
                            '24'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SYE': 0.84, 'EV':0.84},
                            '31'  : {'Dead':0.85, 'SXE': 0.84, 'EV':-0.84},
                            '32'  : {'Dead':0.85, 'SYE': 0.84, 'EV':-0.84},
                            '81'  : {'EV':-0.84},
                        }
                        elif dynamic == 'angular':
                            seismic =  {
                            '2_1'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
                            '2_2'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
                            '3_1'  : {'Dead':0.85, 'AngularDynamic': 0.84, 'EV':-0.84},
                            '81'  : {'EV':-0.84},
                            }
                        gravity.update(seismic)
                        return gravity
                    else:
                        return {
                            '11'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'RoofLive':1.5},
                            '12'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'Snow':1.5},
                            '21'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EV':0.84},
                            '22'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EV':0.84},
                            '23'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EV':0.84},
                            '24'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EV':0.84},
                            '25'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EV':0.84},
                            '26'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EV':0.84},
                            '27'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EV':0.84},
                            '28'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EV':0.84},
                            '29'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EV':0.84},
                            '210' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EV':0.84},
                            '211' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EV':0.84},
                            '212' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EV':0.84},
                            '213' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EV':0.84},
                            '214' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EV':0.84},
                            '215' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EV':0.84},
                            '216' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EV':0.84},
                            '31'  : {'Dead':0.85, 'EXP': 0.84, 'EXP1': 0.84, 'EV':-0.84},
                            '32'  : {'Dead':0.85, 'EXN': 0.84, 'EXN1': 0.84, 'EV':-0.84},
                            '33'  : {'Dead':0.85, 'EXP':-0.84, 'EXP1':-0.84, 'EV':-0.84},
                            '34'  : {'Dead':0.85, 'EXN':-0.84, 'EXN1':-0.84, 'EV':-0.84},
                            '35'  : {'Dead':0.85, 'EYP': 0.84, 'EYP1': 0.84, 'EV':-0.84},
                            '36'  : {'Dead':0.85, 'EYN': 0.84, 'EYN1': 0.84, 'EV':-0.84},
                            '37'  : {'Dead':0.85, 'EYP':-0.84, 'EYP1':-0.84, 'EV':-0.84},
                            '38'  : {'Dead':0.85, 'EYN':-0.84, 'EYN1':-0.84, 'EV':-0.84},
                            '41'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                            '42'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                            '51'  : {'Dead':0.85, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                            '81'  : {'EV':-0.84},
                        }
            elif way == "ASD":
                if dynamic:
                    gravity = {
                        '11'   : {'Dead':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '21'   : {'Dead':1, 'L':1, 'L_5':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '31'   : {'Dead':1, 'Snow':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '32'   : {'Dead':1, 'RoofLive':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    }
                    if dynamic == "100-30":
                        seismic = {
                            '71'   : {'Dead':1, 'SXE': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                            '72'   : {'Dead':1, 'SXE': 0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                            '73'   : {'Dead':1, 'SYE': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                            '74'   : {'Dead':1, 'SYE': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                            '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                            '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                            '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                            '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                            '101'  : {'Dead':0.6, 'SXE': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                            '102'  : {'Dead':0.6, 'SXE': 0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                            '103'  : {'Dead':0.6, 'SYE': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                            '104'  : {'Dead':0.6, 'SYE': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        }
                    elif dynamic == 'angular':
                        seismic = {
                            '7_1'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                            '7_2'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                            '7_3'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                            '7_4'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                            '8_1'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                            '8_2'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                            '8_3'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                            '8_4'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                            '10_1'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                            '10_2'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                            '10_3'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                            '10_4'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        }
                    gravity.update(seismic)
                    return gravity
                else:
                    return {
                        '11'   : {'Dead':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '21'   : {'Dead':1, 'L':1, 'L_5':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '31'   : {'Dead':1, 'Snow':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '32'   : {'Dead':1, 'RoofLive':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '71'   : {'Dead':1, 'EXP': 0.7, 'EXP1': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '72'   : {'Dead':1, 'EXN': 0.7, 'EXN1': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '73'   : {'Dead':1, 'EXP':-0.7, 'EXP1':-0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '74'   : {'Dead':1, 'EXN':-0.7, 'EXN1':-0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '75'   : {'Dead':1, 'EYP': 0.7, 'EYP1': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '76'   : {'Dead':1, 'EYN': 0.7, 'EYN1': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '77'   : {'Dead':1, 'EYP':-0.7, 'EYP1':-0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '78'   : {'Dead':1, 'EYN':-0.7, 'EYN1':-0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '79'   : {'Dead':1, 'EX': 0.7, 'EX1': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '710'  : {'Dead':1, 'EX':-0.7, 'EX1':-0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '711'  : {'Dead':1, 'EY': 0.7, 'EY1': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '712'  : {'Dead':1, 'EY':-0.7, 'EY1':-0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP': 0.525, 'EXP1': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN': 0.525, 'EXN1': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP':-0.525, 'EXP1':-0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN':-0.525, 'EXN1':-0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP': 0.525, 'EYP1': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '86'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN': 0.525, 'EYN1': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '87'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP':-0.525, 'EYP1':-0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '88'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN':-0.525, 'EYN1':-0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '89'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EX1' : 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '810'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EX1' :-0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '811'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EY1' : 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '812'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EY1' :-0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '101'  : {'Dead':0.6, 'EXP': 0.7, 'EXP1': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '102'  : {'Dead':0.6, 'EXN': 0.7, 'EXN1': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '103'  : {'Dead':0.6, 'EXP':-0.7, 'EXP1':-0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '104'  : {'Dead':0.6, 'EXN':-0.7, 'EXN1':-0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '105'  : {'Dead':0.6, 'EYP': 0.7, 'EYP1': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '106'  : {'Dead':0.6, 'EYN': 0.7, 'EYN1': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '107'  : {'Dead':0.6, 'EYP':-0.7, 'EYP1':-0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '108'  : {'Dead':0.6, 'EYN':-0.7, 'EYN1':-0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        '109'  : {'Dead':0.6, 'EX' : 0.7, 'EX1' : 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 1.0},
                        '1010' : {'Dead':0.6, 'EX' :-0.7, 'EX1' :-0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                        '1011' : {'Dead':0.6, 'EY' : 0.7, 'EY1' : 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                        '1012' : {'Dead':0.6, 'EY' :-0.7, 'EY1' :-0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    }
        else:
            if way == "LRFD":
                if code == 'ACI':
                    if dynamic:
                        gravity = {
                        '11'   : {'Dead':1.4},
                        '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5},
                        '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5},
                        '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
                        '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
                        '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
                        '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
                        }
                        if dynamic == '100-30':
                            seismic = {
                            '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'EV':1},
                            '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'EV':1},
                            '71'   : {'Dead':0.9, 'SXE': 1, 'EV':-1},
                            '72'   : {'Dead':0.9, 'SYE': 1, 'EV':-1},
                            '81'   : {'EV':-1},
                            }
                        elif dynamic == 'angular':
                            seismic = {
                            '5_1'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1},
                            '7_1'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1},
                            '81'   : {'EV':-1},
                            }
                        gravity.update(seismic)
                        return gravity
                    else:
                        return {
                            '11'   : {'Dead':1.4},
                            '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5},
                            '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5},
                            '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
                            '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
                            '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
                            '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
                            '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP': 1, 'EXP1': 1, 'EV':1},
                            '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN': 1, 'EXN1': 1, 'EV':1},
                            '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP':-1, 'EXP1':-1, 'EV':1},
                            '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN':-1, 'EXN1':-1, 'EV':1},
                            '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP': 1, 'EYP1': 1, 'EV':1},
                            '56'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN': 1, 'EYN1': 1, 'EV':1},
                            '57'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP':-1, 'EYP1':-1, 'EV':1},
                            '58'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN':-1, 'EYN1':-1, 'EV':1},
                            '71'   : {'Dead':0.9, 'EXP': 1, 'EXP1': 1, 'EV':-1},
                            '72'   : {'Dead':0.9, 'EXN': 1, 'EXN1': 1, 'EV':-1},
                            '73'   : {'Dead':0.9, 'EXP':-1, 'EXP1':-1, 'EV':-1},
                            '74'   : {'Dead':0.9, 'EXN':-1, 'EXN1':-1, 'EV':-1},
                            '75'   : {'Dead':0.9, 'EYP': 1, 'EYP1': 1, 'EV':-1},
                            '76'   : {'Dead':0.9, 'EYN': 1, 'EYN1': 1, 'EV':-1},
                            '77'   : {'Dead':0.9, 'EYP':-1, 'EYP1':-1, 'EV':-1},
                            '78'   : {'Dead':0.9, 'EYN':-1, 'EYN1':-1, 'EV':-1},
                            '81'   : {'EV':-1},
                        }
                elif code.lower() == "csa":
                    if dynamic:
                        gravity = {
                        '11'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'RoofLive':1.5},
                        '12'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'Snow':1.5},
                        '41'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5},
                        '42'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5},
                        }
                        if dynamic == "100-30":
                            seismic = {
                            '21'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SXE': 0.84, 'EV':0.84},
                            '22'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SYE': 0.84, 'EV':0.84},
                            '23'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SXE': 0.84, 'EV':0.84},
                            '24'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SYE': 0.84, 'EV':0.84},
                            '31'  : {'Dead':0.85, 'SXE': 0.84, 'EV':-0.84},
                            '32'  : {'Dead':0.85, 'SYE': 0.84, 'EV':-0.84},
                            '81'  : {'EV':-0.84},
                            }
                        elif dynamic == 'angular':
                            seismic = {
                            '2_1'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
                            '2_2'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
                            '3_1'  : {'Dead':0.85, 'AngularDynamic': 0.84, 'EV':-0.84},
                            '81'  : {'EV':-0.84},
                            }
                        gravity.update(seismic)
                        return gravity

                    else:
                        return {
                            '11'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'RoofLive':1.5},
                            '12'  : {'Dead':1.25, 'L':1.5, 'L_5':1.5, 'Snow':1.5},
                            '21'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EV':0.84},
                            '22'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EV':0.84},
                            '23'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EV':0.84},
                            '24'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EV':0.84},
                            '25'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EV':0.84},
                            '26'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EV':0.84},
                            '27'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EV':0.84},
                            '28'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EV':0.84},
                            '29'  : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EV':0.84},
                            '210' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EV':0.84},
                            '211' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EV':0.84},
                            '212' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EV':0.84},
                            '213' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EV':0.84},
                            '214' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EV':0.84},
                            '215' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EV':0.84},
                            '216' : {'Dead':1.0,  'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EV':0.84},
                            '31'  : {'Dead':0.85, 'EXP': 0.84, 'EXP1': 0.84, 'EV':-0.84},
                            '32'  : {'Dead':0.85, 'EXN': 0.84, 'EXN1': 0.84, 'EV':-0.84},
                            '33'  : {'Dead':0.85, 'EXP':-0.84, 'EXP1':-0.84, 'EV':-0.84},
                            '34'  : {'Dead':0.85, 'EXN':-0.84, 'EXN1':-0.84, 'EV':-0.84},
                            '35'  : {'Dead':0.85, 'EYP': 0.84, 'EYP1': 0.84, 'EV':-0.84},
                            '36'  : {'Dead':0.85, 'EYN': 0.84, 'EYN1': 0.84, 'EV':-0.84},
                            '37'  : {'Dead':0.85, 'EYP':-0.84, 'EYP1':-0.84, 'EV':-0.84},
                            '38'  : {'Dead':0.85, 'EYN':-0.84, 'EYN1':-0.84, 'EV':-0.84},
                            '41'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5},
                            '42'  : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5},
                            '81'  : {'EV':-0.84},
                        }
            elif way == "ASD":
                if dynamic:
                    gravity = {
                        '11'   : {'Dead':1},
                        '21'   : {'Dead':1, 'L':1, 'L_5':1},
                        '31'   : {'Dead':1, 'Snow':1},
                        '32'   : {'Dead':1, 'RoofLive':1},
                        '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75},
                        '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75},
                    }
                    if dynamic == "100-30":
                        seismic = {
                            '71'   : {'Dead':1, 'SXE': 0.7, 'EV':0.7},
                            '72'   : {'Dead':1, 'SYE': 0.7, 'EV':0.7},
                            '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'EV':0.525},
                            '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'EV':0.525},
                            '101'  : {'Dead':0.6, 'SXE': 0.7, 'EV':-0.7},
                            '102'  : {'Dead':0.6, 'SYE': 0.7, 'EV':-0.7},

                        }
                    if dynamic == "angular":
                        seismic = {
                            '7_1'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7},
                            '8_1'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525},
                            '10_1'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7},

                        }
                    gravity.update(seismic)
                    return gravity
                return {
                    '11'   : {'Dead':1},
                    '21'   : {'Dead':1, 'L':1, 'L_5':1},
                    '31'   : {'Dead':1, 'Snow':1},
                    '32'   : {'Dead':1, 'RoofLive':1},
                    '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75},
                    '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75},
                    '71'   : {'Dead':1, 'EXP': 0.7, 'EXP1': 0.7, 'EV':0.7},
                    '72'   : {'Dead':1, 'EXN': 0.7, 'EXN1': 0.7, 'EV':0.7},
                    '73'   : {'Dead':1, 'EXP':-0.7, 'EXP1':-0.7, 'EV':0.7},
                    '74'   : {'Dead':1, 'EXN':-0.7, 'EXN1':-0.7, 'EV':0.7},
                    '75'   : {'Dead':1, 'EYP': 0.7, 'EYP1': 0.7, 'EV':0.7},
                    '76'   : {'Dead':1, 'EYN': 0.7, 'EYN1': 0.7, 'EV':0.7},
                    '77'   : {'Dead':1, 'EYP':-0.7, 'EYP1':-0.7, 'EV':0.7},
                    '78'   : {'Dead':1, 'EYN':-0.7, 'EYN1':-0.7, 'EV':0.7},
                    '79'   : {'Dead':1, 'EX': 0.7, 'EX1': 0.7, 'EV':0.7},
                    '710'  : {'Dead':1, 'EX':-0.7, 'EX1':-0.7, 'EV':0.7},
                    '711'  : {'Dead':1, 'EY': 0.7, 'EY1': 0.7, 'EV':0.7},
                    '712'  : {'Dead':1, 'EY':-0.7, 'EY1':-0.7, 'EV':0.7},
                    '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP': 0.525, 'EXP1': 0.525, 'EV':0.525},
                    '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN': 0.525, 'EXN1': 0.525, 'EV':0.525},
                    '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP':-0.525, 'EXP1':-0.525, 'EV':0.525},
                    '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN':-0.525, 'EXN1':-0.525, 'EV':0.525},
                    '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP': 0.525, 'EYP1': 0.525, 'EV':0.525},
                    '86'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN': 0.525, 'EYN1': 0.525, 'EV':0.525},
                    '87'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP':-0.525, 'EYP1':-0.525, 'EV':0.525},
                    '88'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN':-0.525, 'EYN1':-0.525, 'EV':0.525},
                    '89'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EX1' : 0.525, 'EV':0.525},
                    '810'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EX1' :-0.525, 'EV':0.525},
                    '811'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EY1' : 0.525, 'EV':0.525},
                    '812'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EY1' :-0.525, 'EV':0.525},
                    '101'  : {'Dead':0.6, 'EXP': 0.7, 'EXP1': 0.7, 'EV':-0.7},
                    '102'  : {'Dead':0.6, 'EXN': 0.7, 'EXN1': 0.7, 'EV':-0.7},
                    '103'  : {'Dead':0.6, 'EXP':-0.7, 'EXP1':-0.7, 'EV':-0.7},
                    '104'  : {'Dead':0.6, 'EXN':-0.7, 'EXN1':-0.7, 'EV':-0.7},
                    '105'  : {'Dead':0.6, 'EYP': 0.7, 'EYP1': 0.7, 'EV':-0.7},
                    '106'  : {'Dead':0.6, 'EYN': 0.7, 'EYN1': 0.7, 'EV':-0.7},
                    '107'  : {'Dead':0.6, 'EYP':-0.7, 'EYP1':-0.7, 'EV':-0.7},
                    '108'  : {'Dead':0.6, 'EYN':-0.7, 'EYN1':-0.7, 'EV':-0.7},
                    '109'  : {'Dead':0.6, 'EX' : 0.7, 'EX1' : 0.7, 'EV':-0.7},
                    '1010' : {'Dead':0.6, 'EX' :-0.7, 'EX1' :-0.7, 'EV':-0.7},
                    '1011' : {'Dead':0.6, 'EY' : 0.7, 'EY1' : 0.7, 'EV':-0.7},
                    '1012' : {'Dead':0.6, 'EY' :-0.7, 'EY1' :-0.7, 'EV':-0.7},
                }
    else:
        if retaining_wall:
            if way == "LRFD":
                if code == 'ACI':
                    if dynamic:
                        gravity = {
                        '11'   : {'Dead':1.4 , 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        }
                        if dynamic == "100-30":
                            seismic = {
                            '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'SY': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'SY': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'SY': 0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'SY': 0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'SX': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '56'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'SX': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '57'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'SX': 0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '58'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'SX': 0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '71'   : {'Dead':0.9, 'SXE': 1, 'SY': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '72'   : {'Dead':0.9, 'SXE': 1, 'SY': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '73'   : {'Dead':0.9, 'SXE': 1, 'SY': 0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '74'   : {'Dead':0.9, 'SXE': 1, 'SY': 0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '75'   : {'Dead':0.9, 'SYE': 1, 'SX': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '76'   : {'Dead':0.9, 'SYE': 1, 'SX': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '77'   : {'Dead':0.9, 'SYE': 1, 'SX': 0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '78'   : {'Dead':0.9, 'SYE': 1, 'SX': 0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '81'   : {'EV':-1},
                            }
                        if dynamic == "angular":
                            seismic = {
                            '5_1'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '5_2'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '5_3'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '5_4'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '5_5'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '5_6'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '5_7'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '5_8'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '7_1'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '7_2'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '7_3'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '7_4'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '7_5'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                            '7_6'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                            '7_7'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                            '7_8'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                            '81'   : {'EV':-1},
                            }
                        gravity.update(seismic)
                        return gravity
                    return {
                        '11'   : {'Dead':1.4 , 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP': 1, 'EXP1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN': 1, 'EXN1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP': 1, 'EXP1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN': 1, 'EXN1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP':-1, 'EXP1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '56'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN':-1, 'EXN1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '57'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP':-1, 'EXP1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '58'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN':-1, 'EXN1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '59'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP': 1, 'EYP1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '510'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN': 1, 'EYN1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '511'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP': 1, 'EYP1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '512'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN': 1, 'EYN1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '513'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP':-1, 'EYP1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '514'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN':-1, 'EYN1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '515'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP':-1, 'EYP1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '516'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN':-1, 'EYN1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '71'   : {'Dead':0.9, 'EXP': 1, 'EXP1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '72'   : {'Dead':0.9, 'EXN': 1, 'EXN1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '73'   : {'Dead':0.9, 'EXP': 1, 'EXP1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '74'   : {'Dead':0.9, 'EXN': 1, 'EXN1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '75'   : {'Dead':0.9, 'EXP':-1, 'EXP1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '76'   : {'Dead':0.9, 'EXN':-1, 'EXN1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '77'   : {'Dead':0.9, 'EXP':-1, 'EXP1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '78'   : {'Dead':0.9, 'EXN':-1, 'EXN1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '79'   : {'Dead':0.9, 'EYP': 1, 'EYP1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '710'  : {'Dead':0.9, 'EYN': 1, 'EYN1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 1.6, 'HYN': 0.9},
                        '711'  : {'Dead':0.9, 'EYP': 1, 'EYP1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '712'  : {'Dead':0.9, 'EYN': 1, 'EYN1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 0.9},
                        '713'  : {'Dead':0.9, 'EYP':-1, 'EYP1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '714'  : {'Dead':0.9, 'EYN':-1, 'EYN1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1, 'HXP': 1.6, 'HXN': 0.9, 'HYP': 0.9, 'HYN': 1.6},
                        '715'  : {'Dead':0.9, 'EYP':-1, 'EYP1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '716'  : {'Dead':0.9, 'EYN':-1, 'EYN1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1, 'HXP': 0.9, 'HXN': 1.6, 'HYP': 0.9, 'HYN': 1.6},
                        '81'   : {'EV':-1},
                    }
                elif code == 'CSA':
                    if dynamic:
                        gravity = {
                        '11'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'RoofLive':1.5}, #'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '12'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'Snow':1.5}, #'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '41'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '42'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '51'   : {'Dead':0.85, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},

                        }
                        if dynamic == "100-30":
                            seismic = {
                                    '21'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SXE': 0.84, 'SY': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '22'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SYE': 0.84, 'SX': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '23'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SXE': 0.84, 'SY': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '24'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SYE': 0.84, 'SX': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '31'   : {'Dead':0.85, 'SXE': 0.84, 'SY': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '32'   : {'Dead':0.85, 'SYE': 0.84, 'SX': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '81'   : {'EV':-0.84},
                            }
                        if dynamic == "angular":
                            seismic = {
                                    '2_1'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'AngularDynamic': 0.84, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '2_2'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'AngularDynamic': 0.84, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '3_1'   : {'Dead':0.85, 'AngularDynamic': 0.84, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                                    '81'   : {'EV':-0.84},
                            }
                        gravity.update(seismic)
                        return gravity
                    return {
                        '11'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'RoofLive':1.5}, #'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '12'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'Snow':1.5}, #'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        # '31'   : {'Dead':1.0, 'L':1, 'L_5':0.5, 'RoofLive':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        # '32'   : {'Dead':1.0, 'L':1, 'L_5':0.5, 'Snow':1.6, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        # '41'   : {'Dead':1.0, 'L':1, 'L_5':0.5, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        # '42'   : {'Dead':1.0, 'L':1, 'L_5':0.5, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '21'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '22'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '23'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '24'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '25'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '26'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '27'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '28'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '29'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '210'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '211'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '212'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '213'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '214'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '215'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '216'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '217'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '218'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '219'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '220'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '221'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '222'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '223'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '224'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '225'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '226'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '227'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '228'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '229'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '230'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '231'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '232'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '31'   : {'Dead':0.85, 'EXP': 0.84, 'EXP1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '32'   : {'Dead':0.85, 'EXN': 0.84, 'EXN1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '33'   : {'Dead':0.85, 'EXP': 0.84, 'EXP1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '34'   : {'Dead':0.85, 'EXN': 0.84, 'EXN1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '35'   : {'Dead':0.85, 'EXP':-0.84, 'EXP1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '36'   : {'Dead':0.85, 'EXN':-0.84, 'EXN1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '37'   : {'Dead':0.85, 'EXP':-0.84, 'EXP1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '38'   : {'Dead':0.85, 'EXN':-0.84, 'EXN1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '39'   : {'Dead':0.85, 'EYP': 0.84, 'EYP1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '310'  : {'Dead':0.85, 'EYN': 0.84, 'EYN1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '311'  : {'Dead':0.85, 'EYP': 0.84, 'EYP1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '312'  : {'Dead':0.85, 'EYN': 0.84, 'EYN1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '313'  : {'Dead':0.85, 'EYP':-0.84, 'EYP1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '314'  : {'Dead':0.85, 'EYN':-0.84, 'EYN1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '315'  : {'Dead':0.85, 'EYP':-0.84, 'EYP1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '316'  : {'Dead':0.85, 'EYN':-0.84, 'EYN1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '41'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '42'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '51'   : {'Dead':0.85, 'HXP': 1.5, 'HXN': 1.5, 'HYP': 1.5, 'HYN': 1.5},
                        '81'   : {'EV':-0.84},
                    }
            elif way == "ASD":
                if dynamic:
                    gravity = {
                    '11'   : {'Dead':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '21'   : {'Dead':1, 'L':1, 'L_5':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '31'   : {'Dead':1, 'Snow':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '32'   : {'Dead':1, 'RoofLive':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    }
                    if dynamic == "100-30":
                        seismic = {
                                '71'   : {'Dead':1, 'SXE': 0.7, 'SY': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '72'   : {'Dead':1, 'SXE': 0.7, 'SY': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '73'   : {'Dead':1, 'SXE': 0.7, 'SY': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '74'   : {'Dead':1, 'SXE': 0.7, 'SY': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '75'   : {'Dead':1, 'SYE': 0.7, 'SX': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '76'   : {'Dead':1, 'SYE': 0.7, 'SX': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '77'   : {'Dead':1, 'SYE': 0.7, 'SX': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '78'   : {'Dead':1, 'SYE': 0.7, 'SX': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'SY': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'SY': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'SY': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'SY': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'SX': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '86'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'SX': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '87'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'SX': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '88'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'SX': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '101'  : {'Dead':0.6, 'SXE': 0.7, 'SY': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '103'  : {'Dead':0.6, 'SXE': 0.7, 'SY': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '105'  : {'Dead':0.6, 'SXE': 0.7, 'SY': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '107'  : {'Dead':0.6, 'SXE': 0.7, 'SY': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '109'  : {'Dead':0.6, 'SYE': 0.7, 'SX': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '1011' : {'Dead':0.6, 'SYE': 0.7, 'SX': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '1013' : {'Dead':0.6, 'SYE': 0.7, 'SX': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '1015' : {'Dead':0.6, 'SYE': 0.7, 'SX': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        }
                    elif dynamic == 'angular':
                        seismic = {
                                '7_1'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '7_2'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '7_3'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '7_4'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '8_1'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '8_2'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '8_3'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '8_4'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                                '10_1'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                                '10_2'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                                '10_3'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                                '10_4'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                        }
                    gravity.update(seismic)
                    return gravity
                return {
                    '11'   : {'Dead':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '21'   : {'Dead':1, 'L':1, 'L_5':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '31'   : {'Dead':1, 'Snow':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '32'   : {'Dead':1, 'RoofLive':1, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75, 'HXP': 1.0, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 1.0},
                    '71'   : {'Dead':1, 'EXP': 0.7, 'EXP1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '72'   : {'Dead':1, 'EXN': 0.7, 'EXN1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '73'   : {'Dead':1, 'EXP': 0.7, 'EXP1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '74'   : {'Dead':1, 'EXN': 0.7, 'EXN1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '75'   : {'Dead':1, 'EXP':-0.7, 'EXP1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '76'   : {'Dead':1, 'EXN':-0.7, 'EXN1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '77'   : {'Dead':1, 'EXP':-0.7, 'EXP1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '78'   : {'Dead':1, 'EXN':-0.7, 'EXN1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '79'   : {'Dead':1, 'EYP': 0.7, 'EYP1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '710'  : {'Dead':1, 'EYN': 0.7, 'EYN1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '711'  : {'Dead':1, 'EYP': 0.7, 'EYP1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '712'  : {'Dead':1, 'EYN': 0.7, 'EYN1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '713'  : {'Dead':1, 'EYP':-0.7, 'EYP1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '714'  : {'Dead':1, 'EYN':-0.7, 'EYN1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '715'  : {'Dead':1, 'EYP':-0.7, 'EYP1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '716'  : {'Dead':1, 'EYN':-0.7, 'EYN1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '717'  : {'Dead':1, 'EX': 0.7, 'EX1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '718'  : {'Dead':1, 'EX':-0.7, 'EX1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '719'  : {'Dead':1, 'EX': 0.7, 'EX1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '720'  : {'Dead':1, 'EX':-0.7, 'EX1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '721'  : {'Dead':1, 'EY': 0.7, 'EY1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '722'  : {'Dead':1, 'EY':-0.7, 'EY1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '723'  : {'Dead':1, 'EY': 0.7, 'EY1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '724'  : {'Dead':1, 'EY':-0.7, 'EY1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP': 0.525, 'EXP1': 0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN': 0.525, 'EXN1': 0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP': 0.525, 'EXP1': 0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN': 0.525, 'EXN1': 0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP':-0.525, 'EXP1':-0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '86'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN':-0.525, 'EXN1':-0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '87'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP':-0.525, 'EXP1':-0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '88'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN':-0.525, 'EXN1':-0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '89'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP': 0.525, 'EYP1': 0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '810'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN': 0.525, 'EYN1': 0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '811'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP': 0.525, 'EYP1': 0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '812'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN': 0.525, 'EYN1': 0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '813'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP':-0.525, 'EYP1':-0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '814'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN':-0.525, 'EYN1':-0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '815'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP':-0.525, 'EYP1':-0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '816'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN':-0.525, 'EYN1':-0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '817'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EX1' : 0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '818'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EX1' : 0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '819'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EX1' :-0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '820'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EX1' :-0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '821'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EY1' : 0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '822'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EY1' : 0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '823'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EY1' :-0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '824'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EY1' :-0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '101'  : {'Dead':0.6, 'EXP': 0.7, 'EXP1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '102'  : {'Dead':0.6, 'EXN': 0.7, 'EXN1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '103'  : {'Dead':0.6, 'EXP': 0.7, 'EXP1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '104'  : {'Dead':0.6, 'EXN': 0.7, 'EXN1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '105'  : {'Dead':0.6, 'EXP':-0.7, 'EXP1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '106'  : {'Dead':0.6, 'EXN':-0.7, 'EXN1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '107'  : {'Dead':0.6, 'EXP':-0.7, 'EXP1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '108'  : {'Dead':0.6, 'EXN':-0.7, 'EXN1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '109'  : {'Dead':0.6, 'EYP': 0.7, 'EYP1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '1010' : {'Dead':0.6, 'EYN': 0.7, 'EYN1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '1011' : {'Dead':0.6, 'EYP': 0.7, 'EYP1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '1012' : {'Dead':0.6, 'EYN': 0.7, 'EYN1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '1013' : {'Dead':0.6, 'EYP':-0.7, 'EYP1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '1014' : {'Dead':0.6, 'EYN':-0.7, 'EYN1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '1015' : {'Dead':0.6, 'EYP':-0.7, 'EYP1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '1016' : {'Dead':0.6, 'EYN':-0.7, 'EYN1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '1017' : {'Dead':0.6, 'EX' : 0.7, 'EX1' : 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '1018' : {'Dead':0.6, 'EX' : 0.7, 'EX1' : 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '1019' : {'Dead':0.6, 'EX' :-0.7, 'EX1' :-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '1020' : {'Dead':0.6, 'EX' :-0.7, 'EX1' :-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                    '1021' : {'Dead':0.6, 'EY' : 0.7, 'EY1' : 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 1.0, 'HYN': 0.6},
                    '1022' : {'Dead':0.6, 'EY' : 0.7, 'EY1' : 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 1.0, 'HYN': 0.6},
                    '1023' : {'Dead':0.6, 'EY' :-0.7, 'EY1' :-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7, 'HXP': 1.0, 'HXN': 0.6, 'HYP': 0.6, 'HYN': 1.0},
                    '1024' : {'Dead':0.6, 'EY' :-0.7, 'EY1' :-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7, 'HXP': 0.6, 'HXN': 1.0, 'HYP': 0.6, 'HYN': 1.0},
                }
        else:
            if way == "LRFD":
                if code.lower() == "aci":
                    if dynamic:
                        gravity = {
                                '11'   : {'Dead':1.4},
                                '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5},
                                '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5},
                                '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
                                '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
                                '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
                                '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
                        }
                        if dynamic == "100-30":
                            seismic = {
                                    '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SXE': 1, 'SY': 0.3, 'EV':1},
                                    '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'SYE': 1, 'SX': 0.3, 'EV':1},
                                    '71'   : {'Dead':0.9, 'SXE': 1, 'SY': 0.3, 'EV':-1},
                                    '72'   : {'Dead':0.9, 'SYE': 1, 'SX': 0.3, 'EV':-1},
                                    '81'   : {'EV' :-1},
                            }
                        elif dynamic == "angular":
                            seismic = {
                                    '5_1'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'AngularDynamic': 1, 'EV':1},
                                    '7_1'   : {'Dead':0.9, 'AngularDynamic': 1, 'EV':-1},
                                    '81'   : {'EV' :-1},
                            }
                        gravity.update(seismic)
                        return gravity
                    return {
                        '11'   : {'Dead':1.4},
                        '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5},
                        '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5},
                        '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
                        '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
                        '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
                        '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
                        '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP': 1, 'EXP1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':1},
                        '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN': 1, 'EXN1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':1},
                        '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP': 1, 'EXP1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':1},
                        '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN': 1, 'EXN1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':1},
                        '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP':-1, 'EXP1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':1},
                        '56'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN':-1, 'EXN1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':1},
                        '57'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXP':-1, 'EXP1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':1},
                        '58'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EXN':-1, 'EXN1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':1},
                        '59'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP': 1, 'EYP1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':1},
                        '510'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN': 1, 'EYN1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':1},
                        '511'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP': 1, 'EYP1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':1},
                        '512'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN': 1, 'EYN1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':1},
                        '513'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP':-1, 'EYP1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':1},
                        '514'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN':-1, 'EYN1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':1},
                        '515'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYP':-1, 'EYP1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':1},
                        '516'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EYN':-1, 'EYN1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':1},
                        '71'   : {'Dead':0.9, 'EXP': 1, 'EXP1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1},
                        '72'   : {'Dead':0.9, 'EXN': 1, 'EXN1': 1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1},
                        '73'   : {'Dead':0.9, 'EXP': 1, 'EXP1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1},
                        '74'   : {'Dead':0.9, 'EXN': 1, 'EXN1': 1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1},
                        '75'   : {'Dead':0.9, 'EXP':-1, 'EXP1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1},
                        '76'   : {'Dead':0.9, 'EXN':-1, 'EXN1':-1, 'EY': 0.3, 'EY1': 0.3, 'EV':-1},
                        '77'   : {'Dead':0.9, 'EXP':-1, 'EXP1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1},
                        '78'   : {'Dead':0.9, 'EXN':-1, 'EXN1':-1, 'EY':-0.3, 'EY1':-0.3, 'EV':-1},
                        '79'   : {'Dead':0.9, 'EYP': 1, 'EYP1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1},
                        '710'  : {'Dead':0.9, 'EYN': 1, 'EYN1': 1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1},
                        '711'  : {'Dead':0.9, 'EYP': 1, 'EYP1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1},
                        '712'  : {'Dead':0.9, 'EYN': 1, 'EYN1': 1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1},
                        '713'  : {'Dead':0.9, 'EYP':-1, 'EYP1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1},
                        '714'  : {'Dead':0.9, 'EYN':-1, 'EYN1':-1, 'EX': 0.3, 'EX1': 0.3, 'EV':-1},
                        '715'  : {'Dead':0.9, 'EYP':-1, 'EYP1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1},
                        '716'  : {'Dead':0.9, 'EYN':-1, 'EYN1':-1, 'EX':-0.3, 'EX1':-0.3, 'EV':-1},
                        '81'   : {'EV':-1},
                    }
                elif code.lower() == "csa":
                    if dynamic:
                        gravity = {
                                '11'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'RoofLive':1.5},
                                '12'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'Snow':1.5},
                                '41'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5},
                                '42'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5},
                                '51'   : {'Dead':0.85},
                        }
                        if dynamic == "100-30":
                            seismic = {
                                '21'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SXE': 0.84, 'SY': 0.252, 'EV':0.84},
                                '22'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'SYE': 0.84, 'SX': 0.252, 'EV':0.84},
                                '23'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SXE': 0.84, 'SY': 0.252, 'EV':0.84},
                                '24'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'SYE': 0.84, 'SX': 0.252, 'EV':0.84},
                                '31'   : {'Dead':0.85, 'SXE': 0.84, 'SY': 0.252, 'EV':-0.84},
                                '32'   : {'Dead':0.85, 'SYE': 0.84, 'SX': 0.252, 'EV':-0.84},
                                '81'   : {'EV':-0.84},
                            }
                        elif dynamic == "angular":
                            seismic = {
                                '2_1'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
                                '2_2'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'AngularDynamic': 0.84, 'EV':0.84},
                                '3_1'   : {'Dead':0.85, 'AngularDynamic': 0.84, 'EV':-0.84},
                                '81'   : {'EV':-0.84},
                            }
                        gravity.update(seismic)
                        return gravity
                    return {
                        '11'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'RoofLive':1.5},
                        '12'   : {'Dead':1.25 , 'L':1.5, 'L_5':1.6, 'Snow':1.5},
                        '21'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '22'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '23'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '24'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '25'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '26'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '27'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '28'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '29'   : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '210'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '211'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '212'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '213'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '214'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '215'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '216'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'RoofLive':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '217'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '218'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '219'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP': 0.84, 'EXP1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '220'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN': 0.84, 'EXN1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '221'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '222'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':0.84},
                        '223'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXP':-0.84, 'EXP1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '224'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EXN':-0.84, 'EXN1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':0.84},
                        '225'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '226'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '227'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP': 0.84, 'EYP1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '228'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN': 0.84, 'EYN1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '229'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '230'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':0.84},
                        '231'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYP':-0.84, 'EYP1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '232'  : {'Dead':1.0, 'L':1.2, 'L_5':0.6, 'Snow':1.2, 'EYN':-0.84, 'EYN1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':0.84},
                        '31'   : {'Dead':0.85, 'EXP': 0.84, 'EXP1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84},
                        '32'   : {'Dead':0.85, 'EXN': 0.84, 'EXN1': 0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84},
                        '33'   : {'Dead':0.85, 'EXP': 0.84, 'EXP1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84},
                        '34'   : {'Dead':0.85, 'EXN': 0.84, 'EXN1': 0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84},
                        '35'   : {'Dead':0.85, 'EXP':-0.84, 'EXP1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84},
                        '36'   : {'Dead':0.85, 'EXN':-0.84, 'EXN1':-0.84, 'EY': 0.252, 'EY1': 0.252, 'EV':-0.84},
                        '37'   : {'Dead':0.85, 'EXP':-0.84, 'EXP1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84},
                        '38'   : {'Dead':0.85, 'EXN':-0.84, 'EXN1':-0.84, 'EY':-0.252, 'EY1':-0.252, 'EV':-0.84},
                        '39'   : {'Dead':0.85, 'EYP': 0.84, 'EYP1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84},
                        '310'  : {'Dead':0.85, 'EYN': 0.84, 'EYN1': 0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84},
                        '311'  : {'Dead':0.85, 'EYP': 0.84, 'EYP1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84},
                        '312'  : {'Dead':0.85, 'EYN': 0.84, 'EYN1': 0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84},
                        '313'  : {'Dead':0.85, 'EYP':-0.84, 'EYP1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84},
                        '314'  : {'Dead':0.85, 'EYN':-0.84, 'EYN1':-0.84, 'EX': 0.252, 'EX1': 0.252, 'EV':-0.84},
                        '315'  : {'Dead':0.85, 'EYP':-0.84, 'EYP1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84},
                        '316'  : {'Dead':0.85, 'EYN':-0.84, 'EYN1':-0.84, 'EX':-0.252, 'EX1':-0.252, 'EV':-0.84},
                        '41'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'RoofLive':1.5},
                        '42'   : {'Dead':1.25, 'L':1.5, 'L_5':0.6, 'Snow':1.5},
                        '51'   : {'Dead':0.85},
                        '81'   : {'EV':-0.84},
                    }
            elif way == "ASD":
                if dynamic:
                    gravity = {
                    '11'   : {'Dead':1},
                    '21'   : {'Dead':1, 'L':1, 'L_5':1},
                    '31'   : {'Dead':1, 'Snow':1},
                    '32'   : {'Dead':1, 'RoofLive':1},
                    '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75},
                    '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75},
                    }
                    if dynamic == "100-30":
                        seismic = {
                                '71'   : {'Dead':1, 'SXE': 0.7, 'SY': 0.21, 'EV':0.7},
                                '72'   : {'Dead':1, 'SYE': 0.7, 'SX': 0.21, 'EV':0.7},
                                '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SXE': 0.525, 'SY': 0.1575, 'EV':0.525},
                                '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'SYE': 0.525, 'SX': 0.1575, 'EV':0.525},
                                '101'  : {'Dead':0.6, 'SXE': 0.7, 'SY': 0.21, 'EV':-0.7},
                                '102'  : {'Dead':0.6, 'SYE': 0.7, 'SX': 0.21, 'EV':-0.7},
                        }
                    elif dynamic == "angular":
                        seismic = {
                                '7_1'   : {'Dead':1, 'AngularDynamic': 0.7, 'EV':0.7},
                                '8_1'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'AngularDynamic': 0.525, 'EV':0.525},
                                '10_1'  : {'Dead':0.6, 'AngularDynamic': 0.7, 'EV':-0.7},
                        }
                    gravity.update(seismic)
                    return gravity
                return {
                    '11'   : {'Dead':1},
                    '21'   : {'Dead':1, 'L':1, 'L_5':1},
                    '31'   : {'Dead':1, 'Snow':1},
                    '32'   : {'Dead':1, 'RoofLive':1},
                    '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75},
                    '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75},
                    '71'   : {'Dead':1, 'EXP': 0.7, 'EXP1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7},
                    '72'   : {'Dead':1, 'EXN': 0.7, 'EXN1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7},
                    '73'   : {'Dead':1, 'EXP': 0.7, 'EXP1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7},
                    '74'   : {'Dead':1, 'EXN': 0.7, 'EXN1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7},
                    '75'   : {'Dead':1, 'EXP':-0.7, 'EXP1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7},
                    '76'   : {'Dead':1, 'EXN':-0.7, 'EXN1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7},
                    '77'   : {'Dead':1, 'EXP':-0.7, 'EXP1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7},
                    '78'   : {'Dead':1, 'EXN':-0.7, 'EXN1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7},
                    '79'   : {'Dead':1, 'EYP': 0.7, 'EYP1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7},
                    '710'  : {'Dead':1, 'EYN': 0.7, 'EYN1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7},
                    '711'  : {'Dead':1, 'EYP': 0.7, 'EYP1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7},
                    '712'  : {'Dead':1, 'EYN': 0.7, 'EYN1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7},
                    '713'  : {'Dead':1, 'EYP':-0.7, 'EYP1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7},
                    '714'  : {'Dead':1, 'EYN':-0.7, 'EYN1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7},
                    '715'  : {'Dead':1, 'EYP':-0.7, 'EYP1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7},
                    '716'  : {'Dead':1, 'EYN':-0.7, 'EYN1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7},
                    '717'  : {'Dead':1, 'EX': 0.7, 'EX1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7},
                    '718'  : {'Dead':1, 'EX':-0.7, 'EX1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':0.7},
                    '719'  : {'Dead':1, 'EX': 0.7, 'EX1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7},
                    '720'  : {'Dead':1, 'EX':-0.7, 'EX1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':0.7},
                    '721'  : {'Dead':1, 'EY': 0.7, 'EY1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7},
                    '722'  : {'Dead':1, 'EY':-0.7, 'EY1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':0.7},
                    '723'  : {'Dead':1, 'EY': 0.7, 'EY1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7},
                    '724'  : {'Dead':1, 'EY':-0.7, 'EY1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':0.7},
                    '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP': 0.525, 'EXP1': 0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525},
                    '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN': 0.525, 'EXN1': 0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525},
                    '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP': 0.525, 'EXP1': 0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525},
                    '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN': 0.525, 'EXN1': 0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525},
                    '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP':-0.525, 'EXP1':-0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525},
                    '86'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN':-0.525, 'EXN1':-0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525},
                    '87'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXP':-0.525, 'EXP1':-0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525},
                    '88'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EXN':-0.525, 'EXN1':-0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525},
                    '89'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP': 0.525, 'EYP1': 0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525},
                    '810'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN': 0.525, 'EYN1': 0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525},
                    '811'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP': 0.525, 'EYP1': 0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525},
                    '812'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN': 0.525, 'EYN1': 0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525},
                    '813'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP':-0.525, 'EYP1':-0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525},
                    '814'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN':-0.525, 'EYN1':-0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525},
                    '815'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYP':-0.525, 'EYP1':-0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525},
                    '816'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EYN':-0.525, 'EYN1':-0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525},
                    '817'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EX1' : 0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525},
                    '818'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EX1' : 0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525},
                    '819'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EX1' :-0.525, 'EY': 0.1575, 'EY1': 0.1575, 'EV':0.525},
                    '820'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EX1' :-0.525, 'EY':-0.1575, 'EY1':-0.1575, 'EV':0.525},
                    '821'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EY1' : 0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525},
                    '822'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EY1' : 0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525},
                    '823'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EY1' :-0.525, 'EX': 0.1575, 'EX1': 0.1575, 'EV':0.525},
                    '824'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EY1' :-0.525, 'EX':-0.1575, 'EX1':-0.1575, 'EV':0.525},
                    '101'  : {'Dead':0.6, 'EXP': 0.7, 'EXP1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7},
                    '102'  : {'Dead':0.6, 'EXN': 0.7, 'EXN1': 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7},
                    '103'  : {'Dead':0.6, 'EXP': 0.7, 'EXP1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7},
                    '104'  : {'Dead':0.6, 'EXN': 0.7, 'EXN1': 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7},
                    '105'  : {'Dead':0.6, 'EXP':-0.7, 'EXP1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7},
                    '106'  : {'Dead':0.6, 'EXN':-0.7, 'EXN1':-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7},
                    '107'  : {'Dead':0.6, 'EXP':-0.7, 'EXP1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7},
                    '108'  : {'Dead':0.6, 'EXN':-0.7, 'EXN1':-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7},
                    '109'  : {'Dead':0.6, 'EYP': 0.7, 'EYP1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7},
                    '1010' : {'Dead':0.6, 'EYN': 0.7, 'EYN1': 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7},
                    '1011' : {'Dead':0.6, 'EYP': 0.7, 'EYP1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7},
                    '1012' : {'Dead':0.6, 'EYN': 0.7, 'EYN1': 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7},
                    '1013' : {'Dead':0.6, 'EYP':-0.7, 'EYP1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7},
                    '1014' : {'Dead':0.6, 'EYN':-0.7, 'EYN1':-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7},
                    '1015' : {'Dead':0.6, 'EYP':-0.7, 'EYP1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7},
                    '1016' : {'Dead':0.6, 'EYN':-0.7, 'EYN1':-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7},
                    '1017' : {'Dead':0.6, 'EX' : 0.7, 'EX1' : 0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7},
                    '1018' : {'Dead':0.6, 'EX' : 0.7, 'EX1' : 0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7},
                    '1019' : {'Dead':0.6, 'EX' :-0.7, 'EX1' :-0.7, 'EY': 0.21, 'EY1': 0.21, 'EV':-0.7},
                    '1020' : {'Dead':0.6, 'EX' :-0.7, 'EX1' :-0.7, 'EY':-0.21, 'EY1':-0.21, 'EV':-0.7},
                    '1021' : {'Dead':0.6, 'EY' : 0.7, 'EY1' : 0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7},
                    '1022' : {'Dead':0.6, 'EY' : 0.7, 'EY1' : 0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7},
                    '1023' : {'Dead':0.6, 'EY' :-0.7, 'EY1' :-0.7, 'EX': 0.21, 'EX1': 0.21, 'EV':-0.7},
                    '1024' : {'Dead':0.6, 'EY' :-0.7, 'EY1' :-0.7, 'EX':-0.21, 'EX1':-0.21, 'EV':-0.7},
                }
            
@python_functions.print_arguments
def generate_concrete_load_combinations(
    equivalent_loads : dict,
    prefix : str = 'COMBO',
    suffix : str = '',
    rho_x : float = 1,
    rho_y : float = 1,
    type_ : str = 'Linear Add',
    design_type: str = 'LRFD',
    separate_direction: bool = False,
    ev_negative: bool = True,
    A: float = 0.3,
    I: float = 1,
    sequence_numbering: bool = False,
    add_notional_loads: bool = False,
    retaining_wall: bool = False,
    omega_x: float=0,
    omega_y: float=0,
    rho_x1 : float = 1,
    rho_y1 : float = 1,
    omega_x1: float=0,
    omega_y1: float=0,
    code: str="ACI",
    dynamic: str="", # '100-30' , 'angular'
    mabhas6_load_combinations: dict = {},
    ):
    data = []
    i = 0
    notional_loads = []
    if add_notional_loads:
        for key in ['Dead', 'L', 'L_5', 'RoofLive', 'Snow']:
            values = equivalent_loads.get(key, None)
            if values is not None:
                notional_loads.extend(values)
    if len(mabhas6_load_combinations) == 0:
        mabhas6_load_combinations = get_mabhas6_load_combinations(design_type, separate_direction, retaining_wall, code, dynamic)
    for number, combos in mabhas6_load_combinations.items():
        if add_notional_loads:
            is_gravity = True
            for lateral_load in ('EX', 'EXP', 'EXN', 'EY', 'EYP', 'EYN', 'EX1', 'EXP1', 'EXN1', 'EY1', 'EYP1', 'EYN1', 'EV',
                                    'SXE', 'SYE', 'SX', 'SY', 'AngularDynamic'):
                if lateral_load in combos.keys():
                    is_gravity = False
                    break
        if sequence_numbering:
            i += 1
            number = i
        combo_names = [f'{prefix}{number}{suffix}']
        if add_notional_loads and is_gravity:
            directions = ('X', 'Y', 'X', 'Y')
            sf_multiply = (1, 1, -1, -1)
            for j in range(1,4):
                if sequence_numbering:
                    i += 1
                    number = i
                    combo_names.append(f'{prefix}{number}{suffix}')
                else:
                    combo_names.append(f'{prefix}{number}{j}{suffix}')
        elif "AngularDynamic" in combos.keys():
            if not sequence_numbering:
                u, v = number.split("_")
                v = int(v)
            equal_names = equivalent_loads.get("AngularDynamic", [])
            len_equalname = len(equal_names)
            directions = ('',) * len_equalname
            sf_multiply = ('',) * len_equalname
            combo_names = []
            for j in range(len_equalname):
                if sequence_numbering:
                    i += 1
                    number = i
                    combo_names.append(f'{prefix}{number}{suffix}')
                else:
                    combo_names.append(f'{prefix}{u}{(j + 1) + (v - 1) * len_equalname}{suffix}')
        else:
            directions = ('',)
            sf_multiply = ('',)
        if A == 0.35:
            ev_sf = combos.get('EV', None)
            if ev_sf:
                dead_load_scale_factor = combos.get('Dead', None)
                if dead_load_scale_factor:
                    plus_dead_sf = 0.6 * A * I * ev_sf
                    if ev_negative or ev_sf > 0:
                        combos['Dead'] = dead_load_scale_factor + plus_dead_sf
        for lname, sf in combos.items():
            equal_names = equivalent_loads.get(lname, [])
            if lname in ('EX', 'EXP', 'EXN', 'SXE', 'SX'):
                sf *= max(rho_x, omega_x)
            elif lname in ('EY', 'EYP', 'EYN', 'SYE', 'SY'):
                sf *= max(rho_y, omega_y)
            elif lname in ('EX1', 'EXP1', 'EXN1'):
                sf *= max(rho_x1, omega_x1)
            elif lname in ('EY1', 'EYP1', 'EYN1'):
                sf *= max(rho_y1, omega_y1)
            elif lname == 'EV' and not ev_negative and sf < 0:
                continue
            if lname == "AngularDynamic":
                sf *= max(rho_x, rho_y, omega_x, omega_y)
                for k, name in enumerate(equal_names):
                    data.extend([combo_names[k], type_, name, sf])
            else:
                for name in equal_names:
                    for k, (dir_, sfm) in enumerate(zip(directions, sf_multiply)):
                        data.extend([combo_names[k], type_, name, sf])
                        if add_notional_loads and is_gravity:
                            data.extend([combo_names[k], type_, f'N{name}{dir_}', sfm * sf])

    data = python_functions.get_unique_load_combinations(data, sequence_numbering, prefix, suffix)
    return data, notional_loads