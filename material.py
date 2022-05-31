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
            elif 330 < fy < 350:
                S340.append(rebar)
        return S340, S400

    def get_rebar_sizes(self):
        '''
        Return Rebars that name ends with 'd' like '16d'
        '''
        rebars = self.SapModel.PropRebar.GetNameList()[1]
        d_rebars = [rebar for rebar in rebars if rebar.endswith('d')]
        return sorted(d_rebars)

        