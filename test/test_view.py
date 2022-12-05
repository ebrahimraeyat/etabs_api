import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_show_point(shayesteh):
    shayesteh.view.show_point('STORY4', '23')
    assert shayesteh.SapModel.PointObj.GetSelected('166')[0]

@pytest.mark.getmethod
def test_show_frame(shayesteh):
    shayesteh.view.show_frame('115')
    assert shayesteh.SapModel.FrameObj.GetSelected('115')[0]