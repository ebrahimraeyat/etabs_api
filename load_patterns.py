import pandas as pd
pd.options.mode.chained_assignment = None


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
            37: 'Seismic (Drift)',
            61: 'QuakeDrift',
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
            'Seismic (Drift)' : 37,
            'QuakeDrift' : 61,
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
        all_load_patterns = self.SapModel.LoadPatterns.GetNameList()[1]
        return [text for text in all_load_patterns if not text.startswith('~')]

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
        
    def get_notional_load_pattern_names(self):
        '''
        notional loadType number is 12
        '''
        n = self.map_pattern_to_number.get("Notional", 12)
        return self.get_special_load_pattern_names(n)
    
    def get_drift_load_pattern_names(self):
        '''
        Drift loadType number is 37 in etabs v19 and 61 in etabs v20
        '''
        return self.get_special_load_pattern_names(self.etabs.seismic_drift_load_type)

    def get_load_patterns_in_XYdirection(self, only_ecc=False):
        '''
        return list of load pattern names, x and y direction separately
        '''
        self.select_all_load_patterns()
        names_x = set()
        names_y = set()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        ret = self.etabs.database.read_table(table_key)
        if ret is None:
            return names_x, names_y
        [_, _, fields, _, data, _] = ret
        i_xdir = fields.index('XDir')
        i_xdir_plus = fields.index('XDirPlusE')
        i_xdir_minus = fields.index('XDirMinusE')
        i_ydir = fields.index('YDir')
        i_ydir_plus = fields.index('YDirPlusE')
        i_ydir_minus = fields.index('YDirMinusE')
        i_name = fields.index('Name')
        data = self.etabs.database.reshape_data(fields, data)
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

    def get_seismic_load_patterns(self,
                                  drifts: bool=False,
                                  ):
        '''
        return lists of load pattern names, x, +x, -x, y, +y and -y separately
        '''
        self.select_all_load_patterns()
        xdir = set()
        xdir_plus = set()
        xdir_minus = set()
        ydir = set()
        ydir_plus = set()
        ydir_minus = set()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        ret = self.etabs.database.read_table(table_key)
        if ret is not None:
            [_, _, FieldsKeysIncluded, _, TableData, _] = ret
            i_xdir = FieldsKeysIncluded.index('XDir')
            i_xdir_plus = FieldsKeysIncluded.index('XDirPlusE')
            i_xdir_minus = FieldsKeysIncluded.index('XDirMinusE')
            i_ydir = FieldsKeysIncluded.index('YDir')
            i_ydir_plus = FieldsKeysIncluded.index('YDirPlusE')
            i_ydir_minus = FieldsKeysIncluded.index('YDirMinusE')
            i_name = FieldsKeysIncluded.index('Name')
            data = self.etabs.database.reshape_data(FieldsKeysIncluded, TableData)
            drift_lp_names = self.get_drift_load_pattern_names()
            for earthquake in data:
                name = earthquake[i_name]
                if (drifts and name in drift_lp_names) or (not drifts and name not in drift_lp_names):
                    if all((
                        earthquake[i_xdir] == 'Yes',
                        earthquake[i_xdir_minus] == 'No',
                        earthquake[i_xdir_plus] == 'No',
                        earthquake[i_ydir] == 'No',
                        earthquake[i_ydir_minus] == 'No',
                        earthquake[i_ydir_plus] == 'No',
                        )):
                        xdir.add(name)
                    elif all((
                        earthquake[i_xdir] == 'No',
                        earthquake[i_xdir_minus] == 'Yes',
                        earthquake[i_xdir_plus] == 'No',
                        earthquake[i_ydir] == 'No',
                        earthquake[i_ydir_minus] == 'No',
                        earthquake[i_ydir_plus] == 'No',
                        )):
                        xdir_minus.add(name)
                    elif all((
                        earthquake[i_xdir] == 'No',
                        earthquake[i_xdir_minus] == 'No',
                        earthquake[i_xdir_plus] == 'Yes',
                        earthquake[i_ydir] == 'No',
                        earthquake[i_ydir_minus] == 'No',
                        earthquake[i_ydir_plus] == 'No',
                        )):
                        xdir_plus.add(name)
                    elif all((
                        earthquake[i_xdir] == 'No',
                        earthquake[i_xdir_minus] == 'No',
                        earthquake[i_xdir_plus] == 'No',
                        earthquake[i_ydir] == 'Yes',
                        earthquake[i_ydir_minus] == 'No',
                        earthquake[i_ydir_plus] == 'No',
                        )):
                        ydir.add(name)
                    elif all((
                        earthquake[i_xdir] == 'No',
                        earthquake[i_xdir_minus] == 'No',
                        earthquake[i_xdir_plus] == 'No',
                        earthquake[i_ydir] == 'No',
                        earthquake[i_ydir_minus] == 'Yes',
                        earthquake[i_ydir_plus] == 'No',
                        )):
                        ydir_minus.add(name)
                    elif all((
                        earthquake[i_xdir] == 'No',
                        earthquake[i_xdir_minus] == 'No',
                        earthquake[i_xdir_plus] == 'No',
                        earthquake[i_ydir] == 'No',
                        earthquake[i_ydir_minus] == 'No',
                        earthquake[i_ydir_plus] == 'Yes',
                        )):
                        ydir_plus.add(name)
        return xdir, xdir_minus, xdir_plus, ydir, ydir_minus, ydir_plus

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
            if name in drift_lp_names:
                continue
            if all((
                    not name_x,
                    earthquake[i_xdir] == 'Yes',
                    earthquake[i_xdir_minus] == 'No',
                    earthquake[i_xdir_plus] == 'No',
                )):
                    name_x = name
            if all((
                    not name_y,
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
    
    def get_all_seismic_load_patterns(self):
        '''
        returns a list of seismic load pattern names in seismic table
        '''
        ret = set()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if df is not None:
            ret = set(df.Name.unique())
        return ret

    def get_ex_ey_earthquake_name(self):
        ret = self.get_seismic_load_patterns()
        x_name = ret[0].pop()
        y_name = ret[3].pop()
        return x_name, y_name
    
    def get_earthquake_values(self, names: list,
                              ):
        '''
        Return the list contain earthquake factors
        '''
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        df = self.etabs.database.read(table_key, to_dataframe=True)
        df = df.dropna(subset=['C'])
        c = []
        for name in names:
            if name in df.Name.unique():
                ser = df[df['Name'] == name]['C']
                c.append(float(ser.values))
        return c
    
    def get_expanded_seismic_load_patterns(self) -> tuple:
        '''
        get all seismic loads that have multiple eccentricity in definitions like EXALL, EYALL
        and returns new dataframe for apply in  Auto Seismic - User Coefficient table and
        a dictionary that keys corresponds all seismic user loads and values are converted
        load and type
        '''
        self.etabs.unlock_model()
        self.etabs.lock_and_unlock_model()
        self.etabs.load_patterns.select_all_load_patterns()
        drift_load_names = self.etabs.load_patterns.get_drift_load_pattern_names()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        df = self.etabs.database.read(table_key, to_dataframe=True)
        d = {'Yes' : 1, 'No' : 0}
        cols = {
            'XDir' : '',
            'XDirPlusE' : 'P',
            'XDirMinusE' : 'N',
            'YDir' : '',
            'YDirPlusE' : 'P',
            'YDirMinusE' : 'N',
            }
        for col in cols:
            df[col] = df[col].map(d)
        filt_multi = (df[cols.keys()].sum(axis=1) > 1)
        if True not in filt_multi.values:
            return None
        converted_loads = dict.fromkeys(df['Name'].unique())
        converted_loads_type = dict()
        import copy
        new_rows = []
        for _, row in df.iterrows():
            name = row['Name']
            load_type = self.etabs.seismic_drift_load_type if name in drift_load_names else 5
            if row['XDir'] in (0, 1):
                row_dirs=row[cols.keys()]
            
            for col, prefix in cols.items():
                if row_dirs[col] == 1:
                    load_name = f'{name}{prefix}'
                    new_row = copy.deepcopy(row)
                    new_row[cols.keys()] = 0
                    new_row[col] = 1
                    new_row['Name'] = load_name
                    new_rows.append(new_row)
                    if converted_loads[name] is None:
                        converted_loads[name] = [(load_name, load_type)]
                    else:
                        converted_loads[name].append((load_name, load_type))
                    converted_loads_type[load_name] = load_type
        new_df = pd.DataFrame.from_records(new_rows, columns=df.columns)
        d = {1: 'Yes', 0: 'No'}
        for col in cols:
            new_df[col] = new_df[col].map(d)
        return new_df, converted_loads, converted_loads_type

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

    def add_load_patterns(self,
                names: list,
                type_: str = 'Dead',
                ):
        type_ = LoadPatterns.map_pattern_to_number.get(type_, None)
        if type_ is None:
            return False
        for name in names:
            self.SapModel.LoadPatterns.Add(name, type_)
            self.SapModel.LoadCases.StaticLinear.SetCase(name)
            self.SapModel.LoadCases.StaticLinear.SetLoads(
                name, 1, ('Load',), (name,), (1.0,))

        return True
    
    def add_notional_loads(self,
                           loads: list,
                           ):
        if len(loads) == 0:
            return
        notional_loads_x = [f'N{load}X' for load in loads]
        notional_loads_y = [f'N{load}Y' for load in loads]
        notional_loads = notional_loads_x + notional_loads_y
        self.etabs.load_patterns.add_load_patterns(notional_loads, 'Notional')
        table_key = "Load Pattern Definitions - Auto Notional Loads"
        df = self.etabs.database.read(table_key, to_dataframe=True)
        cols = self.etabs.auto_notional_loads_columns
        df2 = []
        for load in loads:
            df2.extend([[f'N{load}X', load, '.002', 'X'], [f'N{load}Y', load, '.002', 'Y']])
        df2 = pd.DataFrame(df2, columns=cols)
        if df is not None and not df.empty:
            df.columns = cols
            df = pd.concat([df, df2], ignore_index=True)
        else:
            df = df2
        self.etabs.database.apply_data(table_key, df)
        




        
        

    

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
