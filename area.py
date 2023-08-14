from typing import Union
import math
import pandas as pd


if __name__ == '__main__':
    import sys
    FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
    sys.path.append(FREECADPATH)
try:
    import FreeCAD
    import Part
    from safe.punch import punch_funcs
except:
    pass

__all__ = ['Area']


class Area:
    def __init__(
                self,
                etabs=None,
                ):
        self.etabs = etabs
        self.SapModel = etabs.SapModel

    def get_names_of_areas_of_type(
            self,
            type_='floor',
            story : Union[str, bool] = None,
            ):
        '''
        type_: wall:1, floor:2
        '''
        map_dict = {'wall':1, 'floor':2}
        type_ = map_dict.get(type_, 5)
        names = []
        for name in self.SapModel.AreaObj.GetNameList()[1]:
            if self.SapModel.AreaObj.GetDesignOrientation(name)[0] == type_:
                names.append(name)
        return names
    
    def get_slab_names(self,
        types: list=['Slab', 'Waffle'],
        ):
        '''
        get slab names with type in types
        '''
        table_key = "Area Assignments - Section Properties"
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if types:
            filt = df['PropType'].isin(types)
            df = df.loc[filt]
        return df['UniqueName']

    def export_freecad_slabs(self,
        doc : 'App.Document' = None,
        soil_name : str = 'SOIL',
        soil_modulus : float = 2,
        slab_sec_name : Union[str, None] = None,
            ):
        if doc is None:
            doc = FreeCAD.ActiveDocument
        foun = doc.Foundation
        if slab_sec_name is None:
            foun_height = int(foun.height.Value)
            slab_sec_name = f'SLAB{foun_height}'
        # creating concrete material
        fc = int(foun.fc.getValueAs('N/(mm^2)'))
        self.etabs.set_current_unit('N', 'mm')
        self.SapModel.PropMaterial.SetMaterial(f'C{fc}', 2)
        self.SapModel.PropMaterial.SetOConcrete(f'C{fc}', fc, False, 0, 1, 1, .002, .005)
        self.SapModel.PropArea.SetSlab(slab_sec_name, 5, 2, f'C{fc}', foun_height)
        
        slab_names = []
        if foun.foundation_type == 'Strip':
            # write soil table
            names_props = [(soil_name, f'{soil_modulus}')]
            self.etabs.database.create_area_spring_table(names_props)
            self.etabs.set_current_unit('kN', 'mm')
            points = punch_funcs.get_points_of_foundation_plan_and_holes(foun)
            name = self.create_area_by_coord(points[0], slab_sec_name)
            slab_names.append(name)
            self.export_freecad_soil_support(
                slab_names=slab_names,
                soil_name=soil_name,
                soil_modulus=None,
            )
            self.etabs.set_current_unit('kN', 'mm')
            for pts in points[1:]:
                n = len(pts)
                xs = [p.x for p in pts]
                ys = [p.y for p in pts]
                zs = [p.z for p in pts]
                ret = self.SapModel.AreaObj.AddByCoord(n, xs, ys, zs, '', slab_sec_name)
                name = ret[3]
                self.SapModel.AreaObj.SetOpening(name, True)
        elif foun.foundation_type == 'Mat':
            if foun.split:
                names_props = [
                    (soil_name, f'{soil_modulus}'),
                    (f'{soil_name}_1.5', f'{soil_modulus * 1.5}'),
                    (f'{soil_name}_2', f'{soil_modulus * 2}'),
                ]
                self.etabs.database.create_area_spring_table(names_props)
                self.etabs.set_current_unit('kN', 'mm')
                area_points = punch_funcs.get_sub_areas_points_from_face_with_scales(
                    foun.plan_without_openings,
                )
                for points in area_points:
                    name = self.create_area_by_coord(points, slab_sec_name)
                    slab_names.append(name)
                self.export_freecad_soil_support(
                    slab_names=[slab_names[-1]],
                    soil_name=soil_name,
                    soil_modulus=None,
                )
                self.export_freecad_soil_support(
                    slab_names=slab_names[:2],
                    soil_name=f'{soil_name}_2',
                    soil_modulus=None,
                )
                self.export_freecad_soil_support(
                    slab_names=slab_names[2:4],
                    soil_name=f'{soil_name}_1.5',
                    soil_modulus=None,
                )
            else:
                names_props = [(soil_name, f'{soil_modulus}')]
                self.etabs.database.create_area_spring_table(names_props)
                self.etabs.set_current_unit('kN', 'mm')
                edges = foun.plan_without_openings.Edges
                points = self.get_sort_points(edges)
                name = self.create_area_by_coord(points, slab_sec_name)
                slab_names.append(name)
                self.export_freecad_soil_support(
                    slab_names=slab_names,
                    soil_name=soil_name,
                    soil_modulus=None,
                )
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
            ):
        n = len(points)
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        zs = [p.z for p in points]
        if prop_name is None:
            ret = self.SapModel.AreaObj.AddByCoord(n, xs, ys, zs)
        else:
            ret = self.SapModel.AreaObj.AddByCoord(n, xs, ys, zs, '', prop_name)
        return ret[3]

    def export_freecad_openings(self, doc : 'App.Document' = None):
        self.etabs.set_current_unit('kN', 'mm')
        if doc is None:
            doc = FreeCAD.ActiveDocument
        foun = doc.Foundation
        if foun.foundation_type == 'Strip':
            return
        openings = foun.openings
        for opening in openings:
            points = opening.points
            n = len(points)
            xs = [p.x for p in points]
            ys = [p.y for p in points]
            zs = [p.z for p in points]
            ret = self.SapModel.AreaObj.AddByCoord(n, xs, ys, zs)
            name = ret[3]
            self.SapModel.AreaObj.SetOpening(name, True)

    def export_freecad_strips(self,
                              doc : 'App.Document' = None,
                              story: str='',
                              ):
        self.etabs.set_current_unit('N', 'mm')
        z_level = 0
        if story:
            z_level = self.SapModel.Story.GetElevation(story)[0]
        if doc is None:
            doc = FreeCAD.ActiveDocument
        data = []
        for o in doc.Objects:
            if hasattr(o, 'Proxy') and \
                hasattr(o.Proxy, 'Type') and \
                    o.Proxy.Type == 'Strip':
                layer = o.layer
                strip_name = o.Label
                points = o.Base.Points
                sl = o.left_width.Value
                sr = o.right_width.Value
                swl = ewl = sl
                swr = ewr = sr
                placement = o.Placement.Base + o.Base.Placement.Base
                for j, point in enumerate(points):
                    if j == 0:
                        p1 = self.SapModel.PointObj.AddCartesian(
                            point.x + placement.x,
                            point.y + placement.y,
                            z_level,
                            )
                        p1_name = p1[0]
                        p2 = self.SapModel.PointObj.AddCartesian(
                            points[1].x + placement.x,
                            points[1].y + placement.y,
                            z_level,
                            )
                        p2_name = p2[0]
                        data.extend((
                            strip_name,
                            f'{p1_name}',
                            f'{p2_name}',
                            f'{swl}',
                            f'{swr}',
                            f'{ewl}',
                            f'{ewr}',
                            'No',
                            layer,
                            ))
                    elif j > 1:
                        p = self.SapModel.PointObj.AddCartesian(
                            point.x + placement.x,
                            point.y + placement.y,
                            z_level,
                            )
                        p_name = p[0]
                        data.extend((
                            strip_name,
                            '',
                            f'{p_name}',
                            f'{swl}',
                            f'{swr}',
                            f'{ewl}',
                            f'{ewr}',
                            '',
                            '',
                            ))
        fields = [
            'Name',
            'Strip Start Point',
            'Segment End Point',
            'Start Width Left',
            'Start Width Right',
            'End Width Left',
            'End Width Right',
            'Auto Widen',
            'Layer',
        ]
        df = self.etabs.database.reshape_data_to_df(fields, data)
        if self.etabs.etabs_main_version > 19:
            df.columns = ['Name', 'StartPoint', 'EndPoint', 'WStartLeft',
                        'WStartRight', 'WEndLeft', 'WEndRight', 'AutoWiden', 'Layer']
        if self.etabs.software == 'ETABS':
            df.insert(loc=1, column='Story', value=story)
        table_key = 'Strip Object Connectivity'
        self.etabs.database.write(table_key, df)

    def export_freecad_stiff_elements(self, doc : 'App.Document' = None):
        self.etabs.set_current_unit('kN', 'mm')
        self.SapModel.PropMaterial.SetMaterial('CONCRETE_ZERO', 2)
        self.SapModel.PropMaterial.SetWeightAndMass('CONCRETE_ZERO', 1, 0)
        self.SapModel.PropMaterial.SetWeightAndMass('CONCRETE_ZERO', 2, 0)
        self.SapModel.PropArea.SetSlab('COL_STIFF', 2, 2, 'CONCRETE_ZERO', 1500)

        if doc is None:
            doc = FreeCAD.ActiveDocument
        for o in doc.Objects:
            if (hasattr(o, "Proxy") and 
                hasattr(o.Proxy, "Type") and 
                o.Proxy.Type == "Punch"
                ):
                points = self.get_sort_points(o.rect.Edges)
                self.create_area_by_coord(points, prop_name='COL_STIFF')
    
    def export_freecad_wall_loads(self, doc : 'App.Document' = None):
        if doc is None:
            doc = FreeCAD.ActiveDocument
        for o in doc.Objects:
            if (hasattr(o, "Proxy") and 
                hasattr(o.Proxy, "Type") and 
                o.Proxy.Type == "Wall"
                ):
                mass_per_area = o.weight
                height = o.Height.Value / 1000
                p1 = o.Base.start_point
                p2 = o.Base.end_point
                self.etabs.set_current_unit('kgf', 'mm')
                frame = self.SapModel.FrameObj.AddByCoord(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z,'', 'None')
                name = frame[0]
                loadpat = self.etabs.load_patterns.get_special_load_pattern_names(1)[0]
                self.etabs.set_current_unit('kgf', 'm')
                self.etabs.frame_obj.assign_gravity_load_from_wall(
                    name = name,
                    loadpat = loadpat,
                    mass_per_area = mass_per_area,
                    height = height,
                )

    def export_freecad_soil_support(self,
        slab_names : list,
        soil_modulus : float = 2,
        soil_name : str = 'SOIL1',
        ):
        self.etabs.set_current_unit('kgf', 'cm')
        if soil_modulus is not None:
            self.SapModel.PropAreaSpring.SetAreaSpringProp(
                soil_name, 0, 0, soil_modulus , 3)
        for s in slab_names:
            self.SapModel.AreaObj.SetSpringAssignment(s, soil_name)

    def set_uniform_gravity_load(self,
        area_names : list,
        load_pat : str,
        value : float,
        ) -> None:
        self.etabs.set_current_unit('kgf', 'm')
        for area_name in area_names:
            self.SapModel.AreaObj.SetLoadUniform(
                area_name,
                load_pat,
                -value,
                6,  # Dir
            )


    @staticmethod
    def get_vertex_from_point(point):
        return Part.Vertex(point.x, point.y, point.z)
    

    def calculate_slab_weight_per_area(self,
                                    slabs: Union[list, bool] = None,
                                    ):
        self.etabs.set_current_unit('kgf', 'm')
        table_key = "Slab Property Definitions"
        df = self.etabs.database.read(table_key, to_dataframe=True)
        if slabs is not None:
            filt = df['Name'].isin(slabs)
            df = df.loc[filt]
        unit_weights = self.etabs.material.get_unit_weight_of_materials()
        df['UnitWeight'] = df['Material'].map(unit_weights)
        convert_types = {
            'Depth',
            'Thickness',
            'WidthTop',
            'WidthBot',
            'RibSpacing1',
            'RibSpacing2',
            'WMod',
        }
        convert_types = convert_types.intersection(df.columns)
        convert_types = {key: float for key in convert_types}
        df = df.astype(convert_types)
        # flat slabs
        thickness_names = ['Slab', 'Drop', 'Stiff', 'Mat', 'Footing']
        filt = df['PropType'].isin(thickness_names)
        df_thickness = df.loc[filt]
        df_thickness['h_equal'] = df_thickness['Thickness']
        df_thickness['RibWidth'] = None
        # Ribbed Slabs
        filt = df['PropType'] == 'Ribbed'
        df_ribbed = df.loc[filt]
        if not df_ribbed.empty:
            df_ribbed['RibWidth'] = (df_ribbed['WidthTop'] + df_ribbed['WidthBot']) / 2
            df_ribbed['h_equal'] = calculate_equivalent_height_according_to_volume(
                df_ribbed['RibSpacing1'],
                1,
                df_ribbed['Depth'],
                df_ribbed['RibWidth'],
                0,
                df_ribbed['Thickness']
            )
        # Waffle Slabs
        filt = df['PropType'] == 'Waffle'
        df_waffle = df.loc[filt]
        if not df_waffle.empty:
            df_waffle['RibWidth'] = (df_waffle['WidthTop'] + df_waffle['WidthBot']) / 2
            df_waffle['h_equal'] = calculate_equivalent_height_according_to_volume(
                df_waffle['RibSpacing1'],
                df_waffle['RibSpacing2'],
                df_waffle['Depth'],
                df_waffle['RibWidth'],
                df_waffle['RibWidth'],
                df_waffle['Thickness']
            )
        df = pd.concat([df_thickness, df_ribbed, df_waffle])
        df['Weight Kg/m^2'] = df['h_equal'] * df['UnitWeight'] * df['WMod']
        cols = ['Name', 'PropType', 'Material', 'UnitWeight', 'Thickness', 'RibWidth', 'WMod', 'h_equal', 'Weight Kg/m^2']
        df = df[cols]
        return df

    def calculate_deck_weight_per_area(self,
                                    decks: Union[list, bool] = None,
                                    use_user_deck_weight: bool = True
                                    ):
        self.etabs.set_current_unit('kgf', 'm')
        table_key = "Deck Property Definitions"
        cols = ['Name', 'DeckType', 'MaterialSlb', 'MaterialDck', 'SlabDepth', 'RibDepth', 'RibWidthTop', 'RibWidthBot', 'RibSpacing', 'DeckShrThk', 'DeckUnitWt', 'WMod']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        if decks is not None:
            filt = df['Name'].isin(decks)
            df = df.loc[filt]
        filt = df['DeckType'] == 'Filled'
        df = df.loc[filt]
        del df['DeckType']
        convert_types = {
            'SlabDepth': float,
            'RibDepth': float,
            'RibWidthTop': float,
            'RibWidthBot': float,
            'RibSpacing': float,
            'DeckShrThk': float,
            'DeckUnitWt': float,
            'WMod': float,
        }
        df = df.astype(convert_types)
        unit_weights = self.etabs.material.get_unit_weight_of_materials()
        df['UnitWeightSlab'] = df['MaterialSlb'].map(unit_weights)
        df['UnitWeightDeck'] = df['MaterialDck'].map(unit_weights)
        df['RibWidth'] = (df['RibWidthTop'] + df['RibWidthBot']) / 2
        df['d'] = df['SlabDepth'] + df['RibDepth']
        df['h_eq_slab'] = calculate_equivalent_height_according_to_volume(
            df['RibSpacing'],
            1,
            df['d'],
            df['RibWidth'],
            0,
            df['SlabDepth']
        )
        df['slab_weight'] = df['h_eq_slab'] * df['UnitWeightSlab'] * df['WMod']
        if use_user_deck_weight:
            df['deck_weight'] = df['DeckUnitWt']
        else:
            df['h_eq_deck'] = deck_plate_equivalent_height_according_to_volume(
                s=df['RibSpacing'],
                d=df['d'],
                tw_top=df['RibWidthTop'],
                tw_bot=df['RibWidthBot'],
                hc=df['SlabDepth'],
                t_deck=df['DeckShrThk'],
            )
            df['deck_weight'] = df['h_eq_deck'] * df['UnitWeightDeck']
            
        df['weight Kg/m^2'] = df['slab_weight'] + df['deck_weight']
        return df
        
    def get_all_slab_types(self) -> dict:
        '''
        Return all slab types in etabs model definition
        Slab, Drop, Stiff, Ribbed, Waffle, Mat, Footing
        '''
        table_key = "Slab Property Definitions"
        cols = ['Name', 'PropType']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        df = df.set_index('Name')
        return df.to_dict()['PropType']
    
    def get_expanded_shell_uniform_load_sets(self,
                                             areas: Union[list, bool]= None,
                                             ) -> pd.DataFrame:
        '''
        Example:
        "Shell Uniform Load Sets"
            Name	LoadPattern	LoadValue
        0	ROOF	Dead	    0.003	
        1	ROOF	LROOF	    0.0015
        2	ROOF	SNOW	    0.0011
        3	ROOF	WALL	    0.0005

        "Area Load Assignments - Uniform Load Sets"
            Story	Label	UniqueName	LoadSet
        0	Story4	F8	    44	        ROOF

        return:
            Story	Label	UniqueName	LoadSet	LoadPattern	Dir     LoadValue
        0	Story4	F8	    44	        ROOF	Dead	    Gravity 0.003
        1	Story4	F8	    44	        ROOF	LROOF	    Gravity 0.0015
        2	Story4	F8	    44	        ROOF	SNOW	    Gravity 0.0011
        3	Story4	F8	    44	        ROOF	WALL	    Gravity 0.0005
        '''
        self.etabs.set_current_unit('kgf', 'm')
        table_key = 'Area Load Assignments - Uniform Load Sets'
        df1 = self.etabs.database.read(table_key, to_dataframe=True)
        if areas is not None:
            filt = df1['UniqueName'].isin(areas)
            df1 = df1.loc[filt]
        if df1 is None or df1.empty:
            return pd.DataFrame(columns=['Story', 'Label', 'UniqueName', 'LoadSet', 'LoadPattern', 'LoadValue', 'Direction'])
        table_key = 'Shell Uniform Load Sets'
        df2 = self.etabs.database.read(table_key, to_dataframe=True)
        del df2['GUID']
        df = df1.merge(df2, left_on='LoadSet', right_on='Name')
        del df['Name']
        df['Direction'] = 'Gravity'
        return df
    
    def get_shell_uniform_loads(self,
                                areas: Union[list, bool]= None,
                                df1: Union[pd.DataFrame, bool]= None,
                                ) -> pd.DataFrame:
        '''
        Get All uniform loads on areas include uniforms and uniform load sets
        '''
        self.etabs.set_current_unit('kgf', 'm')
        # shell uniform load sets
        if df1 is None:
            df1 = self.get_expanded_shell_uniform_load_sets(areas=areas)
        del df1['LoadSet']
        df1.rename(columns={'LoadValue': 'Load'}, inplace=True)
        # shell uniform load
        table_key = 'Area Load Assignments - Uniform'
        df2 = self.etabs.database.read(table_key, to_dataframe=True)
        if df2 is not None:
            df2 = df2[['Story', 'Label', 'UniqueName', 'LoadPattern', 'Dir', 'Load']]
            df2.rename(columns={'Dir': 'Direction'}, inplace=True)
        df = pd.concat([df1, df2])
        return df
    
    def expand_uniform_load_sets_and_apply_to_model(self,
                                                    df: Union[pd.DataFrame, bool] = None,
                                                    ):
        df = self.get_shell_uniform_loads(df1=df)
        df = df[['UniqueName', 'LoadPattern', 'Direction', 'Load']]
        if self.etabs.etabs_main_version < 20:
            df.columns = ['UniqueName', 'Load Pattern', 'Direction', 'Load']
            df2 = pd.DataFrame(columns=['UniqueName', 'Load Set'])
        else:
            df.columns = ['UniqueName', 'LoadPattern', 'Dir', 'Load']
            df2 = pd.DataFrame(columns=['UniqueName', 'LoadSet'])
        table_key = 'Area Load Assignments - Uniform'
        self.etabs.database.apply_data(table_key, df)
        self.etabs.database.apply_data('Area Load Assignments - Uniform Load Sets', df2)
        return True
    
    def reset_slab_sections_modifiers(self,
            slabs: list=[],
            ):
        if not slabs:
            slabs = self.get_all_slab_types().keys()
        for slab in slabs:
            self.SapModel.PropArea.SetModifiers(slab, 10*[1])

    def assign_slab_modifiers(self,
            slab_names: list=[],
            f11: Union[None, float]=None,
            f22: Union[None, float]=None,
            f12: Union[None, float]=None,
            m11: Union[None, float]=None,
            m22: Union[None, float]=None,
            m12: Union[None, float]=None,
            v13: Union[None, float]=None,
            v23: Union[None, float]=None,
            mass: Union[None, float]=None,
            weight: Union[None, float]=None,
            reset: bool=False,
            ):
        '''
        reset means to set all slab section properties set to 1
        '''
        if reset:
            self.reset_slab_sections_modifiers()
        if len(slab_names) == 0:
            slab_names = self.get_slab_names()
        mod_names = [f11, f22, f12, m11, m22, m12, v13, v23, mass, weight]
        for name in slab_names:
            modifiers = list(self.SapModel.AreaObj.GetModifiers(name)[0])
            for i, mod in enumerate(mod_names):    
                if mod:
                    modifiers[i] = mod
            self.SapModel.AreaObj.SetModifiers(name, modifiers)
    
    def save_as_deflection_filename(self,
                                    slab_name: str,
                                    filename: str='',
    ):
        file_path = self.etabs.get_filepath()
        deflection_path = file_path / 'deflections'
        if not deflection_path.exists():
            import os
            os.mkdir(str(deflection_path))
        if not filename:
            label, story, _ = self.SapModel.AreaObj.GetLabelFromName(slab_name)
            filename = f'deflection_{label}_{story}.EDB'
            print(f'Save file as {filename} ...')
            self.SapModel.File.Save(str(deflection_path / filename))

    def design_slabs(self,
                    slab_names: list,
                    s: float,
                    d: float,
                    tw: float,
                    hc: float,
                    as_top: float,
                    as_bot: float,
                    fill: bool=False,
                    two_way: bool=True,
                    design: bool=True,
    ):
        kwargs = {'slab_names': slab_names,
                     'f11': 1,
                     'f22': 1,
                     'f12': 1,
                     'm11': 0.25,
                     'm22': 0.25,
                     'm12': 0.25,
                     'v13': 1,
                     'v23': 1,
                     'mass': 1,
                     'weight': 1,
                     'reset': True,
        }
        self.assign_slab_modifiers(**kwargs)
        rho_top, rho_bot = calculate_rho(s, d, tw, hc, as_top, as_bot, fill=fill, two_way=two_way)
        self.etabs.database.set_cracking_analysis_option(rho_bot, rho_top)
        if design:
            self.etabs.start_slab_design()

    def get_deflection_of_slab(self,
        dead: list,
        supper_dead: list,
        lives: list,
        slab_name: str,
        s: float,
        d: float,
        tw: float,
        hc: float,
        as_top: float,
        as_bot: float,
        two_way: bool=True,
        lives_percentage: float = 0.25,
        filename: str='',
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
        s: Spacing of Ribs that are Parallel to Slab 1-Axis
        d: Overall Depth
        tw: Average Stem Width
        hc: Slab Thickness
        as_top: Area of top rebars
        as_bot: Area of bottom rebars
        fill: calculate rho according to fill slab or not
        '''
        text = ''
        self.save_as_deflection_filename(slab_name=slab_name, filename=filename)
        self.design_slabs(slab_name, s, d, tw, hc, as_top, as_bot, True, two_way, True)
        self.etabs.unlock_model()
        print("Set frame stiffness modifiers ...")
        beams, columns = self.etabs.frame_obj.get_beams_columns()
        self.etabs.frame_obj.assign_frame_modifiers(
            frame_names=beams + columns,
            i22=1,
            i33=1,
        )
        print("Set Slab stiffness modifiers ...")
        self.assign_slab_modifiers(m11=1, m22=1, m12=1, reset=True)
        print("Set floor cracking for floors ...")
        # self.etabs.database.set_floor_cracking(type_='Frame')
        self.etabs.database.set_floor_cracking(names=[slab_name], type_='Area')
        # calculate rho and lambda
        _, rho = calculate_rho(s, d, tw, hc, as_top, as_bot, fill=False, two_way=two_way)
        landa = 2 / (1 + 50 * rho)
        text += f'lambda = 2 / (1 + 50 x rho) = 2 / (1 + 50 x {rho:.4f}) = {landa:.2f}'
        print(f'\n{rho=}\n{landa=}')
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
        return text
    
    def get_mesh_results(self,
                         slabs: list,
                         case_name: str='deflection1',
                         type_: str='Combo'
                         ) -> dict:
        '''
        returns mesh result suitable for show in FreeCAD
        '''
    
        map_dict = self.etabs.database.get_map_mesh_points()
        mesh_joint = self.etabs.database.area_mesh_joints(slabs, ['Floor'], map_dict=map_dict)
        points = self.etabs.points.get_objects_and_elements_joints_coordinate(map_dict=map_dict, joints=list(mesh_joint[2]))
        disps = self.etabs.results.get_points_displacement(list(mesh_joint[2]), lp_name=case_name, type_=type_, item_type_elm=1, map_dict=map_dict)
        results = [{'time': 1, 'disp': disps}]

        el3 = {}
        if len(mesh_joint[0]) > 0:
            for value in mesh_joint[0].values():
                el3.update(value)
        el4 = {}
        if len(mesh_joint[1]) > 0:
            for value in mesh_joint[1].values():
                el4.update(value)
        m = {
            "Nodes": points,
            "Seg2Elem": {},
            "Seg3Elem": {},
            "Tria3Elem": el3,
            "Tria6Elem": {},
            "Quad4Elem": el4,
            "Quad8Elem": {},
            "Tetra4Elem": {},
            "Tetra10Elem": {},
            "Hexa8Elem": {},
            "Hexa20Elem": {},
            "Penta6Elem": {},
            "Penta15Elem": {},
            "Results": results
            }
        return m

def deck_plate_equivalent_height_according_to_volume(
        s,
        d,
        tw_top,
        tw_bot,
        hc,
        t_deck,
        ) -> float:
    '''
    s: Spacing of Ribs
    d: Overall Depth
    tw_top, tw_bot: Stem Width at top & bot
    hc: Slab Thickness
    return the equivalent height of deck plate
    '''
    hw = d - hc
    eps_width = tw_top - tw_bot
    oblique_len = (hw ** 2 + (eps_width / 2) ** 2) ** 0.5
    equal_length = s - eps_width + 2 * oblique_len
    return equal_length * t_deck / s

def calculate_equivalent_height_according_to_volume(
        s1,
        s2,
        d,
        tw1,
        tw2,
        hc,
        ) -> float:
    '''
    s1: Spacing of Ribs that are Parallel to Slab 1-Axis
    s2: Spacing of Ribs that are Parallel to Slab 2-Axis
    d: Overall Depth
    tw1, tw2: Average Stem Width
    hc: Slab Thickness
    return the equivalent height of slab

    '''
    hw = (d - hc)
    equal_height = d - (s1 - tw1) * (s2 - tw2) * hw / (s1 * s2)
    return equal_height

def calculate_rho(
        s: float,
        d: float,
        tw: float,
        hc: float,
        as_top: float,
        as_bot: float,
        fill: bool=False,
        two_way: bool=True,
    ) -> tuple:
    '''
    s: Spacing of Ribs that are Parallel to Slab 1-Axis
    d: Overall Depth
    tw: Average Stem Width
    hc: Slab Thickness
    as_top: Area of top rebars
    as_bot: Area of bottom rebars
    fill: calculate rho according to fill slab or not
    return the (rho_top, rho_bot)
    '''
    if fill:
        h = d
    else:
        if two_way:
            h = calculate_equivalent_height_according_to_volume(
                s,
                s,
                d,
                tw,
                tw,
                hc,
            )
        else:
            h = calculate_equivalent_height_according_to_volume(
                s,
                1,
                d,
                tw,
                0,
                hc,
            )
    rho_top = as_top / (s * h)
    rho_bot = as_bot / (s * h)
    return rho_top, rho_bot


if __name__ == '__main__':
    import sys
    from pathlib import Path

    # FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
    # sys.path.append(FREECADPATH)
    # import FreeCAD
    # if FreeCAD.GuiUp:
    #     document = FreeCAD.ActiveDocument
    # else:
    #     filename = Path(__file__).absolute().parent.parent / 'etabs_api' / 'test' / 'etabs_api' / 'test_files' / 'freecad' / 'mat.FCStd'
    #     document= FreeCAD.openDocument(str(filename))
    # slabs = document.Foundation.tape_slabs
    # openings = document.Foundation.openings

    etabs_api_path = Path(__file__).parent
    sys.path.insert(0, str(etabs_api_path))
    from etabs_obj import EtabsModel
    # etabs = EtabsModel(backup=False, software='SAFE')
    etabs = EtabsModel(backup=False)
    etabs.area.calculate_deck_weight_per_area()
    # SapModel = etabs.SapModel
    # ret = etabs.area.export_freecad_slabs(document)
    # ret = etabs.area.export_freecad_openings(openings)
    # print('Wow')