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


