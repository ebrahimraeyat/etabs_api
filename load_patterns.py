class LoadPatterns:

    map_number_to_pattern = {
            1 : 'Dead',
            2 : 'Super Dead',
            3 : 'Live',
            4 : 'Reducible Live',
            5 : 'Seismic',
            6 : 'Wind',
            7 : 'Snow',
            8 : 'Other',
            11 : 'ROOF Live',
            12 : 'Notional',
        }

    map_pattern_to_number = {
            'Dead' : 1,
            'Super Dead' : 2,
            'Live' : 3,
            'Reducible Live' : 4,
            'Seismic' : 5,
            'Wind' : 6,
            'Snow' : 7,
            'Other' : 8,
            'EV' : 8,
            'MASS' : 8,
            'ROOF Live' : 11,
            'Notional' : 12,
        }

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

    def get_load_patterns(self):
        return self.SapModel.LoadPatterns.GetNameList(0, [])[1]

    def get_special_load_pattern_names(self, n=5):
        '''
        Each load patterns has a special number ID, for example:
        DEAD is 1, SEISMIC is 5
        '''
        lps = self.get_load_patterns()
        names = []
        for lp in lps:
            if self.SapModel.LoadPatterns.GetLoadType(lp)[0] == n:
                names.append(lp)
        return names
        
    def get_drift_load_pattern_names(self):
        '''
        Drift loadType number is 37, when user ticks the eccentricity of load,
        etabs creates additional (1/3), (2/3), and (3/3) load when structure is analyzed
        '''
        return self.get_special_load_pattern_names(37)

    def get_load_patterns_in_XYdirection(self, only_ecc=False):
        '''
        return list of load pattern names, x and y direction separately
        '''
        self.select_all_load_patterns()
        TableKey = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.etabs.database.read_table(TableKey)
        i_xdir = FieldsKeysIncluded.index('XDir')
        i_xdir_plus = FieldsKeysIncluded.index('XDirPlusE')
        i_xdir_minus = FieldsKeysIncluded.index('XDirMinusE')
        i_ydir = FieldsKeysIncluded.index('YDir')
        i_ydir_plus = FieldsKeysIncluded.index('YDirPlusE')
        i_ydir_minus = FieldsKeysIncluded.index('YDirMinusE')
        i_name = FieldsKeysIncluded.index('Name')
        data = self.etabs.database.reshape_data(FieldsKeysIncluded, TableData)
        names_x = set()
        names_y = set()
        for earthquake in data:
            name = earthquake[i_name]
            if only_ecc:
                if all((
                earthquake[i_xdir] == 'Yes',
                earthquake[i_xdir_minus] == 'No',
                earthquake[i_xdir_plus] == 'No',
                )) or all((
                earthquake[i_ydir] == 'Yes',
                earthquake[i_ydir_minus] == 'No',
                earthquake[i_ydir_plus] == 'No',
                )):
                    continue
            if any((
                earthquake[i_xdir] == 'Yes',
                earthquake[i_xdir_minus] == 'Yes',
                earthquake[i_xdir_plus] == 'Yes',
            )):
                names_x.add(name)
            elif any((
                earthquake[i_ydir] == 'Yes',
                earthquake[i_ydir_minus] == 'Yes',
                earthquake[i_ydir_plus] == 'Yes',
            )):
                names_y.add(name)
            
        return names_x, names_y

    def get_EX_EY_load_pattern(self):
        '''
        return earthquakes in x, y direction that did not eccentricity
        '''
        self.select_all_load_patterns()
        TableKey = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.etabs.database.read_table(TableKey)
        i_xdir = FieldsKeysIncluded.index('XDir')
        i_xdir_plus = FieldsKeysIncluded.index('XDirPlusE')
        i_xdir_minus = FieldsKeysIncluded.index('XDirMinusE')
        i_ydir = FieldsKeysIncluded.index('YDir')
        i_ydir_plus = FieldsKeysIncluded.index('YDirPlusE')
        i_ydir_minus = FieldsKeysIncluded.index('YDirMinusE')
        i_name = FieldsKeysIncluded.index('Name')
        data = self.etabs.database.reshape_data(FieldsKeysIncluded, TableData)
        name_x = None
        name_y = None
        drift_lp_names = self.get_drift_load_pattern_names()
        for earthquake in data:
            name = earthquake[i_name]
            if all((
                    not name_x,
                    not name in drift_lp_names,
                    earthquake[i_xdir] == 'Yes',
                    earthquake[i_xdir_minus] == 'No',
                    earthquake[i_xdir_plus] == 'No',
                )):
                    name_x = name
            if all((
                    not name_y,
                    not name in drift_lp_names,
                    earthquake[i_ydir] == 'Yes',
                    earthquake[i_ydir_minus] == 'No',
                    earthquake[i_ydir_plus] == 'No',
                )):
                    name_y = name
            if name_x and name_y:
                break
        return name_x, name_y

    def get_xy_spectral_load_patterns_with_angle(self, angle : int = 0):
        '''
        return Response spectrum loadcase
        '''
        TableKey = 'Load Case Definitions - Response Spectrum'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.etabs.database.read_table(TableKey)
        data = self.etabs.database.reshape_data(FieldsKeysIncluded, TableData)
        i_name = FieldsKeysIncluded.index('Name')
        names = set([i[i_name] for i in data])
        x_names = []
        y_names = []
        for name in names:
            ret = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
            if ret[0] == 1 and ret[5][0] == angle:
                direction = ret[1][0]
                if direction == 'U1':
                    x_names.append(name)
                elif direction == 'U2':
                    y_names.append(name)
        return x_names, y_names

    def get_ex_ey_earthquake_name(self):
        x_names, y_names = self.get_load_patterns_in_XYdirection()
        x_names = sorted(x_names)
        y_names = sorted(y_names)
        x_name = None
        y_name = None
        drift_load_patterns = self.get_drift_load_pattern_names()
        for name in x_names:
            if name not in drift_load_patterns:
                x_name = name
                break
        for name in y_names:
            if name not in drift_load_patterns:
                y_name = name
                break
        return x_name, y_name

    def get_xy_seismic_load_patterns(self, only_ecc=False):
        x_names, y_names = self.get_load_patterns_in_XYdirection(only_ecc)
        drift_load_pattern_names = self.get_drift_load_pattern_names()
        xy_names = x_names.union(y_names).difference(drift_load_pattern_names)
        return xy_names
      
    def select_all_load_patterns(self):
        load_pattern_names = list(self.get_load_patterns())
        self.SapModel.DatabaseTables.SetLoadPatternsSelectedForDisplay(load_pattern_names) 

    def get_design_type(self, pattern_name):
        '''
        get a load pattern name and return design type of it appropriate
        '''
        type_num = self.SapModel.LoadCases.GetTypeOAPI_1(pattern_name)[2]
        design_type = self.map_number_to_pattern.get(type_num, None)
        return design_type

if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
    ret = etabs.load_patterns.get_xy_spectral_load_patterns_with_angle()
    print('Wow')
