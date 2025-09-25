from pathlib import Path
import math
from typing import Iterable, Union

import numpy as np

from csi_safe import safe

__all__ = ['CreateF2kFile']


class CreateF2kFile(safe.Safe16):
    '''
    load_cases : load cases that user wants to imported in f2k file
    case_types : load case types that user wants to import in f2k file
    append : if False, it create f2k file from scratch, if True,
                it adds contents to current file
    '''
    def __init__(self,
            input_f2k,
            etabs = None,
            load_cases : list = None,
            case_types : list = None,
            model_datum : float = None,
            append: bool = False,
            ):
        if not append:
            input_f2k.touch()
        super().__init__(input_f2k)
        if etabs is None:
            import etabs_obj
            etabs = etabs_obj.EtabsModel(backup=False)
        self.etabs = etabs
        self.etabs.set_current_unit('N', 'mm')
        if model_datum is None:
            # model_datum = self.etabs.story.get_base_name_and_level()[1]
            model_datum = 0
        self.model_datum = model_datum
        if load_cases is None:
            load_cases = self.etabs.load_cases.get_load_cases()
        self.load_cases = load_cases
        if case_types is None:
            case_types = ['LinStatic']
        self.case_types = case_types
        if append:
            self.get_tables_contents()
        else:
            self.tables_contents = dict()
            self.initiate()

    def initiate(self):
        table_key = "PROGRAM CONTROL"
        content = f'ProgramName="SAFE 2014"   Version=14.0.0   ProgLevel="Post Tensioning"   CurrUnits="N, mm, C"  ModelDatum={self.model_datum}\n'
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
        df['BubbleSize'] = 'BubbleSize=1200'
        d = {
            'LineType': 'AxisDir=',
            'ID': 'GridID=',
            'Ordinate' : 'Ordinate=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "GRID LINES"
        self.add_content_to_table(table_key, content)
        return content

    def add_point_coordinates(self):
        # base_name = self.etabs.story.get_base_name_and_level()[0]
        table_key = 'Objects and Elements - Joints'
        cols = ['ElmName', 'GlobalX', 'GlobalY', 'GlobalZ', 'Story']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        # get reaction joints
        self.etabs.load_cases.select_all_load_cases()
        table_key2 = "Joint Design Reactions"
        cols = ['UniqueName']
        df2 = self.etabs.database.read(table_key2, to_dataframe=True, cols=cols)
        joint_names = df2['UniqueName'].unique()
        filt = df['ElmName'].isin(joint_names)
        df = df.loc[filt]
        df['Story'] = "SpecialPt=Yes"
        df['GlobalZ'] = f'{self.model_datum}'
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
        filt = df['Type'] == self.etabs.seismic_drift_text
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
        filt = df['Type'].isin(('Linear Static', 'Response Spectrum'))
        df = df.loc[filt]
        df['DesignType'] = df.Name.apply(get_design_type, args=(self.etabs,))
        df.dropna(inplace=True)
        # Remove drift dynamic loadcases
        dynamic_drift_loadcases = self.etabs.get_dynamic_drift_loadcases()
        filt = df.Name.isin(dynamic_drift_loadcases)
        df = df.loc[~filt]
        replacements = {
            'Linear Static' : 'LinStatic',
            'Response Spectrum' : 'LinStatic',
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
    
    def add_response_spectrum_loadcases_and_loadpatts(self):
        lcs = self.etabs.load_cases.get_response_spectrum_loadcase_name()
        dynamic_drift_loadcases = self.etabs.get_dynamic_drift_loadcases()
        content_loadcase = ''
        content_loadpatts = ''
        for lc in lcs:
            if not lc in dynamic_drift_loadcases:
                content_loadcase += f"\nLoadCase={lc}\tLoadPat={lc}\tSF=1"
                content_loadpatts += f"\nLoadPat={lc}\tType=QUAKE\tSelfWtMult=0"
        table_key = "LOAD CASES 06 - LOADS APPLIED"
        self.add_content_to_table(table_key, content_loadcase)
        table_key = "LOAD PATTERNS"
        self.add_content_to_table(table_key, content_loadpatts)
        return content_loadcase
        
    def add_point_loads(self, append: bool = True):
        self.etabs.load_cases.select_all_load_cases()
        self.etabs.run_analysis()
        table_key = "Joint Design Reactions"
        cols = ['Label', 'UniqueName', 'OutputCase', 'CaseType', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        drift_names = self.etabs.load_patterns.get_drift_load_pattern_names()
        dynamic_drift_loadcases = self.etabs.get_dynamic_drift_loadcases()
        drift_names.extend(dynamic_drift_loadcases)
        filt = df.OutputCase.isin(drift_names)
        df = df.loc[~filt]
        filt = df.CaseType.isin(('LinStatic', 'LinRespSpec'))
        df = df.loc[filt]
        df.UniqueName.fillna(df.Label, inplace=True)
        df.drop(columns=['Label', 'CaseType'], inplace=True)
        for col in ('FX', 'FY', 'MX', 'MY', 'MZ'):
            df[col] = -df[col].astype(float)
        try:
            df2 = self.etabs.database.get_basepoints_coord_and_dims(df)
            df2 = df2.set_index('UniqueName')
            df['xdim'] = df['UniqueName'].map(df2['t2'])
            df['ydim'] = df['UniqueName'].map(df2['t3'])
            # Replace None values with 0 in specific columns
            columns_to_replace = ['xdim', 'ydim']
            df[columns_to_replace] = df[columns_to_replace].fillna(0)
        except (AttributeError, TypeError):
            df['xdim'] = 0
            df['ydim'] = 0
        d = {
            'UniqueName': 'Point=',
            'OutputCase': 'LoadPat=',
            'FX'  : 'Fx=',
            'FY'  : 'Fy=',
            'FZ'  : 'Fgrav=',
            'MX'  : 'Mx=',
            'MY'  : 'My=',
            'MZ'  : 'Mz=',
            'xdim' : 'XDim=',
            'ydim' : 'YDim=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD ASSIGNMENTS - POINT LOADS"
        self.add_content_to_table(table_key, content, append=append)
        return content
    
    def add_load_combinations(
                self,
                types: Iterable = [],
                load_combinations: Union[list, bool] = None,
                ignore_dynamics : bool = False,
        ):
        if not types:
            types = self.etabs.load_combinations.combotyp._member_names_
            types = [t.replace('_', ' ') for t in types]
        self.etabs.load_cases.select_all_load_cases()
        df = self.etabs.load_combinations.get_table_of_load_combinations()
        df.fillna(method='ffill', inplace=True)
        # remove dynamic load combinations
        if ignore_dynamics:
            response_spectrum_loadcases = self.etabs.load_cases.get_loadcase_withtype(4)
            if response_spectrum_loadcases:
                filt = df['LoadName'].isin(response_spectrum_loadcases)
                load_combinations_with_dynamic = df['Name'].loc[filt].unique()
                filt = df['Name'].isin(load_combinations_with_dynamic)
                df = df.loc[~filt]
        filt = df['Type'].isin(types)
        df = df.loc[filt]
        if load_combinations is not None:
            filt = df['Name'].isin(tuple(load_combinations))
            df = df.loc[filt]
        df.replace({'Type': {'Linear Add': '"Linear Add"'}}, inplace=True)
        load_combos_names = self.etabs.database.get_design_load_combinations("concrete")
        if not load_combos_names:
            load_combos_names = self.etabs.database.get_design_load_combinations("steel")
        if not load_combos_names:
            load_combos_names = self.etabs.database.get_design_load_combinations("shearwall")
        if load_combos_names:
            df['strength'] = np.where(df['Name'].isin(load_combos_names), 'Yes', 'No')
        else:
            df['strength'] = 'No'

        d = {
            'Name': 'Combo=',
            'LoadName': 'Load=',
            'Type' : 'Type=',
            'SF' : 'SF=',
            'strength' : 'DSStrength=',
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
        self.add_response_spectrum_loadcases_and_loadpatts()
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
    
class ModifyF2kFile(CreateF2kFile):
    def __init__(self,
            input_f2k,
            etabs = None,
            load_cases : list = None,
            case_types : list = None,
            model_datum : float = None,
            ):
        append = True
        super().__init__(input_f2k, etabs, load_cases, case_types, model_datum, append)
    def set_unit_of_model_according_to_f2k(self):
        force, length = self.force_length_unit()
        self.etabs.set_current_unit(force, length)

    def add_point_loads(self):
        #  set units of model according to f2k file
        self.set_unit_of_model_according_to_f2k()
        self.etabs.load_cases.select_all_load_cases()
        self.etabs.run_analysis()
        table_key = "Joint Design Reactions"
        cols = ['Label', 'UniqueName', 'OutputCase', 'CaseType', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        drift_names = self.etabs.load_patterns.get_drift_load_pattern_names()
        dynamic_drift_loadcases = self.etabs.get_dynamic_drift_loadcases()
        drift_names.extend(dynamic_drift_loadcases)
        filt = df.OutputCase.isin(drift_names)
        df = df.loc[~filt]
        filt = df.CaseType.isin(('LinStatic', 'LinRespSpec'))
        df = df.loc[filt]
        df.UniqueName.fillna(df.Label, inplace=True)
        df.drop(columns=['Label', 'CaseType'], inplace=True)
        for col in ('FX', 'FY', 'MX', 'MY', 'MZ'):
            df[col] = -df[col].astype(float)
        try:
            df2 = self.etabs.database.get_basepoints_coord_and_dims(df)
            df2 = df2.set_index('UniqueName')
            df['xdim'] = df['UniqueName'].map(df2['t2'])
            df['ydim'] = df['UniqueName'].map(df2['t3'])
            # Replace None values with 0 in specific columns
            columns_to_replace = ['xdim', 'ydim']
            df[columns_to_replace] = df[columns_to_replace].fillna(0)
        except (AttributeError, TypeError):
            df['xdim'] = 0
            df['ydim'] = 0
        df = df.astype({'UniqueName': str})
        # check if point exist in model, if not add it
        exist_points = {}
        not_exist_points_content = ''
        curr_point_content = self.get_points_contents()
        for p in df.UniqueName.unique():
            coord = list(self.etabs.points.get_point_coordinate(str(p)))
            coord[2] = self.model_datum
            self.model_datum
            print(coord)
            exist_id = self.is_point_exist(coord, curr_point_content)
            if exist_id:
                exist_points[p] = exist_id
            else:
                last_number = self.get_last_point_number(curr_point_content + not_exist_points_content)
                exist_points[p] = str(last_number)
                not_exist_points_content += f'\nPoint={last_number}   GlobalX={coord[0]}   GlobalY={coord[1]}   GlobalZ={coord[2]}   SpecialPt=Yes'
        if not_exist_points_content:
            table_key = "OBJECT GEOMETRY - POINT COORDINATES"
            self.add_content_to_table(table_key, not_exist_points_content, append=True)

        df['UniqueName'] = df['UniqueName'].map(exist_points).fillna(df['UniqueName'])
        d = {
            'UniqueName': 'Point=',
            'OutputCase': 'LoadPat=',
            'FX'  : 'Fx=',
            'FY'  : 'Fy=',
            'FZ'  : 'Fgrav=',
            'MX'  : 'Mx=',
            'MY'  : 'My=',
            'MZ'  : 'Mz=',
            'xdim' : 'XDim=',
            'ydim' : 'YDim=',
            }
        content = self.add_assign_to_fields_of_dataframe(df, d)
        table_key = "LOAD ASSIGNMENTS - POINT LOADS"
        self.add_content_to_table(table_key, content, append=False)
        return content
        

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

