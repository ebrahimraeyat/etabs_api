from typing import Union


__all__ = ['Func']


class Func:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def names(self):
        return self.SapModel.Func.GetNameList()[1]
    
    def response_spectrum_names(self):
        return [name for name in self.names() if self.SapModel.Func.GetTypeOAPI(name)[0] == 1]
    
    def time_history_names(self):
        return [name for name in self.names() if self.SapModel.Func.GetTypeOAPI(name)[0] == 2]
