import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

@pytest.mark.getmethod
def test_get_points_coords():
    points_coords = etabs.points.get_points_coords(['146', '147', '148'])
    assert list(points_coords.keys()) == ['146', '147', '148']
    assert pytest.approx(points_coords['146'], abs=1) == (12751.4, 3365.6, 5220)

def test_add_point():
    etabs.set_current_unit('N', 'm')
    x1, y1, z1 = 1.01, 12, 20
    name = etabs.points.add_point(x1, y1, z1)
    coords = etabs.points.get_points_coords([name])
    assert pytest.approx(coords[name], abs=1) == (x1, y1, z1)

def test_add_point_on_beam():
    etabs.set_current_unit('N', 'cm')
    name = etabs.points.add_point_on_beam('115')
    coords = etabs.points.get_points_coords([name])
    assert pytest.approx(coords[name], abs=1) == (1086.5, 0, 522)
    # get distance
    distance = etabs.frame_obj.get_length_of_frame(name) / 2
    etabs.points.add_point_on_beam('115', distance=distance)
    assert pytest.approx(coords[name], abs=1) == (1086.5, 0, 522)