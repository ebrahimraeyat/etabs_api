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
        units = self.etabs.get_current_unit()
        self.etabs.set_current_unit('N', 'mm')
        rebars = self.get_material_of_type(6)
        S340 = []
        S400 = []
        for rebar in rebars:
            fy, _ = self.get_rebar_fy_fu(rebar)
            if 390 < fy < 430:
                S400.append(rebar)
            elif 290 < fy < 350:
                S340.append(rebar)
        self.etabs.set_current_unit(*units)
        return S340, S400

    def get_tie_main_rebar_all_sizes(self):
        '''
        return rebars that size is in (10, 12) as tie_rebar_sizes
        and rebars that size is in [14, 16, 18, 20, 22, 25, 28, 30, 32, 36, 40, 50] as main_rebar_sizes
        and all rebars with size and name
        '''
        units = self.etabs.get_current_unit()
        self.etabs.set_current_unit('N', 'mm')
        tie_rebar_sizes = set()
        main_rebar_sizes = set()
        all_rebars = {}
        rebars = self.SapModel.PropRebar.GetNameListWithData()
        for name, size in zip(rebars[1], rebars[3]):
            if not name.startswith('#') or not name.endswith('M') and int(size) == size:
                size = int(size)
                if  size in [10, 12]:
                    tie_rebar_sizes.add(str(size))
                    all_rebars[str(size)] = name
                elif size in [14, 16, 18, 20, 22, 25, 28, 30, 32, 36, 40, 50]:
                    main_rebar_sizes.add(str(size))
                    all_rebars[str(size)] = name
        self.etabs.set_current_unit(*units)
        return tie_rebar_sizes, main_rebar_sizes, all_rebars

    def get_fc(self, conc):
        units = self.etabs.get_current_unit()
        self.etabs.set_current_unit('N', 'mm')
        fc = self.SapModel.PropMaterial.GetOConcrete(conc)[0]
        self.etabs.set_current_unit(*units)
        return fc

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

    def get_unit_weight_of_materials(self) -> dict:
        '''
        Return the unit weight of each material as pair of key, value of dictionary
        '''
        table_key = "Material Properties - Basic Mechanical Properties"
        cols = ['Material', 'UnitWeight']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        df = df.astype({'UnitWeight': float})
        df = df.set_index('Material')
        return df.to_dict()['UnitWeight']

        