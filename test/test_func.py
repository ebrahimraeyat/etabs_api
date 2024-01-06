import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.func.names()
    assert len(names) == 2
    assert set(names) == {'FUNC1', 'RampTH'}

def test_response_spectrum_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.func.response_spectrum_names()
    assert len(names) == 1
    assert set(names) == {'FUNC1'}

def test_time_history_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.func.time_history_names()
    assert len(names) == 1
    assert set(names) == {'RampTH'}


if __name__ == "__main__":
    test_names()
