import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_get_points_coords(shayesteh):
    points_coords = shayesteh.points.get_points_coords(['146', '147', '148'])
    assert list(points_coords.keys()) == ['146', '147', '148']
    assert pytest.approx(points_coords['146'], abs=1) == (12751.4, 3365.6, 5220)