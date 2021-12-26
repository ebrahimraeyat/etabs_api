from typing import Union


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

    def export_freecad_strips(self, doc : 'App.Document' = None):
        self.etabs.set_current_unit('kN', 'mm')
        if doc is None:
            doc = FreeCAD.ActiveDocument
        foun = doc.Foundation
        data = []
        if foun.foundation_type == 'Strip':
            slabs = foun.tape_slabs
            i = j = 0
            for slab in slabs:
                p1 = slab.start_point
                p2 = slab.end_point
                p = self.SapModel.PointObj.AddCartesian(p1.x, p1.y, p1.z)
                p1_name = p[0]
                p = self.SapModel.PointObj.AddCartesian(p2.x, p2.y, p2.z)
                p2_name = p[0]
                swl = ewl = slab.width.Value / 2 + slab.offset
                swr = ewr = slab.width.Value / 2 - slab.offset
                dx = abs(p1.x - p2.x)
                dy = abs(p1.y - p2.y)
                if dx > dy:
                    layer = 'A'
                    i += 1
                    name = f'CS{layer}{i}'
                else:
                    layer = 'B'
                    j += 1
                    name = f'CS{layer}{j}'
                data.extend((
                    name,
                    '1',
                    f'{p1_name}',
                    f'{p2_name}',
                    f'{swl}',
                    f'{swr}',
                    f'{ewl}',
                    f'{ewr}',
                    'NO',
                    f'{layer}',
                    ))
        table_key = 'Strip Object Connectivity'
        fields = ['Name', 'NumSegs', 'StartPoint', 'EndPoint', 'WStartLeft',
            'WStartRight', 'WEndLeft', 'WEndRight', 'AutoWiden', 'Layer']
        if self.etabs.software == 'ETABS':
            fields.insert(1, 'Story')
        assert len(fields) == len(data) / len(slabs)
        self.etabs.database.apply_data(table_key, data, fields)

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


if __name__ == '__main__':
    import sys
    from pathlib import Path

    FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
    sys.path.append(FREECADPATH)
    import FreeCAD
    if FreeCAD.GuiUp:
        document = FreeCAD.ActiveDocument
    else:
        filename = Path(__file__).absolute().parent.parent / 'etabs_api' / 'test' / 'etabs_api' / 'test_files' / 'freecad' / 'mat.FCStd'
        document= FreeCAD.openDocument(str(filename))
    slabs = document.Foundation.tape_slabs
    openings = document.Foundation.openings

    current_path = Path(__file__).parent
    sys.path.insert(0, str(current_path))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False, software='SAFE')
    # etabs.area.get_scale_area_points_with_scale(document.Foundation.plan_without_openings)
    SapModel = etabs.SapModel
    ret = etabs.area.export_freecad_slabs(document)
    ret = etabs.area.export_freecad_openings(openings)
    print('Wow')