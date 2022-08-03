__all__ = ['SelectObj']


from typing import Union


class SelectObj:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def get_selected_obj_type(self,
            n : int,
            ) :
        '''
        n: 
            1 = points
            2 = frames
            5 = area
        '''
        try:
            selected = self.etabs.SapModel.SelectObj.GetSelected()
        except IndexError:
            return []
        types = selected[1]
        all_names = selected[2]
        names = []
        for type_, name in zip(types, all_names):
            if type_ == n:
                names.append(name)
        return names