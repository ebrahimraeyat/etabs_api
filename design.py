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
            distance: float,
            location: str = 'top',
            torsion_area: Union[bool, float] = None,
            frame_area: Union[bool, float] = None,
            cover: float= 0,
        ):
        self.etabs.set_current_unit('N', 'cm')
        beam_rebars = self.SapModel.DesignConcrete.GetSummaryResultsBeam(name)
        if location == 'top':
            areas = beam_rebars[4]
        elif location == 'bot':
            areas = beam_rebars[6]
        first_dist = beam_rebars[2][0]
        last_dist = beam_rebars[2][-1]
        if distance < first_dist:
            area = areas[0]
            if not torsion_area:
                torsion_area = beam_rebars[10][0] / 2
        elif distance > last_dist:
            area = areas[-1]
            if not torsion_area:
                torsion_area = beam_rebars[10][-1] / 2
        else:
            import numpy as np
            from scipy.interpolate import interp1d
            f = interp1d(beam_rebars[2], areas)
            area = f(distance)
            if not torsion_area:
                f = interp1d(beam_rebars[2], beam_rebars[10])
                torsion_area = f(distance) / 2
        area += torsion_area
        if frame_area is None:
            frame_area = self.etabs.frame_obj.get_area(name, cover=cover)
        return area / frame_area
    
    def get_deflection_of_beam(self,
        dead: list,
        supper_dead: list,
        lives: list,
        beam_name: str,
        distance: float,
        location: str = 'top',
        torsion_area: Union[bool, float] = None,
        frame_area: Union[bool, float] = None,
        cover: float= 6,
        lives_percentage: float = 0.25,
        filename: str='',
        ):
        self.etabs.run_analysis()
        self.etabs.start_design()
        print('Getting Rho')
        rho = self.get_rho(
            beam_name,
            distance,
            location,
            torsion_area,
            frame_area,
            cover,
        )
        landa = 2 / (1 + 50 * rho)
        print(f'{rho=}\n{landa=}')
        if not filename:
            filename = f'deflection{beam_name}.EDB'
        print(f'Save file as {filename}')
        self.etabs.save_as(filename)
        beams, columns = self.etabs.frame_obj.get_beams_columns()
        self.etabs.frame_obj.assign_frame_modifires(
            frame_names=beams + columns,
            i22=1,
            i33=1,
        )
        self.etabs.database.set_floor_cracking(type_='Frame')
        self.etabs.database.set_floor_cracking(type_='Area')
        lc1, lc2, lc3 = self.etabs.database.create_nonlinear_loadcases(
            dead=dead,
            supper_dead=supper_dead,
            lives=lives,
            lives_percentage=lives_percentage,
            )
        self.SapModel.RespCombo.Add('deflection1', 0)
        self.SapModel.RespCombo.SetCaseList('deflection1', 0, lc2, 1)
        self.SapModel.RespCombo.SetCaseList('deflection1', 0, lc1, -1)
        self.SapModel.RespCombo.Add('deflection2', 0)
        self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc2, 1)
        self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc1, -1)
        self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc1, landa)
        if supper_dead:
            self.SapModel.RespCombo.SetCaseList('deflection2', 0, lc3, -1)
        self.etabs.run_analysis()
        
        


            






        
        







if __name__ == '__main__':
    from pathlib import Path
    current_path = Path(__file__).parent
    import sys
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    etabs.design.get_code()
    print('Wow')
