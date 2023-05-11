import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

def test_get_selected_objects(shayesteh):
    shayesteh.SapModel.FrameObj.SetSelected('122', True)
    shayesteh.SapModel.PointObj.SetSelected('146', True)
    shayesteh.SapModel.PointObj.SetSelected('147', True)
    ret = shayesteh.select_obj.get_selected_objects()
    assert set(ret.keys()) == {1, 2}
    assert ret.values() == (['122'], ['146', '147'])

def test_select_concrete_columns(shayesteh):
    shayesteh.select_obj.select_concrete_columns()
    _, columns = shayesteh.frame_obj.get_beams_columns(type_=2)
    sel_frames = shayesteh.select_obj.get_selected_obj_type(2)
    for col in sel_frames:
        assert col in columns
