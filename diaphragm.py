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
        