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

    def set_concrete_framing_type(self,
        type_: str = 2,
        beams: bool = True,
        columns: bool = True,
        ):
        '''
        type_:
            0 = Program Default
            1 = Sway special
            2 = Sway Intermediate
            3 = Sway Ordinary
            4 = Non-sway
        '''
        beam_names, column_names = self.etabs.frame_obj.get_beams_columns(type_=2)
        if columns:
            for name in column_names:
                self.set_overwrite(
                    name = name,
                    item = 1, # Framing Type
                    value = type_, # Sway special
                    )
        if beams:
            for name in beam_names:
                self.set_overwrite(
                    name = name,
                    item = 1, # Framing Type
                    value = type_, # Sway special
                    )


        
        







if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    etabs.design.get_code()
    print('Wow')
