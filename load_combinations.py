
from typing import Union


class LoadCombination:
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
        return self.SapModel.RespCombo.GetNameList()[1]

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

    def get_type_of_combo(self,
        name : str,
        ):
        map_dict = {
        0 : 'Linear',
        1 : 'Envelope',
        2 : 'Absolute',
        3 : 'SRSS',
        4 : 'Range',
        }
        type_ = self.etabs.SapModel.RespCombo.GetTypeCombo(name)[0]
        return map_dict[type_]
        
    def get_expand_linear_load_combinations(self,
        expanded_loads : dict,
        ):
        combo_names = self.etabs.SapModel.RespCombo.GetNameList()[1]
        seismic_load_cases = self.etabs.load_cases.get_seismic_load_cases()
        new_combos = []
        EX, EXN, EXP, EY, EYN, EYP = self.etabs.load_patterns.get_seismic_load_patterns()
        for combo in combo_names:
            type_ = self.get_type_of_combo(combo)
            if type_ == 'Linear':
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
        # load_patterns : {Uist,':nio bool] = None,
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
        add_notional_loads: bool = True,
        retaining_wall: bool = False,
        omega_x: float=0,
        omega_y: float=0,
        rho_x1 : float = 1,
        rho_y1 : float = 1,
        omega_x1: float=0,
        omega_y1: float=0,
        code: str="ACI",
        ):
        data = []
        i = 0
        if add_notional_loads:
            gravity_loads = []
            for key in ['Dead', 'L', 'L_5', 'RoofLive', 'Snow']:
                values = equivalent_loads.get(key, None)
                if values is not None:
                    gravity_loads.extend(values)
            self.etabs.load_patterns.add_notional_loads(gravity_loads)
            
        for number, combos in get_mabhas6_load_combinations(design_type, separate_direction, retaining_wall, code).items():
            if add_notional_loads:
                is_gravity = True
                for lateral_load in ('EX', 'EXP', 'EXN', 'EY', 'EYP', 'EYN', 'EX1', 'EXP1', 'EXN1', 'EY1', 'EYP1', 'EYN1'):
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
                        # number = f'{number}{j}'
                        combo_names.append(f'{prefix}{number}{j}{suffix}')
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
                if lname in ('EX', 'EXP', 'EXN'):
                    sf *= max(rho_x, omega_x)
                elif lname in ('EY', 'EYP', 'EYN'):
                    sf *= max(rho_y, omega_y)
                elif lname in ('EX1', 'EXP1', 'EXN1'):
                    sf *= max(rho_x1, omega_x1)
                elif lname in ('EY1', 'EYP1', 'EYN1'):
                    sf *= max(rho_y1, omega_y1)
                elif lname == 'EV' and not ev_negative and sf < 0:
                    continue
                equal_names = equivalent_loads.get(lname, [])
                for name in equal_names:
                    for k, (dir_, sfm) in enumerate(zip(directions, sf_multiply)):
                        data.extend([combo_names[k], type_, name, sf])
                        if add_notional_loads and is_gravity:
                            data.extend([combo_names[k], type_, f'N{name}{dir_}', sfm * sf])
                            
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
        import pandas as pd
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
    ):
    '''
    separate_direction: For 100-30 earthquake
    '''
    if separate_direction:
        if retaining_wall:
            if way == "LRFD":
                if code.lower() == "aci":
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
                    return {
                        '11'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
                        '12'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5, 'HXP': 1.6, 'HXN': 1.6, 'HYP': 1.6, 'HYN': 1.6},
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
