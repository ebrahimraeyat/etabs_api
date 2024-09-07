from typing import Union

__all__ = ['PropFrame']


class PropFrame:
    def __init__(
            self,
            etabs=None,
            ):
        self.etabs = etabs
        self.SapModel = self.etabs.SapModel

    def create_concrete_beam(
        self,
        name : str,
        concrete : str,
        height : float,
        width : float,
        rebar_mat: str,
        tie_mat: str,
        cover: float,
        ):
        self.SapModel.PropFrame.SetRectangle(name, concrete, height, width)
        ret = self.SapModel.propframe.SetRebarBeam(name, rebar_mat, tie_mat, cover, cover, 0, 0, 0, 0)
        if ret == 0:
            return True
        return False
    
    def create_concrete_column(
        self,
        name: str,
        concrete: str,
        height: float,
        width: float,
        rebar_mat: str,
        tie_mat: str,
        cover: float,
        number_3dir_main_bars: int,
        number_2dir_main_bars: int,
        main_rebar_size: str,
        tie_rebar_size: str,
        tie_space: float = 100,
        number_2dir_tie_bars: int = 2,
        number_3dir_tie_bars: int = 2,
        design: bool = False,
        ):
        self.SapModel.PropFrame.SetRectangle(name, concrete, height, width)
        ret = self.SapModel.propframe.SetRebarColumn(
            name, rebar_mat, tie_mat, 1, 0, cover, 0,
            number_3dir_main_bars, number_2dir_main_bars,
            main_rebar_size, tie_rebar_size, tie_space,
            number_2dir_tie_bars, number_3dir_tie_bars, design,
            )
        if ret == 0:
            return True
        return False
    
    def change_beams_columns_section_fc(
        self,
        names: list,
        concrete: str,
        concrete_suffix: str,
        clean_names: bool=True,
        # rebar_mat: Union[None, str, float],
        # rebar_suffix: str,
        # cover: float,
        # design: bool = False,
        frame_types: list=['column'], 
        ):
        rets = set()
        convert_names = {}
        concretes = self.etabs.material.get_material_of_type(2)
        names = [str(name) for name in names]
        section_that_corner_bars_is_different = []
        for name in names:
            sec_name = self.SapModel.FrameObj.GetSection(name)[0]
            _, mat, height, width, *args = self.SapModel.PropFrame.GetRectangle(sec_name)
            # try to remove previous suffix
            original_sec_name = sec_name
            if clean_names:
                for conc in concretes:
                    if sec_name.endswith(conc):
                        sec_name = sec_name[:-len(conc)]
                        if sec_name.endswith("_"):
                            sec_name = sec_name[:-1]
                        break
            new_sec_name = sec_name + concrete_suffix # + rebar_suffix
            if convert_names.get(original_sec_name, None) is None:
                if ('column' in frame_types and self.etabs.frame_obj.is_column(str(name))):
                    args = self.SapModel.propframe.GetRebarColumn_1(
                        original_sec_name
                        )
                    self.SapModel.PropFrame.SetRectangle(new_sec_name, concrete, height, width)
                    ret = self.SapModel.propframe.SetRebarColumn(
                        new_sec_name, *args[:-4]
                        )
                    if args[8] != args[14]: # corner bar is different than other bars
                        section_that_corner_bars_is_different.append(new_sec_name)
                    rets.add(ret)
                elif ('beam' in frame_types and self.etabs.frame_obj.is_beam(str(name))): 
                    args = self.SapModel.propframe.GetRebarBeam(
                        original_sec_name
                        )
                    self.SapModel.PropFrame.SetRectangle(new_sec_name, concrete, height, width)
                    ret = self.SapModel.propframe.SetRebarBeam(
                        new_sec_name, *args[:-1]
                        )
                    rets.add(ret)
                else:
                    continue
                convert_names[original_sec_name] = new_sec_name
            self.SapModel.FrameObj.SetSection(name, new_sec_name)
        if rets == {0}:
            return True, convert_names, section_that_corner_bars_is_different
        return False, convert_names, section_that_corner_bars_is_different

    def get_concrete_rectangular_of_type(self,
        type_ : str = 'Column',
        ):
        table_key = "Frame Section Property Definitions - Concrete Rectangular"
        df = self.etabs.database.read(table_key, to_dataframe=True)
        filt = df.DesignType == type_
        return df[filt].Name

    def convert_columns_design_types(self,
        design : bool = True,
        columns : list = [],
        sections : list = [],
        ):
        '''
        columns : unique name for columns that their section design type must be changed
        sections : sections that their design type must be changed
        '''
        if columns:
            col_sections = [self.SapModel.FrameObj.GetSection(col)[0] for col in columns]
        else:
            col_sections = self.get_concrete_rectangular_of_type(type_='Column')
        for sec in col_sections:
            ret = self.SapModel.PropFrame.GetRebarColumn(sec)
            ret[-2] = design
            self.SapModel.PropFrame.SetRebarColumn(sec, *ret[:-1])

    def get_number_of_rebars_and_areas_of_column_section(self,
                                                         name: str,
                                                         ) -> tuple:
        '''
        return the number of rebars in 3 and 2 dir of section and the
        area of corner and other rebars in section
        '''
        ret = self.SapModel.propframe.GetRebarColumn_1(name)
        n3 = ret[6]
        n2 = ret[7]
        area = ret[15]
        corner_area = ret[16]
        return n3, n2, area, corner_area

