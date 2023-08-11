from pathlib import Path
import sys
from typing import Iterable, Union

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
        # code = code.replace("-", "ـ")
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

    def get_rho(
            self,
            name: str,
            distance: Union[float, str]='middle', # start, end
            location: str = 'top',
            torsion_area: Union[bool, float] = None,
            frame_area: Union[bool, float] = None,
            cover: float= 0,
            additional_rebars: float = 0,
        ):
        text = ''
        self.etabs.set_current_unit('N', 'cm')
        self.etabs.run_analysis()
        self.etabs.start_design()
        beam_rebars = self.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
        if location == 'top':
            areas = beam_rebars[4]
        elif location == 'bot':
            areas = beam_rebars[6]
        first_dist = beam_rebars[2][0]
        last_dist = beam_rebars[2][-1]
        text += f'The area of main rebar of beam name {name} at {location} in '
        if type(distance) == str:
            text += f'{distance} of beam = '
            if distance == 'start':
                distance = first_dist
            elif distance == 'end':
                distance = last_dist
            elif distance == 'middle':
                distance = (last_dist - first_dist) / 2
        else:
            text += f'{distance:.1f} cm = '
        if distance < first_dist:
            area = areas[0]
            if torsion_area is None:
                torsion_area = beam_rebars[10][0] / 2
        elif distance > last_dist:
            area = areas[-1]
            if torsion_area is None:
                torsion_area = beam_rebars[10][-1] / 2
        else:
            from scipy.interpolate import interp1d
            f = interp1d(beam_rebars[2], areas)
            area = f(distance)
            if torsion_area is None:
                f = interp1d(beam_rebars[2], beam_rebars[10])
                torsion_area = f(distance) / 2
        text += f'{area:.1f} Cm2\n'
        text += f'Torsion area = {torsion_area:0.1f} Cm2\n'
        area += torsion_area
        if frame_area is None:
            frame_area = self.etabs.frame_obj.get_area(name, cover=cover)
        area += additional_rebars
        rho = area / frame_area
        text += f'b x d = {frame_area:.1f} Cm2\n'
        text += f'Rho = As / bd = {area:.1f} / {frame_area:.1f} = {rho:.4f}\n'
        return rho, text
    
    def get_deflection_of_beam(self,
        dead: list,
        supper_dead: list,
        lives: list,
        beam_name: str,
        distance_for_calculate_rho: Union[float, str]='middle', # start, end
        location: str = 'top',
        torsion_area: Union[bool, float] = None,
        frame_area: Union[bool, float] = None,
        cover: float= 6,
        lives_percentage: float = 0.25,
        filename: str='',
        point_for_get_deflection: Union[str, None]=None,
        is_console: bool=False,
        rho: Union[float, bool] = None,
        additional_rebars: float=0,
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
        text = ''
        if rho is None:
            print('Getting Rho ...')
            rho, text = self.get_rho(
                beam_name,
                distance_for_calculate_rho,
                location,
                torsion_area,
                frame_area,
                cover,
                additional_rebars,
            )
        landa = 2 / (1 + 50 * rho)
        p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(beam_name)
        text += f'lambda = 2 / (1 + 50 x rho) = 2 / (1 + 50 x {rho:.4f}) = {landa:.2f}'
        print(f'\n{rho=}\n{landa=}')
        if not filename:
            filename1 = 'deflection_beams.EDB'
        else:
            filename1 = filename
        print(f'Save file as {filename1} ...')
        file_path = self.etabs.get_filepath()
        deflection_path = file_path / 'deflections'
        if not deflection_path.exists():
            import os
            os.mkdir(str(deflection_path))
        self.SapModel.File.Save(str(deflection_path / filename1))
        if (
            point_for_get_deflection is None and \
            not is_console and \
            type(distance_for_calculate_rho) == str
            ):
            point_for_get_deflection = self.etabs.points.add_point_on_beam(
                name=beam_name,
                distance=distance_for_calculate_rho,
                unlock_model=False,
                )
        if (
            point_for_get_deflection is None and \
            is_console
            ):
            point_for_get_deflection = p2_name
        if not filename:
            label, story, _ = self.SapModel.FrameObj.GetLabelFromName(beam_name)
            filename = f'deflection_{label}_{story}_p{point_for_get_deflection}.EDB'
            print(f'Save file as {filename} ...')
            self.SapModel.File.Save(str(deflection_path / filename))
        print("Set frame stiffness modifiers ...")
        beams, columns = self.etabs.frame_obj.get_beams_columns()
        self.etabs.frame_obj.assign_frame_modifiers(
            frame_names=beams + columns,
            i22=1,
            i33=1,
        )
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
        self.SapModel.RespCombo.Add('deflection2', 0)
        self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc2, 1)
        self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc1, landa - 1)
        if supper_dead:
            # scale factor set to 0.5 due to xi for 3 month equal to 1.0
            self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc3, -0.5)
            self.etabs.analyze.set_load_cases_to_analyze((lc1, lc2, lc3))
        else:
            self.etabs.analyze.set_load_cases_to_analyze((lc1, lc2))
        self.etabs.run_analysis()
        if self.etabs.etabs_main_version < 20:
            index = 1
        else:
            index = 0
        p1_def1 = self.etabs.results.get_point_abs_displacement(p1_name, 'deflection1', type_='Combo', index=index)[2]
        p1_def2 = self.etabs.results.get_point_abs_displacement(p1_name, 'deflection2', type_='Combo', index=index)[2]
        p2_def1 = self.etabs.results.get_point_abs_displacement(p2_name, 'deflection1', type_='Combo', index=index)[2]
        p2_def2 = self.etabs.results.get_point_abs_displacement(p2_name, 'deflection2', type_='Combo', index=index)[2]
        print(f'\n{p1_def1=}, {p1_def2=}, {p2_def1=}, {p2_def2=}')
        if is_console:
            def1 = p2_def1 - p1_def1
            def2 = p2_def2 - p1_def2
        else:
            def_def1 = self.etabs.results.get_point_abs_displacement(point_for_get_deflection, 'deflection1', type_='Combo', index=index)[2]
            def_def2 = self.etabs.results.get_point_abs_displacement(point_for_get_deflection, 'deflection2', type_='Combo', index=index)[2]
            print(f'\n{def_def1=}, {def_def2=}')
            def1 = def_def1 - (p1_def1 + p2_def1) / 2
            def2 = def_def2 - (p1_def2 + p2_def2) / 2
        print(f'\n{def1=}, {def2=}')
        return abs(def1), abs(def2), text
    
