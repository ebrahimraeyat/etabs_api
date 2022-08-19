import comtypes.client
comtypes.client.gen_dir = None
from pathlib import Path
from typing import Tuple, Union
import shutil
import math
import sys


from load_patterns import LoadPatterns
from load_cases import LoadCases
from load_combinations import LoadCombination
from story import Story
from frame_obj import FrameObj
from analyze import Analyze
from view import View
from database import DatabaseTables
# from sections.sections import Sections
from results import Results
from points import Points
from group import Group
from select_obj import SelectObj
from material import Material
from area import Area
from design import Design
from prop_frame import PropFrame

__all__ = ['EtabsModel']


class EtabsModel:
    force_units = dict(N=3, kN=4, KN=4, kgf=5, Kgf=5, tonf=6, Tonf=6)
    length_units = dict(mm=4, cm=5, m=6)
    enum_units = {
            'kn_mm' : 5,
            'kn_m' : 6,
            'kgf_mm' : 7,
            'kgf_m' : 8,
            'n_mm' : 9,
            'n_m' : 10,
            'tonf_mm' : 11,
            'tonf_m' : 12,
            'kn_cm' : 13,
            'kgf_cm' : 14,
            'n_cm' : 15,
            'tonf_cm' : 16,
    }

    def __init__(
                self,
                attach_to_instance: bool = True,
                backup : bool = True,
                software : str = 'ETABS', # 'SAFE'
                model_path: Union[str, Path] = '',
                software_exe_path: str = '',
                ):
        self.software = software
        self.etabs = None
        self.success = False
        if attach_to_instance:
            try:
                self.etabs = comtypes.client.GetActiveObject(f"CSI.{software}.API.ETABSObject")
                self.success = True
            except (OSError, comtypes.COMError):
                print("No running instance of the program found or failed to attach.")
                self.success = False
                # sys.exit(-1)
            if self.etabs is None:
                helper = comtypes.client.CreateObject('ETABSv1.Helper')
                helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
                if hasattr(helper, 'GetObjectProcess'):
                    try:
                        import psutil
                    except ImportError:
                        import subprocess
                        package = 'psutil'
                        subprocess.check_call(['python', "-m", "pip", "install", package])
                        import psutil
                    pid = None
                    for proc in psutil.process_iter():
                        if software in proc.name().lower():
                            pid = proc.pid
                            break
                    if pid:
                        self.etabs = helper.GetObjectProcess(f"CSI.{software}.API.ETABSObject", pid)
                        self.success = True

        else:
            # sys.exit(-1)
            helper = comtypes.client.CreateObject('ETABSv1.Helper')
            helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
            if software_exe_path:
                try:
                    self.etabs = helper.CreateObject(software_exe_path)
                except (OSError, comtypes.COMError):
                    print(f"Cannot start a new instance of the program from {software_exe_path}")
                    sys.exit(-1)
            else:
                try:
                    self.etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
                except (OSError, comtypes.COMError):
                    print("Cannot start a new instance of the program.")
                    sys.exit(-1)
            self.success = True
            self.etabs.ApplicationStart()
            if model_path:
                self.etabs.SapModel.File.OpenFile(str(model_path))

        if self.success:
            self.SapModel = self.etabs.SapModel
            if backup:
                self.backup_model()
            # solver_options = self.SapModel.Analyze.GetSolverOption_2()
            # solver_options[1] = 1
            # self.SapModel.Analyze.SetSolverOption_2(*solver_options[:-1])
            # self.SapModel.File.Save()
            self.load_patterns = LoadPatterns(None, self)
            self.load_cases = LoadCases(self)
            self.load_combinations = LoadCombination(self)
            self.story = Story(None, self)
            self.frame_obj = FrameObj(self)
            self.analyze = Analyze(self.SapModel, None)
            self.view = View(self.SapModel, None)
            self.database = DatabaseTables(None, self)
            # self.sections = Sections(self.SapModel, None)
            self.results = Results(None, self)
            self.points = Points(None, self)
            self.group = Group(self)
            self.select_obj = SelectObj(self)
            self.material = Material(self)
            self.area = Area(self)
            self.design = Design(self)
            self.prop_frame = PropFrame(self)
    
    def close_etabs(self):
        self.SapModel.SetModelIsLocked(False)
        self.etabs.ApplicationExit(False)
        self.SapModel = None
        self.etabs = None

    def backup_model(self, name=None):
        max_num = 0
        backup_path=None
        if name is None:
            filename = self.get_file_name_without_suffix()
            file_path = self.get_filepath()
            backup_path = file_path / 'backups'
            if not backup_path.exists():
                import os
                os.mkdir(str(backup_path))
            backup_path = backup_path
            for edb in backup_path.glob(f'BACKUP_{filename}*.EDB'):
                num = edb.name.rstrip('.EDB')[len('BACKUP_') + len(filename) + 1:]
                try:
                    num = int(num)
                    max_num = max(max_num, num)
                except:
                    continue
            name = f'BACKUP_{filename}_{max_num + 1}.EDB'
        if not name.lower().endswith('.edb'):
            name += '.EDB'
        asli_file_path = self.get_filename()
        asli_file_path = asli_file_path.with_suffix('.EDB')
        if backup_path is None:
            new_file_path = asli_file_path.parent / name
        else:
            new_file_path = backup_path / name
        shutil.copy(asli_file_path, new_file_path)
        return new_file_path

    def remove_backups(self):
        file_path = self.get_filepath() / 'backups'
        for edb in file_path.glob(f'BACKUP_*.EDB'):
            edb.unlink()
        return None

    def restore_backup(self, filepath):
        current_file_path = self.get_filename()
        self.SapModel.File.OpenFile(str(filepath))
        self.SapModel.File.Save(str(current_file_path))

    def lock_model(self):
        self.SapModel.SetModelIsLocked(True)
    
    def unlock_model(self):
        self.SapModel.SetModelIsLocked(False)

    def lock_and_unlock_model(self):
        self.SapModel.SetModelIsLocked(True)
        self.SapModel.SetModelIsLocked(False)

    def run_analysis(self, open_lock=False):
        if self.SapModel.GetModelIsLocked():
            if open_lock:
                self.SapModel.SetModelIsLocked(False)
                print('Run Alalysis ...')
                self.SapModel.analyze.RunAnalysis()
        else:
            print('Run Alalysis ...')
            self.SapModel.analyze.RunAnalysis()

    def set_current_unit(self, force, length):
        # force_enum = EtabsModel.force_units[force]
        # len_enum = EtabsModel.length_units[length]
        number = self.enum_units.get(f"{force}_{length}".lower(), None)
        if number is None:
            raise KeyError
        self.SapModel.SetPresentUnits(number)
    
    def get_current_unit(self):
        force_enum, len_enum, *argv = self.SapModel.GetPresentUnits_2()
        for key, value in EtabsModel.force_units.items():
            if force_enum == value:
                force = key
                break
        for key, value in EtabsModel.length_units.items():
            if len_enum == value:
                length = key
                break
        return force, length

    def get_file_name_without_suffix(self):
        f = Path(self.SapModel.GetModelFilename())
        name = f.name.replace(f.suffix, '')
        return name

    def add_prefix_suffix_name(self,
            prefix : str = '',
            suffix : str = '',
            open : bool = False,
            ) -> Path:
        '''
        adding prefix and suffix string to the current filename
        '''
        name = self.get_file_name_without_suffix()
        new_name = f'{prefix}{name}{suffix}.EDB'
        new_path = self.get_filepath() / new_name
        if open:
            self.SapModel.File.Save(str(new_path))
        return new_path

    def get_filename(self) -> Path:
        return Path(self.SapModel.GetModelFilename())
    
    def get_filepath(self) -> Path:
        return Path(self.SapModel.GetModelFilename()).parent
        
    def save_as(self, name):
        if not name.lower().endswith('.edb'):
            name += '.EDB'
        asli_file_path = Path(self.SapModel.GetModelFilename())
        asli_file_path = asli_file_path.with_suffix('.EDB')
        new_file_path = asli_file_path.with_name(name)
        self.SapModel.File.Save(str(new_file_path))
        return asli_file_path, new_file_path
    
    def export(self, suffix='.e2k') -> Tuple[Path, Path]:
        asli_file_path = Path(self.SapModel.GetModelFilename())
        asli_file_path = asli_file_path.with_suffix('.EDB')
        new_file_path = asli_file_path.with_suffix(suffix)
        self.SapModel.File.Save(str(new_file_path))
        return asli_file_path, new_file_path

    @staticmethod
    def get_from_list_table(
            list_table: list,
            columns: list,
            values: list,
            ) -> filter:
        from operator import itemgetter
        itemget = itemgetter(*columns)
        assert len(columns) == len(values)
        if len(columns) == 1:
            result = filter(lambda x: itemget(x) == values[0], list_table)
        else:
            result = filter(lambda x: itemget(x) == values, list_table)
        return result

    @staticmethod
    def save_to_json(json_file, data):
        import json
        with open(json_file, 'w') as f:
            json.dump(data, f)

    @staticmethod
    def load_from_json(json_file):
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data

    def save_to_json_in_edb_folder(self, json_name, data):
        json_file = Path(self.SapModel.GetModelFilepath()) / json_name
        self.save_to_json(json_file, data)

    def get_drift_periods(
                self,
                t_filename="T.EDB",
                ):
        '''
        This function creates an Etabs file called T.EDB from current open Etabs file,
        then in T.EDB file change the stiffness properties of frame elements according 
        to ACI 318 to get periods of structure, for this it set M22 and M33 stiffness of
        beams to 0.5 and column and wall to 1.0. Then it runs the analysis and get the x and y period of structure.
        '''
        print(10 * '-' + "Get drift periods" + 10 * '-' + '\n')
        self.SapModel.File.Save()
        asli_file_path = Path(self.SapModel.GetModelFilename())
        if asli_file_path.suffix.lower() != '.edb':
            asli_file_path = asli_file_path.with_suffix(".EDB")
        dir_path = asli_file_path.parent.absolute()
        t_file_path = dir_path / t_filename
        print(f"Saving file as {t_file_path}\n")
        self.SapModel.File.Save(str(t_file_path))
        print("get frame property modifiers and change I values\n")
        IMod_beam = 0.5
        IMod_col_wall = 1
        for label in self.SapModel.FrameObj.GetLabelNameList()[1]:
            if self.SapModel.FrameObj.GetDesignProcedure(label)[0] == 2:  # concrete
                modifiers = list(self.SapModel.FrameObj.GetModifiers(label)[0])
                if self.SapModel.FrameObj.GetDesignOrientation(label)[0] == 1: # Column
                    IMod = IMod_col_wall
                    modifiers[:6] = 6 * [IMod]
                elif self.SapModel.FrameObj.GetDesignOrientation(label)[0] == 2:   # Beam
                    IMod = IMod_beam
                    modifiers[4:6] = [IMod, IMod]
                self.SapModel.FrameObj.SetModifiers(label, modifiers)
        for label in self.SapModel.AreaObj.GetLabelNameList()[1]:
            if self.SapModel.AreaObj.GetDesignOrientation(label)[0] == 1: # Wall
                modifiers = list(self.SapModel.AreaObj.GetModifiers(label)[0])
                modifiers[:6] = 6 * [IMod_col_wall]
                self.SapModel.AreaObj.SetModifiers(label, modifiers)
        # for steel structure
        self.SapModel.DesignSteel.SetCode('AISC ASD 89')
        # run model (this will create the analysis model)
        print("start running T file analysis")
        modal_case = self.load_cases.get_modal_loadcase_name()
        self.analyze.set_load_cases_to_analyze(modal_case)
        self.SapModel.Analyze.RunAnalysis()

        TableKey = "Modal Participating Mass Ratios"
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.database.read_table(TableKey)
        self.SapModel.SetModelIsLocked(False)
        ux_i = FieldsKeysIncluded.index("UX")
        uy_i = FieldsKeysIncluded.index("UY")
        period_i = FieldsKeysIncluded.index("Period")
        uxs = [float(TableData[i]) for i in range(ux_i, len(TableData), len(FieldsKeysIncluded))]
        uys = [float(TableData[i]) for i in range(uy_i, len(TableData), len(FieldsKeysIncluded))]
        periods = [float(TableData[i]) for i in range(period_i, len(TableData), len(FieldsKeysIncluded))]
        ux_max_i = uxs.index(max(uxs))
        uy_max_i = uys.index(max(uys))
        Tx_drift = periods[ux_max_i]
        Ty_drift = periods[uy_max_i]
        print(f"Tx_drift = {Tx_drift}, Ty_drift = {Ty_drift}\n")
        print("opening the main file\n")
        self.SapModel.File.OpenFile(str(asli_file_path))
        return Tx_drift, Ty_drift, asli_file_path

    def get_diaphragm_max_over_avg_drifts(
                    self,
                    loadcases=[],
                    only_ecc=True,
                    cols=None,
                    ):
        self.run_analysis()
        if not loadcases:
            xy_names = self.load_patterns.get_xy_seismic_load_patterns(only_ecc)
            all_load_case_names = self.load_cases.get_load_cases()
            loadcases = set(xy_names).intersection(all_load_case_names)
        x_names, y_names = self.load_patterns.get_load_patterns_in_XYdirection()
        self.load_cases.select_load_cases(loadcases)
        table_key = 'Diaphragm Max Over Avg Drifts'
        if cols is None:
            cols = ['Story', 'OutputCase', 'Max Drift', 'Avg Drift', 'Label', 'Ratio', 'Item']
        df = self.database.read(table_key, to_dataframe=True, cols=cols)
        if len(df) == 0:
            return
        df['Dir'] = df['Item'].str[-1]
        df.drop(columns=['Item'], inplace=True)
        mask = (
                (df['Dir'] == 'X') & (df['OutputCase'].isin(x_names))) ^ (
                (df['Dir'] == 'Y') & (df['OutputCase'].isin(y_names)))
        df = df.loc[mask]
        df = df.astype({'Max Drift': float, 'Avg Drift': float, 'Ratio': float})
        return df

    def get_drifts(self,
            no_story,
            cdx,
            cdy,
            loadcases=None,
            x_loadcases=None,
            y_loadcases=None,
            ):
        self.run_analysis()
        if loadcases is None:
            loadcases = self.etabs.load_cases.get_seismic_drift_load_cases()
        print(loadcases)
        if not x_loadcases:
            x_loadcases, y_loadcases = self.load_cases.get_xy_seismic_load_cases()
        self.load_cases.select_load_cases(loadcases)
        TableKey = 'Diaphragm Max Over Avg Drifts'
        ret = self.database.read_table(TableKey)
        if ret is None:
            return None
        _, _, FieldsKeysIncluded, _, TableData, _ = ret
        data = self.database.reshape_data(FieldsKeysIncluded, TableData)
        try:
            item_index = FieldsKeysIncluded.index("Item")
            case_name_index = FieldsKeysIncluded.index("OutputCase")
        except ValueError:
            return None, None
        # average_drift_index = FieldsKeysIncluded.index("Avg Drift")
        if no_story <= 5:
            limit = .025
        else:
            limit = .02
        new_data = []
        for row in data:
            name = row[case_name_index]
            if row[item_index].endswith("X"):
                if not name in x_loadcases:
                    continue
                cd = cdx
            elif row[item_index].endswith("Y"):
                if not name in y_loadcases:
                    continue
                cd = cdy
            allowable_drift = limit / cd
            row.append(f'{allowable_drift:.4f}')
            new_data.append(row)
        fields = list(FieldsKeysIncluded)
        fields.append('Allowable Drift')
        return new_data, fields

    def apply_cfactor_to_tabledata(self, TableData, FieldsKeysIncluded, building,
            bot_story : str = '',
            top_story : str = '',
            ):
        data = self.database.reshape_data(FieldsKeysIncluded, TableData)
        names_x, names_y = self.load_patterns.get_load_patterns_in_XYdirection()
        i_c = FieldsKeysIncluded.index('C')
        i_k = FieldsKeysIncluded.index('K')
        i_top_story = FieldsKeysIncluded.index('TopStory')
        i_bot_story = FieldsKeysIncluded.index('BotStory')
        cx, cy = str(building.results[1]), str(building.results[2])
        kx, ky = str(building.kx), str(building.ky)
        cx_drift, cy_drift = str(building.results_drift[1]), str(building.results_drift[2])
        kx_drift, ky_drift = str(building.kx_drift), str(building.ky_drift)
        drift_load_pattern_names = self.load_patterns.get_drift_load_pattern_names()
        i_name = FieldsKeysIncluded.index("Name")
        for earthquake in data:
            if bot_story:
                earthquake[i_bot_story] = bot_story
            if top_story:
                earthquake[i_top_story] = top_story
            if not earthquake[i_c]:
                continue
            name = earthquake[i_name]
            if name in drift_load_pattern_names:
                if name in names_x:
                    earthquake[i_c] = str(cx_drift)
                    earthquake[i_k] = str(kx_drift)
                elif name in names_y:
                    earthquake[i_c] = str(cy_drift)
                    earthquake[i_k] = str(ky_drift)
            elif name in names_x:
                earthquake[i_c] = str(cx)
                earthquake[i_k] = str(kx)
            elif name in names_y:
                earthquake[i_c] = str(cy)
                earthquake[i_k] = str(ky)
        table_data = self.database.unique_data(data)
        return table_data

    def apply_cfactor_to_edb(
            self,
            building,
            bot_story : str = '',
            top_story : str = '',
            ):
        print("Applying cfactor to edb\n")
        self.SapModel.SetModelIsLocked(False)
        self.load_patterns.select_all_load_patterns()
        TableKey = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.database.read_table(TableKey)
        # if is_auto_load_yes_in_seismic_load_patterns(TableData, FieldsKeysIncluded):
        #     return 1
        TableData = self.apply_cfactor_to_tabledata(TableData, FieldsKeysIncluded, building, bot_story, top_story)
        NumFatalErrors, ret = self.database.write_seismic_user_coefficient(TableKey, FieldsKeysIncluded, TableData)
        print(f"NumFatalErrors, ret = {NumFatalErrors}, {ret}")
        return NumFatalErrors

    def is_etabs_running(self):
        try:
            comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
            return True
        except OSError:
            return False

    def get_magnification_coeff_aj(self):
        story_length = self.story.get_stories_length()
        cols = ['Story', 'OutputCase', 'Max Drift', 'Avg Drift', 'Ratio', 'Item']
        df = self.get_diaphragm_max_over_avg_drifts(cols=cols)
        df['aj'] = (df['Ratio'] / 1.2) ** 2
        df['aj'].clip(1,3, inplace=True)
        filt = df['aj'] > 1
        df = df.loc[filt]
        df['Ecc. Ratio'] = df['aj'] * .05
        conditions =[]
        choices = []
        for story, xy_lenght in story_length.items():
            conditions.append(df['Dir'].eq('Y') & df['Story'].eq(story))
            conditions.append(df['Dir'].eq('X') & df['Story'].eq(story))
            choices.extend(xy_lenght)
        import numpy as np
        df['Length (Cm)'] = np.select(conditions, choices)
        df['Ecc. Length (Cm)'] = df['Ecc. Ratio'] * df['Length (Cm)']
        story_names = df['Story'].unique()
        story_diaphs = self.story.get_stories_diaphragms(story_names)
        df['Diaph'] = df['Story'].map(story_diaphs)
        if not df.empty:
            df['Diaph'] = df['Diaph'].str.join(',')
        return df

    def get_static_magnification_coeff_aj(self,
            df : Union['pandas.DataFrame', bool] = None,
            ):
        if df is None:
            df = self.get_magnification_coeff_aj()
        df = df.groupby(['OutputCase', 'Story', 'Diaph'], as_index=False)['Ecc. Length (Cm)'].max()
        df = df.astype({'Ecc. Length (Cm)': int})
        return df
    
    def get_dynamic_magnification_coeff_aj(self,
            df : Union['pandas.DataFrame', bool] = None,
            ):
        if df is None:
            df = self.get_magnification_coeff_aj()
        df = df.groupby(['OutputCase', 'Story', 'Diaph', 'Dir'], as_index=False)['Ecc. Length (Cm)'].max()
        df = df.astype({'Ecc. Length (Cm)': int})
        import pandas as pd
        ret_df = pd.DataFrame(columns=['OutputCase', 'Story', 'Diaph', 'Ecc. Length (Cm)'])
        x_names, y_names = self.load_cases.get_response_spectrum_xy_loadcases_names()
        all_specs = self.load_cases.get_response_spectrum_loadcase_name()
        angular_names = set(all_specs).difference(x_names + y_names)
        if x_names:
            new_df = df[df['Dir'] == 'X'].groupby(['Story', 'Diaph'], as_index=False)['Ecc. Length (Cm)'].max()
            for name in x_names:
                new_df['OutputCase'] = name
                ret_df = ret_df.append(new_df)
        if y_names:
            new_df = df[df['Dir'] == 'Y'].groupby(['Story', 'Diaph'], as_index=False)['Ecc. Length (Cm)'].max()
            for name in y_names:
                new_df['OutputCase'] = name
                ret_df = ret_df.append(new_df)
        if angular_names:
            new_df = df.groupby(['Story', 'Diaph'], as_index=False)['Ecc. Length (Cm)'].max()
            for name in angular_names:
                new_df['OutputCase'] = name
                ret_df = ret_df.append(new_df)
        return ret_df

    def apply_aj_df(self, df):
        print("Applying cfactor to edb\n")
        self.SapModel.SetModelIsLocked(False)
        self.load_patterns.select_all_load_patterns()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        input_df = self.database.read(table_key, to_dataframe=True)
        self.database.write_aj_user_coefficient(table_key, input_df, df)
    
    def get_irregularity_of_mass(self, story_mass=None):
        if not story_mass:
            story_mass = self.database.get_story_mass()
        for i, sm in enumerate(story_mass):
            m_neg1 = float(story_mass[i - 1][1]) * 1.5
            m = float(sm[1])
            if i != len(story_mass) - 1:
                m_plus1 = float(story_mass[i + 1][1]) * 1.5
            else:
                m_plus1 = m
            if i == 0:
                m_neg1 = m
            sm.extend([m_neg1, m_plus1])
        fields = ('Story', 'Mass X', '1.5 * Below', '1.5 * Above')
        return story_mass, fields

    def add_load_case_in_center_of_rigidity(self, story_name, x, y):
        self.SapModel.SetPresentUnits(7)
        z = self.SapModel.story.GetElevation(story_name)[0]
        point_name = self.SapModel.PointObj.AddCartesian(float(x),float(y) , z)[0]  
        diaph = self.story.get_story_diaphragms(story_name).pop()
        self.SapModel.PointObj.SetDiaphragm(point_name, 3, diaph)
        LTYPE_OTHER = 8
        lp_name = f'STIFFNESS_{story_name}'
        self.SapModel.LoadPatterns.Add(lp_name, LTYPE_OTHER, 0, True)
        load = 1000
        PointLoadValue = [load,load,0,0,0,0]
        self.SapModel.PointObj.SetLoadForce(point_name, lp_name, PointLoadValue)
        self.analyze.set_load_cases_to_analyze(lp_name)
        return point_name, lp_name

    def get_story_stiffness_modal_way(self):
        story_mass = self.database.get_story_mass()[::-1]
        story_mass = {key: value for key, value in story_mass}
        stories = list(story_mass.keys())
        dx, dy, wx, wy = self.database.get_stories_displacement_in_xy_modes()
        story_stiffness = {}
        n = len(story_mass)
        for i, (phi_x, phi_y) in enumerate(zip(dx.values(), dy.values())):
            if i == n - 1:
                phi_neg_x = 0
                phi_neg_y = 0
            else:
                story_neg = stories[i + 1]
                phi_neg_x = dx[story_neg]
                phi_neg_y = dy[story_neg]
            d_phi_x = phi_x - phi_neg_x
            d_phi_y = phi_y - phi_neg_y
            sigma_x = 0
            sigma_y = 0
            for j in range(0, i + 1):
                story_j = stories[j]
                m_j = float(story_mass[story_j])
                phi_j_x = dx[story_j]
                phi_j_y = dy[story_j]
                sigma_x += m_j * phi_j_x
                sigma_y += m_j * phi_j_y
            kx = wx ** 2 * sigma_x / d_phi_x
            ky = wy ** 2 * sigma_y / d_phi_y
            story_stiffness[stories[i]] = [kx, ky]
        return story_stiffness

    def get_story_stiffness_2800_way(self):
        asli_file_path = Path(self.SapModel.GetModelFilename())
        if asli_file_path.suffix.lower() != '.edb':
            asli_file_path = asli_file_path.with_suffix(".EDB")
        dir_path = asli_file_path.parent.absolute()
        center_of_rigidity = self.database.get_center_of_rigidity()
        story_names = center_of_rigidity.keys()
        story_stiffness = {}
        name = self.get_file_name_without_suffix()
        for story_name in story_names:
            story_file_path = dir_path / f'{name}_STIFFNESS_{story_name}.EDB'
            print(f"Saving file as {story_file_path}\n")
            shutil.copy(asli_file_path, story_file_path)
            print(f"Opening file {story_file_path}\n")
            self.SapModel.File.OpenFile(str(story_file_path))
            x, y = center_of_rigidity[story_name]
            point_name, lp_name = self.add_load_case_in_center_of_rigidity(
                    story_name, x, y)
            self.story.fix_below_stories(story_name)
            self.SapModel.View.RefreshView()
            self.SapModel.Analyze.RunAnalysis()
            disp_x, disp_y = self.results.get_point_xy_displacement(point_name, lp_name)
            kx, ky = 1000 / abs(disp_x), 1000 / abs(disp_y)
            story_stiffness[story_name] = [kx, ky]
        self.SapModel.File.OpenFile(str(asli_file_path))
        return story_stiffness

    def get_story_stiffness_earthquake_way(
                self,
                loadcases: list=None,
                ):
        if loadcases is None:
            loadcases = self.load_patterns.get_EX_EY_load_pattern()
        assert len(loadcases) == 2
        EX, EY = loadcases
        self.run_analysis()
        self.set_current_unit('kgf', 'm')
        self.load_cases.select_load_cases(loadcases)
        TableKey = 'Story Stiffness'
        [_, _, FieldsKeysIncluded, _, TableData, _] = self.database.read_table(TableKey)
        i_story = FieldsKeysIncluded.index('Story')
        i_case = FieldsKeysIncluded.index('OutputCase')
        i_stiff_x = FieldsKeysIncluded.index('StiffX')
        i_stiff_y = FieldsKeysIncluded.index('StiffY')
        data = self.database.reshape_data(FieldsKeysIncluded, TableData)
        columns = (i_case,)
        values_x = (EX,)
        values_y = (EY,)
        result_x = self.get_from_list_table(data, columns, values_x)
        result_y = self.get_from_list_table(data, columns, values_y)
        story_stiffness = {}
        for x, y in zip(list(result_x), list(result_y)):
            story = x[i_story]
            stiff_x = float(x[i_stiff_x])
            stiff_y = float(y[i_stiff_y])
            story_stiffness[story] = [stiff_x, stiff_y]
        return story_stiffness

    def get_story_stiffness_table(self, way='2800', story_stiffness=None):
        '''
        way can be '2800', 'modal' , 'earthquake'
        '''
        name = self.get_file_name_without_suffix()
        if not story_stiffness:
            if way == '2800':
                story_stiffness = self.get_story_stiffness_2800_way()
            elif way == 'modal':
                story_stiffness = self.get_story_stiffness_modal_way()
            elif way == 'earthquake':
                story_stiffness = self.get_story_stiffness_earthquake_way()
        stories = list(story_stiffness.keys())
        retval = []
        for i, story in enumerate(stories):
            stiffness = story_stiffness[story]
            kx = stiffness[0]
            ky = stiffness[1]
            if i == 0:
                stiffness.extend(['-', '-'])
            else:
                k1 = story_stiffness[stories[i - 1]]
                stiffness.extend([
                    kx / k1[0] if k1[0] != 0 else '-',
                    ky / k1[1] if k1[1] != 0 else '-',
                    ])

            if len(stories[:i]) >= 3:
                k2 = story_stiffness[stories[i - 2]]
                k3 = story_stiffness[stories[i - 3]]
                ave_kx = (k1[0] + k2[0] + k3[0]) / 3
                ave_ky = (k1[1] + k2[1] + k3[1]) / 3
                stiffness.extend([kx / ave_kx, ky / ave_ky])
            else:
                stiffness.extend(['-', '-'])
            retval.append((story, *stiffness))
        fields = ('Story', 'Kx', 'Ky', 'Kx / kx+1', 'Ky / ky+1', 'Kx / kx_3ave', 'Ky / ky_3ave')
        json_file = f'{name}_story_stiffness_{way}_table.json'
        self.save_to_json_in_edb_folder(json_file, (retval, fields))
        return retval, fields

    def get_story_forces_with_percentages(
                self,
                loadcases: list=None,
                ):
        vx, vy = self.results.get_base_react()
        story_forces, _ , fields = self.database.get_story_forces(loadcases)
        new_data = []
        i_vx = fields.index('VX')
        i_vy = fields.index('VY')
        for story_force in story_forces:
            fx = float(story_force[i_vx])
            fy = float(story_force[i_vy])
            story_force.extend([f'{fx/vx:.3f}', f'{fy/vy:.3f}'])
            new_data.append(story_force)
        fields = list(fields)
        fields.extend(['Vx %', 'Vy %'])
        return new_data, fields

    def scale_response_spectrums(self,
        ex_name : str,
        ey_name : str,
        x_specs : list,
        y_specs : list,
        x_scale_factor : float = 0.9, # 0.85, 0.9, 1
        y_scale_factor : float = 0.9, # 0.85, 0.9, 1
        num_iteration : int = 3,
        tolerance : float = .05,
        reset_scale : bool = True,
        analyze : bool = True,
        ):
        if reset_scale:
            self.load_cases.reset_scales_for_response_spectrums(loadcases=x_specs+y_specs)
        self.analyze.set_load_cases_to_analyze([ex_name, ey_name] + x_specs + y_specs)
        for i in range(num_iteration):
            vex, vey = self.results.get_base_react(
                    loadcases=[ex_name, ey_name],
                    directions=['x', 'y'],
                    absolute=True,
                    )
            vsx = self.results.get_base_react(
                    loadcases=x_specs,
                    directions=['x'] * len(x_specs),
                    absolute=True,
                    )
            vsy = self.results.get_base_react(
                    loadcases=y_specs,
                    directions=['y'] * len(y_specs),
                    absolute=True,
                    )
            x_scales = []
            y_scales = []
            for v in vsx:
                scale = x_scale_factor * vex / v
                x_scales.append(scale)
            for v in vsy:
                scale = y_scale_factor * vey / v
                y_scales.append(scale)
            print(x_scales, y_scales)
            max_scale = max(x_scales + y_scales)
            min_scale = min(x_scales + y_scales)
            if (max_scale < 1 + tolerance) and (min_scale > 1 - tolerance):
                break
            else:
                for spec, scale in zip(x_specs, x_scales):
                    self.load_cases.multiply_response_spectrum_scale_factor(spec, scale)
                for spec, scale in zip(y_specs, y_scales):
                    self.load_cases.multiply_response_spectrum_scale_factor(spec, scale)
        self.unlock_model()
        self.analyze.set_load_cases_to_analyze()
        if analyze:
            self.run_analysis()

    def angles_response_spectrums_analysis(self,
        ex_name : str,
        ey_name : str,
        specs : list = None,
        section_cuts : list = None,
        scale_factor : float = 0.9, # 0.85, 0.9, 1
        num_iteration : int = 3,
        tolerance : float = .02,
        reset_scale : bool = True,
        analyze : bool = True,
        ):
        if reset_scale:
            self.load_cases.reset_scales_for_response_spectrums(loadcases=specs)
        loadcases = [ex_name, ey_name] + specs
        for i in range(num_iteration):
            self.analyze.set_load_cases_to_analyze(loadcases)
            df = self.database.get_section_cuts_base_shear(loadcases, section_cuts)
            df.drop_duplicates(['SectionCut', 'OutputCase'], keep='last', inplace=True)
            re_dict = self.database.get_section_cuts_angle()
            df['angle'] = df['SectionCut'].replace(re_dict)
            angles = df['angle'].unique()
            re_dict = self.load_cases.get_spectral_with_angles(angles, specs)
            df['angle_spec'] = df['angle'].replace(re_dict)
            spec_sec_angle = df[df['OutputCase'] == df['angle_spec']]
            scales = []
            spec_scales = {}
            for i, row in spec_sec_angle.iterrows():
                spec = row['OutputCase']
                section_cut = row['SectionCut']
                angle = row['angle']
                df_angle_section = df[(df['SectionCut'] == section_cut) & (df['angle'] == angle)][['F1', 'OutputCase']]
                f_ex = abs(float(df_angle_section[df['OutputCase'] == ex_name]['F1']))
                f_ey = abs(float(df_angle_section[df['OutputCase'] == ey_name]['F1']))
                f_spec = abs(float(df_angle_section[df['OutputCase'] == spec]['F1']))
                scale = scale_factor * math.sqrt(f_ex ** 2 + f_ey ** 2) / f_spec
                spec_scales[spec] = scale
                scales.append(scale)
            print(scales)
            max_scale = max(scales)
            min_scale = min(scales)
            if (max_scale < 1 + tolerance) and (min_scale > 1 - tolerance):
                break
            else:
                for spec, scale in spec_scales.items():
                    self.load_cases.multiply_response_spectrum_scale_factor(spec, scale)
        self.unlock_model()
        self.analyze.set_load_cases_to_analyze()
        if analyze:
            self.run_analysis()
            
class Build:
    def __init__(self):
        self.kx = 1
        self.ky = 1
        self.kx_drift = 1
        self.ky_drift = 1
        self.results = [True, 1, 1]
        self.results_drift = [True, 1, 1]

                
if __name__ == '__main__':
    etabs = EtabsModel(
                attach_to_instance=False,
                backup = False,
                # model_path: Path = '',
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 20\ETABS.exe'
    )
    SapModel = etabs.SapModel
    etabs.get_magnification_coeff_aj()