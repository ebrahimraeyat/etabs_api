from pathlib import Path
from typing import Iterable, Union
import time

import pandas

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
                              modifiers: list = 8 * [.01],
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
                consider_min_static_base_shear=False,
                reset_scale=True,
                )
        if open_main_file:
            self.etabs.open_model(main_file)
        return main_file, filename
    
    def start_design(self,
                     max_wait: int=120,
                     interval: int=2,
                     cols: Union[None, Iterable]=None,
                     ) -> Union[pandas.DataFrame, None]:
        self.etabs.select_obj.clear_selection()
        pywin_etabs = self.etabs.get_pywinauto_etabs()
        if pywin_etabs is None:
            print("Can not find the ETABS with pywinauto.")
            return
        self.etabs.run_analysis()
        pywin_etabs.set_focus()
        print("Start Design of Shear Walls ...")
        pywin_etabs.type_keys("+{F10}")
        # Wait for the design to complete
        table_key = None
        wait = 0
        last_size = 0
        while wait < max_wait:
            time.sleep(interval)  # Wait for the design to complete
            wait += interval
            texts = ["Shear Wall Pier Design Summary", "ACI", "318"]
            table_key = self.etabs.database.table_name_that_containe_texts(texts)
            if table_key is not None:
                df = self.etabs.database.read(table_key, to_dataframe=True)
                if df.shape[0] > 0 and df.shape[0] == last_size:
                    break
                last_size = df.shape[0]
        print(f"Design Shear Wall completed after {wait} seconds.")
        if cols:
            df = df[cols]
        return df
    
    def set_design_type(self, type_: str="Program Determined"):
        """
        Set the design type for shear walls.
        :param type_: Type of design check, e.g., "Program Determined" means "Check", "Design".
        """
        if type_ not in ("Program Determined", "Design"):
            raise ValueError("type_ must be 'Program Determined' or 'Design'.")
        self.etabs.unlock_model()
        table_key = ['Shear Wall Pier Design Overwrites', 'ACI', '318']
        table_key = self.etabs.database.table_name_that_containe_texts(table_key)
        if table_key is None:
            return None
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if df is None:
            return
        df['DesignCheck'] = type_
        self.etabs.database.write(table_key, df.astype(str))

    def get_wall_ratios(self) -> pandas.DataFrame:
        self.start_design()
        texts = ["Shear Wall Pier Design Summary", "ACI", "318"]
        table_key = self.etabs.database.table_name_that_containe_texts(texts)
        if table_key is None:
            return None
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if df is None or "DCRatio" not in df.columns:
            print(f"Table '{table_key}' does not contain 'D/C Ratio' column.")
            return None
        cols = ["Story", "Pier", "DCRatio"]
        df = df[cols]
        df = df.groupby(["Story", "Pier"]).max().reset_index()
        return df


            
        


        
            