import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_names():
    names = etabs.diaphragm.names()
    assert len(names) == 1
    assert set(names) == {'D1'}

@open_etabs_file('shayesteh.EDB')
def test_is_diaphragm_assigned():
    is_diaphragm_assigned = etabs.diaphragm.is_diaphragm_assigned()
    assert is_diaphragm_assigned

@open_etabs_file('shayesteh.EDB')
def test_set_area_diaphragms():
    etabs.diaphragm.add_diaphragm('D2')
    etabs.diaphragm.set_area_diaphragms('D2')
    table_key = 'Area Assignments - Diaphragms'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(df.Diaphragm.unique()) == {'D2'}

@open_etabs_file('shayesteh.EDB')
def test_add_diaphragm():
    etabs.diaphragm.add_diaphragm('D2')
    assert 'D2' in etabs.diaphragm.names()
    

if __name__ == "__main__":
    test_is_diaphragm_assigned()
