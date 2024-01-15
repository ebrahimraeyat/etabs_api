import sys
from collections import Iterable
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_create_concrete_beam():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    beam_name = 'B20X20'
    etabs.prop_frame.create_concrete_beam(beam_name, 'CONC', 200, 200, 'RMAT', 'RMAT-1', 400)
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Beam')
    assert beam_name in names.unique()
    etabs.SapModel.PropFrame.Delete(beam_name)
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Beam')
    assert beam_name not in names.unique()

def test_create_concrete_column():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    col_name = 'C50X80'
    etabs.prop_frame.create_concrete_column(col_name, 'CONC', 800, 500, 'RMAT', 'RMAT-1', 75, 3, 6, '20d', '10d')
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Column')
    assert col_name in names.unique()
    etabs.SapModel.PropFrame.Delete(col_name)
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Column')
    assert col_name not in names.unique()

def test_get_concrete_rectangular_of_type():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    ret = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Column')
    assert len(ret) == 112
    assert isinstance(ret, Iterable)

def test_convert_columns_design_types():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.prop_frame.convert_columns_design_types()
    ret = etabs.SapModel.PropFrame.GetRebarColumn("C5016F20")
    assert ret[-2]
    etabs.prop_frame.convert_columns_design_types(design=False)
    etabs.prop_frame.convert_columns_design_types(columns=['107'])
    ret = etabs.SapModel.PropFrame.GetRebarColumn("C5016F20")
    assert ret[-2]
    ret = etabs.SapModel.PropFrame.GetRebarColumn("C4512F18")
    assert not ret[-2]


if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
