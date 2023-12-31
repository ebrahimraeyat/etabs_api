import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_names():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    names = etabs.diaphragm.names()
    assert len(names) == 1
    assert set(names) == {'D1'}

def test_is_diaphragm_assigned():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    is_diaphragm_assigned = etabs.diaphragm.is_diaphragm_assigned()
    assert is_diaphragm_assigned

if __name__ == "__main__":
    test_is_diaphragm_assigned()