def get_deflection_check_result(
    def1: float,
    def2: float,
    ln: float,
    ):
    allow_def1 = ln / 360
    allow_def2 = ln / 480
    ret = f'Ln = {ln:.0f} Cm\n'
    ret += 20 * '-'
    ret += f'\ncombo1 deflection = {def1:.3f} Cm '
    if def1 <= allow_def1:
        ret += f'< Ln / 360 = {allow_def1:.2f} Cm ==> OK'
    else:
        ret += f'> Ln / 360 = {allow_def1:.2f} Cm ==> Not OK'
    # combo 2
    ret += f'\ncombo2 deflection = {def2:.3f} Cm '
    if def2 <= allow_def2:
        ret += f'< Ln / 480 = {allow_def2:.2f} Cm ==> OK\n'
    else:
        ret += f'> Ln / 480 = {allow_def2:.2f} Cm ==> Not OK\n'
    ret += 20 * '-'
    ret += '\n'
    ret += 20 * '-'
    ret += f'\ncombo1 deflection = {def1:.3f} Cm '
    if def1 <= allow_def1 * 2:
        ret += f'< Ln / 180 = {allow_def1 * 2:.2f} Cm ==> OK'
    else:
        ret += f'> Ln / 180 = {allow_def1 * 2:.2f} Cm ==> Not OK'
    # combo 2
    ret += f'\ncombo2 deflection = {def2:.3f} Cm '
    if def2 <= allow_def2 * 2:
        ret += f'< Ln / 240 = {allow_def2 * 2:.2f} Cm ==> OK\n'
    else:
        ret += f'> Ln / 240 = {allow_def2 * 2:.2f} Cm ==> Not OK\n'
    ret += 20 * '-'
    ret += '\n'
    ret += 20 * '-'
    ret += '\nIn Common Structures\n'
    ret += f'\ncombo1 deflection = {def1:.3f} Cm '
    if def1 <= allow_def1:
        ret += f'< Ln / 360 = {allow_def1:.2f} Cm ==> OK'
    else:
        ret += f'> Ln / 360 = {allow_def1:.2f} Cm ==> Not OK'
    # combo 2
    ret += f'\ncombo2 deflection = {def2:.3f} Cm '
    if def2 <= allow_def2 * 2:
        ret += f'< Ln / 240 = {allow_def2 * 2:.2f} Cm ==> OK\n'
    else:
        ret += f'> Ln / 240 = {allow_def2 * 2:.2f} Cm ==> Not OK\n'
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
