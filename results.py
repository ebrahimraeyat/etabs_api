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

    def get_point_xy_displacement(self,
            point_name: str,
            lp_name: str,
            type_: str='Case', # 'Combo
            ):
        x, y, _ = self.get_point_displacement(point_name, lp_name, type_)
        return x, y
    
    def get_point_displacement(self,
            point_name: str,
            lp_name: str,
            type_: str='Case', # 'Combo
            index: int=0,
            item_type_elm: int=0,
            ):
        self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
        exec(f'self.SapModel.Results.Setup.Set{type_}SelectedForOutput("{lp_name}")')
        results = self.SapModel.Results.JointDispl(point_name, item_type_elm)
        index = -1
        x = results[6][index]
        y = results[7][index]
        z = results[8][index]
        return x, y, z
    
    def get_points_min_max_displacements(self,
                                         points: list=[],
                                         load_cases: list=[],
                                         load_combinations: list=[],
                                         ):
        self.etabs.database.select_load_cases_combinations(load_cases=load_cases, load_combinations=load_combinations)
        table_key = 'Joint Displacements'
        cols = ['UniqueName', 'OutputCase', 'Ux', 'Uy', 'Uz']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        if df is None:
            return
        convert_type = {
                    'Ux' : float,
                    'Uy' : float,
                    'Uz' : float,
                    }
        df = df.astype(convert_type)
        if points:
            filt = df['UniqueName'].isin(points)
            df = df.loc[filt]
        return df.groupby(['UniqueName', 'OutputCase']).agg({'Ux': ['min', 'max'], 'Uy': ['min', 'max'], 'Uz': ['min', 'max']})

    def get_point_abs_displacement(self,
            point_name: str,
            lp_name: str,
            type_: str='Case', # 'Combo
            index: int=-1,
            item_type_elm: int=1,
        ):
        self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
        exec(f'self.SapModel.Results.Setup.Set{type_}SelectedForOutput("{lp_name}")')
        results = self.SapModel.Results.JointDisplAbs(point_name, item_type_elm)
        if results[0] == 0:
            results = self.SapModel.Results.JointDisplAbs(point_name, 0)
        print(10 * '*', '\n', point_name, results)
        x = results[6][index]
        y = results[7][index]
        z = results[8][index]
        return x, y, z

    def get_points_displacement(self,
            point_names: list,
            lp_name: str,
            type_: str='Case', # 'Combo
            index: int=0,
            item_type_elm: int=0,
            map_dict: dict={},
            ):
        self.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
        exec(f'self.SapModel.Results.Setup.Set{type_}SelectedForOutput("{lp_name}")')
        displacements = {}
        index = -1
        for point_name in point_names:
            results = self.SapModel.Results.JointDispl(point_name, item_type_elm)
            if results[0] == 0:
                results = self.SapModel.Results.JointDispl(point_name, 0)
            print(10 * '*', '\n', point_name, results)
            x = results[6][index]
            y = results[7][index]
            z = results[8][index]
            if map_dict:
                point_name = int(map_dict.get(point_name, point_name))
            displacements[point_name] = (x, y, z)
        return displacements
    
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
