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

def test_set_area_diaphragms():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.diaphragm.add_diaphragm('D2')
    etabs.diaphragm.set_area_diaphragms('D2')
    table_key = 'Area Assignments - Diaphragms'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert set(df.Diaphragm.unique()) == {'D2'}

def test_add_diaphragm():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.diaphragm.add_diaphragm('D2')
    assert 'D2' in etabs.diaphragm.names()
    

if __name__ == "__main__":
    test_is_diaphragm_assigned()
