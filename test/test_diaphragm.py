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
