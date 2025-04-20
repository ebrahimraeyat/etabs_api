from pathlib import Path
from typing import Iterable, Union

__all__ = ['ShearWall']


class ShearWall:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = self.etabs.SapModel

    def set_modifiers(self,
                      modifiers: list = 6 * [.01],
                      names: Union[list, None]=None,
    ):
        print(f"Set Wall Modifiers: {modifiers}")
        self.etabs.unlock_model()
        if names is None:
            names = self.SapModel.AreaObj.GetLabelNameList()[1]
        for label in names:
            if self.SapModel.AreaObj.GetDesignOrientation(label)[0] == 1: # Wall
                curr_modifiers = list(self.SapModel.AreaObj.GetModifiers(label)[0])
                curr_modifiers[:6] = modifiers
                self.SapModel.AreaObj.SetModifiers(label, curr_modifiers)

    def create_25percent_file(self,
                              modifiers: list = 6 * [.01],
                              dynamic: bool = False,
                              d: Union[dict, None] = None,
                              directory: str='shearwall',
                              suffix: str='25percent',
                              open_main_file: bool=True,
                              ):
        main_file, filename = self.etabs.save_in_folder_and_add_name(directory, suffix)
        # Set Modifiers for Shearwall
        self.set_modifiers(modifiers)
        # Set Realeses for columns
        self.etabs.frame_obj.set_end_release_for_columns_with_pier_label()
        self.etabs.database.multiply_seismic_loads(0.25)
        if dynamic:
            self.etabs.scale_response_spectrum_with_respect_to_settings(
                d,
                analyze=False,
                consider_min_static_base_shear=True,
                reset_scale=True,
                )
        if open_main_file:
            self.etabs.open_model(main_file)
        return main_file, filename
            
        


        
            