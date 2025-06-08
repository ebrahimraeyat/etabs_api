import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_show_point():
    etabs.view.show_point('STORY4', '23')
    assert etabs.SapModel.PointObj.GetSelected('166')[0]

@open_etabs_file('shayesteh.EDB')
def test_show_frame():
    etabs.view.show_frame('115')
    assert etabs.SapModel.FrameObj.GetSelected('115')[0]

@open_etabs_file('shayesteh.EDB')
def test_show_frames():
    frames = ['115', '114', '104']
    etabs.view.show_frames(frames)
    for frame in frames:
        assert etabs.SapModel.FrameObj.GetSelected(frame)[0]
    assert not etabs.SapModel.FrameObj.GetSelected('130')[0]

@open_etabs_file('two_earthquakes.EDB')
def test_show_areas_and_frames_with_pier_and_story():
    etabs.view.show_areas_and_frames_with_pier_and_story('P1', 'STORY1')
    ret = etabs.select_obj.get_selected_objects()
    assert set(ret.keys()) == {2, 5}
    assert len(ret[2]) == 9
    assert len(ret[5]) == 212

if __name__ == '__main__':
    test_show_areas_and_frames_with_pier_and_story()
    # pytest.main([__file__, '-v', '--tb=short'])