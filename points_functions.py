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

def transfer_loads_between_two_models(
        model1,
        model2,
        level1: float,
        level2: float,
        map_loadcases: dict,
        replace: bool=False,
        multiply: float=1,
        ):
    similar_points = get_similar_points_in_two_models(model1, model2, level1, level2)
    not_applied_forces = []
    model1.run_analysis()
    model1.SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
    for lc in map_loadcases.keys():
        model1.SapModel.Results.Setup.SetCaseSelectedForOutput(lc)
    model2.unlock_model()
    for p1, p2 in similar_points.items():
        ret = model1.SapModel.Results.JointReact(p1, 0)
        for i in range(ret[0]):
            lc1 = ret[3][i]
            fx = multiply * -ret[6][i]
            fy = multiply * -ret[7][i]
            fz = multiply * -ret[8][i]
            mx = multiply * -ret[9][i]
            my = multiply * -ret[10][i]
            mz = multiply * -ret[11][i]
            lc2 = map_loadcases.get(lc1, None)
            if lc2 is not None:
                point_load_value = [fx, fy, fz, mx, my, mz]
                model2.SapModel.PointObj.SetLoadForce(p2, lc2, point_load_value, replace)
            else:
                not_applied_forces.append((p1, lc1))
    return not_applied_forces
