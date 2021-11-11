__all__ = ['Group']


class Group:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def names(self):
        return self.SapModel.GroupDef.GetNameList()[1]

    def add(self, name):
        names = self.names()
        if not name in names:
            self.SapModel.GroupDef.SetGroup(name)
            return True
        return False