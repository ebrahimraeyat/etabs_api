from typing import Iterable, Tuple, Union


class LoadCombination:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def get_mabhas6_load_combinations(self):
        return {
            11   : {'Dead':1.4},
            21   : {'Dead':1.2 , 'L':1.6, 'RoofLive':0.5},
            22   : {'Dead':1.2 , 'L':1.6, 'Snow':0.5},
            31   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':1.6},
            32   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':1.6},
            41   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'RoofLive':0.5},
            42   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.5},
            51   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX': 1, 'EY': 0.3, 'EV':1},
            52   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX': 1, 'EY': 0.3, 'EV':1},
            53   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX': 1, 'EY':-0.3, 'EV':1},
            54   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX': 1, 'EY':-0.3, 'EV':1},
            55   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX':-1, 'EY': 0.3, 'EV':1},
            56   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX':-1, 'EY': 0.3, 'EV':1},
            57   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPX':-1, 'EY':-0.3, 'EV':1},
            58   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENX':-1, 'EY':-0.3, 'EV':1},
            59   : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY': 1, 'EX': 0.3, 'EV':1},
            510  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY': 1, 'EX': 0.3, 'EV':1},
            511  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY': 1, 'EX':-0.3, 'EV':1},
            512  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY': 1, 'EX':-0.3, 'EV':1},
            513  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY':-1, 'EX': 0.3, 'EV':1},
            514  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY':-1, 'EX': 0.3, 'EV':1},
            515  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'EPY':-1, 'EX':-0.3, 'EV':1},
            516  : {'Dead':1.2, 'L':1, 'L_5':0.5, 'Snow':0.2, 'ENY':-1, 'EX':-0.3, 'EV':1},
            71   : {'Dead':0.9, 'EPX': 1, 'EY': 0.3, 'EV':1},
            72   : {'Dead':0.9, 'ENX': 1, 'EY': 0.3, 'EV':1},
            73   : {'Dead':0.9, 'EPX': 1, 'EY':-0.3, 'EV':1},
            74   : {'Dead':0.9, 'ENX': 1, 'EY':-0.3, 'EV':1},
            75   : {'Dead':0.9, 'EPX':-1, 'EY': 0.3, 'EV':1},
            76   : {'Dead':0.9, 'ENX':-1, 'EY': 0.3, 'EV':1},
            77   : {'Dead':0.9, 'EPX':-1, 'EY':-0.3, 'EV':1},
            78   : {'Dead':0.9, 'ENX':-1, 'EY':-0.3, 'EV':1},
            79   : {'Dead':0.9, 'ENY': 1, 'EX': 0.3, 'EV':1},
            710  : {'Dead':0.9, 'EPY': 1, 'EX': 0.3, 'EV':1},
            711  : {'Dead':0.9, 'EPY': 1, 'EX':-0.3, 'EV':1},
            712  : {'Dead':0.9, 'ENY': 1, 'EX':-0.3, 'EV':1},
            713  : {'Dead':0.9, 'EPY':-1, 'EX': 0.3, 'EV':1},
            714  : {'Dead':0.9, 'ENY':-1, 'EX': 0.3, 'EV':1},
            715  : {'Dead':0.9, 'EPY':-1, 'EX':-0.3, 'EV':1},
            716  : {'Dead':0.9, 'ENY':-1, 'EX':-0.3, 'EV':1},
        }


    def generate_concrete_load_combinations(self,
        # load_patterns : {Uist,':nio bool] = None,
        equivalent_loads : dict,
        prefix : str = 'COMBO',
        suffix : str = '',
        ):
        data = []
        # df = pd.DataFrame(columns=['Name', 'LoadName', 'SF'])      
        i = 0
        for number, combos in self.get_mabhas6_load_combinations().items():
            i += 1
            for lname, sf in combos.items():
                equal_names = equivalent_loads.get(lname, [])
                for name in equal_names:
                    combo_name = f'{prefix}{i}{suffix}'
                    data.extend([combo_name, 'Linear Add', name, sf])
        return data
        







    
    
        
        
        

    