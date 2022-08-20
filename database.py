from pathlib import Path
import sys
from typing import Iterable, Union

import pandas as pd
pd.options.mode.chained_assignment = None


__all__ = ['DatabaseTables']

class DatabaseTables:
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

    @staticmethod
    def reshape_data(FieldsKeysIncluded, table_data):
        n = len(FieldsKeysIncluded)
        data = [list(table_data[i:i+n]) for i in range(0, len(table_data), n)]
        return data

    @staticmethod
    def reshape_data_to_df(
                FieldsKeysIncluded,
                table_data,
                cols:list=None,
                ) -> 'pandas.DataFrame':
        n = len(FieldsKeysIncluded)
        data = [list(table_data[i:i+n]) for i in range(0, len(table_data), n)]
        df = pd.DataFrame(data, columns=FieldsKeysIncluded)
        if cols is not None:
            df = df[cols]
        return df

    def table_exist(self, table_key):
        all_table = self.SapModel.DatabaseTables.GetAvailableTables()[1]
        if table_key in all_table:
            return True
        return False

    def read(self,
                table_key : str,
                to_dataframe : bool = False,
                cols : list = None,
                ):
        ret = self.read_table(table_key)
        if not ret:
            return None
        _, _, fields, _, data, _ = ret
        if fields[0] is None:
            return None
        if to_dataframe:
            data = self.reshape_data_to_df(fields, data, cols)
        else:
            data = self.reshape_data(fields, data)
        return data

    @staticmethod
    def unique_data(data):
        table_data = []
        for i in data:
            table_data += i
        return table_data

    @staticmethod
    def get_fields_and_data_from_dataframe(df):
        fields = list(df.columns)
        data = list(df.values.reshape(1, df.size)[0])
        return fields, data

    def apply_data(self,
            table_key : str,
            data : Union[list, pd.core.frame.DataFrame],
            fields : Union[list, tuple, bool] = None,
            ) -> None:
        if type(data) == pd.core.frame.DataFrame:
            if fields is None:
                fields, data = self.get_fields_and_data_from_dataframe(data)
            else:
                if len(data.columns) == len(fields):
                    _, data = self.get_fields_and_data_from_dataframe(data)
                else:
                    return False
        self.SapModel.DatabaseTables.SetTableForEditingArray(table_key, 0, fields, 0, data)
        self.apply_table()
        return True

    def apply_table(self):
        if self.SapModel.GetModelIsLocked():
            self.SapModel.SetModelIsLocked(False)
        FillImportLog = True
        NumFatalErrors = 0
        NumErrorMsgs = 0
        NumWarnMsgs = 0
        NumInfoMsgs = 0
        ImportLog = ''
        [NumFatalErrors, NumErrorMsgs, NumWarnMsgs, NumInfoMsgs, ImportLog,
            ret] = self.SapModel.DatabaseTables.ApplyEditedTables(FillImportLog, NumFatalErrors,
                                                            NumErrorMsgs, NumWarnMsgs, NumInfoMsgs, ImportLog)
        return NumFatalErrors, ret

    def read_table(self, table_key):
        GroupName = table_key
        FieldKeyList = []
        TableVersion = 0
        FieldsKeysIncluded = []
        NumberRecords = 0
        TableData = []
        if not self.table_exist(table_key):
            return None
        return self.SapModel.DatabaseTables.GetTableForDisplayArray(table_key, FieldKeyList, GroupName, TableVersion, FieldsKeysIncluded, NumberRecords, TableData)

    @staticmethod
    def remove_df_columns(df,
            columns : Iterable = ('GUID', 'Notes'),
            ):
        for col in columns:
            if col in df.columns:
                del df[col]

    def write_seismic_user_coefficient(self, TableKey, FieldsKeysIncluded, TableData):
        FieldsKeysIncluded1 = ['Name', 'Is Auto Load', 'X Dir?', 'X Dir Plus Ecc?', 'X Dir Minus Ecc?',
                            'Y Dir?', 'Y Dir Plus Ecc?', 'Y Dir Minus Ecc?',
                            'Ecc Ratio', 'Top Story', 'Bottom Story',
                            ]
        if len(FieldsKeysIncluded) == len(FieldsKeysIncluded1) + 2:
            FieldsKeysIncluded1.extend(['C', 'K'])
        else:
            FieldsKeysIncluded1.extend(['Ecc Overwrite Story', 'Ecc Overwrite Diaphragm',
            'Ecc Overwrite Length', 'C', 'K'])
        assert len(FieldsKeysIncluded) == len(FieldsKeysIncluded1)
        self.SapModel.DatabaseTables.SetTableForEditingArray(TableKey, 0, FieldsKeysIncluded1, 0, TableData)
        NumFatalErrors, ret = self.apply_table()
        return NumFatalErrors, ret

    def expand_seismic_load_patterns(self,
        equal_names : dict = {
            'XDir' : 'EX',
            'XDirPlusE' : 'EPX',
            'XDirMinusE' : 'ENX',
            'YDir' : 'EY',
            'YDirPlusE' : 'EPY',
            'YDirMinusE' : 'ENY',
            },
            replace_ex : bool = False,
            replace_ey : bool = False,
            drift_prefix : str = '',
            drift_suffix : str = '_DRIFT',
            ):
        self.etabs.unlock_model()
        self.etabs.lock_and_unlock_model()
        self.etabs.load_patterns.select_all_load_patterns()
        drift_load_names = self.etabs.load_patterns.get_drift_load_pattern_names()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        df = self.read(table_key, to_dataframe=True)
        # remove aj applied
        filt = df['XDir'].isin(('Yes', 'No'))
        df = df.loc[filt]
        self.remove_df_columns(df, ('OverStory', 'OverDiaph', 'OverEcc'))
        # obtain multi assign loads
        d = {'Yes' : 1, 'No' : 0}
        cols = list(equal_names.keys())
        for col in cols:
            df[col] = df[col].map(d)
        filt_multi = (df[cols].sum(axis=1) > 1)
        if not True in filt_multi.values:
            return None
        df_multi = df.loc[filt_multi]
        # search for existence of EX and EY
        filt_ex = ~((df['XDir'] == 1) & (df[cols].sum(axis=1) == 1))
        is_ex = False in filt_ex.values
        filt_ey = ~((df['YDir'] == 1) & (df[cols].sum(axis=1) == 1))
        is_ey = False in filt_ey.values
        if replace_ex:
            df = df.loc[filt_ex]
        if replace_ey:
            filt = ~((df['YDir'] == 1) & (df[cols].sum(axis=1) == 1))
            df = df.loc[filt]
        additional_rows = []
        import copy
        multi_load_names = list(df_multi['Name'].values)
        converted_loads = dict.fromkeys(multi_load_names)
        for i, row in df.loc[filt_multi].iterrows():
            name = row['Name']
            load_type = 37 if name in drift_load_names else 5
            for col in cols:
                if row[col] == 1:
                    if all((
                            col == 'XDir',
                            is_ex,
                            load_type == 5,
                            not replace_ex,
                        )) or all((
                            col == 'YDir',
                            is_ey,
                            load_type == 5,
                            not replace_ey,
                        )):
                        continue
                    load_name = equal_names[col]
                    if name in drift_load_names:
                        load_name = f'{drift_prefix}{load_name}{drift_suffix}'
                    new_row = copy.deepcopy(row)
                    new_row[cols] = 0
                    new_row[col] = 1
                    new_row['Name'] = load_name
                    additional_rows.append(new_row)
                    if converted_loads[name] is None:
                        converted_loads[name] = [(load_name, load_type)]
                    else:
                        converted_loads[name].append((load_name, load_type))
                    self.SapModel.LoadPatterns.Add(load_name, load_type, 0, False)

        df_expanded = pd.DataFrame.from_records(additional_rows, columns=df.columns)
        # remove ex or ey if replace
        if replace_ex and replace_ey:
            filt = ~((filt_ex == False) | (filt_ey == False))
        elif replace_ex:
            filt = filt_ex
        elif replace_ey:
            filt = filt_ey
        if replace_ex or replace_ey:
            df = df.loc[filt]
        filt = ~(df['Name'].isin(multi_load_names))
        df = df.loc[filt]
        df = df.append(df_expanded)
        d = {1: 'Yes', 0: 'No'}
        for col in cols:
            df[col] = df[col].map(d)
        return df, converted_loads


    def expand_loadcases(self,
            loads_expanded : Union[dict, bool] = None,
            ):
        if loads_expanded is None:
            ret = self.expand_seismic_load_patterns()
            if ret is None:
                return
            loads_expanded = ret[1]
        zip_loadpatterns = list(loads_expanded.keys())
        table_key = 'Load Case Definitions - Linear Static'
        loadcases_df = self.read(table_key, to_dataframe=True)
        self.remove_df_columns(loadcases_df)
        filt = loadcases_df['LoadName'].isin(zip_loadpatterns)
        loadcases_include_zip_loadpatterns = list(loadcases_df.loc[filt]['Name'])
        filt = ~(loadcases_df['Name'].isin(loadcases_include_zip_loadpatterns))
        new_loadcase_df = loadcases_df.loc[filt]
        zip_loadcases = dict()
        for loadcase in loadcases_include_zip_loadpatterns:
            filt = loadcases_df['Name'] == loadcase
            zip_df = loadcases_df.loc[filt]
            load_names = list(zip_df['LoadName'])
            for zip_loadpat, expand_loaded in loads_expanded.items():
                if zip_loadpat in load_names:
                    for i, (load, load_type) in enumerate(expand_loaded):
                        append_df = zip_df.replace(zip_loadpat, load)
                        scale_factor_name = append_df['LoadSF'].str.replace('1', '') + append_df['LoadName']
                        names = scale_factor_name.to_list()
                        new_names = [names[0]]
                        for name in names[1:]:
                            new_names.append(name) if name.startswith('-') else new_names.append(f'+{name}')
                        name = ''.join(new_names)
                        append_df['Name'] = name
                        new_loadcase_df = new_loadcase_df.append(append_df)
                        # if load_type == 5:
                        if i == 0:
                            zip_loadcases[loadcase] = [name]
                        else:
                            zip_loadcases[loadcase].append(name)
        return new_loadcase_df, zip_loadcases

    def expand_linear_loadcombos(self,
            loads_expanded : Union[dict, bool] = None,
            loadcombos_df : Union[pd.DataFrame, bool] = None,
            ):
        if loads_expanded is None:
            ret = self.expand_loadcases()
            if ret is None:
                return
            loads_expanded = ret[1]
        zip_loadcases = list(loads_expanded.keys())
        if loadcombos_df is None:
            table_key = 'Load Combination Definitions'
            loadcombos_df = self.read(table_key, to_dataframe=True)
        self.remove_df_columns(loadcombos_df, ('GUID',))
        # remove envelop combos, because envelopes not to be iterate, must be add
        envelop_combos = list(loadcombos_df[loadcombos_df['Type'] == 'Envelope']['Name'])
        filt_envelope = loadcombos_df['Name'].isin(envelop_combos)
        new_loadcombo_df = loadcombos_df.loc[~filt_envelope]
        filt = new_loadcombo_df['LoadName'].isin(zip_loadcases)
        loadcombos_include_zip_loadcases = list(new_loadcombo_df.loc[filt]['Name'].unique())
        filt = ~(new_loadcombo_df['Name'].isin(loadcombos_include_zip_loadcases))
        new_loadcombo_df = new_loadcombo_df.loc[filt]
        zip_loadcombos = dict()
        for loadcombo in loadcombos_include_zip_loadcases:
            filt = loadcombos_df['Name'] == loadcombo
            zip_df = loadcombos_df.loc[filt]
            load_names = list(zip_df['LoadName'])
            for zip_loadpat, expand_loaded in loads_expanded.items():
                n = len(expand_loaded)
                if zip_loadpat in load_names:
                    for i, load in enumerate(expand_loaded, start=1):
                        append_df = zip_df.replace(zip_loadpat, load)
                        name = f'{loadcombo}({i}/{n})'
                        append_df['Name'] = name
                        new_loadcombo_df = new_loadcombo_df.append(append_df)
                        # if load_type == 5:
                        if i == 1:
                            zip_loadcombos[loadcombo] = [name]
                        else:
                            zip_loadcombos[loadcombo].append(name)
        return new_loadcombo_df, zip_loadcombos

    def expand_envelop_loadcombos(self,
            loads_expanded : Union[dict, bool] = None,
            loadcombos_df : Union[pd.DataFrame, bool] = None,
            ):
        if loads_expanded is None:
            ret = self.expand_loadcases()
            if ret is None:
                return
            loads_expanded = ret[1]
        zip_loadcases = list(loads_expanded.keys())
        if loadcombos_df is None:
            table_key = 'Load Combination Definitions'
            loadcombos_df = self.read(table_key, to_dataframe=True)
        self.remove_df_columns(loadcombos_df, ('GUID',))
        # remove envelop combos, because envelopes not to be iterate, must be add
        envelop_combos = list(loadcombos_df[loadcombos_df['Type'] == 'Envelope']['Name'])
        filt_envelope = loadcombos_df['Name'].isin(envelop_combos)
        new_loadcombo_df = loadcombos_df.loc[filt_envelope]
        filt = new_loadcombo_df['LoadName'].isin(zip_loadcases)
        df_loadcombos_include_zip_loadcases = new_loadcombo_df.loc[filt]
        df_loadcombos_not_include_zip_loadcases = new_loadcombo_df.loc[~filt]
        df_loadcombos_include_zip_loadcases.loc[:, 'LoadName'] = df_loadcombos_include_zip_loadcases.loc[:, 'LoadName'].map(loads_expanded)
        df_loadcombos_include_zip_loadcases = df_loadcombos_include_zip_loadcases.explode('LoadName')
        df = df_loadcombos_not_include_zip_loadcases.append(df_loadcombos_include_zip_loadcases)
        return df

    def expand_loadcombos(self,
            convert_loadcases : dict):
        df_linear_combos, convert_lcombos = self.expand_linear_loadcombos(convert_loadcases)
        additional_convert_lcombos = convert_lcombos.copy()
        while additional_convert_lcombos:
            df_linear_combos, additional_convert_lcombos = self.expand_linear_loadcombos(additional_convert_lcombos, df_linear_combos)
            convert_lcombos.update(additional_convert_lcombos)
        df_envelop_combos = self.expand_envelop_loadcombos(convert_lcombos)
        df = df_linear_combos.append(df_envelop_combos)
        return df, convert_lcombos

    def expand_design_combos(self,
            convert_loadcombos : dict,
            ):
        expanded_dfs = dict()
        table_keys = {
            'concrete': 'Concrete Frame Design Load Combination Data',
            'steel': 'Steel Design Load Combination Data',
            'shearwall': 'Shear Wall Design Load Combination Data',
            'slab': 'Concrete Slab Design Load Combination Data',
        }
        for type_ in ('concrete', 'steel', 'shearwall', 'slab'):
            table_key = table_keys[type_]
            df = self.expand_table(table_key, convert_loadcombos, 'ComboName')
            if df is not None:
                expanded_dfs[table_key] = df
        return expanded_dfs

    def set_expand_seismic_load_patterns(self,
            df : pd.core.frame.DataFrame,
            converted_loads : dict,
            ):
        fields, data = self.get_fields_and_data_from_dataframe(df)
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        self.write_seismic_user_coefficient(table_key, fields, data)
        # remove multi loadpat
        table_key = 'Load Pattern Definitions'
        dflp = self.read(table_key, to_dataframe=True)
        multi_load_names = list(converted_loads.keys())
        filt = ~(dflp.Name.isin(multi_load_names))
        dflp = dflp.loc[filt]
        self.apply_data(table_key, dflp)

    def set_expand_loadcases(self,
            df : pd.core.frame.DataFrame,
            converted_loadcases : dict,
            ):
        table_key = 'Load Case Definitions - Summary'
        df_loadcases_summary = self.read(table_key, to_dataframe=True)
        self.remove_df_columns(df_loadcases_summary)
        df_loadcases_summary = self.expand_table(df_loadcases_summary, converted_loadcases, 'Name')
        self.apply_data(table_key, df_loadcases_summary)
        table_key = 'Load Case Definitions - Linear Static'
        equal_fields = {
            'Name' : 'Name',
            'Group' : 'Exclude Group',
            'MassSource' : 'Mass Source',
            'StiffType' : 'Stiffness Type',
            'LoadType' : 'Load Type',
            'LoadName' : 'Load Name',
            'LoadSF' : 'LoadSF',
            'DesignType' : 'Design Type',
            'UserDesType' : 'User Design Type',
            }
        etabs_fields = []
        fields = []
        for col in df.columns:
            field = equal_fields.get(col, None)
            if field:
                etabs_fields.append(field)
                fields.append(col)
        df = df[fields]
        # fields = ('Name', 'Exclude Group', 'Mass Source', 'Stiffness Type', 'Load Type', 'Load Name', 'Load SF', 'Design Type', 'User Design Type')
        # df = df[['Name', 'Group', 'MassSource', 'StiffType', 'LoadType', 'LoadName', 'LoadSF', 'DesignType', 'UserDesType']]
        ret = self.apply_data(table_key, df, etabs_fields)
        if not ret:
            all_loadcases = list(df['Name'].unique())
            for loadcase in all_loadcases:
                temp_df = df.loc[df['Name'] == loadcase]
                lcs = tuple(temp_df['LoadName'])
                n = len(lcs)
                lsf = tuple(temp_df['LoadSF'])
                lsf = [float(i) for i in lsf]
                self.SapModel.LoadCases.StaticLinear.SetLoads(loadcase, n, n * ('Load',), lcs, lsf)

    def set_expand_load_combinations(self,
        df : pd.DataFrame,
        ):
        table_key = 'Load Combination Definitions'
        fields = ('Name', 'Type', 'Is Auto', 'Load Name', 'SF', 'Notes')
        df = df[['Name', 'Type', 'IsAuto', 'LoadName', 'SF', 'Notes']]
        ret = self.apply_data(table_key, df, fields)
        if not ret:
            all_loadcases = self.etabs.load_cases.get_load_cases()
            for _, row in df.iterrows():
                name = row['Name']
                loadname = row['LoadName']
                type_ = 1
                if loadname in all_loadcases:
                    type_ = 0
                scale_factor = float(row['SF'])
                self.SapModel.RespCombo.SetCaseList(name, type_, loadname, scale_factor)

    def apply_expand_design_combos(self,
            expanded_tables : dict,
            ):
        for table_key, df in expanded_tables.items():
            if len(df.columns) == 3:
                fields = ('Design Type', 'Combo Type', 'Combo Name')
            elif len(df.columns) == 2:
                fields = ('Combo Type', 'Combo Name')
            self.apply_data(table_key, df, fields)

    def expand_loads(self,
        equal_names : dict = {
            'XDir' : 'EX',
            'XDirPlusE' : 'EPX',
            'XDirMinusE' : 'ENX',
            'YDir' : 'EY',
            'YDirPlusE' : 'EPY',
            'YDirMinusE' : 'ENY',
            },
            replace_ex : bool = False,
            replace_ey : bool = False,
            drift_prefix : str = '',
            drift_suffix : str = '_DRIFT',
            ):
        yield ("Get expanding seismic load patterns ...", 5)
        ret = self.expand_seismic_load_patterns(equal_names, replace_ex, replace_ey, drift_prefix, drift_suffix)
        if ret is None:
            yield ('There is No zip load pattern in this Model.', 100)
            return False
        dflp, convert_lps = ret
        yield ("Get expanding load cases ...", 15)
        dflc, convert_lcs = self.expand_loadcases(convert_lps)
        yield ("Get expanding load combinations ...", 25)
        df_loadcombo, convert_lcombos = self.expand_loadcombos(convert_lcs)
        yield ("Get expanding Design load combinations ...", 35)
        expanded_design_tables = self.expand_design_combos(convert_lcombos)
        yield ("Apply expanding  seismic load patterns ...", 45)
        self.set_expand_seismic_load_patterns(dflp, convert_lps)
        yield ("Apply expanding load cases ...", 60)
        self.set_expand_loadcases(dflc, convert_lcs)
        yield ("Apply expanding load combinations ...", 70)
        self.set_expand_load_combinations(df_loadcombo)
        yield ("Apply expanding Design load combinations ...", 90)
        self.apply_expand_design_combos(expanded_design_tables)
        yield ("Expanding Load Patterns Finished ...", 100)
        yield True

    def expand_table(self,
            df : Union[pd.DataFrame, str],
            expand : dict,
            col_name : str,
            ):
        expand_keys = list(expand.keys())
        if type(df) == str:
            df = self.read(df, to_dataframe=True)
            if df is None:
                return
        filt = df[col_name].isin(expand_keys)
        df_include = df[filt]
        df_not_include = df[~filt]
        df_include.loc[:, col_name] = df_include.loc[:, col_name].map(expand)
        df_include = df_include.explode(col_name)
        new_df = df_not_include.append(df_include)
        return new_df

    def get_story_mass(self):
        self.etabs.set_current_unit('kgf', 'm')
        self.etabs.run_analysis()
        TableKey = 'Centers Of Mass And Rigidity'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.read_table(TableKey)
        data = self.reshape_data(FieldsKeysIncluded, TableData)
        i_mass_x = FieldsKeysIncluded.index('MassX')
        # i_mass_y = FieldsKeysIncluded.index('MassY')
        i_story = FieldsKeysIncluded.index('Story')
        story_mass = []
        for row in data[::-1]:
            story = row[i_story]
            massx = row[i_mass_x]
            # massy = data[i_mass_y]
            story_mass.append([story, massx])
        return story_mass

    def write_aj_user_coefficient(self, table_key, input_df, df):
        if len(df) == 0: return
        FieldsKeysIncluded1 = ['Name', 'Is Auto Load', 'X Dir?', 'X Dir Plus Ecc?', 'X Dir Minus Ecc?',
                            'Y Dir?', 'Y Dir Plus Ecc?', 'Y Dir Minus Ecc?',
                            'Ecc Ratio', 'Top Story', 'Bot Story', 'Ecc Overwrite Story',
                            'Ecc Overwrite Diaphragm', 'Ecc Overwrite Length', 'C', 'K'
                            ]
        extra_fields = ('OverStory', 'OverDiaph', 'OverEcc')
        if input_df.shape[1] < len(FieldsKeysIncluded1):
            i_ecc_ow_story = FieldsKeysIncluded1.index('Ecc Overwrite Story')
            indexes = range(i_ecc_ow_story, i_ecc_ow_story + 3)
            for i, header in zip(indexes, extra_fields):
                input_df.insert(i, header, None)
        cases = df['OutputCase'].unique()
        input_df['C'] = input_df['C'].astype(str)
        input_df = input_df.loc[input_df['C'] != 'None']
        for field in extra_fields:
            input_df[field] = None
        additional_rows = []
        import copy
        for i, row in input_df.iterrows():
            case = row['Name']
            if case in cases:
                ecc_length = df[
                    (df['OutputCase'] == case)]
                for k, (_, row_aj) in enumerate(ecc_length.iterrows()):
                    story = row_aj['Story']
                    diaph = row_aj['Diaph']
                    length = row_aj['Ecc. Length (Cm)']
                    if k == 0:
                        row['OverStory'] = story
                        row['OverDiaph'] = diaph
                        row['OverEcc'] = str(length)
                    else:
                        new_row = copy.deepcopy(row)
                        new_row[2:] = ''
                        new_row['OverStory'] = story
                        new_row['OverDiaph'] = diaph
                        new_row['OverEcc'] = str(length)
                        additional_rows.append(new_row)
        # input_df = input_df.append(pd.DataFrame.from_records(additional_rows, columns=FieldsKeysIncluded1))
        for row in additional_rows:
            input_df = input_df.append(row)
        self.apply_data(table_key, input_df, FieldsKeysIncluded1)
    
    
    def write_daynamic_aj_user_coefficient(self, df=None):
        if df is None:
            df = self.etabs.get_dynamic_magnification_coeff_aj()
        if len(df) == 0: return
        print("Applying dynamic aj to edb\n")
        loadcases = list(df['OutputCase'].unique())
        self.etabs.load_cases.select_load_cases(loadcases)
        table_key = 'Load Case Definitions - Response Spectrum'
        fields = [
                'Name', 'MassSource', 'LoadName', 'Function', 'TransAccSF',
                'CoordSys', 'Angle', 'ModalCase', 'ModalCombo',
                'DirCombo', 'EccenRatio', 
                ]
        col_map = {
                    'MassSource': 'Mass Source',
                    'LoadName': 'Load Name',
                    'TransAccSF': 'Trans Accel SF',
                    'CoordSys': 'Coordinate System',
                    'ModalCase': 'Modal Case',
                    'ModalCombo': 'Modal Combo Method',
                    'DirCombo': 'Directional Combo Type',
                    'EccenRatio': 'Eccentricity Ratio', 
                    'OverDiaph': 'Diaphragm Overwrite',
                    'OverEccen': 'Eccentricity OverWrite',
                    'OverStory': 'Story Overwrite',
                    }
        df1 = self.read(table_key, to_dataframe=True, cols=fields)
        extra_fields = ('OverStory', 'OverDiaph', 'OverEccen')
        for field in extra_fields:
            df1[field] = None
        df1['Angle'] = df1['Angle'].astype(str)
        df1 = df1.loc[df1['Angle'] != 'None']
        additional_rows = []
        import copy
        for i, row in df1.iterrows():
            case = row['Name']
            if case in loadcases:
                ecc_length = df[
                    (df['OutputCase'] == case)]
                for k, (_, row_aj) in enumerate(ecc_length.iterrows()):
                    story = row_aj['Story']
                    diaph = row_aj['Diaph']
                    length = row_aj['Ecc. Length (Cm)']
                    if k == 0:
                        row['OverStory'] = story
                        row['OverDiaph'] = diaph
                        row['OverEccen'] = str(length)
                    else:
                        new_row = copy.deepcopy(row)
                        new_row[2:] = ''
                        new_row['OverStory'] = story
                        new_row['OverDiaph'] = diaph
                        new_row['OverEccen'] = str(length)
                        additional_rows.append(new_row)
        for row in additional_rows:
            df1 = df1.append(row)
        df1 = df1.rename(col_map, axis=1)
        self.SapModel.SetModelIsLocked(False)
        self.apply_data(table_key, df1)

    def get_center_of_rigidity(self):
        self.etabs.run_analysis()
        self.etabs.set_current_unit('kgf', 'm')
        TableKey = 'Centers Of Mass And Rigidity'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.read_table(TableKey)
        data = self.reshape_data(FieldsKeysIncluded, TableData)
        i_xcr = FieldsKeysIncluded.index('XCR')
        i_ycr = FieldsKeysIncluded.index('YCR')
        i_story = FieldsKeysIncluded.index('Story')
        story_rigidity = {}
        for row in data:
            story = row[i_story]
            x = row[i_xcr]
            y = row[i_ycr]
            story_rigidity[story] = (x, y)
        return story_rigidity

    def get_stories_displacement_in_xy_modes(self):
        f1, _ = self.etabs.save_as('modal_stiffness.EDB')
        story_point = self.etabs.story.add_points_in_center_of_rigidity_and_assign_diph()
        modal = self.etabs.load_cases.get_modal_loadcase_name()
        self.etabs.analyze.set_load_cases_to_analyze(modal)
        self.SapModel.Analyze.RunAnalysis()
        wx, wy, ix, iy = self.etabs.results.get_xy_frequency()
        TableKey = 'Joint Displacements'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.read_table(TableKey)
        data = self.reshape_data(FieldsKeysIncluded, TableData)
        i_story = FieldsKeysIncluded.index('Story')
        i_name = FieldsKeysIncluded.index('UniqueName')
        i_case = FieldsKeysIncluded.index('OutputCase')
        i_steptype = FieldsKeysIncluded.index('StepType')
        i_stepnumber = FieldsKeysIncluded.index('StepNumber')
        i_ux = FieldsKeysIncluded.index('Ux')
        i_uy = FieldsKeysIncluded.index('Uy')
        columns = (i_story, i_name, i_case, i_steptype, i_stepnumber)
        x_results = {}
        for story, point in story_point.items():
            values = (story, point, modal, 'Mode', str(ix))
            result = self.etabs.get_from_list_table(data, columns, values)
            result = list(result)
            assert len(result) == 1
            ux = float(result[0][i_ux])
            x_results[story] = ux
        y_results = {}
        for story, point in story_point.items():
            values = (story, point, modal, 'Mode', str(iy))
            result = self.etabs.get_from_list_table(data, columns, values)
            result = list(result)
            assert len(result) == 1
            uy = float(result[0][i_uy])
            y_results[story] = uy
        self.SapModel.File.OpenFile(str(f1))
        return x_results, y_results, wx, wy

    def multiply_seismic_loads(
            self,
            x: float = .67,
            y=None,
            ):
        if not y:
            y = x
        self.SapModel.SetModelIsLocked(False)
        self.etabs.lock_and_unlock_model()
        self.etabs.load_patterns.select_all_load_patterns()
        TableKey = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.read_table(TableKey)
        data = self.reshape_data(FieldsKeysIncluded, TableData)
        names_x, names_y = self.etabs.load_patterns.get_load_patterns_in_XYdirection()
        i_c = FieldsKeysIncluded.index('C')
        i_name = FieldsKeysIncluded.index("Name")
        for earthquake in data:
            if not earthquake[i_c]:
                continue
            name = earthquake[i_name]
            c = float(earthquake[i_c])
            cx = x * c
            cy = y * c
            if name in names_x:
                earthquake[i_c] = str(cx)
            elif name in names_y:
                earthquake[i_c] = str(cy)
        TableData = self.unique_data(data)
        NumFatalErrors, ret = self.write_seismic_user_coefficient(TableKey, FieldsKeysIncluded, TableData)
        # edb_filename, e2k_filename = self.etabs.export('.$et')
        # self.SapModel.File.OpenFile(str(e2k_filename))
        # solver_options = self.SapModel.Analyze.GetSolverOption_2()
        # solver_options[1] = 1
        # self.SapModel.Analyze.SetSolverOption_2(*solver_options[:-1])
        # self.SapModel.File.Save(str(edb_filename))
        return NumFatalErrors, ret

    def get_story_forces(
                    self,
                    loadcases: list=None,
                    ):
        if not loadcases:
            loadcases = self.etabs.load_patterns.get_ex_ey_earthquake_name()
        # assert len(loadcases) == 2
        self.etabs.set_current_unit('kgf', 'm')
        self.etabs.load_cases.select_load_cases(loadcases)
        TableKey = 'Story Forces'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.read_table(TableKey)
        i_loc = FieldsKeysIncluded.index('Location')
        data = self.reshape_data(FieldsKeysIncluded, TableData)
        columns = (i_loc,)
        values = ('Bottom',)
        result = self.etabs.get_from_list_table(data, columns, values)
        story_forces = list(result)
        return story_forces, loadcases, FieldsKeysIncluded

    def select_design_load_combinations(self,
            types : list = ['concrete'],
            ):
        load_combinations = set()
        type_combos = dict()
        for type_ in types:
            combinations = self.get_design_load_combinations(type_)
            type_combos[type_] = combinations
            if combinations:
                load_combinations = load_combinations.union(combinations)
        self.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay('')
        self.SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay(load_combinations)
        return type_combos

    def get_beams_forces(self,
                        load_combinations : list = None,
                        beams : list = None,
                        cols : list = None,
                        ) -> 'pandas.DataFrame':
        return self.get_element_forces(
            element_type='Beams',
            load_combinations=load_combinations,
            elements=beams,
            cols=cols,
        )

    def get_element_forces(self,
                        element_type : str = 'Beams', # 'Columns'
                        load_combinations : list = None,
                        elements : list = None,
                        cols : list = None,
                        ) -> 'pandas.DataFrame':
        '''
        cols : columns in dataframe that we want to get
        '''
        self.etabs.run_analysis()
        if load_combinations is None:
            load_combinations = self.get_concrete_frame_design_load_combinations()
        self.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay('')
        self.SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay(load_combinations)
        table_key = f'Element Forces - {element_type}'
        df = self.read(table_key, to_dataframe=True, cols=cols)
        if elements is not None:
            df = df[df['UniqueName'].isin(elements)]
        return df

    def get_beams_torsion(self,
                        load_combinations : list = None,
                        beams : list = None,
                        cols : list = None,
                        ) -> pd.DataFrame:
        if cols is None:
            cols = ['Story', 'Beam', 'UniqueName', 'T']
        self.etabs.set_current_unit('tonf', 'm')
        df = self.get_beams_forces(load_combinations, beams, cols)
        df['T'] = pd.to_numeric(df['T']).abs()
        df = df.loc[df.groupby('UniqueName')['T'].idxmax()]
        if len(cols) == 2:
            return dict(zip(df[cols[0]], df[cols[1]]))
        return df

    def get_concrete_frame_design_load_combinations(self):
        table_key = 'Concrete Frame Design Load Combination Data'
        df = self.read(table_key, to_dataframe=True)
        return list(df['ComboName'])

    def get_design_load_combinations(self,
            type_ : str = 'concrete', # 'steel', 'shearwall', 'slab'
            ):
        if type_ == 'concrete':
            table_key = 'Concrete Frame Design Load Combination Data'
        elif type_ == 'steel':
            table_key = 'Steel Design Load Combination Data'
        elif type_ == 'shearwall':
            table_key = 'Shear Wall Design Load Combination Data'
        elif type_ == 'slab':
            table_key = 'Concrete Slab Design Load Combination Data'
        df = self.read(table_key, to_dataframe=True)
        if df is None:
            return None
        return list(df['ComboName'])

    def create_section_cuts(self,
            group : str,
            prefix : str = 'SEC',
            angles : list = range(0, 180, 15),
            ):
        fields = ('Name', 'Defined By', 'Group', 'Result Type', 'Result Location', 'Rotation About Z', 'Rotation About Y', 'Rotation About X')
        data = []
        for angle in angles:
            name = f'{prefix}{angle}'
            data.append(
            (name, 'Group', group, 'Analysis', 'Default', f'{angle}', '0', '0')
            )
        data = self.unique_data(data)
        table = 'Section Cut Definitions'
        self.SapModel.DatabaseTables.SetTableForEditingArray(table, 0, fields, 0, data)
        self.apply_table()

    def get_section_cuts(self, cols=['Name', 'Group', 'RotAboutZ']):
        table = 'Section Cut Definitions'
        df = self.read(table, to_dataframe=True, cols=cols)
        df['RotAboutZ'] = df['RotAboutZ'].astype(int)
        return df

    def get_section_cuts_angle(self):
        df1 = self.get_section_cuts(cols=['Name', 'RotAboutZ'])
        re_dict = df1.set_index('Name').to_dict()['RotAboutZ']
        return re_dict

    def get_section_cuts_base_shear(self,
            loadcases : list = None,
            section_cuts: list = None,
            ):
        self.etabs.run_analysis()
        table = 'Section Cut Forces - Analysis'
        columns = ['SectionCut', 'OutputCase', 'F1', 'F2']
        self.etabs.load_cases.select_load_cases(loadcases)
        df = self.read(table, to_dataframe=True, cols=columns)
        df = df[
                (df['OutputCase'].isin(loadcases)) &
                (df['SectionCut'].isin(section_cuts))
                ]
        return df

    def get_joint_design_reactions(self,
        types : list = ['concrete'],
        select_combos : bool = True,
        ):
        if select_combos:
            self.select_design_load_combinations(types)
        table_key = 'Joint Design Reactions'
        df = self.read(table_key, to_dataframe=True)
        if 'StepType' in df.columns:
            cols = ['UniqueName', 'OutputCase', 'StepType', 'FZ', 'MX', 'MY']
            df = df[cols]
            df['StepType'].fillna('Max', inplace=True)
            df['OutputCase'] = df['OutputCase'] + '_' + df['StepType']
            df.drop(columns=['StepType'], inplace=True)
        else:
            cols = ['UniqueName', 'OutputCase', 'FZ', 'MX', 'MY']
            df = df[cols]
        df.dropna(inplace=True)
        return df

    def get_frame_assignment_summary(self,
            frames : list = None):
        table_key = 'Frame Assignments - Summary'
        df = self.read(table_key, to_dataframe=True)
        if 'AxisAngle' in df.columns:
            cols = ['Story', 'Label', 'UniqueName', 'Type', 'AnalysisSect', 'AxisAngle']
            df = df[cols]
            df['AxisAngle'].fillna(0, inplace=True)
        else:
            cols = ['Story', 'Label', 'UniqueName', 'Type', 'AnalysisSect']
            df = df[cols]
            df['AxisAngle'] = 0
        if frames is not None:
            filt = df['UniqueName'].isin(frames)
            df = df.loc[filt]
        return df

    def get_base_columns_summary(self):
        df = self.get_frame_assignment_summary()
        d_j = self.get_joint_design_reactions()
        base_points = d_j.UniqueName.unique()
        df_cols = self.get_frame_connectivity('Column')
        filt = df_cols.UniquePtI.isin(base_points)
        base_columns = df_cols.loc[filt]['UniqueName']
        filt = (df['UniqueName'].isin(base_columns)) & (df['Type'] == 'Column')
        return df.loc[filt]

    def get_frame_section_property_definitions_concrete_rectangular(self, cols=None):
        table_key = 'Frame Section Property Definitions - Concrete Rectangular'
        if cols is None:
            cols = ['Name', 't3', 't2']
        df = self.read(table_key, to_dataframe=True, cols=cols)
        return df

    def get_base_column_summary_with_section_dimensions(self):
        df_props = self.get_base_columns_summary()
        cols = ['Name', 't3', 't2']
        df_sections = self.get_frame_section_property_definitions_concrete_rectangular(cols=cols)
        filt = df_sections['Name'].isin(df_props['AnalysisSect'])
        df_sections = df_sections.loc[filt]
        for t in ['t2', 't3']:
            s = df_sections[t]
            s.index = df_sections['Name']
            df_props[t] = df_props['AnalysisSect'].map(s)
        return df_props

    def get_frame_connectivity(self, frame_type='Beam'):
        '''
        frame type : 'Beam', 'Column'
        '''
        table_key = f'{frame_type} Object Connectivity'
        cols = ['UniqueName', 'UniquePtI', 'UniquePtJ']
        df = self.read(table_key, to_dataframe=True, cols=cols)
        return df

    def get_points_connectivity(self,
            stories : tuple = (),
            ):
        table_key = 'Point Object Connectivity'
        if stories:
            cols = ['UniqueName', 'Story', 'X', 'Y', 'Z']
            df = self.read(table_key, to_dataframe=True, cols=cols)
            filt = df['Story'].isin(stories)
            df = df.loc[filt]
        else:
            cols = ['UniqueName', 'X', 'Y', 'Z']
            df = self.read(table_key, to_dataframe=True, cols=cols)
        import pandas as pd
        df[['X', 'Y', 'Z']] = df[['X', 'Y', 'Z']].apply(pd.to_numeric, downcast='float')
        return df

    def get_frame_points_xyz(self,
            frames : Union[list, None] = None,
            frame_type : str = 'Beam',  # 'Column'
            ) -> 'pandas.DataFrame':
        if frames is None:
            frames = self.SapModel.SelectObj.GetSelected()[2]
        df_frames = self.get_frame_connectivity(frame_type=frame_type)
        filt = df_frames['UniqueName'].isin(frames)
        df_frames = df_frames.loc[filt]
        df_points = self.get_points_connectivity()
        for i in ['X', 'Y', 'Z']:
            col_name = f'{i.lower()}i'
            s = df_points[i]
            s.index = df_points['UniqueName']
            df_frames[col_name] = df_frames['UniquePtI'].map(s)
        for i in ['X', 'Y', 'Z']:
            col_name = f'{i.lower()}j'
            s = df_points[i]
            s.index = df_points['UniqueName']
            df_frames[col_name] = df_frames['UniquePtJ'].map(s)
        return df_frames

    def get_basepoints_coord_and_dims(self,
        joint_design_reactions_df : Union['pandas.DataFrame', None] = None,
        base_columns_df : Union['pandas.DataFrame', None] = None,
        ):
        '''
        get base points coordinates and related column dimensions
        '''
        if joint_design_reactions_df is None:
            joint_design_reactions_df = self.get_joint_design_reactions()
        df = pd.DataFrame()
        points = joint_design_reactions_df['UniqueName'].unique()
        df['UniqueName'] = points
        points_and_columns = self.get_points_connectivity_with_type(points, 2)
        dic_x = {}
        dic_y = {}
        dic_z = {}
        for name in points:
            x, y, z, _ = self.SapModel.PointObj.GetCoordCartesian(name)
            dic_x[name] = x
            dic_y[name] = y
            dic_z[name] = z
        for col, dic in zip(('column', 'x', 'y', 'z'), (points_and_columns, dic_x, dic_y, dic_z)):
            df[col] = df['UniqueName'].map(dic)
        if base_columns_df is None:
            base_columns_df = self.get_base_column_summary_with_section_dimensions()
        st2 = pd.Series(base_columns_df['t2'])
        st2.index = base_columns_df['UniqueName']
        st3 = pd.Series(base_columns_df['t3'])
        st3.index = base_columns_df['UniqueName']
        s_axisangle = pd.Series(base_columns_df['AxisAngle'])
        s_axisangle.index = base_columns_df['UniqueName']
        df['t2'] = df['column'].map(st2)
        df['t3'] = df['column'].map(st3)
        df['AxisAngle'] = df['column'].map(s_axisangle)
        return df

    def get_point_connectivity_with_type(self, point, type_=2):
        types, names = self.SapModel.PointObj.GetConnectivity(point)[1:3]
        for t, name in zip(types, names):
            if t == type_:
                return name
        return None

    def get_points_connectivity_with_type(self, points, type_=2) -> dict:
        connections = {}
        for p in points:
            connections[p] = self.get_point_connectivity_with_type(p, type_)
        return connections

    def get_strip_connectivity(self):
        table_key = 'Strip Object Connectivity'
        cols = ['Name', 'NumSegs', 'StartPoint', 'EndPoint', 'WStartLeft',
            'WStartRight', 'WEndLeft', 'WEndRight', 'AutoWiden', 'Layer']
        if self.etabs.software == 'ETABS':
            cols.insert(1, 'Story')
        df = self.read(table_key, to_dataframe=True, cols=cols)
        return df

    def create_area_spring_table(self,
            names_props : list,
            ) -> None:
        table_key = 'Spring Property Definitions - Area Springs'
        fields = ('Name', 'SubModulus', 'NonlinOpt')
        data = []
        for name, submodulus in names_props:
            data.append(
            (name, submodulus, 'Compression Only')
            )
        data = self.unique_data(data)
        self.etabs.set_current_unit('kgf', 'cm')
        self.apply_data(table_key, data, fields)

    def create_punching_shear_general_table(self,
            punches : list,
            ) -> None:
        table_key = 'Concrete Slab Design Overwrites - Punching Shear - General'
        fields = ('UniqueName', 'CheckPunchingShear', 'LocationType', 'Perimeter',
                'EffDepthType', 'EffDepth', 'OpeningDef'
                )
        data = []
        for punch in punches:
            data.append(
            (punch.id,
            'Program Determined',
            punch.Location,
            'Specified Perimeter',
            # f'{punch.bx}',
            # f'{punch.by}',
            # f'{punch.angle.Value}',
            'Specified',
            f'{punch.d}',
            'Specified',
            ))
        data = self.unique_data(data)
        self.etabs.set_current_unit('kgf', 'mm')
        self.apply_data(table_key, data, fields)

    def create_punching_shear_perimeter_table(self,
            punches : list,
            ) -> None:
        try:
            from safe.punch import punch_funcs
        except:
            import punch_funcs
        table_key = 'Concrete Slab Design Overwrites - Punching Shear - Perimeter'
        fields = ('UniqueName', 'PointNum', 'XCoord', 'YCoord', 'Radius', 'IsNull')
        data = []
        for punch in punches:
            name = punch.id
            nulls, null_points = punch_funcs.punch_null_points(punch)
            for i, (point, is_null) in enumerate(zip(null_points, nulls), start=1):
                x, y = point.x, point.y
                data.append(
                    (name,
                    str(i),
                    f'{x}',
                    f'{y}',
                    '0',
                    is_null,
                ))
        data = self.unique_data(data)
        self.etabs.set_current_unit('kgf', 'mm')
        self.apply_data(table_key, data, fields)

    def get_hight_pressure_columns(self,
        ):
        self.etabs.set_current_unit('N', 'mm')
        cols = ['Story', 'Column', 'OutputCase', 'UniqueName', 'P']
        column_forces = self.get_element_forces(element_type='Columns', cols=cols)
        load_combinations = self.get_design_load_combinations('concrete')
        filt = column_forces['OutputCase'].isin(load_combinations)
        column_forces = column_forces.loc[filt]
        column_forces['P'] = pd.to_numeric(column_forces['P'])
        column_forces['P'] = column_forces['P'] * -1
        filt = column_forces.groupby(['UniqueName'])['P'].idxmax()
        column_forces = column_forces.loc[filt, :]
        col_names = list(column_forces['UniqueName'])
        assignment = self.get_frame_assignment_summary(frames=col_names)
        assignment.set_index(assignment.UniqueName, inplace=True)
        column_forces['section'] = column_forces.UniqueName.map(assignment.AnalysisSect)
        cols = ['Name', 'Material', 't3', 't2']
        df_sections = self.get_frame_section_property_definitions_concrete_rectangular(cols=cols)
        filt = df_sections['Name'].isin(column_forces['section'])
        df_sections = df_sections.loc[filt]
        for t in ['Material', 't2', 't3']:
            s = df_sections[t]
            s.index = df_sections['Name']
            column_forces[t] = column_forces['section'].map(s)
        materials = column_forces.Material.unique()
        d = dict()
        for m in materials:
            d[m] = self.SapModel.PropMaterial.GetOConcrete(m)[0]
        column_forces['fc'] = column_forces.Material.map(d)
        for col in ('t2', 't3', 'fc'):
            column_forces[col] = pd.to_numeric(column_forces[col])
        column_forces['0.3*Ag*fc'] = 0.3 * column_forces['t2'] * column_forces['t3'] * column_forces['fc']
        import numpy as np
        column_forces['high pressure'] = np.where(column_forces['P'] > column_forces['0.3*Ag*fc'], True, False)
        fields = ('Story', 'Column', 'OutputCase', 'UniqueName', 'P', 'section',  't2', 't3', 'fc', '0.3*Ag*fc', 'high pressure')
        return column_forces, fields



if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
    joint_design_reactions = etabs.database.get_joint_design_reactions()
    basepoints_coord_and_dims = etabs.database.get_basepoints_coord_and_dims(
                joint_design_reactions
            )
    print('Wow')
