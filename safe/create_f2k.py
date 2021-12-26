from pathlib import Path
from typing import Union


__all__ = ['Safe', 'CreateF2kFile']


class Safe():
    def __init__(self,
            input_f2k_path : Path = None,
            output_f2k_path : Path = None,
        ) -> None:
        self.input_f2k_path = input_f2k_path
        if output_f2k_path is None:
            output_f2k_path = input_f2k_path
        self.output_f2k_path = output_f2k_path
        self.__file_object = None
        self.tables_contents = None

    def __enter__(self):
        self.__file_object = open(self.input_f2k_path, 'r')
        return self.__file_object

    def __exit__(self, type, val, tb):
        self.__file_object.close()

    def get_tables_contents(self):
        with open(self.input_f2k_path, 'r') as reader:
            lines = reader.readlines()
            tables_contents = dict()
            n = len("TABLE:  ")
            context = ''
            table_key = None
            for line in lines:
                if line.startswith("TABLE:"):
                    if table_key and context:
                        tables_contents[table_key] = context
                    context = ''
                    table_key = line[n+1:-2]
                else:
                    context += line
        self.tables_contents = tables_contents
        return tables_contents

    def get_points_coordinates(self,
            content : str = None,
            ) -> dict:
        if content is None:
            content = self.tables_contents["OBJECT GEOMETRY - POINT COORDINATES"]
        lines = content.split('\n')
        points_coordinates = dict()
        for line in lines:
            if not line:
                continue
            line = line.lstrip(' ')
            fields_values = line.split()
            coordinates = []
            for i, field_value in enumerate(fields_values[:-1]):
                if i == 0:
                    point_name = str(field_value.split('=')[1])
                else:
                    value = float(field_value.split('=')[1])
                    coordinates.append(value)
            points_coordinates[point_name] = coordinates
        return points_coordinates

    def is_point_exist(self,
            coordinate : list,
            content : Union[str, bool] = None,
            ):
        points_coordinates = self.get_points_coordinates(content)
        for id, coord in points_coordinates.items():
            if coord == coordinate:
                return id
        return None
                    
    def add_content_to_table(self, table_key, content):
        curr_content = self.tables_contents.get(table_key, '')
        self.tables_contents[table_key] = curr_content + content
        return None

    def force_length_unit(self,
        content : Union[str, bool] = None,
        ):
        if content is None:
            if self.tables_contents is None:
                self.get_tables_contents()
            table_key = "PROGRAM CONTROL"
            content = self.tables_contents.get(table_key, None)
            if content is None:
                return
        label = 'CurrUnits="'
        init_curr_unit = content.find(label)
        init_unit_index = init_curr_unit + len(label)
        end_unit_index = content[init_unit_index:].find('"') + init_unit_index
        force, length, _ = content[init_unit_index: end_unit_index].split(', ')
        self.force_unit, self.length_unit = force, length
        self.force_units = self.get_force_units(self.force_unit)
        self.length_units = self.get_length_units(self.length_unit)
        return force, length

    def write(self):
        if self.tables_contents is None:
            self.get_tables_contents()
        with open(self.output_f2k_path, 'w') as writer:
            for table_key, content in self.tables_contents.items():
                writer.write(f'\n\nTABLE:  "{table_key}"\n')
                writer.write(content)
            writer.write("\nEND TABLE DATA")
        return None

    def get_force_units(self, force_unit : str):
        '''
        force_unit can be 'N', 'KN', 'Kgf', 'tonf'
        '''
        if force_unit == 'N':
            return dict(N=1, KN=1000, Kgf=9.81, tonf=9810)
        elif force_unit == 'KN':
            return dict(N=.001, KN=1, Kgf=.00981, tonf=9.81)
        elif force_unit == 'Kgf':
            return dict(N=1/9.81, KN=1000/9.81, Kgf=1, tonf=1000)
        elif force_unit == 'tonf':
            return dict(N=.000981, KN=.981, Kgf=.001, tonf=1)
        else:
            raise KeyError

    def get_length_units(self, length_unit : str):
        '''
        length_unit can be 'mm', 'cm', 'm'
        '''
        if length_unit == 'mm':
            return dict(mm=1, cm=10, m=1000)
        elif length_unit == 'cm':
            return dict(mm=.1, cm=1, m=100)
        elif length_unit == 'm':
            return dict(mm=.001, cm=.01, m=1)
        else:
            raise KeyError


