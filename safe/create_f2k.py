from pathlib import Path
from typing import Union
import math


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
            contex = ''
            table_key = None
            for line in lines:
                if line.startswith("TABLE:"):
                    if table_key and contex:
                        tables_contents[table_key] = contex
                    contex = ''
                    table_key = line[n+1:-2]
                else:
                    contex += line
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
            ):
        input_f2k.touch()
        super().__init__(input_f2k)
        if etabs is None:
            from etabs_api import etabs_obj
            etabs = etabs_obj.EtabsModel(backup=False)
        self.etabs = etabs
        self.etabs.set_current_unit('N', 'mm')
        if load_cases is None:
            load_cases = self.etabs.load_cases.get_load_cases()
        self.load_cases = load_cases
        if case_types is None:
            case_types = ['LinModEigen', 'LinStatic', 'LinRespSpec']
        self.case_types = case_types
        self.initiate()

    def initiate(self):
        table_key = "PROGRAM CONTROL"
        content = 'ProgramName="SAFE 2016"   Version=16.0.0   ProgLevel="Post Tensioning"   CurrUnits="N, mm, C"\n'
        self.tables_contents = dict()
        self.tables_contents[table_key] =  content

    def add_point_coordinates(self):
        base_name = self.etabs.story.get_base_name_and_level()[0]
        table_key = 'Point Object Connectivity'
        cols = ['UniqueName', 'X', 'Y', 'Z', 'Story']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        filt = df['Story'] == base_name
        df = df.loc[filt]
        df['Story'] = "SpecialPt=Yes"
        d = {'UniqueName' : 'Point=', 'X': 'GlobalX=', 'Y': 'GlobalY=', 'Z': 'GlobalZ=', }
        for col, pref in d.items():
            df[col] = pref + df[col]
        content = df.to_string(header=False, index=False)
        table_key = "OBJECT GEOMETRY - POINT COORDINATES"
        self.add_content_to_table(table_key, content)
        return content
        


        





    
    


