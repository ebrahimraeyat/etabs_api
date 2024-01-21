import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_names():
    names = etabs.func.names()
    assert len(names) == 2
    assert set(names) == {'FUNC1', 'RampTH'}

@open_etabs_file('shayesteh.EDB')
def test_response_spectrum_names():
    names = etabs.func.response_spectrum_names()
    assert len(names) == 1
    assert set(names) == {'FUNC1'}

@open_etabs_file('shayesteh.EDB')
def test_time_history_names():
    names = etabs.func.time_history_names()
    assert len(names) == 1
    assert set(names) == {'RampTH'}


if __name__ == "__main__":
    test_names()
