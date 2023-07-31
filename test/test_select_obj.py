import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_get_selected_objects():
    etabs.SapModel.FrameObj.SetSelected('122', True)
    etabs.SapModel.PointObj.SetSelected('146', True)
    etabs.SapModel.PointObj.SetSelected('147', True)
    ret = etabs.select_obj.get_selected_objects()
    assert set(ret.keys()) == {1, 2}
    assert ret.values() == (['122'], ['146', '147'])

def test_select_concrete_columns():
    etabs.select_obj.select_concrete_columns()
    _, columns = etabs.frame_obj.get_beams_columns(type_=2)
    sel_frames = etabs.select_obj.get_selected_obj_type(2)
    for col in sel_frames:
        assert col in columns
