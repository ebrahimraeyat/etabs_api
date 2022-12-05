import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_names(shayesteh):
    names = shayesteh.group.names()
    assert len(names) == 1
    assert names == ('All',)

@pytest.mark.setmethod
def test_add(shayesteh):
    ret = shayesteh.group.add('sec')
    assert ret
    names = shayesteh.group.names()
    assert 'sec' in names
    ret = shayesteh.group.add('sec')
    assert not ret
