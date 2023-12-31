from typing import Union


__all__ = ['Diaphragm']


class Diaphragm:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def names(self):
        return self.SapModel.Diaphragm.GetNameList()[1]

    def is_diaphragm_assigned(self):
        table_key = 'Area Assignments - Diaphragms'
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if df is not None:
            filt = df['Diaphragm'] == 'None'
            if len(df.loc[filt]) < len(df) / 2:
                return True
        table_key = 'Joint Assignments - Diaphragms'
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if df is None:
            return False
        filt = df['Diaphragm'] == "From Shell Object"
        if len(df.loc[filt]) < len(df) / 2:
            return True
        return False
    
    def set_area_diaphragms(self,
                            diaph_name: str,
                            areas: Union[list, None]=None,
                            ):
        if areas is None:
            areas = self.etabs.area.get_names_of_areas_of_type(type_='floor')
        for area in areas:
            self.etabs.SapModel.AreaObj.SetDiaphragm(area, diaph_name)

    def add_diaphragm(self,
                      diaph_name: str,
                      semi_rigid: bool=False,
                      ):
        self.etabs.SapModel.Diaphragm.SetDiaphragm(diaph_name, semi_rigid)

        