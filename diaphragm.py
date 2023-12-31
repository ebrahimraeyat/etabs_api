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
