import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_get_selected_objects(shayesteh):
    shayesteh.SapModel.FrameObj.SetSelected('122', True)
    shayesteh.SapModel.PointObj.SetSelected('146', True)
    shayesteh.SapModel.PointObj.SetSelected('147', True)
    ret = shayesteh.select_obj.get_selected_objects()
    assert set(ret.keys()) == {1, 2}
    assert ret.values() == (['122'], ['146', '147'])