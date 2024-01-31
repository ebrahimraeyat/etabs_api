'''
Design Module
'''



from pathlib import Path
import sys
from typing import Union

import pandas as pd
pd.options.mode.chained_assignment = None


__all__ = ['Design']

class Design:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def get_code(self,
            type_ : str = 'Concrete',  # 'Steel'
            ):
            if type_ == 'Concrete':
                return self.SapModel.DesignConcrete.getCode()[0]
            elif type_ == 'Steel':
                return self.SapModel.DesignSteel.getCode()[0]

    def get_code_string(self,
        type_: str = 'Concrete', # 'Steel'
        code : Union[str, None] = None,
        ):
        ''' 
        get code of design in format 'ACI 318-14' and return 'ACI318_14'
        '''
        if code is None:
            code = self.get_code(type_=type_)
        code = code.replace(" ", "")
        i = code.find('-')
        code = code[:i] + '_' + code[i + 1:]
        if 'ACI318_08' in code:
            code += '_IBC2009'
        return code

    def set_overwrite(self,
        name: str,
        item: int,
        value: float,
        type_: str = 'Concrete', # 'Steel'
        code: Union[str, bool] = None,
        ):
        if code is None:
            code = self.get_code_string(type_)
        exec(f"self.SapModel.Design{type_}.{code}.SetOverwrite('{name}',{item}, {value})")

    def set_concrete_framing_type(self,
        type_: str = 2,
        beams: bool = True,
        columns: bool = True,
        ):
        '''
        type_:
            0 = Program Default
            1 = Sway special
            2 = Sway Intermediate
            3 = Sway Ordinary
            4 = Non-sway
        '''
        beam_names, column_names = self.etabs.frame_obj.get_beams_columns(type_=2)
        if columns:
            for name in column_names:
                self.set_overwrite(
                    name = name,
                    item = 1, # Framing Type
                    value = type_, # Sway special
                    )
        if beams:
            for name in beam_names:
                self.set_overwrite(
                    name = name,
                    item = 1, # Framing Type
                    value = type_, # Sway special
                    )
                
    def set_preference(self,
        item: int,
        value,
        type_: str = 'Concrete', # 'Steel'
        code: Union[str, bool] = None,
        ):
        if code is None:
            code = self.get_code_string(type_)
        exec(f"self.SapModel.Design{type_}.{code}.SetPreference({item}, {value})")

    def model_designed(self,
                       type_: str='Concrete',
                       ):
        all_table = self.SapModel.DatabaseTables.GetAvailableTables()[1]
        import python_functions
        if (
            type_ == 'Concrete' and
            python_functions.is_text_in_list_elements(all_table, 'Concrete Beam Design Summary')
        ) or (
            type_ == 'Steel' and
            python_functions.is_text_in_list_elements(all_table, 'Steel Frame Design Summary')
        ):
            return True
        return False

    def set_phi_joint_shear(self,
        value=0.75,
        code=None,
        ):
        if code is None:
            code = self.get_code_string('Concrete')
        item = 15
        if '11' in code:
            item = 14
        elif '08' in code:
            item = 10
        self.set_preference(item, value, code=code)
    
    def get_rho_of_beams(
            self,
            names: "list[str]",
            distances: "list[Union[float, str], float, str]"='middle', # start, end
            locations: "Union[list[str], str]" = 'top',
            torsion_areas: "Union[list[float], bool]" = None,
            frame_areas: "Union[list[float], bool]" = None,
            covers: "list[float]"= [6],
            additionals_rebars: "Union[list[float], float]"=0,
            widths: "Union[list[float], None]" = None,
            heights: "Union[list[float], None]" = None,
    ) -> "tuple(list, list)":
        from scipy.interpolate import interp1d
        rhos = []
        texts = []
        units = self.etabs.get_current_unit()
        self.etabs.set_current_unit('N', 'cm')
        self.etabs.run_analysis()
        self.etabs.frame_obj.set_frame_obj_selected(names)
        self.etabs.start_design(check_designed=True)
        if torsion_areas is None:
            torsion_areas = len(names) * [None]
        if frame_areas is None:
            frame_areas = len(names) * [None]
        if widths is None:
            widths = len(names) * [None]
        if heights is None:
            heights = len(names) * [None]
        if isinstance(covers, (int, float)):
            covers = len(names) * [covers]
        if isinstance(distances, (float, int, str)):
            distances = len(names) * [distances]
        if isinstance(locations, (float, int, str)):
            locations = len(names) * [locations]
        if isinstance(additionals_rebars, (int, float)):
            additionals_rebars = len(names) * [additionals_rebars]
        for i, name in enumerate(names):
            location = locations[i]
            distance = distances[i]
            torsion_area = torsion_areas[i]
            frame_area = frame_areas[i]
            width = widths[i]
            height = heights[i]
            cover = covers[i]
            additional_rebars = additionals_rebars[i]
            text = ''
            print(f'{name=}\n')
            beam_rebars = self.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
            if location == 'top':
                areas = beam_rebars[4]
            elif location == 'bot':
                areas = beam_rebars[6]
            first_dist = beam_rebars[2][0]
            last_dist = beam_rebars[2][-1]
            text += f'The Calculated area of main rebar of beam name {name} at {location} in '
            if isinstance(distance, str):
                text += f'{distance} of beam = '
                if distance == 'start':
                    distance = first_dist
                elif distance == 'end':
                    distance = last_dist
                elif distance == 'middle':
                    distance = (last_dist - first_dist) / 2
            else:
                text += f'{distance:.1f} cm = '
            torsion_percent = 3 / 8
            total_torsion_area = None
            if distance < first_dist:
                area = areas[0]
                if torsion_area is None:
                    total_torsion_area = beam_rebars[10][0]
            elif distance > last_dist:
                area = areas[-1]
                if torsion_area is None:
                    total_torsion_area = beam_rebars[10][-1]
            else:
                f = interp1d(beam_rebars[2], areas)
                area = f(distance)
                if torsion_area is None:
                    f = interp1d(beam_rebars[2], beam_rebars[10])
                    total_torsion_area = f(distance)
            text += f'{area:.1f} Cm2\n'
            if torsion_area is None:
                torsion_area = total_torsion_area * torsion_percent
            if total_torsion_area is not None:
                text += f'Total torsion area = {total_torsion_area:0.1f} Cm2, Assume 3/8 for {location} ==> '
            text += f'Torsion Area = {torsion_area:0.1f}\n'
            text += f'As = bending + torsion + add rebar = {area:0.1f} + {torsion_area:0.1f} + {additional_rebars:0.1f}\n'
            area += torsion_area
            area += additional_rebars
            if frame_area is None:
                frame_area = self.etabs.frame_obj.get_area(name, cover=cover)
            rho = area / frame_area
            if width is not None:
                text += f'b = {width}, d = {height} - {cover} = {height - cover} ==> '
            text += f'b x d = {frame_area:.1f} Cm2\n'
            text += f'Rho = As / b x d = {area:.1f} / {frame_area:.1f} = {rho:.4f}\n'
            rhos.append(rho)
            texts.append(text)
        self.etabs.set_current_unit(*units)
        return rhos, texts
    
    def get_deflection_of_beams(self,
        dead: list,
        supper_dead: list,
        lives: list,
        beam_names: "Union[list[str], pd.DataFrame]",
        distances_for_calculate_rho: "list[Union[float, str], float, str]"='middle', # start, end
        locations: "Union[list[str], str]" = 'top',
        torsion_areas: "Union[list[float], bool]" = None,
        frame_areas: "Union[list[float], bool]" = None,
        covers: "Union[list[float, int], float, int]"= 6,
        lives_percentage: float = 0.25,
        filename: str='',
        points_for_get_deflection: "Union[list[str], bool]" = None,
        is_consoles: "Union[list[bool], bool]"=False,
        rhos: "Union[list[float, bool], bool]" = None,
        additionals_rebars: "Union[list[float, int], int, float]"=0,
        ):
        '''
        dead: a list of Dead loads
        supper_dead: a list of supper Dead loads
        lives: a list of live loads
        beam_name: The name of beam for calculating deflection
        distance_for_calculate_rho: A string or float length for calculating rho, string can be 'middle', 'start' and 'end'
        location: location for getting rebar area, 'top' and 'bot'
        torsion_area: area of torsion rebars, if it None, automatically 1/2 of torsion area added to flextural rebar area
        frame_area: The area of concrete section, when it is None, obtain automatically
        cover: cover of beam
        lives_percentage: live load percentage for considering to calculate short term cracking deflection
        filename: The etabs file name for creating deflection model
        point_for_get_deflection: The name of the point for calculate deflection on it, if it is None, for console it is 'start'
                and for contiues beam it is 'middle'
        is_console: If beam is console
        rho: As / bd
        additional_rebars: Add this to rebar area for calculating rho
        '''
            # prepare inputs for calculate deflections
        if isinstance(beam_names, pd.DataFrame):
            def add_beam_prop_to_df(row):
                torsion_rebar = 'Torsion Rebar'
                print(row)
                if row[torsion_rebar]:
                    row[torsion_rebar] = None
                else:
                    row[torsion_rebar] = 0
                if row['Console']:
                    row['location'] = 'bot'
                    row['distance_for_calculate_rho'] = 'start'
                else:
                    row['location'] = 'top'
                    row['distance_for_calculate_rho'] = 'middle'
                cover = row['Cover']
                b = row['Width']
                h = row['Height']
                row['d'] = h - cover
                row['frame_area'] = b * row['d']
                return row
            
            df = beam_names.apply(add_beam_prop_to_df, axis=1)
            beam_names = df['Name']
            torsion_areas = df['Torsion Rebar']
            is_consoles = df['Console']
            locations = df['location']
            distances = df['distance_for_calculate_rho']
            covers = df['Cover']
            widths = df['Width']
            heights = df['Height']
            frame_areas = df['frame_area']
            additionals_rebars = df['Add Rebar']
        else:
            if isinstance(distances_for_calculate_rho, (float, int, str)):
                distances = len(beam_names) * [distances_for_calculate_rho]
            else:
                distances = distances_for_calculate_rho
            if isinstance(is_consoles, bool):
                is_consoles = len(beam_names) * [is_consoles]
        if points_for_get_deflection is None:
            points_for_get_deflection = len(beam_names) * [None]
        # Get rhos of beams
        if rhos is None:
            rhos, texts = self.get_rho_of_beams(
                beam_names,
                distances=distances,
                locations=locations,
                torsion_areas=torsion_areas,
                frame_areas=frame_areas,
                covers = covers,
                additionals_rebars=additionals_rebars,
                widths = widths,
                heights = heights,
            )
        # Save As etabs model with filename
        if not filename:
            filename = 'deflection_beams_' + '_'.join(beam_names) + '.EDB'
        print(f'Save file as {filename} ...')
        file_path = self.etabs.get_filepath()
        deflection_path = file_path / 'deflections'
        if not deflection_path.exists():
            import os
            os.mkdir(str(deflection_path))
        self.SapModel.File.Save(str(deflection_path / filename))
        # Set frame stiffness modifiers
        print("Set frame stiffness modifiers ...")
        beams, columns = self.etabs.frame_obj.get_beams_columns()
        self.etabs.frame_obj.assign_frame_modifiers(
            frame_names=beams + columns,
            i22=1,
            i33=1,
        )
        print("Set Slab stiffness modifiers ...")
        self.etabs.area.assign_slab_modifiers(m11=1, m22=1, m12=1, reset=True)
        print("Set floor cracking for beams and floors ...")
        self.etabs.database.set_floor_cracking(type_='Frame')
        self.etabs.database.set_floor_cracking(type_='Area')
        print("Create nonlinear load cases ...")
        lc1, lc2, lc3 = self.etabs.database.create_nonlinear_loadcases(
            dead=dead,
            supper_dead=supper_dead,
            lives=lives,
            lives_percentage=lives_percentage,
            )
        print("Create deflection load combinations ...")
        self.SapModel.RespCombo.Add('deflection1', 0)
        self.SapModel.RespCombo.SetCaseList('deflection1', 0, lc2, 1)
        self.SapModel.RespCombo.SetCaseList('deflection1', 0, lc1, -1)
        if supper_dead:
            self.etabs.analyze.set_load_cases_to_analyze((lc1, lc2, lc3))
        else:
            self.etabs.analyze.set_load_cases_to_analyze((lc1, lc2))
        new_points_for_get_deflection = []
        beams_points = []
        for i, beam_name in enumerate(beam_names):
            print(20 * '=' + '\n')
            print(f'Calculating Deflection for {beam_name=}\n')

            point_for_get_deflection = points_for_get_deflection[i]
            is_console = is_consoles[i]
            distance = distances[i]
            rho = rhos[i]
            landa = 2 / (1 + 50 * rho)
            texts[i] += f'lambda = 2 / (1 + 50 x rho) = 2 / (1 + 50 x {rho:.4f}) = {landa:.2f}'
            print(f'\n{rho=}\n{landa=}')
            p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(beam_name)
            beams_points.append([p1_name, p2_name])
            if (
                point_for_get_deflection is None and \
                not is_console and \
                isinstance(distance, str)
                ):
                point_for_get_deflection = self.etabs.points.add_point_on_beam(
                    name=beam_name,
                    distance=distance,
                    unlock_model=False,
                    )
            if (
                point_for_get_deflection is None and \
                is_console
                ):
                point_for_get_deflection = p2_name
            new_points_for_get_deflection.append(point_for_get_deflection)
            print("Create deflection load combinations ...")
            self.SapModel.RespCombo.Add(f'deflection2_beam{beam_name}', 0)
            self.SapModel.RespCombo.SetCaseList(f'deflection2_beam{beam_name}', 0, lc2, 1)
            self.SapModel.RespCombo.SetCaseList(f'deflection2_beam{beam_name}', 0, lc1, landa - 1)
            if supper_dead:
                # scale factor set to 0.5 due to xi for 3 month equal to 1.0
                self.SapModel.RespCombo.SetCaseList(f'deflection2_beam{beam_name}', 0, lc3, -0.5)
        self.etabs.run_analysis()
        import python_functions
        pts = python_functions.flatten_list(beams_points) + new_points_for_get_deflection
        combos = ['deflection1'] + [f'deflection2_beam{beam_name}' for beam_name in beam_names]
        pts_displacements = self.etabs.results.get_points_min_max_displacements(points=pts, load_combinations=combos)
        deflections1 = []
        deflections2 = []
        for i, beam_name in enumerate(beam_names):
            p1_name, p2_name = beams_points[i]
            p1_def1 = pts_displacements.loc[(p1_name, 'deflection1'), ('Uz', 'min')]
            p2_def1 = pts_displacements.loc[(p2_name, 'deflection1'), ('Uz', 'min')]
            p1_def2 = pts_displacements.loc[(p1_name, f'deflection2_beam{beam_name}'), ('Uz', 'min')]
            p2_def2 = pts_displacements.loc[(p2_name, f'deflection2_beam{beam_name}'), ('Uz', 'min')]
            print(f'\n{p1_def1=}, {p1_def2=}, {p2_def1=}, {p2_def2=}')
            if is_consoles[i]:
                def1 = p2_def1 - p1_def1
                def2 = p2_def2 - p1_def2
            else:
                def_def1 =  pts_displacements.loc[(new_points_for_get_deflection[i], 'deflection1'), ('Uz', 'min')]
                def_def2 =  pts_displacements.loc[(new_points_for_get_deflection[i], f'deflection2_beam{beam_name}'), ('Uz', 'min')]
                print(f'\n{def_def1=}, {def_def2=}')
                def1 = def_def1 - (p1_def1 + p2_def1) / 2
                def2 = def_def2 - (p1_def2 + p2_def2) / 2
            print(f'\n{def1=}, {def2=}')
            deflections1.append(abs(def1))
            deflections2.append(abs(def2))
        return deflections1, deflections2, texts
        
def get_deflection_check_result(
    def1: float,
    def2: float,
    ln: float,
    short_term: float=360,
    long_term: float=480,
    ):
    allow_def1 = ln / short_term
    allow_def2 = ln / long_term
    ret = f'Ln = {ln:.0f} Cm\n'
    ret += 20 * '-'
    ret += f'\ncombo1 deflection = {def1:.3f} Cm '
    if def1 <= allow_def1:
        ret += f'< Ln / {short_term} = {allow_def1:.2f} Cm ==> OK'
    else:
        ret += f'> Ln / {short_term} = {allow_def1:.2f} Cm ==> Not OK'
    # combo 2
    ret += f'\ncombo2 deflection = {def2:.3f} Cm '
    if def2 <= allow_def2:
        ret += f'< Ln / {long_term} = {allow_def2:.2f} Cm ==> OK\n'
    else:
        ret += f'> Ln / {long_term} = {allow_def2:.2f} Cm ==> Not OK\n'
    ret += 20 * '-'
    return ret


        


if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    etabs.design.get_code()
    print('Wow')
