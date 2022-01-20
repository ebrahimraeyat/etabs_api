from pathlib import Path
import sys
from typing import Iterable, Union

import pandas as pd
pd.options.mode.chained_assignment = None


__all__ = ['Design']

class Design:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def get_code(self,
            type_ : str = 'Concrete',  # 'Steel'
            ):
            if type_ == 'Concrete':
                return self.SapModel.DesignConcrete.getCode()[0]
            elif type_ == 'Steel':
                return self.SapModel.DesignSteel.getCode()[0]

    def get_code_string(self,
        type_: str = 'Concrete', # 'Steel'
        code : Union[str, None] = None,
        ):
        ''' 
        get code of design in format 'ACI 318-14' and return 'ACI318_14'
        '''
        if code is None:
            code = self.get_code(type_=type_)
        code = code.replace(" ", "")
        i = code.find('-')
        # code = code.replace("-", "ـ")
        code = code[:i] + '_' + code[i + 1:]
        return code

    def set_overwrite(self,
        name: str,
        item: int,
        value: float,
        type_: str = 'Concrete', # 'Steel'
        code: Union[str, bool] = None,
        ):
        if code is None:
            code = self.get_code_string(type_)
        exec(f"self.SapModel.Design{type_}.{code}.SetOverwrite('{name}',{item}, {value})")



        
        







if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    etabs.design.get_code()
    print('Wow')
