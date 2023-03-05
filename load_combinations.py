
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
            
        for number, combos in get_mabhas6_load_combinations(design_type, separate_direction).items():
            if add_notional_loads:
                is_gravity = True
                for lateral_load in ('EX', 'EPX', 'ENX', 'EY', 'EPY', 'ENY'):
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
                if lname in ('EX', 'EPX', 'ENX'):
                    sf *= rho_x
                elif lname in ('EY', 'EPY', 'ENY'):
                    sf *= rho_y
                elif lname == 'EV' and not ev_negative and sf < 0:
                    continue
                equal_names = equivalent_loads.get(lname, [])
                for name in equal_names:
                    for k, (dir_, sfm) in enumerate(zip(directions, sf_multiply)):
                        data.extend([combo_names[k], type_, name, sf])
                        if add_notional_loads and is_gravity:
                            data.extend([combo_names[k], type_, f'N{name}{dir_}', sfm * sf])
                            
        return data
            
def get_mabhas6_load_combinations(
    way='LRFD', # 'ASD'
    separate_direction: bool = False,
    ):
    '''
    separate_direction: For 100-30 earthquake
    '''
    if separate_direction:
        if way == "LRFD":
            return {
                '11'   : {'Dead':1.4},
                '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5},
                '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5},
                '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
                '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
                '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
                '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
                '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX': 1, 'EV':1},
                '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX': 1, 'EV':1},
                '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX':-1, 'EV':1},
                '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX':-1, 'EV':1},
                '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY': 1, 'EV':1},
                '56'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY': 1, 'EV':1},
                '57'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY':-1, 'EV':1},
                '58'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY':-1, 'EV':1},
                '71'   : {'Dead':0.9, 'EPX': 1, 'EV':-1},
                '72'   : {'Dead':0.9, 'ENX': 1, 'EV':-1},
                '73'   : {'Dead':0.9, 'EPX':-1, 'EV':-1},
                '74'   : {'Dead':0.9, 'ENX':-1, 'EV':-1},
                '75'  : {'Dead':0.9, 'EPY': 1, 'EV':-1},
                '76'   : {'Dead':0.9, 'ENY': 1, 'EV':-1},
                '77'  : {'Dead':0.9, 'EPY':-1, 'EV':-1},
                '78'  : {'Dead':0.9, 'ENY':-1, 'EV':-1},
            }
        elif way == "ASD":
            return {
                '11'   : {'Dead':1},
                '21'   : {'Dead':1, 'L':1, 'L_5':1},
                '31'   : {'Dead':1, 'Snow':1},
                '32'   : {'Dead':1, 'RoofLive':1},
                '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75},
                '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75},
                '71'   : {'Dead':1, 'EPX': 0.7, 'EV':0.7},
                '72'   : {'Dead':1, 'ENX': 0.7, 'EV':0.7},
                '73'   : {'Dead':1, 'EPX':-0.7, 'EV':0.7},
                '74'   : {'Dead':1, 'ENX':-0.7, 'EV':0.7},
                '75'   : {'Dead':1, 'ENY': 0.7, 'EV':0.7},
                '76'  : {'Dead':1, 'EPY': 0.7, 'EV':0.7},
                '77'  : {'Dead':1, 'EPY':-0.7, 'EV':0.7},
                '78'  : {'Dead':1, 'ENY':-0.7, 'EV':0.7},
                '79'  : {'Dead':1, 'EX': 0.7, 'EV':0.7},
                '710'  : {'Dead':1, 'EX':-0.7, 'EV':0.7},
                '711'  : {'Dead':1, 'EY': 0.7, 'EV':0.7},
                '712'  : {'Dead':1, 'EY':-0.7, 'EV':0.7},
                '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPX': 0.525, 'EV':0.525},
                '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENX': 0.525, 'EV':0.525},
                '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPX':-0.525, 'EV':0.525},
                '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENX':-0.525, 'EV':0.525},
                '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENY': 0.525, 'EV':0.525},
                '86'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPY': 0.525, 'EV':0.525},
                '87'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPY':-0.525, 'EV':0.525},
                '88'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENY':-0.525, 'EV':0.525},
                '89'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EV':0.525},
                '810'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EV':0.525},
                '811'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EV':0.525},
                '812'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EV':0.525},
                '101'  : {'Dead':0.6, 'EPX': 0.7, 'EV':-0.7},
                '102'  : {'Dead':0.6, 'ENX': 0.7, 'EV':-0.7},
                '103'  : {'Dead':0.6, 'EPX':-0.7, 'EV':-0.7},
                '104'  : {'Dead':0.6, 'ENX':-0.7, 'EV':-0.7},
                '105'  : {'Dead':0.6, 'ENY': 0.7, 'EV':-0.7},
                '106' : {'Dead':0.6, 'EPY': 0.7, 'EV':-0.7},
                '107' : {'Dead':0.6, 'EPY':-0.7, 'EV':-0.7},
                '108' : {'Dead':0.6, 'ENY':-0.7, 'EV':-0.7},
                '109' : {'Dead':0.6, 'EX' : 0.7, 'EV':-0.7},
                '1010' : {'Dead':0.6, 'EX' :-0.7, 'EV':-0.7},
                '1011' : {'Dead':0.6, 'EY' : 0.7, 'EV':-0.7},
                '1012' : {'Dead':0.6, 'EY' :-0.7, 'EV':-0.7},
            }
    else:
        if way == "LRFD":
            return {
                '11'   : {'Dead':1.4},
                '21'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'RoofLive':0.5},
                '22'   : {'Dead':1.2 , 'L':1.6, 'L_5':1.6, 'Snow':0.5},
                '31'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
                '32'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
                '41'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
                '42'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
                '51'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX': 1, 'EY': 0.3, 'EV':1},
                '52'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX': 1, 'EY': 0.3, 'EV':1},
                '53'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX': 1, 'EY':-0.3, 'EV':1},
                '54'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX': 1, 'EY':-0.3, 'EV':1},
                '55'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX':-1, 'EY': 0.3, 'EV':1},
                '56'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX':-1, 'EY': 0.3, 'EV':1},
                '57'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX':-1, 'EY':-0.3, 'EV':1},
                '58'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX':-1, 'EY':-0.3, 'EV':1},
                '59'   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY': 1, 'EX': 0.3, 'EV':1},
                '510'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY': 1, 'EX': 0.3, 'EV':1},
                '511'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY': 1, 'EX':-0.3, 'EV':1},
                '512'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY': 1, 'EX':-0.3, 'EV':1},
                '513'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY':-1, 'EX': 0.3, 'EV':1},
                '514'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY':-1, 'EX': 0.3, 'EV':1},
                '515'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY':-1, 'EX':-0.3, 'EV':1},
                '516'  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY':-1, 'EX':-0.3, 'EV':1},
                '71'   : {'Dead':0.9, 'EPX': 1, 'EY': 0.3, 'EV':-1},
                '72'   : {'Dead':0.9, 'ENX': 1, 'EY': 0.3, 'EV':-1},
                '73'   : {'Dead':0.9, 'EPX': 1, 'EY':-0.3, 'EV':-1},
                '74'   : {'Dead':0.9, 'ENX': 1, 'EY':-0.3, 'EV':-1},
                '75'   : {'Dead':0.9, 'EPX':-1, 'EY': 0.3, 'EV':-1},
                '76'   : {'Dead':0.9, 'ENX':-1, 'EY': 0.3, 'EV':-1},
                '77'   : {'Dead':0.9, 'EPX':-1, 'EY':-0.3, 'EV':-1},
                '78'   : {'Dead':0.9, 'ENX':-1, 'EY':-0.3, 'EV':-1},
                '79'   : {'Dead':0.9, 'ENY': 1, 'EX': 0.3, 'EV':-1},
                '710'  : {'Dead':0.9, 'EPY': 1, 'EX': 0.3, 'EV':-1},
                '711'  : {'Dead':0.9, 'EPY': 1, 'EX':-0.3, 'EV':-1},
                '712'  : {'Dead':0.9, 'ENY': 1, 'EX':-0.3, 'EV':-1},
                '713'  : {'Dead':0.9, 'EPY':-1, 'EX': 0.3, 'EV':-1},
                '714'  : {'Dead':0.9, 'ENY':-1, 'EX': 0.3, 'EV':-1},
                '715'  : {'Dead':0.9, 'EPY':-1, 'EX':-0.3, 'EV':-1},
                '716'  : {'Dead':0.9, 'ENY':-1, 'EX':-0.3, 'EV':-1},
            }
        elif way == "ASD":
            return {
                '11'   : {'Dead':1},
                '21'   : {'Dead':1, 'L':1, 'L_5':1},
                '31'   : {'Dead':1, 'Snow':1},
                '32'   : {'Dead':1, 'RoofLive':1},
                '41'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75},
                '42'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'RoofLive':0.75},
                '71'   : {'Dead':1, 'EPX': 0.7, 'EY': 0.21, 'EV':0.7},
                '72'   : {'Dead':1, 'ENX': 0.7, 'EY': 0.21, 'EV':0.7},
                '73'   : {'Dead':1, 'EPX': 0.7, 'EY':-0.21, 'EV':0.7},
                '74'   : {'Dead':1, 'ENX': 0.7, 'EY':-0.21, 'EV':0.7},
                '75'   : {'Dead':1, 'EPX':-0.7, 'EY': 0.21, 'EV':0.7},
                '76'   : {'Dead':1, 'ENX':-0.7, 'EY': 0.21, 'EV':0.7},
                '77'   : {'Dead':1, 'EPX':-0.7, 'EY':-0.21, 'EV':0.7},
                '78'   : {'Dead':1, 'ENX':-0.7, 'EY':-0.21, 'EV':0.7},
                '79'   : {'Dead':1, 'ENY': 0.7, 'EX': 0.21, 'EV':0.7},
                '710'  : {'Dead':1, 'EPY': 0.7, 'EX': 0.21, 'EV':0.7},
                '711'  : {'Dead':1, 'EPY': 0.7, 'EX':-0.21, 'EV':0.7},
                '712'  : {'Dead':1, 'ENY': 0.7, 'EX':-0.21, 'EV':0.7},
                '713'  : {'Dead':1, 'EPY':-0.7, 'EX': 0.21, 'EV':0.7},
                '714'  : {'Dead':1, 'ENY':-0.7, 'EX': 0.21, 'EV':0.7},
                '715'  : {'Dead':1, 'EPY':-0.7, 'EX':-0.21, 'EV':0.7},
                '716'  : {'Dead':1, 'ENY':-0.7, 'EX':-0.21, 'EV':0.7},
                '717'  : {'Dead':1, 'EX': 0.7, 'EY': 0.21, 'EV':0.7},
                '718'  : {'Dead':1, 'EX':-0.7, 'EY': 0.21, 'EV':0.7},
                '719'  : {'Dead':1, 'EX': 0.7, 'EY':-0.21, 'EV':0.7},
                '720'  : {'Dead':1, 'EX':-0.7, 'EY':-0.21, 'EV':0.7},
                '721'  : {'Dead':1, 'EY': 0.7, 'EX': 0.21, 'EV':0.7},
                '722'  : {'Dead':1, 'EY':-0.7, 'EX': 0.21, 'EV':0.7},
                '723'  : {'Dead':1, 'EY': 0.7, 'EX':-0.21, 'EV':0.7},
                '724'  : {'Dead':1, 'EY':-0.7, 'EX':-0.21, 'EV':0.7},
                '81'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPX': 0.525, 'EY': 0.1575, 'EV':0.525},
                '82'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENX': 0.525, 'EY': 0.1575, 'EV':0.525},
                '83'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPX': 0.525, 'EY':-0.1575, 'EV':0.525},
                '84'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENX': 0.525, 'EY':-0.1575, 'EV':0.525},
                '85'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPX':-0.525, 'EY': 0.1575, 'EV':0.525},
                '86'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENX':-0.525, 'EY': 0.1575, 'EV':0.525},
                '87'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPX':-0.525, 'EY':-0.1575, 'EV':0.525},
                '88'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENX':-0.525, 'EY':-0.1575, 'EV':0.525},
                '89'   : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENY': 0.525, 'EX': 0.1575, 'EV':0.525},
                '810'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPY': 0.525, 'EX': 0.1575, 'EV':0.525},
                '811'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPY': 0.525, 'EX':-0.1575, 'EV':0.525},
                '812'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENY': 0.525, 'EX':-0.1575, 'EV':0.525},
                '813'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPY':-0.525, 'EX': 0.1575, 'EV':0.525},
                '814'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENY':-0.525, 'EX': 0.1575, 'EV':0.525},
                '815'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EPY':-0.525, 'EX':-0.1575, 'EV':0.525},
                '816'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'ENY':-0.525, 'EX':-0.1575, 'EV':0.525},
                '817'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EY': 0.1575, 'EV':0.525},
                '818'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' : 0.525, 'EY':-0.1575, 'EV':0.525},
                '819'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EY': 0.1575, 'EV':0.525},
                '820'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EX' :-0.525, 'EY':-0.1575, 'EV':0.525},
                '821'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EX': 0.1575, 'EV':0.525},
                '822'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' : 0.525, 'EX':-0.1575, 'EV':0.525},
                '823'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EX': 0.1575, 'EV':0.525},
                '824'  : {'Dead':1, 'L':0.75, 'L_5':0.75, 'Snow':0.75, 'EY' :-0.525, 'EX':-0.1575, 'EV':0.525},
                '101'  : {'Dead':0.6, 'EPX': 0.7, 'EY': 0.21, 'EV':-0.7},
                '102'  : {'Dead':0.6, 'ENX': 0.7, 'EY': 0.21, 'EV':-0.7},
                '103'  : {'Dead':0.6, 'EPX': 0.7, 'EY':-0.21, 'EV':-0.7},
                '104'  : {'Dead':0.6, 'ENX': 0.7, 'EY':-0.21, 'EV':-0.7},
                '105'  : {'Dead':0.6, 'EPX':-0.7, 'EY': 0.21, 'EV':-0.7},
                '106'  : {'Dead':0.6, 'ENX':-0.7, 'EY': 0.21, 'EV':-0.7},
                '107'  : {'Dead':0.6, 'EPX':-0.7, 'EY':-0.21, 'EV':-0.7},
                '108'  : {'Dead':0.6, 'ENX':-0.7, 'EY':-0.21, 'EV':-0.7},
                '109'  : {'Dead':0.6, 'ENY': 0.7, 'EX': 0.21, 'EV':-0.7},
                '1010' : {'Dead':0.6, 'EPY': 0.7, 'EX': 0.21, 'EV':-0.7},
                '1011' : {'Dead':0.6, 'EPY': 0.7, 'EX':-0.21, 'EV':-0.7},
                '1012' : {'Dead':0.6, 'ENY': 0.7, 'EX':-0.21, 'EV':-0.7},
                '1013' : {'Dead':0.6, 'EPY':-0.7, 'EX': 0.21, 'EV':-0.7},
                '1014' : {'Dead':0.6, 'ENY':-0.7, 'EX': 0.21, 'EV':-0.7},
                '1015' : {'Dead':0.6, 'EPY':-0.7, 'EX':-0.21, 'EV':-0.7},
                '1016' : {'Dead':0.6, 'ENY':-0.7, 'EX':-0.21, 'EV':-0.7},
                '1017' : {'Dead':0.6, 'EX' : 0.7, 'EY': 0.21, 'EV':-0.7},
                '1018' : {'Dead':0.6, 'EX' : 0.7, 'EY':-0.21, 'EV':-0.7},
                '1019' : {'Dead':0.6, 'EX' :-0.7, 'EY': 0.21, 'EV':-0.7},
                '1020' : {'Dead':0.6, 'EX' :-0.7, 'EY':-0.21, 'EV':-0.7},
                '1021' : {'Dead':0.6, 'EY' : 0.7, 'EX': 0.21, 'EV':-0.7},
                '1022' : {'Dead':0.6, 'EY' : 0.7, 'EX':-0.21, 'EV':-0.7},
                '1023' : {'Dead':0.6, 'EY' :-0.7, 'EX': 0.21, 'EV':-0.7},
                '1024' : {'Dead':0.6, 'EY' :-0.7, 'EX':-0.21, 'EV':-0.7},
            }








    
    
        
        
        

    