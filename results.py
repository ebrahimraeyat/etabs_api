from typing import Union


class Results:
    def __init__(
                self,
                SapModel=None,
                etabs=None,
                ):
        if not SapModel:
            self.etabs = etabs
            self.SapModel = etabs.SapModel
        else:
            self.SapModel = SapModel

    def get_xy_period(self):
        self.etabs.run_analysis()
        modal_name = self.etabs.load_cases.get_modal_loadcase_name()
        self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
        self.SapModel.Results.Setup.SetCaseSelectedForOutput(modal_name)
        ux = self.SapModel.Results.ModalParticipatingMassRatios()[5]
        uy = self.SapModel.Results.ModalParticipatingMassRatios()[6]
        x_index = ux.index(max(ux))
        y_index = uy.index(max(uy))
        periods = self.SapModel.Results.ModalParticipatingMassRatios()[4]
        Tx = periods[x_index]
        Ty = periods[y_index]
        return Tx, Ty, x_index + 1, y_index + 1

    def get_xy_frequency(self):
        Tx, Ty, i_x, i_y = self.get_xy_period()
        from math import pi
        return (2 * pi / Tx, 2 * pi / Ty, i_x, i_y)

    def get_point_xy_displacement(self, point_name, lp_name):
        self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
        self.SapModel.Results.Setup.SetCaseSelectedForOutput(lp_name)
        results = self.SapModel.Results.JointDispl(point_name, 0)
        x = results[6][0]
        y = results[7][0]
        return x, y

    def get_base_react(self,
            loadcases: Union[list, bool] = None,
            directions: Union[list, bool] = None,
            absolute : bool = False,
            ) -> list:
        # self.etabs.set_current_unit('kgf', 'm')
        if loadcases is None:
            loadcases = self.etabs.load_patterns.get_ex_ey_earthquake_name()
        if directions is None:
            directions = ['x', 'y']
        assert len(loadcases) == len(directions)
        self.etabs.run_analysis()
        self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
        for lc in loadcases:
            self.SapModel.Results.Setup.SetCaseSelectedForOutput(lc)
        base_react = self.SapModel.Results.BaseReact()
        load_cases = base_react[1]
        vxs = base_react[4]
        vys = base_react[5]
        V = []
        for lc, dir_ in zip(loadcases, directions):
            i = load_cases.index(lc)
            if dir_ == 'x':
                V.append(abs(vxs[i]) if absolute else vxs[i])
            elif dir_ == 'y':
                V.append(abs(vys[i]) if absolute else vys[i])
        return V
