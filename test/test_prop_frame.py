import sys
from collections import Iterable
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

@open_etabs_file('shayesteh.EDB')
def test_create_concrete_beam():
    beam_name = 'B20X20'
    etabs.prop_frame.create_concrete_beam(beam_name, 'CONC', 200, 200, 'RMAT', 'RMAT-1', 400)
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Beam')
    assert beam_name in names.unique()
    etabs.SapModel.PropFrame.Delete(beam_name)
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Beam')
    assert beam_name not in names.unique()

@open_etabs_file('shayesteh.EDB')
def test_create_concrete_column():
    col_name = 'C50X80'
    etabs.prop_frame.create_concrete_column(col_name, 'CONC', 800, 500, 'RMAT', 'RMAT-1', 75, 3, 6, '20d', '10d')
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Column')
    assert col_name in names.unique()
    etabs.SapModel.PropFrame.Delete(col_name)
    names = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Column')
    assert col_name not in names.unique()

@open_etabs_file('shayesteh.EDB')
def test_get_concrete_rectangular_of_type():
    ret = etabs.prop_frame.get_concrete_rectangular_of_type(type_='Column')
    assert len(ret) == 112
    assert isinstance(ret, Iterable)

@open_etabs_file('shayesteh.EDB')
def test_convert_columns_design_types():
    etabs.prop_frame.convert_columns_design_types()
    ret = etabs.SapModel.PropFrame.GetRebarColumn("C5016F20")
    assert ret[-2]
    etabs.prop_frame.convert_columns_design_types(design=False)
    etabs.prop_frame.convert_columns_design_types(columns=['107'])
    ret = etabs.SapModel.PropFrame.GetRebarColumn("C5016F20")
    assert ret[-2]
    ret = etabs.SapModel.PropFrame.GetRebarColumn("C4512F18")
    assert not ret[-2]

@open_etabs_file('rashidzadeh.EDB')
def test_change_beams_columns_section_fc():
    names = {135, 396, 160, 159, 397, 153, 150, 129}
    ret, _, section_that_corner_bars_is_different = etabs.prop_frame.change_beams_columns_section_fc(names, concrete='C35', concrete_suffix='_C35')
    assert ret
    assert len(section_that_corner_bars_is_different) == 3
    # ret = etabs.SapModel.PropFrame.GetRebarColumn("C5016F20")
    # assert ret[-2]
    # etabs.prop_frame.convert_columns_design_types(design=False)
    # etabs.prop_frame.convert_columns_design_types(columns=['107'])
    # ret = etabs.SapModel.PropFrame.GetRebarColumn("C5016F20")
    # assert ret[-2]
    # ret = etabs.SapModel.PropFrame.GetRebarColumn("C4512F18")
    # assert not ret[-2]


if __name__ == '__main__':
    test_change_columns_section_fc_fy_cover_design()
