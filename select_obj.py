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
            ) -> list:
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
    
    def get_selected_objects(self):
        '''
            1 = points
            2 = frames
            5 = area
        '''
        try:
            selected = self.etabs.SapModel.SelectObj.GetSelected()
        except IndexError:
            return {}
        types = selected[1]
        all_names = selected[2]
        selected_objects = {}
        for t, name in zip(types, all_names):
            objects = selected_objects.get(t, None)
            if objects is None:
                selected_objects[t] = []
            selected_objects[t].append(name)
        return selected_objects
    
    def select_concrete_columns(self):
        _, columns = self.etabs.frame_obj.get_beams_columns(type_=2)
        for name in columns:
            self.SapModel.FrameObj.SetSelected(name, True)

    