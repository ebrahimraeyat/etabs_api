import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_get_selected_objects():
    etabs.SapModel.FrameObj.SetSelected('122', True)
    etabs.SapModel.PointObj.SetSelected('146', True)
    etabs.SapModel.PointObj.SetSelected('147', True)
    ret = etabs.select_obj.get_selected_objects()
    assert set(ret.keys()) == {1, 2}
    assert set(ret[2]) == {'122'}
    assert set(ret[1]) ==  {'146', '147'}

@open_etabs_file('shayesteh.EDB')
def test_select_concrete_columns():
    etabs.select_obj.select_concrete_columns()
    _, columns = etabs.frame_obj.get_beams_columns(type_=2)
    sel_frames = etabs.select_obj.get_selected_obj_type(2)
    for col in sel_frames:
        assert col in columns

@open_etabs_file('steel.EDB')
def test_get_selected_beams_and_columns():
    etabs.SapModel.FrameObj.SetSelected('94', True)
    etabs.SapModel.FrameObj.SetSelected('95', True)
    etabs.SapModel.FrameObj.SetSelected('96', True)
    beams, columns = etabs.select_obj.get_selected_beams_and_columns(type_=1)
    assert set(beams) == {'94', '95', '96'}
    assert len(columns) == 0