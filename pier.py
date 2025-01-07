from pathlib import Path
from typing import Iterable, Union
import math
import copy

from python_functions import change_unit

try:
    import freecad_funcs
except NameError:
    pass


class Pier:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = self.etabs.SapModel

    def add_piers(self,
                  names: Union[list, None]=None,
                  n: int=11,
                  ):
        if names is None:
            names = ['P' + str(i) for i in range(1, n)]
        for name in names:
            self.SapModel.PierLabel.SetPier(name)
        return names
    
    def get_names(self):
        return self.SapModel.PierLabel.GetNameList()[1]




if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel()
    SapModel = etabs.SapModel.PierLabel.SetPier()
    # filename = Path(r'F:\alaki\zibaee\steel\100_30.EDB')
    df = etabs.frame_obj.require_100_30(type_='Steel')
    print(df)
    print('Wow')




    
        