from typing import Union
import enum


__all__ = ['PropFrame']


@enum.unique
class CompareTwoColumnsEnum(enum.IntEnum):
    section_area = 0
    corner_rebar_size = 1
    longitudinal_rebar_size = 2
    total_rebar_area = 3
    local_axes = 4
    section_dimension = 5
    rebar_number = 6
    rebar_slop = 7
    OK = 8
    not_checked = 9


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
    
    def check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention(self,
                                                                        below_col: str,
                                                                        above_col: str,
                                                                        ) -> tuple:
        below_angle = self.etabs.SapModel.FrameObj.GetLocalAxes(below_col)[0]
        above_angle = self.etabs.SapModel.FrameObj.GetLocalAxes(above_col)[0]
        below_angle = below_angle % 180
        above_angle = above_angle % 180
        n1 = below_angle % 90
        n2 = above_angle % 90
        rotation_is_ok = True
        if n1 != n2:
            rotation_is_ok = False
        n1 = below_angle // 90
        n2 = above_angle // 90
        need_to_convert_dimention = False
        if n1 != n2:
            need_to_convert_dimention = True
        return rotation_is_ok, need_to_convert_dimention
    
    def check_if_dimention_of_above_column_is_greater_than_below_column(self,
                                                                        below_col: str,
                                                                        above_col: str,
                                                                        below_sec: Union[str, None]=None,
                                                                        above_sec: Union[str, None]=None,
                                                                        rotation_is_ok: Union[bool, None]=None,
                                                                        need_to_convert_dimention: Union[bool, None]=None,
                                                                        ):
        if below_sec is None:
            below_sec = self.etabs.SapModel.FrameObj.GetSection(below_col)[0]
        if above_sec is None:
            above_sec = self.etabs.SapModel.FrameObj.GetSection(above_col)[0]
        x_below, y_below = self.etabs.SapModel.PropFrame.GetRectangle(below_sec)[2:4]
        x_above, y_above = self.etabs.SapModel.PropFrame.GetRectangle(above_sec)[2:4]
        if rotation_is_ok is None:
            rotation_is_ok, need_to_convert_dimention = \
            self.check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention(below_col, above_col)
        if need_to_convert_dimention:
            x_above, y_above = y_above, x_above
        if x_above > x_below or y_above > y_below:
            return True, (x_above, y_above, x_below, y_below)
        return False, (x_above, y_above, x_below, y_below)

    def compare_two_columns(self,
                            below_col: str,
                            above_col: str,
                            section_areas: Union[dict, None]=None,
                            below_sec: Union[str, None]=None,
                            above_sec: Union[str, None]=None,
                            ) -> CompareTwoColumnsEnum:
        # self.etabs.SapModel.PropFrame.GetTypeOAPI()  8: rectangle 9: circle
        if section_areas is None:
            column_names = self.etabs.frame_obj.concrete_section_names('Column')
            section_areas = self.etabs.frame_obj.get_section_area(column_names)
        if below_sec is None:
            below_sec = self.SapModel.FrameObj.GetSection(below_col)[0]
        if above_sec is None:
            above_sec = self.SapModel.FrameObj.GetSection(above_col)[0]
        below_area = section_areas.get(below_sec, None)
        above_area = section_areas.get(above_sec, None)
        if above_area > below_area:
            return CompareTwoColumnsEnum.section_area
        # check the rebars areas
        n3_below, n2_below, area_below, corner_area_below = self.etabs.prop_frame.get_number_of_rebars_and_areas_of_column_section(below_sec)
        n3_above, n2_above, area_above, corner_area_above = self.etabs.prop_frame.get_number_of_rebars_and_areas_of_column_section(above_sec)
        if corner_area_above > corner_area_below:
            return CompareTwoColumnsEnum.corner_rebar_size
        if area_above > area_below:
            return CompareTwoColumnsEnum.longitudinal_rebar_size
        total_rebar_area_above = 4 * corner_area_above + ((n3_above - 2) + (n2_above - 2)) * 2 * area_above
        total_rebar_area_below = 4 * corner_area_below + ((n3_below - 2) + (n2_below - 2)) * 2 * area_below
        if total_rebar_area_above > total_rebar_area_below:
            return CompareTwoColumnsEnum.total_rebar_area
        # Control dimension
        rotation_is_ok, need_to_convert_dimention = \
            self.check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention(below_col, above_col)
        if not rotation_is_ok:
            return CompareTwoColumnsEnum.local_axes
        is_dimention_greater, dimentions = \
            self.check_if_dimention_of_above_column_is_greater_than_below_column(
                                                                        below_col,
                                                                        above_col,
                                                                        below_sec,
                                                                        above_sec,
                                                                        rotation_is_ok,
                                                                        need_to_convert_dimention,
        )
        if is_dimention_greater:
            return CompareTwoColumnsEnum.section_dimension
        # Control number of rebars
        if need_to_convert_dimention:
            n3_above, n2_above = n2_above, n3_above
        if n3_above > n3_below or n2_above > n2_below:
            return CompareTwoColumnsEnum.rebar_number
        # Rebar Slop error
        x_above, y_above, x_below, y_below = dimentions
        if (x_below - x_above) > 10 or (y_below - y_above) > 10:
            return CompareTwoColumnsEnum.rebar_slop
        # There is no error
        return CompareTwoColumnsEnum.OK