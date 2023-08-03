from typing import Iterable, Union
import math

class Points:
    def __init__(
                self,
                SapModel=None,
                etabs=None,
                ):
        if not SapModel:
            self.etabs = etabs
            self.SapModel = etabs.SapModel
        else:
            self.SapModel = SapModel

    def set_point_restraint(self,
            point_names,
            restraint: list= [True, True, False, False, False, False]):
        for point_name in point_names:
            self.SapModel.PointObj.SetRestraint(point_name, restraint)

    def get_distance_between_two_points_in_XY(self,
            p1 : Union[str, tuple],
            p2 : Union[str, tuple],
            ) -> float:
        if isinstance(p1, tuple):
            x1, y1 = p1
        else:
            x1, y1 = self.SapModel.PointObj.GetCoordCartesian(p1)[:2]
        if isinstance(p2, tuple):
            x2, y2 = p2
        else:
            x2, y2 = self.SapModel.PointObj.GetCoordCartesian(p2)[:2]
        d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return d

    def get_points_coords(self, points : Iterable):
        points_xyz = {}
        for p in points:
            x, y, z, _ = self.SapModel.PointObj.GetCoordCartesian(p)
            points_xyz[p] = (x, y, z)
        return points_xyz
    
    def add_point(self,
        x: float,
        y: float,
        z: float,
        unlock_model: bool=True,
        ):
        if unlock_model:
            self.etabs.unlock_model()
        name = self.SapModel.PointObj.AddCartesian(float(x), float(y), float(z))[0]
        return name
    
    def add_point_on_beam(self,
        name: str,
        distance: Union[str, float]='middle', #start, end 
        unlock_model: bool=True,
        ):
        p1_name, p2_name, _ = self.SapModel.FrameObj.GetPoints(name)
        x1, y1, z1 = self.SapModel.PointObj.GetCoordCartesian(p1_name)[:3]
        x2, y2, z2 = self.SapModel.PointObj.GetCoordCartesian(p2_name)[:3]
        length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
        if type(distance) == str:
            if distance == 'middle':
                distance = length / 2
        rel = distance / length
        x = (x2 - x1) * rel + x1
        y = (y2 - y1) * rel + y1
        z = (z2 - z1) * rel + z1
        return self.add_point(x, y, z, unlock_model=unlock_model)
    
    def get_points_coordinates(self,
        points: list=[],
        to_dict: bool=False,
    ):
        '''
        return a dataframe with point_name and x, y, z coordinate,
        or a dictionary like {'10': (0, 0, 0), ...}
        '''
        table_key = 'Point Object Connectivity'
        cols = ['UniqueName', 'X', 'Y', 'Z']
        df = self.etabs.database.read(table_key, to_dataframe=True, cols=cols)
        if points:
            filt = df['UniqueName'].isin(points)
            df = df.loc[filt]
        df = df.astype({'UniqueName': int, 'X': float, 'Y': float, 'Z': float})
        if to_dict:
            return df.set_index("UniqueName").apply(tuple, axis=1).to_dict()
        else:
            return df
        
    def get_objects_and_elements_joints_coordinate(self,
            types: list=[], # [Joint, Shell]
            unit: str = 'mm',
            to_dict: bool=True,
            map_dict: dict={},
            joints: Iterable=[],
            ) -> dict:
        '''
        map_dict: A dictionary for mapping mesh points name to int point name
        Return all joints coordinates in FEM, include mesh joints
        '''
        force, length = self.etabs.get_current_unit()
        self.etabs.set_current_unit(force, unit)
        self.etabs.run_analysis()
        table_key = 'Objects and Elements - Joints'
        cols = ['ObjType', 'ElmName', 'GlobalX', 'GlobalY', 'GlobalZ']
        df = self.etabs.database.read(table_key=table_key, to_dataframe=True, cols=cols)
        if joints:
            df = df[df['ElmName'].isin(joints)]
        if types:
            df = df[df['ObjType'].isin(types)]
        del df['ObjType']
        df = df.astype({'GlobalX': float, 'GlobalY': float, 'GlobalZ': float, })
        self.etabs.set_current_unit(force, length)
        if map_dict:
            col = 'ElmName'
            df[col] = df[col].map(map_dict).fillna(df[col])
            df[col] = df[col].astype(int)
        if to_dict:
            return df.set_index("ElmName").apply(tuple, axis=1).to_dict()
        else:
            return df
        
    def get_maximum_point_number_in_model(self):
        df = self.get_points_coordinates()
        max_number = df.UniqueName.max()
        return max_number
    
    