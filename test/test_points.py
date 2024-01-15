import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

@pytest.mark.getmethod
def test_get_points_coords():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.set_current_unit('N', 'mm')
    points_coords = etabs.points.get_points_coords(['146', '147', '148'])
    assert list(points_coords.keys()) == ['146', '147', '148']
    assert pytest.approx(points_coords['146'], abs=1) == (12751.4, 3365.6, 5220)

def test_add_point():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.set_current_unit('N', 'm')
    x1, y1, z1 = 1.01, 12, 20
    name = etabs.points.add_point(x1, y1, z1)
    coords = etabs.points.get_points_coords([name])
    assert pytest.approx(coords[name], abs=1) == (x1, y1, z1)

def test_add_point_on_beam():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.set_current_unit('N', 'cm')
    name = etabs.points.add_point_on_beam('115')
    coords = etabs.points.get_points_coords([name])
    assert pytest.approx(coords[name], abs=1) == (1086.5, 0, 522)
    # get distance
    distance = etabs.frame_obj.get_length_of_frame(name) / 2
    etabs.points.add_point_on_beam('115', distance=distance)
    assert pytest.approx(coords[name], abs=1) == (1086.5, 0, 522)

def test_get_points_coordinates():
    import pandas as pd
    open_model(etabs=etabs, filename='khiabany.EDB')
    df = etabs.points.get_points_coordinates()
    assert isinstance(df, pd.DataFrame)
    assert df.dtypes.UniqueName == 'int32'
    for i in ('X', 'Y', 'Z'):
        assert df.dtypes[i] == 'float64'
    assert len(df) == 181
    df = etabs.points.get_points_coordinates(to_dict=True)
    assert isinstance(df, dict)
    for key, (x, y, z) in df.items():
        assert isinstance(key, int)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)
    assert len(df) == 181
    df = etabs.points.get_points_coordinates(points=['1', '2', '3'])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3

def test_get_objects_and_elements_joints_coordinate():
    open_model(etabs=etabs, filename="khiabany.EDB")
    ret = etabs.points.get_objects_and_elements_joints_coordinate(types=['Shell'])
    print(ret)
    if version < 20:
        assert set(ret['~199']) == set([5750, -1700, 15840])
    else:
        assert set(ret['~208']) == set([5750, -1700, 15840])
    # multi shells
    ret = etabs.points.get_objects_and_elements_joints_coordinate(types=['Shell'])
    if version < 20:
        assert set(ret['~199']) == set([5750, -1700, 15840])
    else:
        assert set(ret['~208']) == set([5750, -1700, 15840])

def test_get_maximum_point_number_in_model():
    open_model(etabs=etabs, filename="khiabany.EDB")
    n = etabs.points.get_maximum_point_number_in_model()
    assert n == 201