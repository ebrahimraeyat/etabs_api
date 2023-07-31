import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

@pytest.mark.getmethod
def test_names():
    names = etabs.group.names()
    assert len(names) == 1
    assert names == ('All',)

@pytest.mark.setmethod
def test_add():
    ret = etabs.group.add('sec')
    assert ret
    names = etabs.group.names()
    assert 'sec' in names
    ret = etabs.group.add('sec')
    assert not ret
