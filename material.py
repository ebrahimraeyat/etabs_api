__all__ = ['Material']


class Material:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def all_material(self):
        return self.SapModel.PropMaterial.GetNameList()[1]

    def material_type(self, name):
        return self.SapModel.PropMaterial.GetTypeOAPI(name)[0]

    def get_material_of_type(self, type_):
        '''
        type_ can be: 
            1: Steel
            2: Concrete
            6: Rebar
        '''
        mats = [mat for mat in self.all_material() if self.material_type(mat) == type_]
        return mats

    def get_rebar_fy_fu(self, rebar):
        return self.SapModel.PropMaterial.GetORebar(rebar)[0:2]

    def get_S340_S400_rebars(self):
        '''
        try to find S400 (AIII) and S340 (AII) Rebars material
        '''
        self.etabs.set_current_unit('N', 'mm')
        rebars = self.get_material_of_type(6)
        S340 = []
        S400 = []
        for rebar in rebars:
            fy, _ = self.get_rebar_fy_fu(rebar)
            if 390 < fy < 410:
                S400.append(rebar)
            elif 290 < fy < 350:
                S340.append(rebar)
        return S340, S400

    def get_standard_rebar_size(
            self,
            standard_size = (8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30),
            ):
        '''
        Return Rebars that diameters is in standard_size'
        '''
        rebars = self.SapModel.PropRebar.GetNameListWithData()
        names = []
        for name, size in zip(rebars[1], rebars[3]):
            if int(size) == size and size in standard_size:
                names.append(name)
        return sorted(names)

    def get_tie_main_rebars(self):
        tie_rebars = []
        main_rebars = []
        rebars = self.SapModel.PropRebar.GetNameListWithData()
        for name, size in zip(rebars[1], rebars[3]):
            if int(size) == size:
                if  size in [10, 12]:
                    tie_rebars.append(name)
                elif size in [14, 16, 18, 20, 22, 25, 28, 30]:
                    main_rebars.append(name)
        return tie_rebars, main_rebars

    def get_fc(self, conc):
        self.etabs.set_current_unit('N', 'mm')
        return self.SapModel.PropMaterial.GetOConcrete(conc)[0]

    def add_material(
        self,
        name: str,
        type_: int,
        ):
        '''
        type_ can be: 
            1: Steel
            2: Concrete
            6: Rebar
        '''
        self.SapModel.PropMaterial.SetMaterial(name, type_)

    def add_AIII_rebar(
        self,
        name: str = 'AIII',
        ):
        self.add_material(name, 6)
        self.SapModel.PropMaterial.SetORebar(name, 400, 600, 500, 750, 1, 1, 0.01, 0.09, False, 0)
    
    def add_AII_rebar(
        self,
        name: str = 'AII',
        ):
        self.add_material(name, 6)
        self.SapModel.PropMaterial.SetORebar(name, 300, 500, 375, 625, 1, 1, 0.01, 0.09, False, 0)

        