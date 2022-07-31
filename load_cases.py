from typing import Iterable, Tuple, Union

from numpy import int16


class LoadCases:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def get_load_cases(self):
        load_case_names = self.SapModel.LoadCases.GetNameList(0, [])[1]
        return load_case_names

    def select_all_load_cases(self):
        load_case_names = self.get_load_cases()
        self.SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay('')
        self.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay(load_case_names)

    def select_load_cases(self, names):
        self.SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay('')
        self.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay(names)

    def get_loadcase_withtype(self, n) -> list:
        '''
        return load cases that match load case type number:
        1 : LinearStatic
        2 : NonlinearStatic
        3 : Modal
        4 : ResponseSpectrum
        '''
        load_cases = self.get_load_cases()
        ret = []
        for lc in load_cases:
            if self.SapModel.LoadCases.GetTypeOAPI(lc)[0] == n:
                ret.append(lc)
        return ret

    def get_modal_loadcase_name(self):
        load_cases = self.get_load_cases()
        for lc in load_cases:
            if self.SapModel.LoadCases.GetTypeOAPI(lc)[0] == 3:
                return lc
        return None
    
    def get_response_spectrum_loadcase_name(self):
        load_cases = self.get_load_cases()
        names = []
        for lc in load_cases:
            if self.SapModel.LoadCases.GetTypeOAPI(lc)[0] == 4:
                names.append(lc)
        return names
    
    def get_response_spectrum_loadcase_with_dir_angle(self, direction, angle):
        specs = self.get_response_spectrum_loadcase_name()
        for name in specs:
            n, dirs, _, _, _, angles, _ = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
            if n == 1 and dirs[0] == direction and float(angles[0]) == angle:
                return name
        return None

    def get_response_spectrum_xy_loadcase_name(self):
        sx = self.get_response_spectrum_loadcase_with_dir_angle('U1', 0)
        if sx is None:
            sx = self.get_response_spectrum_loadcase_with_dir_angle('U2', 90)
        sy = self.get_response_spectrum_loadcase_with_dir_angle('U2', 0)
        if sy is None:
            sy = self.get_response_spectrum_loadcase_with_dir_angle('U1', 90)
        return sx, sy
    
    def get_response_spectrum_xy_loadcases_names(self):
        x_names = []
        y_names = []
        specs = self.get_response_spectrum_loadcase_name()
        for name in specs:
            n, dirs, _, _, _, angles, _ = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
            if n == 1:
                if dirs[0] == 'U1':
                    if float(angles[0]) == 0:
                        x_names.append(name)
                    elif float(angles[0]) == 90:
                        y_names.append(name)
                elif dirs[0] == 'U2':
                    if float(angles[0]) == 90:
                        x_names.append(name)
                    elif float(angles[0]) == 0:
                        y_names.append(name)
        return x_names, y_names

    def multiply_response_spectrum_scale_factor(self,
            name : str,
            scale : float,
            scale_min : Union[float, bool] = 1.0,
            all : bool = False,
            ):
        self.etabs.unlock_model()
        if scale_min is not None:
            scale = max(scale, scale_min)
        ret = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
        if all:
            scales = (i * scale for i in ret[3])
            scales = tuple(scales)
        else:
            scales = (ret[3][0] * scale,) + tuple(ret[3][1:])
        ret[3] = scales
        self.SapModel.LoadCases.ResponseSpectrum.SetLoads(name, *ret[:-1])
        return None

    def get_spectral_with_angles(self,
                angles : Union[Iterable, bool] = None,
                specs : Iterable = None,
                ) -> dict:
        '''
        return angles and Response spectrum loadcase
        {0: spec}
        '''
        table = 'Load Case Definitions - Response Spectrum'
        df = self.etabs.database.read(table, to_dataframe=True, cols=['Name', 'Angle'])
        df.dropna(inplace=True)
        df['Angle'] = df['Angle'].astype(int16)
        df.drop_duplicates(['Name'], keep=False, inplace=True)
        if angles is not None:
            df = df[df['Angle'].isin(angles)]
        if specs is not None:
            df = df[df['Name'].isin(specs)]
        # df.drop_duplicates(['Angle'], keep='first', inplace=True)
        angles_specs = dict()
        for _, row in df.iterrows():
            angle = row['Angle']
            name = row['Name']
            angles_specs[int(angle)] = name
        return angles_specs

    def reset_scales_for_response_spectrums(self,
                    scale : float = 1,
                    loadcases : Union[list, bool] = None,
                    length_unit : str = 'mm',  # 'cm', 'm'
                    ) -> None:
        self.etabs.unlock_model()
        self.etabs.set_current_unit('N', length_unit)
        if loadcases is None:
            loadcases = self.get_loadcase_withtype(4)
        for name in loadcases:
            ret = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
            scales = (scale,) + tuple(ret[3][1:])
            ret[3] = scales
            self.SapModel.LoadCases.ResponseSpectrum.SetLoads(name, *ret[:-1])
        return None

    def get_seismic_load_cases(
        self,
        ):
        '''
        Search for Response spectrum load case and load cases that have at least one seismic load pattern
        '''
        seismic_load_cases = []
        for lc in self.get_load_cases():
            load_case_type = self.SapModel.LoadCases.GetTypeOAPI(lc)[0]
            if load_case_type == 1:  # Static Linear
                for lp in self.SapModel.LoadCases.StaticLinear.GetLoads(lc)[2]:
                    if self.SapModel.LoadPatterns.GetLoadType(lp)[0] == 5:  # seismic load pattern
                        seismic_load_cases.append(lc)
                        break
            elif load_case_type == 4: # Adding Response Spectrum load cases
                seismic_load_cases.append(lc)
        return seismic_load_cases
    
    def get_seismic_drift_load_cases(
        self,
        ):
        '''
        Search for  load cases that have at least one seismic drift load pattern
        '''
        seismic_drift_load_cases = []
        for lc in self.get_load_cases():
            load_case_type = self.SapModel.LoadCases.GetTypeOAPI(lc)[0]
            if load_case_type == 1:  # Static Linear
                for lp in self.SapModel.LoadCases.StaticLinear.GetLoads(lc)[2]:
                    if self.SapModel.LoadPatterns.GetLoadType(lp)[0] == 37:  # seismic load pattern
                        seismic_drift_load_cases.append(lc)
                        break
        return seismic_drift_load_cases
    
    def get_xy_seismic_load_cases(
        self,
        ):
        '''
        Search for  load cases that all load patterns are in x or y direction
        '''
        x_seismic_load_cases = []
        y_seismic_load_cases = []
        x_names, y_names = self.etabs.load_patterns.get_load_patterns_in_XYdirection()
        for lc in self.get_load_cases():
            load_case_type = self.SapModel.LoadCases.GetTypeOAPI(lc)[0]
            if load_case_type == 1:  # Static Linear
                dir_set = set()
                for lp in self.SapModel.LoadCases.StaticLinear.GetLoads(lc)[2]:
                    if lp in x_names:
                        dir_set.add('x')
                    elif lp in y_names:
                        dir_set.add('y')
                if dir_set == {'x'}:
                    x_seismic_load_cases.append(lc)
                elif dir_set == {'y'}:
                    y_seismic_load_cases.append(lc)

        return x_seismic_load_cases, y_seismic_load_cases
        
        
        
        
        

    