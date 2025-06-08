__all__ = ['View']


class View:
    def __init__(
                self,
                etabs,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def show_point(
            self,
            story : str,
            label : str,
            ):
        self.SapModel.SelectObj.ClearSelection()
        name = self.SapModel.PointObj.GetNameFromLabel(label, story)[0]
        self.SapModel.PointObj.SetSelected(name, True)
        self.SapModel.View.RefreshView()
        return True
    
    def show_frame(
            self,
            name : str,
            ):
        self.SapModel.SelectObj.ClearSelection()
        self.SapModel.FrameObj.SetSelected(name, True)
        self.SapModel.View.RefreshView()
        return True
    
    def show_frame_with_lable_and_story(
            self,
            label : str,
            story : str,
            ):
        name = self.SapModel.FrameObj.GetNameFromLabel(label, story)[0]
        self.SapModel.SelectObj.ClearSelection()
        self.SapModel.FrameObj.SetSelected(name, True)
        self.SapModel.View.RefreshView()
        return True
    
    def show_frames(
            self,
            names : str,
            ):
        self.SapModel.SelectObj.ClearSelection()
        for name in names:
            self.SapModel.FrameObj.SetSelected(name, True)
        self.SapModel.View.RefreshView()
        return True
    
    def show_areas(
            self,
            names : str,
            ):
        self.SapModel.SelectObj.ClearSelection()
        for name in names:
            self.SapModel.AreaObj.SetSelected(name, True)
        self.SapModel.View.RefreshView()
        return True
    
    def show_areas_and_frames_with_pier_and_story(
            self,
            pier : str,
            story: str
            ):
        self.SapModel.SelectObj.ClearSelection()
        names = self.etabs.pier.get_area_names_with_pier_label(piers=pier)
        frame_names = names.get(pier, {}).get(story, [])
        names = self.etabs.pier.get_columns_names_with_pier_label(piers=pier)
        area_names = names.get(pier, {}).get(story, [])
        for name in frame_names:
            self.SapModel.AreaObj.SetSelected(name, True)
        for name in area_names:
            self.SapModel.FrameObj.SetSelected(name, True)
        self.SapModel.View.RefreshView()
        return True
    
    def refresh_view(self):
        self.SapModel.View.RefreshView()