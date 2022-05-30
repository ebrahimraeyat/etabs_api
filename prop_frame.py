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