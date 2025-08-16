import comtypes.client
comtypes.client.gen_dir = None
from pathlib import Path
from typing import Tuple, Union
import shutil
import math
import sys
import json


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
from diaphragm import Diaphragm
from func import Func
from pier import Pier
from shearwall import ShearWall

__all__ = ['EtabsModel']


class EtabsModel:
    force_units = dict(Ib=1, kip=2, N=3, kN=4, KN=4, kgf=5, Kgf=5, tonf=6, Tonf=6)
    length_units = dict(inch=1, ft=2, micron=3, mm=4, cm=5, m=6)
    length_units['in'] = 1
    enum_units = {
        'ib_inch': 1,
        'ib_ft': 2,
        'kip_inch': 3,
        'kip_ft': 4,
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
                software : str = 'ETABS', # 'SAFE', 'SAP2000'
                model_path: Union[str, Path] = '',
                software_exe_path: str = '',
                ):
        self.software = software
        self.etabs = None
        self.success = False
        helper = comtypes.client.CreateObject(f'{software}v1.Helper')
        exec(f"helper = helper.QueryInterface(comtypes.gen.{software}v1.cHelper)")
        if attach_to_instance:
            try:
                if software in ("ETABS", "SAFE"):
                    self.etabs = helper.GetObject(f"CSI.{software}.API.ETABSObject")
                elif software == "SAP2000":
                    self.etabs = helper.GetObject(f"CSI.{software}.API.SapObject")
                self.success = True
            except (OSError, comtypes.COMError):
                print("No running instance of the program found or failed to attach.")
                self.success = False
            finally:
                if not self.success and  hasattr(helper, 'GetObjectProcess'):
                    try:
                        import psutil
                    except ImportError:
                        import subprocess
                        package = 'psutil'
                        subprocess.check_call(['python', "-m", "pip", "install", package])
                        import psutil
                    pid = None
                    for proc in psutil.process_iter():
                        if software.lower() in proc.name().lower():
                            pid = proc.pid
                            break
                    if pid is not None:
                        if software in ("ETABS", "SAFE"):
                            self.etabs = helper.GetObjectProcess(f"CSI.{software}.API.ETABSObject", pid)
                        elif software == 'SAP2000':
                            self.etabs = helper.GetObjectProcess(f"CSI.{software}.API.SapObject", pid)
                        self.success = True
                # sys.exit(-1)
        else:
            # sys.exit(-1)
            # helper = comtypes.client.CreateObject(f'{software}v1.Helper')
            # helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
            if software_exe_path:
                try:
                    self.etabs = helper.CreateObject(software_exe_path)
                except (OSError, comtypes.COMError):
                    print(f"Cannot start a new instance of the program from {software_exe_path}")
                    sys.exit(-1)
            else:
                try:
                    if software in ("ETABS", "SAFE"):
                        self.etabs = helper.CreateObjectProgID(f"CSI.{software}.API.ETABSObject")
                    elif software == "SAP2000":
                        self.etabs = helper.CreateObjectProgID(f"CSI.{software}.API.SapObject")
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
            self.view = View(self)
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
            self.diaphragm = Diaphragm(self)
            self.func = Func(self)
            self.pier = Pier(self)
            self.shearwall = ShearWall(self)
            self.set_special_values_according_to_software_and_version()
            self.etabs_pywinauto = None
    
    @staticmethod
    def connect_to_the_software_using_the_executable_path(exe_path):
        exe_name = Path(exe_path).name
        software = exe_name.split('.')[0]
        helper = comtypes.client.CreateObject(f'{software}v1.Helper')
        exec(f"helper = helper.QueryInterface(comtypes.gen.{software}v1.cHelper)")
        software_instance = helper.CreateObject(exe_path)
        return software_instance

    def get_pywinauto_etabs(self):
        if self.etabs_pywinauto is not None:
            try:
                self.etabs_pywinauto.is_enabled()
                print(f"The {self.software} is still Open.")
                return self.etabs_pywinauto
            except comtypes.COMError:
                print(f"The {self.software} has been closed by the user.")
                self.etabs_pywinauto = None
        try:
            from pywinauto import Desktop
        except ImportError:
            import freecad_funcs
            freecad_funcs.install_package('pywinauto')
            from pywinauto import Desktop
        # windows = Desktop(backend="uia").windows(title_re=".*ETABS.*")
        # if not windows:
        #     return None
        print("Available ETABS windows:")
        info = self.SapModel.GetProgramInfo()
        title = f"{info[0]}.*{info[2]}.*{info[1]}"
        try:
            # from pywinauto import Desktop
            windows = Desktop(backend="uia").windows(title_re=f".*{title}.*")
            if len(windows) > 0:
                print(f"{' '.join(info[:-1])}")
                self.etabs_pywinauto = windows[0]
                return windows[0]
            # ver = self.version()
            # for i, window in enumerate(windows):
            #     title = window.window_text()
            #     print(f"{i}: {title}")
            #     if ver in title:
            #         self.etabs_pywinauto = window
            #         return self.etabs_pywinauto
        except (comtypes.COMError, AttributeError):
            print(f"No ETABS version found with title: {' '.join(info[:-1])}.")
            if windows:
                self.etabs_pywinauto = windows[0]
            else:
                self.etabs_pywinauto = None
        return self.etabs_pywinauto

    def set_special_values_according_to_software_and_version(self):
        self.etabs_main_version = self.get_etabs_main_version()
        if self.software == "ETABS":
            if self.etabs_main_version < 20:
                self.seismic_drift_text = 'Seismic (Drift)'
                self.seismic_drift_load_type = 37
                self.ecc_overwrite_story = 'Ecc Overwrite Story'
                self.auto_seismic_user_coefficient_columns_part1 = [
                    'Name',
                    'Is Auto Load',
                    'X Dir?',
                    'X Dir Plus Ecc?',
                    'X Dir Minus Ecc?',
                    'Y Dir?',
                    'Y Dir Plus Ecc?',
                    'Y Dir Minus Ecc?',
                    'Ecc Ratio',
                    'Top Story',
                    'Bottom Story',
                ]
                self.auto_seismic_user_coefficient_columns_part2 = [
                    self.ecc_overwrite_story,
                    'Ecc Overwrite Diaphragm',
                    'Ecc Overwrite Length',
                ]
                self.auto_notional_loads_columns = ['Load Pattern', 'Base Load Pattern', 'Load Ratio', 'Load Direction']
            else:
                self.seismic_drift_text = 'QuakeDrift'
                self.seismic_drift_load_type = 61
                self.ecc_overwrite_story = 'OverStory'
                self.auto_seismic_user_coefficient_columns_part1 = [
                    'Name',
                    'IsAuto',
                    'XDir',
                    'XDirPlusE',
                    'XDirMinusE',
                    'YDir',
                    'YDirPlusE',
                    'YDirMinusE',
                    'EccRatio',
                    'TopStory',
                    'BotStory',
                ]
                self.auto_seismic_user_coefficient_columns_part2 = [
                    self.ecc_overwrite_story,
                    'OverDiaph',
                    'OverEcc',
                ]
                self.auto_notional_loads_columns = ['LoadPattern', 'BasePattern', 'LoadRatio', 'LoadDir']

    def get_etabs_main_version(self):
        ver = self.SapModel.GetVersion()
        return int(ver[0].split('.')[0])
    
    def close_etabs(self):
        self.SapModel.SetModelIsLocked(False)
        self.etabs.ApplicationExit(False)
        self.SapModel = None
        self.etabs = None

    def backup_model(self, name=None):
        max_num = 0
        backup_path=None
        asli_file_path = self.get_filename()
        suffix = asli_file_path.suffix
        if name is None:
            filename = self.get_file_name_without_suffix()
            file_path = self.get_filepath()
            backup_path = file_path / 'backups'
            if not backup_path.exists():
                import os
                os.mkdir(str(backup_path))
            for edb in backup_path.glob(f'BACKUP_{filename}*{suffix}'):
                num = edb.name.rstrip(suffix)[len('BACKUP_') + len(filename) + 1:]
                try:
                    num = int(num)
                    max_num = max(max_num, num)
                except ValueError:
                    continue
            name = f'BACKUP_{filename}_{max_num + 1}{suffix}'
        if not name.lower().endswith(suffix.lower()):
            name += suffix
        asli_file_path = asli_file_path.with_suffix(suffix)
        if backup_path is None:
            new_file_path = asli_file_path.parent / name
        else:
            new_file_path = backup_path / name
        shutil.copy(asli_file_path, new_file_path)
        return new_file_path

    def remove_backups(self):
        file_path = self.get_filepath() / 'backups'
        asli_file_path = self.get_filename()
        suffix = asli_file_path.suffix
        for edb in file_path.glob(f'BACKUP_*{suffix}'):
            edb.unlink()
        return None

    def restore_backup(self, filepath):
        current_file_path = self.get_filename()
        self.SapModel.File.OpenFile(str(filepath))
        self.SapModel.File.Save(str(current_file_path))

    def lock_model(self):
        self.SapModel.SetModelIsLocked(True)
    
    def unlock_model(self):
        name = self.get_filename()
        print(f"Unlock Model: {name}")
        self.SapModel.SetModelIsLocked(False)

    def lock_and_unlock_model(self):
        self.SapModel.SetModelIsLocked(True)
        self.SapModel.SetModelIsLocked(False)

    def run_analysis(self, open_lock=False):
        if self.SapModel.GetModelIsLocked():
            if open_lock:
                self.SapModel.SetModelIsLocked(False)
                print('Run Analysis ...')
                self.SapModel.analyze.RunAnalysis()
        else:
            print('Run Analysis ...')
            self.SapModel.analyze.RunAnalysis()

    def start_design(self,
        type_: str = 'Concrete', # Steel
        check_designed: bool=True,
        ):
        if check_designed and self.design.model_designed(type_=type_):
            return
        self.run_analysis()
        print(f"Starting Design {type_}")
        exec(f"self.SapModel.Design{type_}.StartDesign()")

    def start_slab_design(self):
        if self.etabs_main_version < 20:
            raise NotImplementedError
        self.run_analysis()
        print("Starting Design Slabs")
        self.SapModel.DesignConcreteSlab.StartSlabDesign()

    def set_current_unit(self, force, length):
        # force_enum = EtabsModel.force_units[force]
        # len_enum = EtabsModel.length_units[length]
        number = self.enum_units.get(f"{force}_{length}".lower(), None)
        if number is None:
            raise KeyError
        self.SapModel.SetPresentUnits(number)
    
    def get_current_unit(self,
                         ):
        unit_num = self.SapModel.GetPresentUnits()
        found = False
        for unit_str, n in self.enum_units.items():
            if n == unit_num:
                force, length = unit_str.split("_")[0:2]
                found = True
                break
        if not found:
            force, length = 'N', 'mm'
            self.set_current_unit(force, length)
        return force, length

    def get_file_name_without_suffix(self):
        f = Path(self.SapModel.GetModelFilename())
        name = f.name.replace(f.suffix, '')
        return name
    
    def get_filename_with_suffix(self,
            suffix: str= '.EDB',
            ):
        f = Path(self.SapModel.GetModelFilename())
        f = f.with_suffix(suffix)
        return f.name
    
    def get_filename_path_with_suffix(self,
            suffix: str= '.EDB',
            ):
        file_path = Path(self.etabs.SapModel.GetModelFilename())
        return file_path.with_suffix(suffix)

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

    def get_filename(self) -> Union[Path, None]:
        '''
        return: WindowsPath('H:/1402/montazer/rashidzadeh/etabs/test.EDB')
        '''
        filename = self.SapModel.GetModelFilename()
        if filename is None:
            return None
        return Path(filename)
    
    def get_filepath(self) -> Path:
        return Path(self.SapModel.GetModelFilename()).parent
        
    def save(self):
        self.SapModel.File.Save()

    def save_as(self, name):
        if not name.lower().endswith('.edb'):
            name += '.EDB'
        asli_file_path = Path(self.SapModel.GetModelFilename())
        asli_file_path = asli_file_path.with_suffix('.EDB')
        new_file_path = asli_file_path.with_name(name)
        self.SapModel.File.Save(str(new_file_path))
        return asli_file_path, new_file_path
    
    def get_new_filename_in_folder_and_add_name(self,
                                  folder_name: str,
                                  name: str,
                                  ):
        '''
        Get the current file with FILENAME_name in folder_name
        forlder of etabs file
        '''
        asli_file_path = Path(self.SapModel.GetModelFilename())
        if asli_file_path.suffix.lower() != '.edb':
            asli_file_path = asli_file_path.with_suffix(".EDB")
        # Create folder if not exists
        file_path = self.get_filepath()
        folder_path = file_path / folder_name
        if not folder_path.exists():
            import os
            os.mkdir(str(folder_path))
        filename_without_suffix = self.get_file_name_without_suffix()
        filename = filename_without_suffix + f"_{name}.EDB"
        filename = folder_path / filename
        return asli_file_path, filename
    
    def save_in_folder_and_add_name(self,
                                  folder_name: str,
                                  name: str,
                                  ):
        '''
        Save the current file with FILENAME_name in folder_name
        folder of etabs file
        '''
        asli_file_path, new_filename = self.get_new_filename_in_folder_and_add_name(
            folder_name=folder_name,
            name=name,
            )
        print(f" Save Model As {new_filename}")
        self.SapModel.File.Save(str(new_filename))
        return asli_file_path, new_filename
    
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

    def open_model(self, filename: Union[str, Path]):
        self.SapModel.File.OpenFile(str(filename))

    def get_main_periods(self,
                         modal_case: str='',
                         ):
        print("start running T file analysis")
        if not modal_case:
            modal_case = self.load_cases.get_modal_loadcase_name()
        self.analyze.set_load_cases_to_analyze([modal_case])
        self.SapModel.Analyze.RunAnalysis()
        table_key = "Modal Participating Mass Ratios"
        df = self.database.read(table_key=table_key, to_dataframe=True)
        df = df.astype({'UX': float, 'UY': float})
        self.SapModel.SetModelIsLocked(False)
        max_value_index = df['UX'].idxmax()
        tx_drift = df.loc[max_value_index, 'Period']
        max_value_index = df['UY'].idxmax()
        ty_drift = df.loc[max_value_index, 'Period']
        print(f"Tx_drift = {tx_drift}, Ty_drift = {ty_drift}\n")
        return float(tx_drift), float(ty_drift)

    def get_drift_periods(
                self,
                t_filename: str="",
                structure_type: str='concrete',
                ):
        '''
        This function creates an Etabs file called T.EDB from current open Etabs file,
        then in T.EDB file change the stiffness properties of frame elements according 
        to ACI 318 to get periods of structure, for this it set M22 and M33 stiffness of
        beams to 0.5 and column and wall to 1.0. Then it runs the analysis and get the x
        and y period of structure.
        '''
        print(10 * '-' + "Get drift periods" + 10 * '-' + '\n')
        self.SapModel.File.Save()
        asli_file_path = Path(self.SapModel.GetModelFilename())
        if asli_file_path.suffix.lower() != '.edb':
            asli_file_path = asli_file_path.with_suffix(".EDB")
        # Create periods folder if not exists
        file_path = self.get_filepath()
        period_path = file_path / 'periods'
        if not period_path.exists():
            import os
            os.mkdir(str(period_path))
        filename_without_suffix = self.get_file_name_without_suffix()
        if not t_filename:
            t_filename = filename_without_suffix + "_T.EDB"
        t_file_path = period_path / t_filename
        print(f"Saving file as {t_file_path}\n")
        self.SapModel.File.Save(str(t_file_path))
        # for steel structure
        self.SapModel.DesignSteel.SetCode('AISC ASD 89')
        # for steel structures create a copy of main file
        if structure_type == 'steel':
            t_steel_filename = filename_without_suffix + "_drift.EDB"
            drift_file_path = period_path / t_steel_filename
            shutil.copy(t_file_path, drift_file_path)
        print("get frame property modifiers and change I values\n")
        IMod_beam = 0.5
        IMod_col_wall = 1
        IMod_Floors = 0.25 * 1.5
        for label in self.SapModel.FrameObj.GetLabelNameList()[1]:
            if self.SapModel.FrameObj.GetDesignProcedure(label)[0] == 2:  # concrete
                modifiers = list(self.SapModel.FrameObj.GetModifiers(label)[0])
                if self.SapModel.FrameObj.GetDesignOrientation(label)[0] == 1: # Column
                    modifiers[:6] = 6 * [IMod_col_wall]
                elif self.SapModel.FrameObj.GetDesignOrientation(label)[0] == 2:  # Beam
                    modifiers[4:6] = [IMod_beam, IMod_beam]
                self.SapModel.FrameObj.SetModifiers(label, modifiers)
        # Area Objects
        self.area.reset_slab_sections_modifiers()
        for label in self.SapModel.AreaObj.GetLabelNameList()[1]:
            modifiers = list(self.SapModel.AreaObj.GetModifiers(label)[0])
            if self.SapModel.AreaObj.GetDesignOrientation(label)[0] == 1: # Wall
                modifiers[:6] = 6 * [IMod_col_wall]
            elif self.SapModel.AreaObj.GetDesignOrientation(label)[0] == 2: # Floor
                weight_factor = modifiers[-1]
                for i in range(3, 6):
                    modifiers[i] = IMod_Floors * weight_factor
            self.SapModel.AreaObj.SetModifiers(label, modifiers)
        # run model (this will create the analysis model)
        tx_drift, ty_drift = self.get_main_periods()
        if structure_type == 'concrete':
            print("opening the main file\n")
            self.SapModel.File.OpenFile(str(asli_file_path))
        else:
            # for steel structure
            print("opening the Drift file\n")
            self.SapModel.File.OpenFile(str(drift_file_path))
        return tx_drift, ty_drift, asli_file_path

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
        if loadcases is None:
            loadcases = self.load_cases.get_seismic_drift_load_cases()
        print(loadcases)
        x_cases, y_cases = self.load_cases.get_xy_seismic_load_cases()
        if x_loadcases is None:
            x_loadcases = x_cases
        if y_loadcases is None:
            y_loadcases = y_cases
        self.analyze.change_run_status_of_load_cases(
            loadcases + x_loadcases + y_loadcases,
            True,
            )
        self.run_analysis()
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
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        [_, _, fields_keys_included, _, table_data, _] = self.database.read_table(table_key)
        table_data = self.apply_cfactor_to_tabledata(table_data, fields_keys_included, building, bot_story, top_story)
        num_fatal_errors, ret = self.database.write_seismic_user_coefficient(table_key, fields_keys_included, table_data)
        print(f"num_fatal_errors, ret = {num_fatal_errors}, {ret}")
        return num_fatal_errors
    
    def apply_cfactors_to_edb(
            self,
            data: list,
            d: dict={},
            ):
        '''
        data is a list contain lists, each list contain two list, first
        list is list of earthquakes names and second list is in format
        ['TopStory', 'BotStory', 'C', 'K']
        example:
        data = [
                (['QX', 'QXN'], ["STORY5", "STORY1", '0.128', '1.37']),
                (['QY', 'QYN'], ["STORY4", "STORY2", '0.228', '1.39']),
                ]
        d: dictionary of etabs config file
        '''
        df = self.check_seismic_names(d=d)
        print("Applying cfactor to edb\n")
        cols = self.auto_seismic_user_coefficient_columns_part1[-2:] + ['C', 'K']
        for earthquakes, new_factors in data:
            df.loc[df.Name.isin(earthquakes), cols] = new_factors
        print(df)
        num_fatal_errors, ret = self.database.write_seismic_user_coefficient_df(df)
        print(f"num_fatal_errors, ret = {num_fatal_errors}, {ret}")
        return num_fatal_errors

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
        self.set_current_unit('kgf', 'm')
        z = self.SapModel.story.GetElevation(story_name)[0]
        point_name = self.SapModel.PointObj.AddCartesian(float(x),float(y) , z)[0]  
        diaph = self.story.get_story_diaphragms(story_name).pop()
        self.SapModel.PointObj.SetDiaphragm(point_name, 3, diaph)
        LTYPE_OTHER = 8
        lp_name_x = f'X_STIFFNESS_{story_name}'
        lp_name_y = f'Y_STIFFNESS_{story_name}'
        for lp_name in (lp_name_x, lp_name_y):
            self.SapModel.LoadPatterns.Add(lp_name, LTYPE_OTHER, 0, True)
        load = 100000
        point_load_value_x = [load, 0, 0, 0, 0, 0]
        point_load_value_y = [0, load, 0, 0, 0, 0]
        self.SapModel.PointObj.SetLoadForce(point_name, lp_name_x, point_load_value_x)
        self.SapModel.PointObj.SetLoadForce(point_name, lp_name_y, point_load_value_y)
        self.analyze.set_load_cases_to_analyze([lp_name_x, lp_name_y])
        return point_name, lp_name_x, lp_name_y

    def get_story_stiffness_modal_way(self):
        story_mass = self.database.get_story_mass()[::-1]
        story_mass = {key: value for key, value in story_mass}
        storyname_and_levels = self.story.storyname_and_levels()
        stories = sorted(storyname_and_levels, key=storyname_and_levels.get, reverse=True)[:-1]
        dx, dy, wx, wy = self.database.get_stories_displacement_in_xy_modes()
        story_stiffness = {}
        for i, story in enumerate(stories):
            if story not in story_mass.keys():
                continue
            if story == stories[-1]:
                phi_below_x = 0
                phi_below_y = 0
            else:
                below_story = stories[i + 1]
                phi_below_x = dx.get(below_story)
                phi_below_y = dy.get(below_story)
            d_phi_x = dx.get(story) - phi_below_x
            d_phi_y = dy.get(story) - phi_below_y
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
        folder_name = "story_stiffness"
        folder_path = dir_path / folder_name
        if not folder_path.exists():
            import os
            os.mkdir(str(folder_path))
        for story_name in story_names:
            story_file_path = folder_path / f'{name}_STIFFNESS_{story_name}.EDB'
            print(f"Saving file as {story_file_path}\n")
            shutil.copy(asli_file_path, story_file_path)
            print(f"Opening file {story_file_path}\n")
            self.SapModel.File.OpenFile(str(story_file_path))
            x, y = center_of_rigidity[story_name]
            point_name, lp_name_x, lp_name_y = self.add_load_case_in_center_of_rigidity(
                    story_name, x, y)
            self.story.fix_below_stories(story_name)
            self.SapModel.View.RefreshView()
            self.SapModel.Analyze.RunAnalysis()
            disp_x = self.results.get_point_xy_displacement(point_name, lp_name_x)[0]
            disp_y = self.results.get_point_xy_displacement(point_name, lp_name_y)[1]
            kx, ky = 100000 / abs(disp_x), 100000 / abs(disp_y)
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
        storyname_and_levels = self.story.storyname_and_levels()
        stories = sorted(storyname_and_levels, key=storyname_and_levels.get, reverse=True)
        retval = []
        for i, story in enumerate(stories):
            stiffness = story_stiffness.get(story, None)
            if stiffness is None:
                continue
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
        ex_name : Union[str, list],
        ey_name : Union[str, list],
        x_specs : list,
        y_specs : list,
        x_scale_factor : float = 0.9, # 0.85, 0.9, 1
        y_scale_factor : float = 0.9, # 0.85, 0.9, 1
        num_iteration : int = 3,
        tolerance : float = .05,
        reset_scale : bool = True,
        analyze : bool = True,
        consider_min_static_base_shear : bool = False,
        d: Union[None, dict] = None,
        ):
        assert x_scale_factor in (0.85, 0.9, 1)
        assert y_scale_factor in (0.85, 0.9, 1)
        if isinstance(ex_name, str):
            ex_name = [ex_name]
        if isinstance(ey_name, str):
            ey_name = [ey_name]
        ex_names = ex_name
        ey_names = ey_name
        print(f'{ex_names=}, {ey_names=}, {x_specs=}, {y_specs=}, {x_scale_factor=}, {y_scale_factor=}, {tolerance=}')
        self.SapModel.File.Save()
        if reset_scale:
            self.load_cases.reset_scales_for_response_spectrums(loadcases=x_specs+y_specs)
        self.set_current_unit('kgf', 'm')
        self.analyze.set_load_cases_to_analyze(ex_names + ey_names + x_specs + y_specs)
        V = self.results.get_base_react(
                loadcases=ex_names + ey_names,
                directions=len(ex_names) * ['x'] + len(ey_names) * ['y'],
                absolute=True,
                )
        vexes = V[0:len(ex_names)]
        veyes = V[len(ex_names):]
        vex = sum(vexes)
        vey = sum(veyes)
        if consider_min_static_base_shear:
            def acceleration(risk_level):
                accs = {'کم': 0.20,
                        'متوسط': 0.25,
                        'زیاد': 0.3,
                        'خیلی زیاد': 0.35}
                return accs[risk_level]
            if d is None:
                d = self.get_settings_from_model()
            acc = acceleration(d.get("risk_level"))
            importance_factor = float(d.get("importance_factor"))
            earthquake_factors = self.load_patterns.get_earthquake_values(ex_names + ey_names)
            cxes = earthquake_factors[0: len(ex_names)]
            cyes = earthquake_factors[len(ex_names):]
            wx = sum([vex / cx for vex, cx in zip(vexes, cxes)])
            wy = sum([vey / cy for vey, cy in zip(veyes, cyes)])
            c_min = 0.12 * acc * importance_factor
            vx_min = c_min * wx
            vy_min = c_min * wy
            print(f"{cxes=}, {cyes=}, {wx=}, {wy=}, {c_min=}, {vx_min=}, {vy_min=}")
        print(f'{vexes=}, {veyes=}')
        for i in range(num_iteration):
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
            print(f'{vsx=}, {vsy=}')
            x_scales = []
            y_scales = []
            for v in vsx:
                scale = x_scale_factor * vex / v
                if consider_min_static_base_shear:
                    scale = max(vx_min / v, scale)
                x_scales.append(scale)
            for v in vsy:
                scale = y_scale_factor * vey / v
                if consider_min_static_base_shear:
                    scale = max(vy_min / v, scale)
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
        force = self.get_current_unit()[0]
        import pandas as pd
        load_cases = ['&'.join(ex_names),  '&'.join(ey_names)] + x_specs + y_specs
        base_shear = [vex, vey] + vsx + vsy
        ratios = [1, 1] + [vx / vex for vx in vsx] + [vy / vey for vy in vsy]
        final_scales = [1, 1] # Get final scales that applied in etabs model
        for name in x_specs + y_specs:
            ret = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(name)
            final_scales.append(ret[3][0])
        df = pd.DataFrame({
            'Case': load_cases,
            f'V ({force})': base_shear,
            'Ratio': ratios,
            'Scale': final_scales,
            })
        self.unlock_model()
        self.analyze.set_load_cases_to_analyze()
        if analyze:
            self.run_analysis()
        return x_scales, y_scales, df

    def angles_response_spectrums_analysis(self,
        ex_name : list,
        ey_name : list,
        specs : list = None,
        section_cuts : list = None,
        scale_factor : float = 0.9, # 0.85, 0.9, 1
        num_iteration : int = 3,
        tolerance : float = .02,
        reset_scale : bool = True,
        analyze : bool = True,
        ):
        if isinstance(ex_name, str):
            ex_name = [ex_name]
        if isinstance(ey_name, str):
            ey_name = [ey_name]
        ex_names = ex_name
        ey_names = ey_name
        print(f"{ex_names=}, {ey_names=}, {specs=}, {section_cuts=}")
        self.SapModel.File.Save()
        if reset_scale:
            self.load_cases.reset_scales_for_response_spectrums(loadcases=specs)
        loadcases = ex_names + ey_names + specs
        base_shear_spec = {}
        base_shear_ex = {}
        base_shear_ey = {}
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
            angle_specs = {}
            df['F1'] = df['F1'].astype(float)
            for i, row in spec_sec_angle.iterrows():
                spec = row['OutputCase']
                section_cut = row['SectionCut']
                angle = row['angle']
                angle_specs[angle] = spec
                df_angle_section = df[(df['SectionCut'] == section_cut) & (df['angle'] == angle)][['F1', 'OutputCase']]
                df_angle_section.set_index('OutputCase', inplace=True)
                f_ex = abs(sum(df_angle_section.loc[ex_names, 'F1']))
                f_ey = abs(sum(df_angle_section.loc[ey_names, 'F1']))
                f_spec = abs(df_angle_section.loc[spec, 'F1'])
                scale = scale_factor * math.sqrt(f_ex ** 2 + f_ey ** 2) / f_spec
                spec_scales[spec] = scale
                scales.append(scale)
                base_shear_spec[angle] = f_spec
                base_shear_ex[angle] = f_ex
                base_shear_ey[angle] = f_ey
            print(scales)
            max_scale = max(scales)
            min_scale = min(scales)
            if (max_scale < 1 + tolerance) and (min_scale > 1 - tolerance):
                break
            else:
                for spec, scale in spec_scales.items():
                    self.load_cases.multiply_response_spectrum_scale_factor(spec, scale)
        force = self.get_current_unit()[0]
        import pandas as pd
        base_shear_specs = []
        base_shear_exs = []
        base_shear_eys = []
        load_cases =  []
        final_scales = []
        for angle in angles:
            base_shear_specs.append(base_shear_spec[angle])
            base_shear_exs.append(base_shear_ex[angle])
            base_shear_eys.append(base_shear_ey[angle])
            load_cases.append(angle_specs[angle])
            ret = self.SapModel.LoadCases.ResponseSpectrum.GetLoads(angle_specs[angle])
            final_scales.append(ret[3][0])
        ex_names_str = '&'.join(ex_names)
        ey_names_str = '&'.join(ey_names)
        ex_name_col_title = ex_names_str + f' {force}'
        ey_name_col_title = ey_names_str + f' {force}'
        spec_col_title = f'SPEC ({force})'
        df = pd.DataFrame({
            "Name": load_cases,
            'Angle': angles,
            spec_col_title: base_shear_specs,
            ex_name_col_title: base_shear_exs,
            ey_name_col_title: base_shear_eys,
            # 'Ratio': ratios,
            # 'Scale': final_scales,
            })
        static_col_title = f"({ex_names_str}^2 + {ey_names_str}^2) ^0.5"
        df[static_col_title] = df.apply(
            lambda row: math.sqrt(row[ex_name_col_title] ** 2 + row[ey_name_col_title] ** 2),
            axis=1,
            )
        df['Scale'] = final_scales
        df['Ratio'] = df.apply(
            lambda row: row[spec_col_title] / row[static_col_title], axis=1
        )
        self.unlock_model()
        self.analyze.set_load_cases_to_analyze()
        if analyze:
            self.run_analysis()
        return scales, df

    def create_joint_shear_bcc_file(self,
        file_name: Union[str, Path]= 'js',
        structure_type: str = 'Sway Intermediate',
        open_main_file: bool =  False,
        create_file: bool = True,
        ):
        version = self.etabs_main_version
        if version < 22 and create_file:
            # get main file path
            main_file_path = Path(self.SapModel.GetModelFilename())
            main_file_path = main_file_path.with_suffix(".EDB")
            if structure_type == 'Sway Intermediate':
                self.save_in_folder_and_add_name(folder_name="joint_shear", name=str(file_name))
                phi = 0.75
                self.design.set_concrete_framing_type(1, beams=False)
            else:
                phi = 0.85
            self.design.set_phi_joint_shear(phi)
        self.start_design()
        table_key = self.database.table_name_that_containe("Concrete Joint Design Summary")
        if table_key is None:
            return None
        cols = ['Story', 'Label', 'UniqueName', 'JSMajRatio', 'JSMinRatio', 'BCMajRatio', 'BCMinRatio']
        df = self.database.read(table_key=table_key, to_dataframe=True, cols=cols)
        if all((
            create_file,
            structure_type == 'Sway Intermediate',
            open_main_file,
            version < 22,
        )):
            self.SapModel.File.OpenFile(str(main_file_path))
        return df
    
    def purge_model(self):
        '''
        Remove All frames and areas from model
        '''
        self.frame_obj.delete_frames()
        self.area.delete_areas()
    
    def get_type_of_structure(self):
        '''
        Return 'steel' or 'concrete'
        '''
        steel = 'steel'
        concrete = 'concrete'
        steel_beams, steel_columns = self.frame_obj.get_beams_columns(type_=1)
        concrete_beams, concrete_columns = self.frame_obj.get_beams_columns(type_=2)
        if len(concrete_columns) > len(steel_columns):
            return concrete
        elif len(concrete_columns) < len(steel_columns):
            return steel
        if len(concrete_beams) > len(steel_beams):
            return concrete
        elif len(concrete_beams) < len(steel_beams):
            return steel
        return concrete
    
    def get_settings_from_model(self):
        d = {}
        info = self.SapModel.GetProjectInfo()
        json_str = info[2][0]
        try:
            company_name = json.loads(json_str)
        except json.JSONDecodeError:
            return d
        if isinstance(company_name, dict):
            d = company_name
        return d
    
    def update_setting(
        self,
        keys: Union[list, dict],
        values: Union[list, None] = None,
        ):
        '''
        update etabs setting dictionary with keys and values or dict 
        '''
        d = self.get_settings_from_model()
        if isinstance(keys, dict):
            new_d = keys
        else:
            new_d = dict(zip(keys, values))
        d.update(new_d)
        self.set_settings_to_model(d)

    def set_settings_to_model(self, d: dict):
        json_str = json.dumps(d)
        self.SapModel.SetProjectInfo("Company Name", json_str)
        self.SapModel.File.Save()
        
    def get_first_system_seismic(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        ex = d.get('ex_combobox', 'EX')
        exn = d.get('exn_combobox', 'EXN')
        exp = d.get('exp_combobox', 'EXP')
        ey = d.get('ey_combobox', 'EY')
        eyn = d.get('eyn_combobox', 'EYN')
        eyp = d.get('eyp_combobox', 'EYP')
        return ex, exn, exp, ey, eyn, eyp

    def get_second_system_seismic(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        ex = d.get('ex1_combobox', 'EX1')
        exn = d.get('exn1_combobox', 'EXN1')
        exp = d.get('exp1_combobox', 'EXP1')
        ey = d.get('ey1_combobox', 'EY1')
        eyn = d.get('eyn1_combobox', 'EYN1')
        eyp = d.get('eyp1_combobox', 'EYP1')
        return ex, exn, exp, ey, eyn, eyp
    
    def get_first_system_seismic_drift(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        ex = d.get('ex_drift_combobox', 'EX(Drift)')
        exn = d.get('exn_drift_combobox', 'EXN(Drift)')
        exp = d.get('exp_drift_combobox', 'EXP(Drift)')
        ey = d.get('ey_drift_combobox', 'EY(Drift)')
        eyn = d.get('eyn_drift_combobox', 'EYN(Drift)')
        eyp = d.get('eyp_drift_combobox', 'EYP(Drift)')
        return ex, exn, exp, ey, eyn, eyp

    def get_second_system_seismic_drift(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        ex = d.get('ex1_drift_combobox', 'EX1(Drift)')
        exn = d.get('exn1_drift_combobox', 'EXN1(Drift)')
        exp = d.get('exp1_drift_combobox', 'EXP1(Drift)')
        ey = d.get('ey1_drift_combobox', 'EY1(Drift)')
        eyn = d.get('eyn1_drift_combobox', 'EYN1(Drift)')
        eyp = d.get('eyp1_drift_combobox', 'EYP1(Drift)')
        return ex, exn, exp, ey, eyn, eyp
    
    def get_dynamic_loadcases(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        sx = d.get('sx_combobox', 'SX')
        sxe = d.get('sxe_combobox', 'SXE')
        sy = d.get('sy_combobox', 'SY')
        sye = d.get('sye_combobox', 'SYE')
        return sx, sxe, sy, sye
    
    def get_dynamic_drift_loadcases(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        sx = d.get('sx_drift_combobox', 'SX(Drift)')
        sxe = d.get('sxe_drift_combobox', 'SXE(Drift)')
        sy = d.get('sy_drift_combobox', 'SY(Drift)')
        sye = d.get('sye_drift_combobox', 'SYE(Drift)')
        return sx, sxe, sy, sye

    def get_angular_dynamic_loadcases(self, d: dict={}):
        '''
        return dict{angle: (sec_cut, spec)}
        '''
        if not d:
            d = self.get_settings_from_model()
        dic = d.get("angular_tableview", {})
        return dic
    
    def get_top_bot_stories(self, d: dict={}):
        if not d:
            d = self.get_settings_from_model()
        bot_1 = d.get('bot_x_combo', '')
        top_1 = d.get('top_x_combo', '')
        bot_2 = d.get('bot_x1_combo', '')
        top_2 = d.get('top_x1_combo', '')
        return bot_1, top_1, bot_2, top_2

    def check_seismic_names(
            self,
            d: dict={},
            apply: bool=False,
            ):
        import pandas as pd
        import copy
        if not d:
            d = self.get_settings_from_model()
        seismic_loads = self.load_patterns.get_seismic_load_patterns()
        seismic_loads_drifts = self.load_patterns.get_seismic_load_patterns(drifts=True)
        self.SapModel.SetModelIsLocked(False)
        self.load_patterns.select_all_load_patterns()
        table_key = 'Load Pattern Definitions - Auto Seismic - User Coefficient'
        df = self.database.read(table_key, to_dataframe=True)
        if df is None:
            df = pd.DataFrame(columns=self.auto_seismic_user_coefficient_columns_part1+['C', 'K'])
            df.loc[0] = ''
            df['IsAuto'] = 'No'
        row = copy.deepcopy(df.iloc[0])
        seismic_columns = ['XDir', 'XDirMinusE', 'XDirPlusE', 'YDir', 'YDirMinusE', 'YDirPlusE']
        row[seismic_columns] = 'No'
        row['EccRatio'] = '0.0'
        if self.ecc_overwrite_story in df.columns:
            row[self.auto_seismic_user_coefficient_columns_part2] = None
        new_rows = []
        not_es = []
        not_es_drifts = []
        # First system
        first_system_seismic = self.get_first_system_seismic(d)
        for es, e, col in zip(seismic_loads, first_system_seismic, seismic_columns):
            if e not in es:
                not_es.append(e)
                new_row = copy.deepcopy(row)
                new_row[col] = 'Yes'
                new_row['Name'] = e
                if 'usE' in col:
                    new_row['EccRatio'] = '0.05'
                new_rows.append(new_row)
        # Drift seismic loads
        first_system_seismic = self.get_first_system_seismic_drift(d)
        # First system Drifts
        for es, e, col in zip(seismic_loads_drifts, first_system_seismic, seismic_columns):
            if e not in es:
                not_es_drifts.append(e)
                new_row = copy.deepcopy(row)
                new_row[col] = 'Yes'
                new_row['Name'] = e
                if 'usE' in col:
                    new_row['EccRatio'] = '0.05'
                new_rows.append(new_row)
        # Second system
        if d.get('activate_second_system', False):
            second_system_seismic = self.get_second_system_seismic(d)
            for es, e, col in zip(seismic_loads, second_system_seismic, seismic_columns):
                if e not in es:
                    not_es.append(e)
                    new_row = copy.deepcopy(row)
                    new_row[col] = 'Yes'
                    new_row['Name'] = e
                    if 'usE' in col:
                        new_row['EccRatio'] = '0.05'
                    new_rows.append(new_row)
            # Drift seismic loads
            second_system_seismic = self.get_second_system_seismic_drift(d)
            # First system Drifts
            for es, e, col in zip(seismic_loads_drifts, second_system_seismic, seismic_columns):
                if e not in es:
                    not_es_drifts.append(e)
                    new_row = copy.deepcopy(row)
                    new_row[col] = 'Yes'
                    new_row['Name'] = e
                    if 'usE' in col:
                        new_row['EccRatio'] = '0.05'
                    new_rows.append(new_row)
        if len(not_es) > 0:
            self.load_patterns.add_load_patterns(not_es, 'Seismic')
        if len(not_es_drifts) > 0:
            self.load_patterns.add_load_patterns(not_es_drifts, self.seismic_drift_text)
        df2 = pd.DataFrame(new_rows)
        df = pd.concat([df, df2])
        if apply:
            self.database.write_seismic_user_coefficient_df(df)
        return df
    
    def get_json_file_path_for_table_results(
            self,
            json_filename: str,
    ) -> Path:
        '''
        json_filename: json filename
        '''
        name = self.get_file_name_without_suffix()
        table_result_path = self.get_filepath() / f"{name}_table_results"
        if not table_result_path.exists():
            table_result_path.mkdir()
        if not json_filename.endswith('.json'):
            json_filename += ".json"
        return table_result_path / json_filename
    
    def scale_response_spectrum_with_respect_to_settings(self,
                                                         d: Union[dict, None]=None,
                                                         analyze: bool=False,
                                                         consider_min_static_base_shear: bool=False,
                                                         reset_scale: bool=True,
                                                         ):
        if d is None:
            d = self.get_settings_from_model()
        ex_name = d.get("ex_combobox")
        ey_name = d.get("ey_combobox")
        x_scale_factor = float(d.get("x_scalefactor_combobox", 1.0))
        y_scale_factor = float(d.get("y_scalefactor_combobox", 1.0))
        if d.get("combination_response_spectrum_checkbox", False):
            print("Start 100-30 Scale Response Spectrum\n")
            sx, sxe, sy, sye = self.get_dynamic_loadcases(d)
            x_specs = [sx, sxe]
            y_specs = [sy, sye]
            self.scale_response_spectrums(
                ex_name,
                ey_name,
                x_specs,
                y_specs,
                x_scale_factor,
                y_scale_factor,
                analyze=analyze,
                consider_min_static_base_shear=consider_min_static_base_shear,
                reset_scale=reset_scale,
                d=d,
            )
        elif d.get("angular_response_spectrum_checkbox", False):
            print("Start angular Scale Response Spectrum\n")
            specs = []
            section_cuts = []
            key = "angular_tableview"
            dic = d.get(key, None)
            if dic is not None:
                for sec_cut, spec in dic.values():
                    section_cuts.append(sec_cut)
                    specs.append(spec)
                self.angles_response_spectrums_analysis(
                    ex_name,
                    ey_name,
                    specs,
                    section_cuts,
                    x_scale_factor,
                    analyze=analyze,
                    reset_scale=reset_scale,
                )

    def get_x_and_y_system_ductility(self,
                                     d: Union[dict, None],
                                     ) -> list:
        '''
        H: High, M: Medium, L: Low
        '''
        if d is None:
            d = self.get_settings_from_model()
        x_system = d.get('x_system', [2, 1])
        y_system = d.get('y_system', [2, 1])
        ductilities = []
        for system in (x_system, y_system):
            if system in (
                [0, 0],
                [1, 0], [1, 4], [1, 7],
                [2, 0], [2, 3],
                [3, 0], [3, 4], [3, 5], [3, 6], [3, 7],
                [4, 0],
                ):
                ductilities.append('H')
            elif system in (
                [0, 1],
                [1, 1],
                [2, 1], [2, 4],
                [3, 2], [3, 3],
            ):
                ductilities.append('M')
            elif system in (
                [0, 2],
                [1, 2], [1, 6],
                [2, 2], [2, 5],
            ):
                ductilities.append('L')
            else:
                ductilities.append(None)
        return ductilities




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