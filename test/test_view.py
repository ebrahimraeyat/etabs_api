import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_show_point():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.view.show_point('STORY4', '23')
    assert etabs.SapModel.PointObj.GetSelected('166')[0]

def test_show_frame():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.view.show_frame('115')
    assert etabs.SapModel.FrameObj.GetSelected('115')[0]

def test_show_frames():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    frames = ['115', '114', '104']
    etabs.view.show_frames(frames)
    for frame in frames:
        assert etabs.SapModel.FrameObj.GetSelected(frame)[0]
    assert not etabs.SapModel.FrameObj.GetSelected('130')[0]