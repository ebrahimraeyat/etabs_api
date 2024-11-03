from pathlib import Path
from typing import Iterable, Union
import math

from python_functions import change_unit

try:
    import freecad_funcs
except NameError:
    pass


class FrameObj:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = self.etabs.SapModel

    def set_end_release_frame(self, name):
        end_release = self.SapModel.FrameObj.GetReleases(name)
        II = list(end_release[0])
        JJ = list(end_release[1])
        II[3:] = [True] * len(II[3:])
        JJ[4:] = [True] * len(II[4:])
        end_release[0] = tuple(II)
        end_release[1] = tuple(JJ)
        end_release.insert(0, name)
        er = self.SapModel.FrameObj.SetReleases(*end_release)
        return er

    def is_column(self, name):
        return self.SapModel.FrameObj.GetDesignOrientation(name)[0] == 1
    
    def is_beam(self, name):
        return self.SapModel.FrameObj.GetDesignOrientation(name)[0] == 2
    
    def is_brace(self, name):
        return self.SapModel.FrameObj.GetDesignOrientation(name)[0] == 3

    def get_section_name(self, frame_name):
        return self.SapModel.FrameObj.GetSection(frame_name)[0]
    
    def set_section_name(self,
        frame_name : str,
        name : str,
        ):
        self.SapModel.FrameObj.SetSection(frame_name, name)

    def set_sections_name(self,
        frame_names : list,
        name : str,
        ):
        for frame in frame_names:
            self.set_section_name(frame, name)

    def set_end_length_offsets(self,
                               value: float=0.5,
                               ):
        beams, columns = self.get_beams_columns(types=range(1,10))
        for frame in beams + columns:
            self.SapModel.FrameObj.SetEndLengthOffset(frame, True, 0, 0, value)

        # cols = ['UniqueName', 'OffsetOpt', 'OffsetI', 'OffsetJ', 'RigidFact', 'SelfWtOpt']
        # table_key = 'Frame Assignments - End Length Offsets'
        # df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        # df.RigidFact = str(value)
        # if self.etabs.etabs_main_version < 20:
        #     df.columns = ['UniqueName', 'Offset Option', 'Offset I', 'Offset J', 'Rigid Factor', 'Self Weight Option']
        # self.etabs.database.write(table_key, df)

    def is_frame_on_story(self, frame, story=None):
        if story is None:
            return True
        st = self.SapModel.FrameObj.GetLabelFromName(frame)[1]
        return st == story

    def get_design_procedure(self, name):
        '''    
        Program determined = 0
        Steel Frame Design = 1
        Concrete Frame Design = 2
        Composite Beam Design = 3
        Steel Joist Design = 4
        No Design = 7
        Composite Column Design = 13
        '''
        map_dict = {
            0 : 'auto',
            1 : 'steel',
            2 : 'concrete',
            3 : 'composite beam',
            7 : 'No Design',
            13 : 'composite column'
        }
        number = self.SapModel.FrameObj.GetDesignProcedure(name)[0]
        type_ = map_dict.get(number, None)
        return type_

    def get_beams_columns(
            self,
            type_=2,
            types : list =[],
            story : Union[str, bool] = None,
            stories: list=[],
            ):
        '''
        type_: 1=steel and 2=concrete
        '''
        beams = []
        columns = []
        others = []
        types = set(types).union([type_])
        if story is None and len(stories) > 0:
            story = stories[0]
        stories = set(stories).union([story])
        try:
            frames = self.SapModel.FrameObj.GetLabelNameList()
        except:
            return beams, columns
        for label in frames[1]:
            if self.SapModel.FrameObj.GetDesignProcedure(label)[0] in types:
                for story in stories:
                    if self.is_frame_on_story(label, story):
                        if self.is_column(label):
                            columns.append(label)
                        elif self.is_beam(label):
                            beams.append(label)
                        else:
                            others.append(label)
        return beams, columns
    
    def get_beams_columns_on_stories(
            self,
            ) -> dict:
        '''
        type_: 1=steel and 2=concrete
        return a dict with story names as key and a list with beams and columns as values
        {'Story1': [beams, columns]}
        '''
        d = {}
        # Beams
        table_key = "Beam Object Connectivity"
        df = self.etabs.database.read(table_key=table_key, to_dataframe=True, cols=['UniqueName', 'Story'])
        beam_groups = df.groupby('Story')
        for story, group in beam_groups:
            d[story] = [group['UniqueName']]
        # Columns
        table_key = "Column Object Connectivity"
        df = self.etabs.database.read(table_key=table_key, to_dataframe=True, cols=['UniqueName', 'Story'])
        column_groups = df.groupby('Story')
        for story, group in column_groups:
            story_frames = d.get(story, [])
            story_frames.append(group['UniqueName'])
            if len(story_frames) == 1: # Beams not exists on this story
                story_frames.insert(0, [])
                d[story] = story_frames
        for story, group in beam_groups:
            story_frames = d.get(story, [])
            # story_frames.append(group['UniqueName'])
            if len(story_frames) == 1: # columns not exists on this story
                story_frames.insert(1, [])
                d[story] = story_frames
        return d
    
    def get_unique_frames(self,
        frame_names: list,
        ):
        unique_names = []
        labels = []
        for frame in frame_names:
            label, _, _ = self.etabs.SapModel.FrameObj.GetLabelFromName(frame)
            if label not in labels:
                labels.append(label)
                unique_names.append(frame)
        return unique_names, labels
    
    def get_columns_type_names(self) -> dict:
        '''
        return the column types in a dict like 
        { c1: [12, 22, 32], c2: [13, 23, 33], ...}
        '''
        ret = {}
        columns = self.get_beams_columns(types=[1,2])[1]
        labels = self.get_unique_frames(columns)[1]
        stories = self.etabs.story.get_level_names()[1:]
        for lable in labels:
            names = []
            for story in stories:
                name = self.SapModel.FrameObj.GetNameFromLabel(lable, story)[0]
                names.append(name)
            ret[lable] = names
        return ret

    def get_columns_type_sections(self,
                                  dataframe: bool=False,
                                  ) -> Union[dict, 'pandas.DataFrame']:
        '''
        return the column type sections in a dict like 
        { c1: ['C5012A', 'C5012AC', 'C5012C'], c2: [...], ...}
        '''
        ret = {}
        columns_type_names = self.get_columns_type_names()
        for key, value in columns_type_names.items():
            sections = []
            for name in value:
                if name is None:
                    sections.append(None)
                else:
                    sections.append(self.get_section_name(name))
            ret[key] = sections
        if dataframe:
            import pandas as pd
            df = pd.DataFrame(ret)
            stories = self.etabs.story.get_level_names()[1:]
            df.set_index(pd.Index(stories), inplace=True)
            ret = pd.DataFrame(df).iloc[::-1]
            df1 = pd.DataFrame(columns_type_names)
            df1.set_index(pd.Index(stories), inplace=True)
            columns_type_names = pd.DataFrame(df1).iloc[::-1]
        return ret, columns_type_names

    def get_columns_pmm_and_beams_rebars(self, frame_names):
        if not self.SapModel.GetModelIsLocked():
            self.etabs.analyze.set_load_cases_to_analyze()
            self.etabs.run_analysis()
        if not self.SapModel.DesignConcrete.GetResultsAvailable():
            self.set_frame_obj_selected(frame_names)
            self.SapModel.SelectObj.ClearSelection()
            print('Start Design ...')
            self.SapModel.DesignConcrete.StartDesign()
        self.etabs.set_current_unit('kgf', 'cm')
        beams, columns = self.get_beams_columns()
        beams = set(frame_names).intersection(beams)
        columns = set(frame_names).intersection(columns)
        columns_pmm = dict()
        for col in columns:
            pmm = max(self.SapModel.DesignConcrete.GetSummaryResultsColumn(col)[6])
            columns_pmm[col] = round(pmm, 3)
        beams_rebars = dict()
        for name in beams:
            d = dict()
            beam_rebars = self.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
            d['location'] = beam_rebars[2]
            d['TopArea'] = beam_rebars[4]
            d['BotArea'] = beam_rebars[6]
            d['VRebar'] = beam_rebars[8]
            beams_rebars[name] = d
        return columns_pmm, beams_rebars

    def combine_beams_columns_weakness_structure(
                self,
                columns_pmm,
                beams_rebars,
                columns_pmm_weakness,
                beams_rebars_weakness,
                dir_ : str = 'x',
                ):
        columns_pmm_main_and_weakness = []
        for key, value in columns_pmm.items():
            value2 = columns_pmm_weakness[key]
            label, story, _ = self.SapModel.FrameObj.GetLabelFromName(key)
            ratio = round(value2/value, 3)
            columns_pmm_main_and_weakness.append((story, label, value, value2, ratio))
        col_fields = ('Story', 'Label', 'PMM Ratio1', 'PMM ratio2', 'Ratio')
        beams_rebars_main_and_weakness = []
        for key, d in beams_rebars.items():
            d2 = beams_rebars_weakness[key]
            label, story, _ = self.SapModel.FrameObj.GetLabelFromName(key)
            locations = d['location']
            top_area1 = d['TopArea']
            top_area2 = d2['TopArea']
            bot_area1 = d['BotArea']
            bot_area2 = d2['BotArea']
            vrebar1 = d['VRebar']
            vrebar2 = d2['VRebar']
            for l, ta1, ta2, ba1, ba2, v1, v2 in zip(locations,
                    top_area1, top_area2, bot_area1, bot_area2, vrebar1, vrebar2):
                beams_rebars_main_and_weakness.append((
                    story,
                    label,
                    l,
                    ta1, ta2,
                    ba1, ba2,
                    v1, v2,
                    ))
        beam_fields = (
                'Story', 'Label', 'location',
                'Top Area1', 'Top Area2',
                'Bot Area1', 'Bot Area2',
                'VRebar1', 'VRebar2',
                )
        json_name = f'columns_pmm_beams_rebars_{dir_}.json'
        data = (columns_pmm_main_and_weakness, col_fields,
            beams_rebars_main_and_weakness, beam_fields)
        self.etabs.save_to_json_in_edb_folder(json_name, data)
        return (columns_pmm_main_and_weakness, col_fields,
            beams_rebars_main_and_weakness, beam_fields)

    def get_beams_columns_weakness_structure(
                    self,
                    name: str = '',
                    weakness_filename : Union[str, Path] = "weakness.EDB",
                    dir_ : str = 'x',
                    dynamic: bool=False,
                    d: Union[dict, None] = None,
                    ):
        if not name:
            try:
                name = self.SapModel.SelectObj.GetSelected()[2][0]
            except IndexError:
                return None
        self.SapModel.File.Save()
        story = self.SapModel.FrameObj.GetLabelFromName(name)[1]
        story_frames = list(self.SapModel.FrameObj.GetNameListOnStory(story)[1])
        story_frames.remove(name)
        print('get columns pmm and beams rebars')
        columns_pmm, beams_rebars = self.get_columns_pmm_and_beams_rebars(story_frames)
        asli_file_path = Path(self.SapModel.GetModelFilename())
        if asli_file_path.suffix.lower() != '.edb':
            asli_file_path = asli_file_path.with_suffix(".EDB")
        if isinstance(weakness_filename, Path) and weakness_filename.exists():
            self.SapModel.File.OpenFile(str(weakness_filename))
        else:
            print(f"Saving file as {weakness_filename}\n")
            weakness_file_path = asli_file_path.with_name(weakness_filename)
            self.SapModel.File.Save(str(weakness_file_path))
            self.etabs.lock_and_unlock_model()
            print('multiply earthquake factor with 0.67')
            self.etabs.database.multiply_seismic_loads(.67)
            if dynamic:
                if d is None:
                    d = self.etabs.get_settings_from_model()
                ex_name = d.get("ex_combobox")
                ey_name = d.get("ey_combobox")
                x_scale_factor = float(d.get("x_scalefactor_combobox", 1.0))
                y_scale_factor = float(d.get("y_scalefactor_combobox", 1.0))
                if d.get("combination_response_spectrum_checkbox", False):
                    print("Start 100-30 Scale Response Spectrum\n")
                    sx, sxe, sy, sye = self.etabs.get_dynamic_loadcases(d)
                    x_specs = [sx, sxe]
                    y_specs = [sy, sye]
                    self.etabs.scale_response_spectrums(
                        ex_name,
                        ey_name,
                        x_specs,
                        y_specs,
                        x_scale_factor,
                        y_scale_factor,
                        analyze=False,
                        consider_min_static_base_shear=False,
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
                        self.etabs.angles_response_spectrums_analysis(
                            ex_name,
                            ey_name,
                            specs,
                            section_cuts,
                            x_scale_factor,
                            analyze=False,
                        )
            self.set_end_release_frame(name)
        print('get columns pmm and beams rebars')
        columns_pmm_weakness, beams_rebars_weakness = self.get_columns_pmm_and_beams_rebars(story_frames)
        columns_pmm_main_and_weakness, col_fields, \
            beams_rebars_main_and_weakness, beam_fields = self.combine_beams_columns_weakness_structure(
                columns_pmm,
                beams_rebars,
                columns_pmm_weakness,
                beams_rebars_weakness,
                dir_, 
            )
        self.SapModel.File.OpenFile(str(asli_file_path))
        return (columns_pmm_main_and_weakness, col_fields,
            beams_rebars_main_and_weakness, beam_fields)

    def set_frame_obj_selected_in_story(self, story_name):
        frames = self.SapModel.FrameObj.GetNameListOnStory(story_name)[1]
        self.set_frame_obj_selected(frames)
        return frames

    def set_frame_obj_selected(self, frame_objects):
        for fname in frame_objects:
            self.SapModel.FrameObj.SetSelected(fname, True)
        self.SapModel.View.RefreshView()

    def set_constant_j(self,
                j : float = 1,
                beam_names: list = None,
                ):
        assert j <= 1
        if beam_names is None:
            beam_names, _ = self.get_beams_columns(2)
        self.SapModel.SetModelIsLocked(False)
        for name in beam_names:
            modifiers = list(self.SapModel.FrameObj.GetModifiers(name)[0])
            modifiers[3] = j
            self.SapModel.FrameObj.SetModifiers(name, modifiers)
    
    def apply_torsion_stiffness_coefficient(self,
                beams_coeff : dict,
                ):
        self.SapModel.SetModelIsLocked(False)
        for name, ratio in beams_coeff.items():
            modifiers = list(self.SapModel.FrameObj.GetModifiers(name)[0])
            modifiers[3] = ratio
            self.SapModel.FrameObj.SetModifiers(name, modifiers)
        
    def get_t_crack(self,
                    beams_names = None,
                    phi : float = 0.75,
                    ) -> dict:
        import math
        # self.etabs.run_analysis()
        self.etabs.set_current_unit('N', 'mm')
        if beams_names is None:
            beams_names, _ = self.get_beams_columns()
        beams_sections = (self.SapModel.FrameObj.GetSection(name)[0] for name in beams_names)
        beams_sections = set(beams_sections)
        sec_t = {}
        for sec_name in beams_sections:
            _, mat, h, b, *args = self.SapModel.PropFrame.GetRectangle(sec_name)
            fc = self.SapModel.PropMaterial.GetOConcrete(mat)[0]
            A = b * h
            p = 2 * (b + h)
            t_crack = phi * .33 * math.sqrt(fc) * A ** 2 / p 
            sec_t[sec_name] = t_crack / 1000000 / 9.81
        return sec_t

    def get_unit_weight_of_beams(self,
                    beams_names = None,
                    ) -> dict:
        if beams_names is None:
            beams_names, _ = self.get_beams_columns(types=[1,2,3])
        table_key = "Frame Assignments - Property Modifiers"
        cols = ['Story', 'Label', 'UniqueName', 'AMod', 'WMod']
        import pandas as pd
        df = pd.DataFrame(beams_names, columns=['UniqueName'])
        df['AMod_Beam'] = 1
        df['WMod_Beam'] = 1
        df1 = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        if df1 is not None:
            filt = df1['UniqueName'].isin(beams_names)
            df1 = df1.loc[filt]
            cols = {'AMod':'AMod_Beam', 'WMod':'WMod_Beam'}
            df1.rename(columns=cols, inplace=True)
            df.merge(df1, on='UniqueName', how='left')
        # df.columns = ['Story', 'Label', 'UniqueName', 'AMod_Beam', 'WMod_Beam']
        beam_names = df.UniqueName.unique()
        beams_sections  = self.get_beams_sections(beam_names)
        df['Section'] = df['UniqueName'].map(beams_sections)

        table_key = "Frame Section Property Definitions - Summary"
        cols = ['Name', 'Material', 'Area', 'AMod', 'WMod']
        df_sec = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        df = df.merge(df_sec, left_on='Section', right_on='Name')
        del df['Name']
        unit_weights = self.etabs.material.get_unit_weight_of_materials()
        df['mat_unit_weight'] = df['Material'].map(unit_weights)
        df.dropna(inplace=True)
        convert_type = {
                    'Area' : float,
                    'AMod_Beam' : float,
                    'AMod' : float,
                    # 'mat_unit_weight' : float,
                    'WMod_Beam' : float,
                    'WMod' : float,
                    }
        df = df.astype(convert_type)
        df['unit_weight'] = df['Area'] * df['AMod_Beam'] * df['AMod'] * df['mat_unit_weight'] * df['WMod_Beam'] * df['WMod']
        return df


    def get_beams_sections(self,
            beams_names : Iterable[str] = None,
            ) -> dict:
        if beams_names is None:
            beams_names, _  = self.get_beams_columns()
        beams_sections = {name : self.SapModel.FrameObj.GetSection(name)[0] for name in beams_names}
        return beams_sections
    
    @change_unit('N', 'cm')
    def assign_frame_modifiers(self,
            frame_names: list,
            area: Union[None, float]=None,
            as2: Union[None, float]=None,
            as3: Union[None, float]=None,
            torsion: Union[None, float]=None,
            i22: Union[None, float]=None,
            i33: Union[None, float]=None,
            mass: Union[None, float]=None,
            weight: Union[None, float]=None,
            design_procedure: str='',
            design_orientation: str='',
            ):
        '''
        design_procedure: steel: 1, concrete: 2
        '''
        # filter desired procedure
        design_procedures = {'steel': 1, 'concrete': 2}
        design_procedure = design_procedures.get(design_procedure, None)
        if design_procedure is not None:
            desired_procedure = []
            for name in frame_names:
                if self.SapModel.FrameObj.GetDesignProcedure(name)[0] == design_procedure:
                    desired_procedure.append(name)
            frame_names = desired_procedure
        # filter desired orientation
        design_orientations = {'column': 1, 'beam': 2}
        design_orientation = design_orientations.get(design_orientation)
        if design_orientation is not None:
            desired_orientation = []
            for name in frame_names:
                if self.SapModel.FrameObj.GetDesignOrientation(name)[0] == design_orientation:
                    desired_orientation.append(name)
            frame_names = desired_orientation
        mod_names = [area, as2, as3, torsion, i22, i33, mass, weight]
        for name in frame_names:
            modifiers = list(self.SapModel.FrameObj.GetModifiers(name)[0])
            for i, mod in enumerate(mod_names):
                if mod:
                    if mod > 1:
                        section_name = self.SapModel.FrameObj.GetSection(name)[0]
                        try:
                            h = self.SapModel.PropFrame.GetRectangle(section_name)[2]
                        except: # Non prismitic sections
                            continue
                        ratio = mod / h
                        if ratio < 1:
                            mod = 1 - ratio
                    modifiers[i] = mod
            self.SapModel.FrameObj.SetModifiers(name, modifiers)
    
    def get_beams_torsion_prop_modifiers(self,
            beams_names : Iterable[str] = None,
            ) -> dict:
        if beams_names is None:
            beams_names, _  = self.get_beams_columns()
        beams_j = {}
        for name in beams_names:
            modifiers = list(self.SapModel.FrameObj.GetModifiers(name)[0])
            beams_j[name] = modifiers[3]
        return beams_j

    def correct_torsion_stiffness_factor(self,
                load_combinations : Iterable[str] = None,
                beams_names : Iterable[str] = None,
                phi : float = 0.75,
                num_iteration : int = 5,
                tolerance : float = .1,
                j_max_value = 1.0,
                j_min_value = 0.01,
                initial_j : Union[float, None] = None,
                decimals : Union[int, None] = None,
                ):
        import numpy as np
        if beams_names is None:
            beams_names, _  = self.get_beams_columns()
        if initial_j is not None:
            self.set_constant_j(initial_j, beams_names)
        section_t_crack = self.get_t_crack(beams_names, phi=phi)
        beams_sections = self.get_beams_sections(beams_names)
        beams_j = self.get_beams_torsion_prop_modifiers(beams_names)
        df = self.etabs.database.get_beams_torsion(load_combinations, beams_names)
        df['section'] = df['UniqueName'].map(beams_sections)
        df['j'] = df['UniqueName'].map(beams_j)
        df['init_j'] = df['j']
        df['phi_Tcr'] = df['section'].map(section_t_crack)
        low = 1 - tolerance
        for i in range(num_iteration):
            df['ratio'] = df['phi_Tcr'] / df['T']
            df['ratio'].replace([np.inf, -np.inf], 1, inplace=True)
            df['ratio'].fillna(1, inplace=True)
            mask = (df['ratio'] > low)
            if mask.all():
                yield num_iteration - 1
                break
            else:
                df['j'] = df['ratio'] * df['j']
                df['j'] = df['j'].clip(j_min_value, j_max_value)
                mask = (df['T'] / df['phi_Tcr'] < low)
                if mask.any():
                    df['ratio'] = df['ratio'].clip(j_min_value, j_max_value)
                    df.loc[mask, 'j'] = df.loc[mask, 'ratio']
                j_dict = dict(zip(df['UniqueName'],
                    df['j'].round(decimals=decimals) if decimals else df['j']))
                self.apply_torsion_stiffness_coefficient(j_dict)
                self.etabs.run_analysis()
                cols=['UniqueName', 'T']
                torsion_dict = self.etabs.database.get_beams_torsion(load_combinations, beams_names, cols)
                df['T'] = df['UniqueName'].map(torsion_dict)
            yield i
        df.drop(columns=['ratio'], inplace=True)
        df = df[['Story', 'Beam', 'UniqueName', 'section', 'phi_Tcr', 'T', 'j', 'init_j']]
        yield df

    def angle_between_two_lines(self,
        line1 : Union[str, Iterable],
        line2 : Union[str, Iterable],
        ):
        if type(line1) != type(line2):
            return
        if type(line1) == str: # frame name in etabs model
            l1_x1, l1_y1, l1_x2, l1_y2 = self.get_xy_of_frame_points(line1)
            l2_x1, l2_y1, l2_x2, l2_y2 = self.get_xy_of_frame_points(line2)
        elif type(line1) in (tuple, list):
            l1_x1, l1_y1, l1_x2, l1_y2 = line1
            l2_x1, l2_y1, l2_x2, l2_y2 = line2
        def dot(vector_a, vector_b):
            return vector_a[0]*vector_b[0]+vector_a[1]*vector_b[1]
        vector_a = [(l1_x1-l1_x2), (l1_y1-l1_y2)]
        vector_b = [(l2_x1-l2_x2), (l2_y1-l2_y2)]
        dot_prod = dot(vector_a, vector_b)
        magnitudes_a = dot(vector_a, vector_a)**0.5
        magnitudes_b = dot(vector_b, vector_b)**0.5
        angle = math.acos(dot_prod / magnitudes_b / magnitudes_a)
        ang_deg = math.degrees(angle)%360
        if ang_deg-180>=0:
            return 360 - ang_deg
        else: 
            return ang_deg

    def get_frame_angle(self,
        line : Union[str, Iterable],
        ):
        if type(line) == str: # frame name in etabs model
            x1, y1, x2, y2 = self.get_xy_of_frame_points(line)
        elif type(line) == Iterable:
            x1, y1, x2, y2 = line
        if x2 == x1:
            return 90
        return math.degrees(math.atan((y2 - y1) / (x2 - x1)))
    
    def get_frame_direction(self,
        name: str,
        ):
        x1, y1, x2, y2 = self.get_xy_of_frame_points(name)
        if x2 == x1 or abs(y2 - y1) > abs(x2 - x1):
            return 'y'
        else:
            return 'x'

    def get_xy_of_frame_points(self, name : str):
        p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(name)
        x1, y1 = self.SapModel.PointObj.GetCoordCartesian(p1_name)[:2]
        x2, y2 = self.SapModel.PointObj.GetCoordCartesian(p2_name)[:2]
        return x1, y1, x2, y2
    
    def get_length_of_frame(self,
            name : str,
            unit: Union[str, bool]=None,
            ):
        if unit is not None:
            force_unit, _ = self.etabs.get_current_unit()
            self.etabs.set_current_unit(force_unit, unit)
        p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(name)
        x1, y1, z1 = self.SapModel.PointObj.GetCoordCartesian(p1_name)[:3]
        x2, y2, z2 = self.SapModel.PointObj.GetCoordCartesian(p2_name)[:3]
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def offset_frame(self, 
                distance : float,
                neg : bool =False,
                names : Union[list, bool] = None,
                ) -> list:
        if names is None:
            try:
                names = self.SapModel.SelectObj.GetSelected()[2]
            except IndexError:
                print('You must select at least one beam')
                return
        lines = []
        for name in names:
            p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(name)
            x1, y1, z1 = self.SapModel.PointObj.GetCoordCartesian(p1_name)[:3]
            x2, y2 = self.SapModel.PointObj.GetCoordCartesian(p2_name)[:2]
            x1_offset, y1_offset, x2_offset, y2_offset = self.offset_frame_points(x1, y1, x2, y2, distance, neg)
            line = self.SapModel.FrameObj.AddByCoord(x1_offset, y1_offset, z1, x2_offset, y2_offset, z1)[0]
            lines.append(line)
        self.SapModel.SelectObj.ClearSelection()
        self.SapModel.View.RefreshView()
        return lines

    @staticmethod
    def offset_frame_points(x1, y1, x2, y2, distance, neg:bool):
        if x2 == x1:
            dy = 0
            dx = distance
        else:
            import math
            m = (y2 - y1) / (x2 - x1)
            dy = distance / math.sqrt(1 + m ** 2)
            dx = m * dy
        if neg:
            dx *= -1
            dy *= -1
        x1_offset = x1 - dx
        x2_offset = x2 - dx
        y1_offset = y1 + dy
        y2_offset = y2 + dy
        return x1_offset, y1_offset, x2_offset, y2_offset

    def connect_two_beams(self,
                names : Union[list, bool] = None,
                points : Union[list, bool] = None,
                ) -> None:
        if not names:
            try:
                names = self.SapModel.SelectObj.GetSelected()[2]
            except IndexError:
                print('You must select at least two beam')
                return
        b1, b2 = names[:2]
        p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(b1)
        x1, y1 = self.SapModel.PointObj.GetCoordCartesian(p1_name)[:2]
        x2, y2 = self.SapModel.PointObj.GetCoordCartesian(p2_name)[:2]
        p3_name, p4_name, _ = self.SapModel.FrameObj.GetPoints(b2)
        x3, y3 = self.SapModel.PointObj.GetCoordCartesian(p3_name)[:2]
        x4, y4 = self.SapModel.PointObj.GetCoordCartesian(p4_name)[:2]
        D = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if D == 0:
            print('Two lines are parallel!')
            return None
        xp = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / D
        yp = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / D
        # move points to xp, yp
        if points is None:
            points = []
            d1 = self.etabs.points.get_distance_between_two_points_in_XY(p1_name, (xp, yp))
            d2 = self.etabs.points.get_distance_between_two_points_in_XY(p2_name, (xp, yp))
            d3 = self.etabs.points.get_distance_between_two_points_in_XY(p3_name, (xp, yp))
            d4 = self.etabs.points.get_distance_between_two_points_in_XY(p4_name, (xp, yp))
            if d1 < d2:
                points.append(p1_name)
            else:
                points.append(p2_name)
            if d3 < d4:
                points.append(p3_name)
            else:
                points.append(p4_name)
        for point in points:
            assert point in (p1_name, p2_name, p3_name, p4_name)
            x, y = self.SapModel.PointObj.GetCoordCartesian(point)[:2]
            dx = xp - x
            dy = yp - y
            self.SapModel.SelectObj.ClearSelection()
            self.SapModel.PointObj.SetSelected(point, True)
            self.SapModel.EditGeneral.Move(dx, dy, 0)
        self.SapModel.SelectObj.ClearSelection()
        self.SapModel.View.RefreshView()
        return None

    def get_above_frames(self,
            name: Union[str, bool] = None,
            stories: Union[list, bool] = None,
            ):
        if name is None:
            name = self.SapModel.SelectObj.GetSelected()[2][-1]
        if stories is None:
            stories = self.SapModel.Story.GetNameList()[1]
        lable = self.SapModel.FrameObj.GetLabelFromName(name)[0]
        names = []
        for story in stories:
            bname = self.SapModel.FrameObj.GetNameFromLabel(lable, story)[0]
            if bname is not None:
                names.append(bname)
        return names

    def get_height_of_beam(self, name, none_beam_h=0):
        '''
        default: if h = 0, it returns default value
        '''
        sec_name = self.SapModel.FrameObj.GetSection(name)[0]
        if sec_name == 'None':
            return none_beam_h
        h = self.SapModel.PropFrame.GetRectangle(sec_name)[2]
        return h

    def get_heigth_from_top_of_beam_to_buttom_of_above_beam(self,
                name,
                none_beam_h : float = 0,
                default : float = 0):
        '''
        none_beam_h: if the section of beam is None, it gives this value as height of beam
        default : if there is no beam above the beam name, it returns the default value
        '''
        lable, story, _ = self.SapModel.FrameObj.GetLabelFromName(name)
        stories = self.SapModel.Story.GetNameList()[1]
        i_story = stories.index(story)
        if i_story == 0:
            return default
        above_story = stories[i_story - 1]
        above_beam = self.SapModel.FrameObj.GetNameFromLabel(lable, above_story)[0]
        if above_beam == None:
            return default
        above_beam_h = self.get_height_of_beam(above_beam, none_beam_h)
        story_h = self.SapModel.Story.GetHeight(above_story)[0]
        height = story_h - above_beam_h
        return height

    def get_heigth_from_top_of_below_story_to_below_of_beam(self,
                name,
                none_beam_h : float = 0,
                ):
        '''
        none_beam_h: if the section of beam is None, it gives this value as height of beam
        '''
        story = self.SapModel.FrameObj.GetLabelFromName(name)[1]
        beam_h = self.get_height_of_beam(name, none_beam_h)
        story_h = self.SapModel.Story.GetHeight(story)[0]
        height = story_h - beam_h
        return height

    def assign_gravity_load(self,
            name: str,
            loadpat : str,
            val1 : float,
            val2 : float,
            dist1 : float = 0,
            dist2 : float = 1,
            load_type : int = 1, # 1: Force per len , 2: Moment per len
            relative : bool = True,
            replace : bool = True,
            item_type : int = 0, # 0: object, 2: selected_obj
            ):
        self.SapModel.FrameObj.SetLoadDistributed(
            name,
            loadpat,
            load_type,
            6,
            dist1,
            dist2,
            -val1,
            -val2,
            'Global',
            relative,
            replace,
            item_type,
            )
        return None
    
    def assign_point_load(self,
            name: str,
            loadpat : str,
            val : float,
            dist : float = 0,
            load_type : int = 1, # 1: Force per len , 2: Moment per len
            relative : bool = True,
            replace : bool = True,
            item_type : int = 0, # 0: object, 2: selected_obj
            ):
        self.SapModel.FrameObj.SetLoadPoint(
            name,
            loadpat,
            load_type,
            6,
            dist,
            -val,
            'Global',
            relative,
            replace,
            item_type,
            )
        return None

    def assign_gravity_load_from_wall(self,
            name: str,
            loadpat : str,
            mass_per_area : float,
            dist1 : float = 0,
            dist2 : float = 1,
            load_type : int = 1, # 1: Force per len , 2: Moment per len
            relative : bool = True,
            replace : bool = True,
            item_type : int = 0, # 0: object, 2: selected_obj
            height : Union[float, bool] = None,
            none_beam_h : float = 0,
            parapet : float = 0,
            height_from_below : bool = False,
            opening_ratio : float = 0,
            ):
        if height is None:
            if height_from_below:
                height = self.get_heigth_from_top_of_below_story_to_below_of_beam(name, none_beam_h) * .5
            else:
                height = self.get_heigth_from_top_of_beam_to_buttom_of_above_beam(name, none_beam_h, parapet)
        if height == 0: 
            return
        value = math.ceil(mass_per_area * height * (1 - opening_ratio))
        self.assign_gravity_load(name, loadpat, value, value, dist1, dist2, load_type, relative, replace, item_type)
        return None
    
    def update_gravity_loads_from_wall(self,
            names: str,
            ):
        d = self.etabs.get_settings_from_model()
        beam_wall_props_key = 'beams_wall_loads'
        beams_props = d.get(beam_wall_props_key, {})
        if not beams_props:
            return
        self.etabs.unlock_model()
        wall_weight_per_areas = beams_props.get('wall_weight_per_area')
        wall_loadpats = beams_props.get('wall_loadpat')
        wall_opening_ratios = beams_props.get('wall_opening_ratio')
        wall_dists1 = beams_props.get('wall_dist1')
        wall_dists2 = beams_props.get('wall_dist2')
        height_from_belows = beams_props.get('height_from_below')
        parapets = beams_props.get('parapet')
        none_beams_h = beams_props.get('none_beam_h')
        current_names = wall_loadpats.keys()
        self.etabs.set_current_unit('kgf', 'm')
        for name in names:
            if name in current_names:
                mass_per_area = wall_weight_per_areas.get(name)
                loadpat = wall_loadpats.get(name)
                opening_ratio = wall_opening_ratios.get(name)
                dist1 = wall_dists1.get(name)
                dist2 = wall_dists2.get(name)
                height_from_below = height_from_belows.get(name, False)
                parapet = parapets.get(name)
                none_beam_h = none_beams_h.get(name, .15)
                if height_from_below:
                    height = self.get_heigth_from_top_of_below_story_to_below_of_beam(name, none_beam_h) * .5
                else:
                    height = self.get_heigth_from_top_of_beam_to_buttom_of_above_beam(name, none_beam_h, parapet)
                if height == 0:
                    continue
                value = math.ceil(mass_per_area * height * (1 - opening_ratio))
                self.assign_gravity_load(name, loadpat, value, value, dist1, dist2,)
        return None

    def assign_gravity_load_to_selfs_and_above_beams(self,
            loadpat : str,
            mass_per_area : float,
            dist1 : float = 0,
            dist2 : float = 1,
            names : Union[list, bool] = None,
            stories : Union[list, bool] = None,
            load_type : int = 1, # 1: Force per len , 2: Moment per len
            relative : bool = True,
            replace : bool = True,
            item_type : int = 0, # 0: object, 2: selected_obj
            height : Union[float, bool] = None,
            none_beam_h : float = 0,
            parapet : float = 0,
            height_from_below : bool = False,
            opening_ratio : float = 0,
        ):
        d = self.etabs.get_settings_from_model()
        beam_wall_props_key = 'beams_wall_loads'
        beams_props = d.get(beam_wall_props_key, {})
        self.etabs.unlock_model()
        self.etabs.set_current_unit('kgf', 'm')
        if names is None:
            names = []
            types, all_names = self.SapModel.SelectObj.GetSelected()[1:3]
            for t, name in zip(types, all_names):
                if t == 2 and self.is_beam(name):
                    names.append(name)
        if stories is None:
            stories = self.SapModel.Story.GetNameList()[1]
        for name in names:
            beam_names = self.get_above_frames(name, stories)
            for beam_name in beam_names:
                self.assign_gravity_load_from_wall(beam_name, loadpat,
                    mass_per_area, dist1, dist2, load_type, relative,
                    replace, item_type, height, none_beam_h, parapet,
                    height_from_below, opening_ratio)
                if height_from_below:
                    continue
                wall_loads_dict = {
                'wall_loadpat': loadpat,
                'wall_weight_per_area': mass_per_area,
                'wall_opening_ratio': opening_ratio,
                'wall_dist1': dist1,
                'wall_dist2': dist2,
                'height_from_below': height_from_below,
                'parapet': parapet,
                'none_beam_h': none_beam_h,
                }
                for key, value in wall_loads_dict.items():
                    props = beams_props.get(key, {})
                    if props:
                        props[beam_name] = value
                    else:
                        props[beam_name] = value
                        beams_props[key] = props
        self.etabs.update_setting([beam_wall_props_key], [beams_props])
        self.SapModel.View.RefreshView()
        return None
    
    def assign_wall_loads_to_etabs(
            self,
            wall_loadpat: str = '',
            wall_weight: float = 0,
            walls: list = [],
        ):
        d = self.etabs.get_settings_from_model()
        beam_wall_props_key = 'beams_wall_loads'
        beams_props = d.get(beam_wall_props_key, {})
        names = set()
        len_unit = 'm'
        weight_unit = 'kg'
        self.etabs.set_current_unit(f'{weight_unit}f', len_unit)
        if not walls:
            import FreeCAD
            walls = FreeCAD.ActiveDocument.Objects
        self.etabs.unlock_model()
        for obj in walls:
            if (
                hasattr(obj, 'IfcType') and
                obj.IfcType == 'Wall'
            ):
                if hasattr(obj, 'loadpat') and hasattr(obj, 'weight'):
                    loadpat = obj.loadpat
                    weight = obj.weight.getValueAs(f"{weight_unit}/({len_unit}*s^2)").Value
                elif wall_loadpat and wall_weight:
                    loadpat = wall_loadpat
                    weight = wall_weight
                else:
                    continue
                name = ''
                if hasattr(obj, 'base'):
                    name = obj.base.Label2
                if not name:
                    if hasattr(obj, 'base'):
                        label, story = obj.base.Label.split('_')[:2]
                    elif hasattr(obj, 'Base'):
                        label, story = obj.Base.Label.split('_')[:2]
                    name = self.etabs.SapModel.FrameObj.GetNameFromLabel(label, story)[0]
                height, percent = freecad_funcs.equivalent_height_in_meter(obj)
                load_value = math.ceil(height * weight)
                dist1, dist2 = freecad_funcs.get_relative_dists(obj)

                self.assign_gravity_load(
                    name=name,
                    loadpat=loadpat,
                    val1=load_value,
                    val2=load_value,
                    dist1=dist1,
                    dist2=dist2,
                    relative=True,
                    replace=name not in names,
                )
                names.add(name)
                wall_loads_dict = {
                    'wall_loadpat': loadpat,
                    'wall_weight_per_area': weight,
                    'wall_opening_ratio': percent,
                    'wall_dist1': dist1,
                    'wall_dist2': dist2,
                    'height_from_below': False,
                    'parapet': obj.parapet.getValueAs(len_unit).Value,
                    'none_beam_h': obj.none_beam_h.getValueAs(len_unit).Value,
                    }
                for key, value in wall_loads_dict.items():
                    props = beams_props.get(key, {})
                    props[name] = value
                    if not props:
                        beams_props[key] = props
        self.etabs.update_setting([beam_wall_props_key], [beams_props])

    def concrete_section_names(self, type_='Beam'):
        '''
        type_ can be 'Beam' or 'Column'
        '''
        table_key = f'Frame Section Property Definitions - Concrete {type_} Reinforcing'
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=['Name'])
        if df is None:
            return []
        names = list(df.Name.unique())
        return names

    def all_section_names(self):
        return self.SapModel.PropFrame.GetNameList()[1]

    def other_sections(self, sections):
        '''
        return all frame sections except sections
        '''
        all_sections = self.all_section_names()
        return list(set(all_sections).difference(sections))

    def assign_sections(self,
            sec_name : str,
            frame_names : Union[list, bool] = None,
        ) -> None:
        if frame_names is None:
            return
        for name in frame_names:
            self.SapModel.FrameObj.SetSection(name, sec_name)

    def assign_sections_stories(self,
            sec_name : str,
            stories : Union[list, bool] = None,
            frame_names : Union[list, bool] = None,
            sec_type : str = 'other',
            ) -> None:
        if frame_names is None:
            frame_names = []
            types, all_names = self.SapModel.SelectObj.GetSelected()[1:3]
            func = None
            if sec_type == 'beam':
                func  = self.is_beam
            elif sec_type == 'column':
                func = self.is_column
            for t, name in zip(types, all_names):
                if t == 2:
                    if func is None:
                        frame_names.append(name)
                    else:
                        if func(name):
                            frame_names.append(name)
        if stories is None:
            stories = self.SapModel.Story.GetNameList()[1]
        for name in frame_names:
            curr_names = self.get_above_frames(name, stories)
            self.assign_sections(sec_name, curr_names)
        self.SapModel.View.RefreshView()
        return None

    def set_column_dns_overwrite(self,
            code : str,
            type_: str = 'Concrete', # 'Steel'
            ):
        type_number = 1 if type_ == 'Steel' else 2
        epsilon = .00000001
        columns = []
        succeed = True
        if type_ == 'Concrete':
            try:
                table_key = f'Concrete Column Overwrites - {code}'
                df = self.etabs.database.read(table_key, to_dataframe=True)
                for col in ('DnsMajor', 'DnsMinor', 'DsMajor', 'DsMinor'):
                    df[col] = f'{epsilon}'
                df['MinEcc'] = 'No'
                self.etabs.database.remove_df_columns(df, ('Story', 'Label', 'Type'))
                df.columns = (
                    'Unique Name',
                    'Design Section',
                    'Frame Type',
                    'LLRF',
                    'Unbraced Length Ratio (Major)',
                    'Unbraced Length Ratio (Minor)',
                    'Effective Length Factor (K Major)',
                    'Effective Length Factor (K Minor)',
                    'Moment Coefficient (Cm Major)',
                    'Moment Coefficient (Cm Minor)',
                    'Non Sway Moment Factor (Dns Major)',
                    'Non Sway Moment Factor (Dns Minor)',
                    'Sway Moment Factor (Ds Major)',
                    'Sway Moment Factor (Ds Minor)',
                    'Consider Minimum Eccentricity?',
                    )
                self.etabs.database.write(table_key, df)
            except:
                succeed = False
        if type_ == 'Steel' or not succeed:

            for name in self.SapModel.FrameObj.GetLabelNameList()[1]:
                if (self.is_column(name) and
                    self.SapModel.FrameObj.GetDesignProcedure(name)[0] == type_number
                    ):
                    self.etabs.design.set_overwrite(name, 9, epsilon, type_, code)
                    self.etabs.design.set_overwrite(name, 10, epsilon, type_, code)
                    self.etabs.design.set_overwrite(name, 11, epsilon, type_, code)
                    self.etabs.design.set_overwrite(name, 12, epsilon, type_, code)
                    # self.etabs.design.set_overwrite(name, 13, False, type_, code)
                    columns.append(name)
            return columns

    def set_infinite_bending_capacity_for_steel_columns(self,
            code_string : str,
            ):
        type_number = 1 # 'Steel' 
        infinit = 1e10
        columns = []
        if code_string == 'AISC360_05':
            mn3 = 39
            mn2 = 40
        if code_string == 'AISC360_10':
            mn3 = 42
            mn2 = 43
        if code_string == 'AISC360_16':
            mn3 = 46
            mn2 = 47
        for name in self.SapModel.FrameObj.GetLabelNameList()[1]:
            if (self.is_column(name) and
                self.SapModel.FrameObj.GetDesignProcedure(name)[0] == type_number
                ):
                self.etabs.design.set_overwrite(name, mn3, infinit, 'Steel', code_string)
                self.etabs.design.set_overwrite(name, mn2, infinit, 'Steel', code_string)
                columns.append(name)
        return columns
        
    def require_100_30(self,
            loads: Union[list, None]=None,
            file_name: Union[str, Path] = '100_30.EDB',
            type_: str = 'Concrete', # 'Steel'
            code : Union[str, None] = None,
            ):
        # create new file and open it
        asli_file_path = Path(self.SapModel.GetModelFilename())
        asli_file_path = asli_file_path.with_suffix(".EDB")
        self.SapModel.File.Save(str(asli_file_path))
        print(asli_file_path)
        if isinstance(file_name, Path):
            new_file_path = file_name
        else:
            new_file_path = self.etabs.backup_model(name=file_name)
        print(f"Saving file as {new_file_path}\n")
        self.SapModel.File.Save(str(new_file_path))
        if loads is None:
            loads = self.etabs.get_first_system_seismic()
        print(f'{loads=}')
        load_cases, columns, code = self.etabs.load_combinations.create_load_combinations_from_loads(
            loads,
            suffix='_100_30',
            type_=type_,
            code=code,
            )
        # run analysis
        self.etabs.analyze.set_load_cases_to_analyze(load_cases)
        self.etabs.run_analysis()
        self.set_frame_obj_selected(columns)
        print('Start Design ...')
        exec(f"self.SapModel.Design{type_}.StartDesign()")
        # get the PMM ratio table
        self.etabs.set_current_unit('tonf', 'm')
        if type_ == 'Concrete':
            table_key = f'Concrete Column PMM Envelope - {code}'
            df = self.etabs.database.read(table_key, to_dataframe=True)
            del df['Location']
            df['Ratio'] = df['RatioRebar'].astype(float)
            del df['RatioRebar']
            df['MMajor'] = df['MMajor'].astype(float).astype(int)
            df['MMinor'] = df['MMinor'].astype(float).astype(int)
            df['P'] = df['P'].astype(float)
            filt = df.groupby(['UniqueName'])['Ratio'].idxmax()
            df = df.loc[filt, :]
        elif type_ == 'Steel':
            table_key = f'Steel Frame Design Summary - {code}'
            cols = ['Story', 'Label', 'UniqueName', 'DesignType', 'DesignSect', 
                    'PMMCombo', 'PMMRatio', 'PRatio', 'MMajRatio', 'MMinRatio']
            df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
            filt = df['DesignType'] == 'Column'
            df = df.loc[filt]
            del df['DesignType']
            df['Ratio'] = df['PMMRatio'].astype(float)
            df['MMajor'] = df['MMajRatio'].astype(float)
            df['MMinor'] = df['MMinRatio'].astype(float)
            df['P'] = df['PRatio'].astype(float)
            for col in ('PMMRatio', 'PRatio', 'MMajRatio', 'MMinRatio'):
                del df[col]
            filt = df.groupby(['UniqueName'])['Ratio'].idxmax()
            df = df.loc[filt, :]
        df['Result'] = df['Ratio'] < .2
        self.SapModel.File.OpenFile(str(asli_file_path))
        # self.SapModel.File.Save(str(asli_file_path))
        return df

    def assign_ev(
        self,
        frames : list,
        load_patterns : list,
        acc : float,
        ev : str,
        importance_factor : float = 1,
        replace : bool  = True,
        self_weight : bool = False,
        ):
        self.etabs.unlock_model()
        self.etabs.set_current_unit('kgf', 'm')
        # Distributed loads
        table_key = 'Frame Loads Assignments - Distributed'
        df = self.etabs.database.read(table_key=table_key, to_dataframe=True)
        ev_value = 0.6 * acc * importance_factor
        if replace:
            # remove current loads
            for name in frames:
                self.SapModel.FrameObj.DeleteLoadDistributed(
                    Name = name,
                    LoadPat = ev,
                )
                self.SapModel.FrameObj.DeleteLoadPoint(
                    Name = name,
                    LoadPat = ev,
                )
        if df is not None:
            del df['GUID']
            filt = (df.UniqueName.isin(frames) & df.LoadPattern.isin(load_patterns))
            df = df[filt]

            for i, row in df.iterrows():
                val1 = math.ceil(float(row['ForceA']) * ev_value)
                val2 = math.ceil(float(row['ForceB']) * ev_value)
                self.assign_gravity_load(
                    name = row['UniqueName'],
                    loadpat = ev,
                    val1 = val1,
                    val2 = val2,
                    dist1 = float(row['RelDistA']),
                    dist2 = float(row['RelDistB']),
                    load_type = 1 if row['LoadType'] == 'Force' else 2,
                    replace = False,
                )
        # point load
        table_key = 'Frame Loads Assignments - Point'
        df = self.etabs.database.read(table_key=table_key, to_dataframe=True)
        if df is not None:
            del df['GUID']
            filt = (df.UniqueName.isin(frames) & df.LoadPattern.isin(load_patterns))
            df = df[filt]
            for i, row in df.iterrows():
                val = math.ceil(float(row['Force']) * ev_value)
                self.assign_point_load(
                    name = row['UniqueName'],
                    loadpat = ev,
                    val = val,
                    dist = float(row['RelDist']),
                    load_type = 1 if row['LoadType'] == 'Force' else 2,
                    replace = False,
                )
        # self weight load apply in load patterns
        if self_weight:
            df = self.get_unit_weight_of_beams(frames)
            for i, row in df.iterrows():
                val = math.ceil(row['unit_weight'] * ev_value)
                self.assign_gravity_load(
                    name = row['UniqueName'],
                    loadpat = ev,
                    val1 = val,
                    val2 = val,
                    dist1 = 0,
                    dist2 = 1,
                    load_type = 1,
                    replace = False,
                )

    def get_area(self,
        name: str,
        cover: float=0,
        location: Union[bool, float] = None,
        ):
        '''
        Return area of section in cm^2
        '''
        # self.etabs.set_current_unit('N', 'cm')
        section_name = self.SapModel.FrameObj.GetSection(name)[0]
        _, _, h, b, *_ = self.SapModel.PropFrame.GetRectangle(section_name)
        if cover == 0:
            len_unit = self.etabs.get_current_unit()[1]
            multiply = {'m': 0.01, 'cm': 1, 'mm': 10}
            cover = 6 * multiply.get(len_unit)
        return (b * (h - cover))
    
    def get_section_area(self,
                         names: Union[list, None]=None,
                         ):
        table_key = "Frame Section Property Definitions - Summary"
        cols = ['Name', 'Area']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        if names is not None:
            filt = df['Name'].isin(names)
            df = df.loc[filt]
        df['Area'] = df['Area'].astype(float)
        return df.set_index('Name').to_dict()['Area']
    
    def delete_frames(self,
                      frames: Union[list, None]=None,
                      ) -> None:
        if frames is None:
            self.SapModel.FrameObj.Delete('ALL', ItemType=1) # Group
        else:
            for frame in frames:
                self.SapModel.FrameObj.Delete(frame)




if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel()
    SapModel = etabs.SapModel
    # filename = Path(r'F:\alaki\zibaee\steel\100_30.EDB')
    df = etabs.frame_obj.require_100_30(type_='Steel')
    print(df)
    print('Wow')




    
        