import math


def get_similar_points_in_two_models(
        model1,
        model2,
        level1: float,
        level2: float,
        ):
    '''
    Return points with similar (x, y) coordinates in two models
    '''
    model1.set_current_unit("kgf", 'm')
    model2.set_current_unit("kgf", 'm')
    left_points = model1.SapModel.PointObj.GetNameList()[1]
    right_points = model2.SapModel.PointObj.GetNameList()[1]
    used_points = []
    similar_points = {}
    for p1 in left_points:
        p1_x, p1_y, p1_z, _ = model1.SapModel.PointObj.GetCoordCartesian(p1)
        if math.isclose(p1_z, level1, abs_tol=.01):
            for p2 in right_points:
                if p2 not in used_points:
                    p2_x, p2_y, p2_z, _ = model2.SapModel.PointObj.GetCoordCartesian(p2)
                    if math.isclose(p2_z, level2, abs_tol=.01) and math.isclose(p1_x, p2_x, abs_tol=.01) and math.isclose(p1_y, p2_y, abs_tol=.01):
                        similar_points[p1] = p2
                        used_points.append(p2)
                        break
    return similar_points