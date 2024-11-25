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

    def get_selected_floors(self):
        all_selected_areas = self.get_selected_obj_type(n=5)
        all_floors = self.etabs.area.get_names_of_areas_of_type(type_='floor')
        selected_floors = set(all_selected_areas).intersection(all_floors)
        return selected_floors
    
    def get_selected_beams_and_columns(self, type_:int=2):
        "type_: 1=steel and 2=concrete"
        all_selected_frames = self.get_selected_obj_type(n=2)
        beams, columns = self.etabs.frame_obj.get_beams_columns(type_=type_)
        selected_beams = set(all_selected_frames).intersection(beams)
        selected_columns = set(all_selected_frames).intersection(columns)
        return selected_beams, selected_columns


    