class CreateF2kFile(Safe):
    '''
    load_cases : load cases that user wants to imported in f2k file
    case_types : load case types that user wants to import in f2k file
    '''
    def __init__(self,
            input_f2k,
            etabs = None,
            load_cases : list = None,
            case_types : list = None,
            model_datum : float = None,
            ):
        input_f2k.touch()
        super().__init__(input_f2k)
        if etabs is None:
            from etabs_api import etabs_obj
            etabs = etabs_obj.EtabsModel(backup=False)
        self.etabs = etabs
        self.etabs.set_current_unit('N', 'mm')
        if model_datum is None:
            model_datum = self.etabs.story.get_base_name_and_level()[1]
        self.model_datum = model_datum
        if load_cases is None:
            load_cases = self.etabs.load_cases.get_load_cases()
        self.load_cases = load_cases
        if case_types is None:
            case_types = ['LinStatic']
        self.case_types = case_types
        self.initiate()

    def initiate(self):
        table_key = "PROGRAM CONTROL"
        content = f'ProgramName="SAFE 2014"   Version=14.0.0   ProgLevel="Post Tensioning"   CurrUnits="N, mm, C"  ModelDatum={self.model_datum}\n'
        self.tables_contents = dict()
        self.tables_contents[table_key] =  content

    def add_grids(self):
        table_key = 'Grid Definitions - Grid Lines'
        cols = ['LineType', 'ID', 'Ordinate']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        filt = df.LineType.isin(('X (Cartesian)', 'Y (Cartesian)'))
        df = df.loc[filt]
        replacements = {
            'X (Cartesian)' : 'X',
            'Y (Cartesian)' : 'Y',
            }
        df.replace({'LineType' : replacements}, inplace=True)
        df.insert(loc=0, column='CoordSys', value='CoordSys=GLOBAL')
        df['ID'] = '"' +  df['ID'] + '"'
        d = {
            'LineType': 'AxisDir=',
            'ID': 'GridID=',
            'Ordinate' : 'Ordinate='
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "GRID LINES"
        self.add_content_to_table(table_key, content)
        return content

    def add_point_coordinates(self):
        base_name = self.etabs.story.get_base_name_and_level()[0]
        table_key = 'Objects and Elements - Joints'
        cols = ['ElmName', 'GlobalX', 'GlobalY', 'GlobalZ', 'Story']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        filt = df['Story'] == base_name
        df = df.loc[filt]
        df['Story'] = "SpecialPt=Yes"
        d = {'ElmName' : 'Point=', 'GlobalX': 'GlobalX=', 'GlobalY': 'GlobalY=', 'GlobalZ': 'GlobalZ=', }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "OBJECT GEOMETRY - POINT COORDINATES"
        self.add_content_to_table(table_key, content)
        return content

    def add_load_patterns(self):
        self.etabs.load_patterns.select_all_load_patterns()
        table_key = 'Load Pattern Definitions'
        cols = ['Name', 'Type', 'SelfWtMult']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        # remove drift load patterns
        filt = df['Type'] == 'Seismic (Drift)'
        df = df.loc[~filt]
        # drift_names = df.loc[filt]['Name'].unique()
        df['Type'] = df.Name.apply(get_design_type, args=(self.etabs,))
        df.dropna(inplace=True)
        # add load cases ! with 2 or more load patterns. Safe define
        # this load cases in load patterns!
        load_pats = list(df.Name.unique())
        all_load_cases = self.etabs.SapModel.LoadCases.GetNameList()[1]
        load_cases = set(all_load_cases).difference(load_pats)
        import pandas as pd
        for load_case in load_cases:
            try:
                loads = self.etabs.SapModel.LoadCases.StaticLinear.GetLoads(load_case)
                n = loads[0]
                if n > 1:
                    type_ = get_design_type(load_case, self.etabs)
                    if type_ is None:
                        continue
                    load_pats = pd.Series([load_case, type_, 0], index=df.columns)
                    df = df.append(load_pats, ignore_index=True)
            except IndexError:
                pass
        d = {
            'Name': 'LoadPat=',
            'Type': 'Type=',
            'SelfWtMult': 'SelfWtMult=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD PATTERNS"
        self.add_content_to_table(table_key, content)
        return content

    def add_loadcase_general(self):
        table_key = 'Load Case Definitions - Summary'
        cols = ['Name', 'Type']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        filt = df['Type'].isin(('Linear Static',))
        df = df.loc[filt]
        df['DesignType'] = df.Name.apply(get_design_type, args=(self.etabs,))
        df.dropna(inplace=True)
        replacements = {
            'Linear Static' : 'LinStatic',
            # 'Response Spectrum' : 'LinRespSpec',
            # 'Modal - Eigen' : 'LinModal',
            }
        df.replace({'Type' : replacements}, inplace=True)
        d = {
            'Name': 'LoadCase=',
            'Type': 'Type=',
            'DesignType' : 'DesignType='
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD CASES 01 - GENERAL"
        self.add_content_to_table(table_key, content)
        return content
    
    def add_modal_loadcase_definitions(self):
        table_key = 'Modal Case Definitions - Eigen'
        cols = ['Name', 'MaxModes', 'MinModes']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        df.dropna(inplace=True)
        df['InitialCond'] = 'Zero'
        df['ModeType'] = 'Eigen'
        d = {
            'Name': 'LoadCase=',
            'MaxModes' : 'MaxModes=',
            'MinModes' : 'MinModes=',
            'InitialCond' : 'InitialCond=',
            'ModeType' : 'ModeType=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD CASES 04 - MODAL"
        self.add_content_to_table(table_key, content)
        return content
    
    def add_loadcase_definitions(self):
        table_key = 'Load Case Definitions - Linear Static'
        cols = ['Name', 'LoadName', 'LoadSF']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        drifts = self.etabs.load_patterns.get_drift_load_pattern_names()
        if drifts:
            filt = df['LoadName'].isin(drifts)
            df = df.loc[~filt]
            filt = df['Name'].isin(drifts)
            df = df.loc[~filt]
        df.dropna(inplace=True)
        d = {
            'Name': 'LoadCase=',
            'LoadName': 'LoadPat=',
            'LoadSF' : 'SF='
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD CASES 06 - LOADS APPLIED"
        self.add_content_to_table(table_key, content)
        return content
    
    def add_point_loads(self):
        self.etabs.load_cases.select_all_load_cases()
        table_key = "Joint Design Reactions"
        cols = ['Label', 'UniqueName', 'OutputCase', 'CaseType', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        drift_names = self.etabs.load_patterns.get_drift_load_pattern_names()
        filt = df.OutputCase.isin(drift_names)
        df = df.loc[~filt]
        filt = df.CaseType == 'LinStatic'
        df = df.loc[filt]
        df.UniqueName.fillna(df.Label, inplace=True)
        df.drop(columns=['Label', 'CaseType'], inplace=True)
        for col in ('FX', 'FY', 'MX', 'MY', 'MZ'):
            df[col] = -df[col].astype(float)
        df['xim'] = 'XDim=0'
        df['yim'] = 'YDim=0'
        d = {
            'UniqueName': 'Point=',
            'OutputCase': 'LoadPat=',
            'FX' : 'Fx=',
            'FY' : 'Fy=',
            'FZ' : 'Fgrav=',
            'MX' : 'Mx=',
            'MY' : 'My=',
            'MZ' : 'Mz=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD ASSIGNMENTS - POINT LOADS"
        self.add_content_to_table(table_key, content)
        return content
    
    def add_load_combinations(self):
        self.etabs.load_cases.select_all_load_cases()
        table_key = "Load Combination Definitions"
        cols = ['Name', 'LoadName', 'Type', 'SF']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        df.fillna(method='ffill', inplace=True)
        # design_load_combinations = set()
        # for type_ in ('concrete', 'steel', 'shearwall', 'slab'):
        #     load_combos_names = self.etabs.database.get_design_load_combinations(type_)
        #     if load_combos_names is not None:
        #         design_load_combinations.update(load_combos_names)
        # filt = df['Name'].isin(design_load_combinations)
        filt = df['Type'] == 'Linear Add'
        df = df.loc[filt]
        df.replace({'Type': {'Linear Add': '"Linear Add"'}}, inplace=True)

        d = {
            'Name': 'Combo=',
            'LoadName': 'Load=',
            'Type' : 'Type=',
            'SF' : 'SF=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD COMBINATIONS"
        self.add_content_to_table(table_key, content)
        return content

    def create_f2k(self):
        yield ('Write Points Coordinates ...', 5, 1)
        self.add_point_coordinates()
        self.add_grids()
        yield ('Add Load Patterns ...', 20, 2)
        self.add_load_patterns()
        yield ('Add Load Cases ...', 30, 3)
        self.add_loadcase_general()
        # self.add_modal_loadcase_definitions()
        self.add_loadcase_definitions()
        yield ('Add Loads ...', 50, 4)
        self.add_point_loads()
        yield ('Add Load Combinations ...', 70, 5)
        self.add_load_combinations()
        yield (f'Successfully Write {self.output_f2k_path} ...', 100, 6)
        self.write()

    @staticmethod
    def add_assign_to_fields_of_dataframe(
        df,
        assignment : dict,
        content : bool = True,
        ):
        '''
        adding a prefix to each member of dataframe for example:
        LIVE change to Type=LIVE
        content : if content is True, the string of dataframe return
        '''
        for col, pref in assignment.items():
            df[col] = pref + df[col].astype(str)
        if content:
            return df.to_string(header=False, index=False)
        return df

def get_design_type(case_name, etabs):
    '''
    get a load case name and return design type of it appropriate
    to write in f2k file
    '''
    map_dict = {
        1 : 'DEAD',
        2 : '"SUPER DEAD"',
        3 : 'LIVE',
        4 : '"REDUCIBLE LIVE"',
        5 : 'QUAKE',
        6 : 'WIND',
        7 : 'SNOW',
        8 : 'OTHER',
        11 : 'LIVE',
        37 : None,
    }
    type_num = etabs.SapModel.LoadCases.GetTypeOAPI_1(case_name)[2]
    design_type = map_dict.get(type_num, 'OTHER')
    return design_type

