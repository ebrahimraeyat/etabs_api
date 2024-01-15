import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_names():
    names = etabs.group.names()
    assert len(names) == 1
    assert names[0] == 'ALL'

def test_add():
    etabs.group.add('sec')
    names = etabs.group.names()
    assert 'sec' in names
