from pathlib import Path
from typing import Union
import math


__all__ = ['Safe16']


class Safe16():
    def __init__(self,
            input_f2k_path : Path = None,
            output_f2k_path : Path = None,
        ) -> None:
        self.input_f2k_path = input_f2k_path
        if output_f2k_path is None:
            output_f2k_path = input_f2k_path
        self.output_f2k_path = output_f2k_path
        self.__file_object = None
        self.tables_contents = {}

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
                if line.startswith("TABLE:") or "END TABLE DATA" in line:
                    if table_key and context:
                        tables_contents[table_key] = context
                    context = ''
                    table_key = line[n+1:-2]
                else:
                    context += line
        self.tables_contents = tables_contents
        return tables_contents
    
    def get_points_contents(self):
        return self.tables_contents.get("OBJECT GEOMETRY - POINT COORDINATES", '')

    def get_points_coordinates(self,
            content : str = None,
            ) -> dict:
        if content is None:
            content = self.get_points_contents()
        lines = content.split('\n')
        points_coordinates = dict()
        for line in lines:
            point_name = None
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
            if point_name is not None:
                points_coordinates[point_name] = coordinates
        return points_coordinates

    def is_point_exist(self,
            coordinate : list,
            content : Union[str, bool] = None,
            points_coordinates : Union[bool, dict] = None,
            ):
        if points_coordinates is None:
            points_coordinates = self.get_points_coordinates(content)
        for _id, coord in points_coordinates.items():
            if (
                len(coord) == 3 and
                math.isclose(coord[0], coordinate[0], abs_tol=.001) and
                math.isclose(coord[1], coordinate[1], abs_tol=.001) and
                math.isclose(coord[2], coordinate[2], abs_tol=.001)
                ):
                return _id
        return None
    
    def get_last_point_number(self,
        content: Union[str, bool]=None,
        ):
        point_coordinated = self.get_points_coordinates(content=content)
        # get points with numbers, maybe some point did not number ~1000
        point_numbers = set()
        for id_ in point_coordinated.keys():
            try:
                id_ = int(id_)
                point_numbers.add(id_)
            except:
                continue
        if len(point_numbers) == 0:
            return 1000000
        return max(point_numbers) + 1
                    
    def add_content_to_table(self, table_key, content, append=True):
        '''
        if append is True, content add to current content
        '''
        if append:
            curr_content = self.tables_contents.get(table_key, '')
        else:
            curr_content = ''
        self.tables_contents[table_key] = curr_content + content
        return None

    def set_analysis_type(self, is_2d='Yes'):
        table_key =  "ADVANCED MODELING OPTIONS"
        content = f"2DOnly={is_2d}   RigDiaTop=No   NoOffsets=Yes"
        self.add_content_to_table(table_key, content, append=False)
    
    def set_mesh_options(self, mesh_size=300):
        table_key =  "AUTOMATIC SLAB MESH OPTIONS"
        content = f"MeshOpt=Rectangular   Localize=Yes   Merge=Yes   MaxSize={mesh_size * self.length_units.get('mm')}"
        self.add_content_to_table(table_key, content, append=False)

    def force_length_unit(self,
        content : Union[str, bool] = None,
        ):
        if content is None:
            if len(self.tables_contents) == 0:
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
    
    def set_sthtbelow(self,
                      level: float=0,
                      content : Union[str, bool] = None,
                      ):
        table_key = "PROGRAM CONTROL"
        if content is None:
            if len(self.tables_contents) == 0:
                self.get_tables_contents()
            content = self.tables_contents.get(table_key, None)
            if content is None:
                return None
        label = 'StHtBelow='
        first_label_index = content.find(label)
        if first_label_index == -1: # version 14
            label = 'ModelDatum='
            first_label_index = content.find(label)
        last_label_index = first_label_index + len(label)
        space_index = content[last_label_index:].find(' ')
        if space_index == -1:
            content = content[:last_label_index] + f'{level}'
        else:
            end_index = space_index + last_label_index
            content = content[:last_label_index] + f'{level}' + content[end_index:] 
        self.tables_contents[table_key] = content
        return content

    def write(self):
        if len(self.tables_contents) == 0:
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