class FreecadReadwriteModel():

    def __init__(
                self,
                input_f2k_path : Path,
                output_f2k_path : Path = None,
                doc: 'App.Document' = None,
                ):
        if output_f2k_path is None:
            output_f2k_path = input_f2k_path
        self.safe = Safe(input_f2k_path, output_f2k_path)
        self.safe.get_tables_contents()
        self.safe.force_length_unit()
        self.force_unit = self.safe.force_unit
        self.length_unit = self.safe.length_unit
        if doc is None:
            doc = FreeCAD.ActiveDocument
        self.doc = doc
        self.last_point_number = 1000
        self.last_area_number = 1000
        self.last_line_number = 1000

    def export_freecad_slabs(self,
        split_mat : bool = True,
        soil_name : str = 'SOIL',
        soil_modulus : float = 2,
        slab_sec_name : Union[str, None] = None,
            ):
        
        foun = self.doc.Foundation
        if slab_sec_name is None:
            foun_height = foun.height.getValueAs(f'{self.length_unit}')
            slab_sec_name = f'SLAB{foun_height}'
        # creating concrete material
        mat_name = self.create_concrete_material(foun=foun)
        # define slab
        self.create_solid_slab(slab_sec_name, 'Mat', mat_name, foun_height)
        slab_names = []
        if foun.foundation_type == 'Strip':
            # soil content
            names_props = [(soil_name, soil_modulus)]
            soil_content = self.create_soil_table(names_props)
            points = punch_funcs.get_points_of_foundation_plan_and_holes(foun)
            name = self.create_area_by_coord(points[0], slab_sec_name)
            slab_names.append(name)
            soil_assignment_content =  self.export_freecad_soil_support(
                slab_names=slab_names,
                soil_name=soil_name,
                soil_modulus=None,
            )
            for pts in points[1:]:
                self.create_area_by_coord(pts, is_opening=True)
        
        elif foun.foundation_type == 'Mat':
            if split_mat:
                names_props = [
                    (soil_name, soil_modulus),
                    (f'{soil_name}_1.5', soil_modulus * 1.5),
                    (f'{soil_name}_2', soil_modulus * 2),
                ]
                soil_content = self.create_soil_table(names_props)
                area_points = punch_funcs.get_sub_areas_points_from_face_with_scales(
                    foun.plane_without_openings,
                )
                for points in area_points:
                    name = self.create_area_by_coord(points, slab_sec_name)
                    slab_names.append(name)
                soil_assignment_content = self.export_freecad_soil_support(
                    slab_names=[slab_names[-1]],
                    soil_name=soil_name,
                    soil_modulus=None,
                )
                soil_assignment_content += self.export_freecad_soil_support(
                    slab_names=slab_names[:2],
                    soil_name=f'{soil_name}_2',
                    soil_modulus=None,
                )
                soil_assignment_content += self.export_freecad_soil_support(
                    slab_names=slab_names[2:4],
                    soil_name=f'{soil_name}_1.5',
                    soil_modulus=None,
                )
                
            else:
                names_props = [(soil_name, soil_modulus)]
                soil_content = self.create_soil_table(names_props)
                edges = foun.plane_without_openings.Edges
                points = self.get_sort_points(edges)
                name = self.create_area_by_coord(points, slab_sec_name)
                slab_names.append(name)
                soil_assignment_content = self.export_freecad_soil_support(
                    slab_names=slab_names,
                    soil_name=soil_name,
                    soil_modulus=None,
                )
        table_key = "SOIL PROPERTIES"
        self.safe.add_content_to_table(table_key, soil_content)
        table_key = "SOIL PROPERTY ASSIGNMENTS"
        self.safe.add_content_to_table(table_key, soil_assignment_content)
        return slab_names

    def get_sort_points(self, edges, vector=True):
        points = []
        edges = Part.__sortEdges__(edges)
        for e in edges:
            v = e.firstVertex()
            if vector is True:
                points.append(FreeCAD.Vector(v.X, v.Y, v.Z))
            else:
                points.append(v)
        return points

    def create_area_by_coord(self,
            points : 'Base.Vector',
            prop_name : Union[str, bool] = None,
            is_opening : bool = False,
            ):
        n = len(points)
        nodes = []
        points_content = ''
        area_name = self.last_area_number
        areas_content = f"\tArea={area_name}   NumPoints={n}"
        length_scale = self.safe.length_units.get('mm')
        for i, point in enumerate(points, start=1):
            x = point.x * length_scale
            y = point.y * length_scale
            z = point.z * length_scale
            if i % 4 == 0:
                points_content += f"Point={self.last_point_number}   GlobalX={x}   GlobalY={y}   GlobalZ={z}   SpecialPt=No\n"
                nodes.append(self.last_point_number)
                self.last_point_number += 1
                if i == 4:
                    areas_content += f"\tPoint1={nodes[0]}   Point2={nodes[1]}   Point3={nodes[2]}   Point4={nodes[3]}\n"
                else:
                    areas_content += f"\tArea={area_name}   Point1={nodes[0]}   Point2={nodes[1]}   Point3={nodes[2]}   Point4={nodes[3]}\n"
                nodes = []
            else:
                points_content += f"Point={self.last_point_number}   GlobalX={x}   GlobalY={y}   GlobalZ={z}   SpecialPt=No\n"
                nodes.append(self.last_point_number)
                self.last_point_number += 1
        for i, node in enumerate(nodes, start=1):
            if i == 1 and n > 4:
                areas_content += f"Area={area_name}"
            areas_content += f"\tPoint{i}={node}   "
        self.last_area_number += 1
        areas_content += '\n'
        table_key = "OBJECT GEOMETRY - POINT COORDINATES"
        self.safe.add_content_to_table(table_key, points_content)
        table_key = "OBJECT GEOMETRY - AREAS 01 - GENERAL"
        self.safe.add_content_to_table(table_key, areas_content)
        if is_opening:
            slab_assignment_content = f"\tArea={area_name}   SlabProp=None   OpeningType=Unloaded\n"
        else:
            slab_assignment_content = f"\tArea={area_name}   SlabProp={prop_name}   OpeningType=None\n"
        table_key = "SLAB PROPERTY ASSIGNMENTS"
        self.safe.add_content_to_table(table_key, slab_assignment_content)

        return area_name

    def export_freecad_openings(self, doc : 'App.Document' = None):
        foun = self.doc.Foundation
        if foun.foundation_type == 'Strip':
            return
        openings = foun.openings
        names = []
        for opening in openings:
            points = opening.points
            name = self.create_area_by_coord(points, is_opening=True)
            names.append(name)
        return names

    def export_freecad_strips(self):
        foun = self.doc.Foundation
        point_coords_table_key = "OBJECT GEOMETRY - POINT COORDINATES"
        points_content = ''
        curr_point_content = self.safe.tables_contents.get(point_coords_table_key, '')
        strip_table_key = "OBJECT GEOMETRY - DESIGN STRIPS"
        strip_content = ''
        strip_assign_table_key = "SLAB DESIGN OVERWRITES 01 - STRIP BASED"
        strip_assign_content = ''
        self.create_rebar_material('AIII', 400)
        scale_factor = self.safe.length_units['mm']
        if foun.foundation_type == 'Strip':
            slabs = foun.tape_slabs
            continuous_slabs = punch_funcs.get_continuous_slabs(slabs)
            i_strip = j = 0
            for ss in continuous_slabs:
                last = len(ss) - 1
                for i, slab in enumerate(ss):
                    if i == 0:
                        p1 = slab.start_point
                        coord1 = [coord * scale_factor for coord in (p1.x, p1.y, p1.z)]
                        p1_name = self.safe.is_point_exist(coord1, curr_point_content + points_content)
                        if p1_name is None:
                            points_content += f"Point={self.last_point_number}   GlobalX={coord1[0]}   GlobalY={coord1[1]}   GlobalZ={coord1[2]}   SpecialPt=No\n"
                            p1_name = self.last_point_number
                            self.last_point_number += 1
                    p2 = slab.end_point
                    coord2 = [coord * scale_factor for coord in (p2.x, p2.y, p2.z)]
                    p2_name = self.safe.is_point_exist(coord2, curr_point_content + points_content)
                    if p2_name is None:
                        points_content += f"Point={self.last_point_number}   GlobalX={coord2[0]}   GlobalY={coord2[1]}   GlobalZ={coord2[2]}   SpecialPt=No\n"
                        p2_name = self.last_point_number
                        self.last_point_number += 1
                    swl = ewl = (slab.width.Value / 2 + slab.offset) * scale_factor
                    swr = ewr = (slab.width.Value / 2 - slab.offset) * scale_factor
                    if i != last:
                        next_slab = ss[i + 1]
                        next_swl = (next_slab.width.Value / 2 + next_slab.offset) * scale_factor
                        next_swr = (next_slab.width.Value / 2 - next_slab.offset) * scale_factor
                    if i == 0:
                        dx = abs(p1.x - p2.x)
                        dy = abs(p1.y - p2.y)
                        if dx > dy:
                            layer = 'A'
                            i_strip += 1
                            name = f'CS{layer}{i_strip}'
                        else:
                            layer = 'B'
                            j += 1
                            name = f'CS{layer}{j}'
                    if i == 0:
                        strip_content += f'\tStrip={name}   Point={p1_name}   GlobalX={coord1[0]}   GlobalY={coord1[1]}   WALeft={swl}   WARight={swr}   AutoWiden=No\n'
                    if i == last: # last strip
                        strip_content += f'\tStrip={name}   Point={p2_name}   GlobalX={coord2[0]}   GlobalY={coord2[1]}   WBLeft={ewl}   WBRight={ewr}\n'
                    else:
                        strip_content += f'\tStrip={name}   Point={p2_name}   GlobalX={coord2[0]}   GlobalY={coord2[1]}   WBLeft={ewl}   WBRight={ewr} WALeft={next_swl}   WARight={next_swr} \n'
                strip_assign_content += f'\tStrip={name}   Layer={layer}   DesignType=Column   RLLF=1   Design=Yes   IgnorePT=No   RebarMat=AIII   CoverType=Preferences\n'
        self.safe.add_content_to_table(point_coords_table_key, points_content)
        self.safe.add_content_to_table(strip_table_key, strip_content)
        self.safe.add_content_to_table(strip_assign_table_key, strip_assign_content)

    def export_freecad_stiff_elements(self):
        fc_mpa = self.doc.Foundation.fc.getValueAs('MPa')
        self.create_concrete_material('CONCRETE_ZERO', fc_mpa, 0)
        thickness = 1500 * self.safe.length_units['mm']
        self.create_solid_slab('COL_STIFF', 'Stiff', 'CONCRETE_ZERO', thickness)
        for o in self.doc.Objects:
            if (hasattr(o, "Proxy") and 
                hasattr(o.Proxy, "Type") and 
                o.Proxy.Type == "Punch"
                ):
                points = self.get_sort_points(o.rect.Edges)
                self.create_area_by_coord(points, prop_name='COL_STIFF')
    
    def export_freecad_wall_loads(self):
        point_coords_table_key = "OBJECT GEOMETRY - POINT COORDINATES"
        points_content = ''
        curr_point_content = self.safe.tables_contents.get(point_coords_table_key, '')
        scale_factor = self.safe.length_units['mm']
        line_content = ''
        line_load_content = ''
        points_content = ''
        for o in self.doc.Objects:
            if (hasattr(o, "Proxy") and
                hasattr(o.Proxy, "Type") and
                o.Proxy.Type == "Wall"
                ):
                mass_per_area = o.weight
                height = o.Height.getValueAs('m')
                loadpat = o.loadpat
                value = mass_per_area * height * self.safe.force_units['Kgf'] / self.safe.length_units['m']
                p1 = o.Base.start_point
                p2 = o.Base.end_point
                coord1 = [i * scale_factor for i in (p1.x, p1.y, p1.z)]
                coord2 = [i * scale_factor for i in (p2.x, p2.y, p2.z)]
                p1_name = self.safe.is_point_exist(coord1, curr_point_content + points_content)
                p2_name = self.safe.is_point_exist(coord2, curr_point_content + points_content)
                if p1_name is None:
                    points_content += f"Point={self.last_point_number}   GlobalX={coord1[0]}   GlobalY={coord1[1]}   GlobalZ={coord1[2]}   SpecialPt=No\n"
                    p1_name = self.last_point_number
                    self.last_point_number += 1
                if p2_name is None:
                    points_content += f"Point={self.last_point_number}   GlobalX={coord2[0]}   GlobalY={coord2[1]}   GlobalZ={coord2[2]}   SpecialPt=No\n"
                    p2_name = self.last_point_number
                    self.last_point_number += 1
                line_content += f'Line={self.last_line_number}   PointI={p1_name}   PointJ={p2_name}   LineType=Beam\n'
                name = self.last_line_number
                self.last_line_number += 1
                line_load_content += f'Line={name}   LoadPat={loadpat}   Type=Force   Dir=Gravity   DistType=RelDist   RelDistA=0   RelDistB=1   FOverLA={value}   FOverLB={value}\n'
                
        if points_content:
            self.safe.add_content_to_table(point_coords_table_key, points_content)
        table_key = "OBJECT GEOMETRY - LINES 01 - GENERAL"
        self.safe.add_content_to_table(table_key, line_content)
        table_key = "LOAD ASSIGNMENTS - LINE OBJECTS - DISTRIBUTED LOADS"
        self.safe.add_content_to_table(table_key, line_load_content)

    def export_freecad_soil_support(self,
        slab_names : list,
        soil_name : str = 'SOIL',
        soil_modulus : Union[float, bool] = None,
        ):
        # self.etabs.set_current_unit('kgf', 'cm')
        # if soil_modulus is not None:
        #     self.SapModel.PropAreaSpring.SetAreaSpringProp(
        #         soil_name, 0, 0, soil_modulus , 3)
        soil_assignment_content = ''
        for slab_name in slab_names:
            soil_assignment_content += f"Area={slab_name}   SoilProp={soil_name}\n"
        return soil_assignment_content

    def export_punch_props(self,
            punches : Union[list, bool] = None,
            ):
        if punches is None:
            punches = []
            for o in self.doc.Objects:
                if hasattr(o, "Proxy") and \
                    hasattr(o.Proxy, "Type") and \
                    o.Proxy.Type == "Punch":
                    punches.append(o)
        punch_general_content = ''
        punch_perimeter_content = ''
        scale = self.safe.length_units['mm']
        for punch in punches:
            id_ = punch.id
            loc = punch.Location
            depth = punch.d * scale
            punch_general_content += f'\tPoint={id_}   Check="Program Determined"   LocType="{loc}"   Perimeter="User Perimeter"   EffDepth=User   UserDepth={depth}   Openings=User   ReinfType=None\n'
            nulls, null_points = punch_funcs.punch_null_points(punch)
            for i, (point, is_null) in enumerate(zip(null_points, nulls), start=1):
                x, y = point.x * scale, point.y * scale
                punch_perimeter_content += f'\tPoint={id_}   PointNum={i}   X={x}   Y={y}   Radius=0   IsNull={is_null}\n'

        punch_general_table_key = "PUNCHING SHEAR DESIGN OVERWRITES 01 - GENERAL"
        punch_perimeter_table_key = "PUNCHING SHEAR DESIGN OVERWRITES 02 - USER PERIMETER"
        self.safe.add_content_to_table(punch_general_table_key, punch_general_content)
        self.safe.add_content_to_table(punch_perimeter_table_key, punch_perimeter_content)

    def add_uniform_gravity_load(self,
        area_names : list,
        load_pat : str,
        value : float,
        ) -> None:
        table_key = "LOAD ASSIGNMENTS - SURFACE LOADS"
        content = ''
        value *= self.safe.force_units['Kgf'] / self.safe.length_units['m'] ** 2
        for area_name in area_names:
            content += f'Area={area_name}   LoadPat={load_pat}   Dir=Gravity   UnifLoad={value}   A=0   B=0   C=0\n'
        self.safe.add_content_to_table(table_key, content)

    @staticmethod
    def get_vertex_from_point(point):
        return Part.Vertex(point.x, point.y, point.z)

    def create_soil_table(self, soil_prop):
        soil_content = ''
        for name, ks in soil_prop:
            ks *= self.safe.force_units['Kgf'] / self.safe.length_units['cm'] ** 3
            soil_content += f'Soil={name}   Subgrade={ks}   NonlinOpt="Compression Only"\n'
        return soil_content

    def add_material(self,
            name : str,
            type_ : str,
            ):
        '''
        type can be 'Concrete', 'Rebar', ...
        '''
        table_key = "MATERIAL PROPERTIES 01 - GENERAL"
        material_content = f'\tMaterial={name}   Type={type_}\n'
        self.safe.add_content_to_table(table_key, material_content)
        
    def create_concrete_material(self,
            mat_name = '',
            fc_mpa = 0,
            weight = 2400,
            foun = None,
            ):
        if foun is not None:
            fc_mpa = int(foun.fc.getValueAs("MPa"))
            mat_name = f'C{fc_mpa}'
        fc = fc_mpa * self.safe.force_units['N'] / self.safe.length_units['mm'] ** 2
        self.add_material(mat_name, 'Concrete')
        table_key = "MATERIAL PROPERTIES 03 - CONCRETE"
        A = 9.9E-06
        unit_weight = weight * self.safe.force_units['Kgf'] / self.safe.length_units['m'] ** 3
        if weight == 0:
            Ec = .043 * 2400 ** 1.5 * math.sqrt(fc_mpa)
        else:
            Ec = .043 * weight ** 1.5 * math.sqrt(fc_mpa)
        mat_prop_content = f'Material={mat_name}   E={Ec}   U=0.2   A={A}   UnitWt={unit_weight}   Fc={fc}   LtWtConc=No   UserModRup=No\n'
        self.safe.add_content_to_table(table_key, mat_prop_content)
        return mat_name
    
    def create_rebar_material(self,
            mat_name = 'AIII',
            fy_mpa : int = 400,
            ):
        self.add_material(mat_name, 'Rebar')
        table_key = "MATERIAL PROPERTIES 04 - REBAR"
        weight = 7850
        unit_weight = weight * self.safe.force_units['Kgf'] / self.safe.length_units['m'] ** 3
        E = 2e5 * self.safe.force_units['N'] / self.safe.length_units['mm'] ** 2
        fy = fy_mpa * self.safe.force_units['N'] / self.safe.length_units['mm'] ** 2
        fu = 1.25 * fy
        mat_prop_content = f'Material={mat_name}   E={E}   UnitWt={unit_weight}   Fy={fy}   Fu={fu}\n'
        self.safe.add_content_to_table(table_key, mat_prop_content)
        return mat_name

    def create_solid_slab(self,
            name : str,
            type_ : str, # 'Mat', 'Stiff', 'Slab'
            material,
            thickness,
            is_thick='Yes',
            ):
        table_key = "SLAB PROPERTIES 01 - GENERAL"
        slab_general_content = f'Slab={name}   Type={type_}   ThickPlate={is_thick}\n'
        self.safe.add_content_to_table(table_key, slab_general_content)
        table_key = "SLAB PROPERTIES 02 - SOLID SLABS"
        slab_prop_content = f'Slab={name}   Type={type_}   MatProp={material}   Thickness={thickness}   Ortho=No\n'
        self.safe.add_content_to_table(table_key, slab_prop_content)

    def add_preferences(self):
        table_key = "DESIGN PREFERENCES 02 - REBAR COVER - SLABS"
        foun = self.doc.Foundation
        cover_mm = foun.cover.getValueAs('mm')
        cover = cover_mm * self.safe.length_units['mm']
        content = f'\tCoverTop={cover}   CoverBot={cover}   BarSize=20\n'
        self.safe.tables_contents[table_key] = content

if __name__ == '__main__':
    import sys
    from pathlib import Path

    FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
    sys.path.append(FREECADPATH)
    import FreeCAD
    if FreeCAD.GuiUp:
        document = FreeCAD.ActiveDocument
    else:
        filename = Path(__file__).absolute().parent.parent / 'test' / 'etabs_api' / 'test_files' / 'freecad' / 'mat.FCStd'
        document= FreeCAD.openDocument(str(filename))
    slabs = document.Foundation.tape_slabs
    openings = document.Foundation.openings

    current_path = Path(__file__).parent
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False, software='SAFE')
    # etabs.area.get_scale_area_points_with_scale(document.Foundation.plane_without_openings)
    SapModel = etabs.SapModel
    ret = etabs.area.export_freecad_slabs(document)
    ret = etabs.area.export_freecad_openings(openings)
    print('Wow')

