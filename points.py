from typing import Iterable, Union

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
        import math
        d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return d

    def get_points_coords(self, points : Iterable):
        points_xyz = {}
        for p in points:
            x, y, z, _ = self.SapModel.PointObj.GetCoordCartesian(p)
            points_xyz[p] = (x, y, z)
        return points_xyz



