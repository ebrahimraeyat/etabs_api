import sys
from collections import Iterable
from pathlib import Path
import pytest

import numpy as np

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

@open_etabs_file('PowelsRd-Rev26.EDB')
def test_create_steel_tube():
    name = 'Box'
    material = "ST37(Plate)"
    depth = 300
    width = 200
    t = 2.3
    etabs.prop_frame.create_steel_tube(name, material, depth, width, t, t)
    ret = etabs.SapModel.PropFrame.GetTube(name)
    assert ret[1] == material
    assert ret[2] == depth


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

@open_etabs_file('rashidzadeh.EDB')
def test_get_number_of_rebars_and_areas_of_column_section():
    name = "C5516AC"
    etabs.set_current_unit('kgf', 'mm')
    n3, n2, area, corner_area = etabs.prop_frame.get_number_of_rebars_and_areas_of_column_section(name)
    assert n3 == 5
    assert n2 == 5
    area25 = np.pi * 25 ** 2 / 4
    area20 = np.pi * 20 ** 2 / 4
    np.testing.assert_almost_equal(area25, corner_area, decimal=0)
    np.testing.assert_almost_equal(area20, area, decimal=0)
    name = "C5012AC"
    n3, n2, area, corner_area = etabs.prop_frame.get_number_of_rebars_and_areas_of_column_section(name)
    assert n3 == 4
    assert n2 == 4
    np.testing.assert_almost_equal(area25, corner_area, decimal=0)
    np.testing.assert_almost_equal(area20, area, decimal=0)

@open_etabs_file('rashidzadeh.EDB')
def test_compare_two_columns():
    below_col = '233'
    above_col = '161'
    below_sec = "C5012CD"
    new_sections = (below_sec, "C6012C", "C5012C", "C5016C", "C5012AC")
    errors = ('OK', "section_area", 'longitudinal_rebar_size', "longitudinal_rebar_size", 'corner_rebar_size')
    for section, error in zip(new_sections, errors):
        etabs.SapModel.FrameObj.SetSection(above_col, section)
        er = etabs.prop_frame.compare_two_columns(below_col, above_col)
        assert er.name == error

@open_etabs_file('rashidzadeh.EDB')
def test_check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention():
    below_col = '233'
    above_col = '161'
    below_sec = "C40X70"
    above_sec = "C60X30"
    etabs.SapModel.PropFrame.SetRectangle(below_sec, 'C30', 70, 40)
    etabs.SapModel.PropFrame.SetRectangle(above_sec, 'C30', 30, 60)
    etabs.SapModel.FrameObj.SetSection(below_col, below_sec)
    etabs.SapModel.FrameObj.SetSection(above_col, above_sec)
    for angle in range(-1000, 1000, 10):
        etabs.SapModel.FrameObj.SetLocalAxes(above_col, angle)
        etabs.SapModel.FrameObj.SetLocalAxes(below_col, angle + 90)
        rotation_is_ok, need_to_convert_dimention = etabs.prop_frame.check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention(below_col, above_col)
        assert rotation_is_ok
        assert need_to_convert_dimention
        etabs.SapModel.FrameObj.SetLocalAxes(below_col, angle)
        rotation_is_ok, need_to_convert_dimention = etabs.prop_frame.check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention(below_col, above_col)
        assert rotation_is_ok
        assert not need_to_convert_dimention
        etabs.SapModel.FrameObj.SetLocalAxes(below_col, angle + 10)
        rotation_is_ok, need_to_convert_dimention = etabs.prop_frame.check_if_rotation_of_two_columns_is_ok_and_need_to_convert_dimention(below_col, above_col)
        assert not rotation_is_ok
        if (angle + 10) % 90 == 0:
            assert need_to_convert_dimention
        else:
            assert not need_to_convert_dimention

@open_etabs_file('rashidzadeh.EDB')
def test_check_if_dimention_of_above_column_is_greater_than_below_column():
    below_col = '233'
    above_col = '161'
    below_sec = "C40X70"
    above_sec = "C60X30"
    etabs.SapModel.PropFrame.SetRectangle(below_sec, 'C30', 70, 40)
    etabs.SapModel.PropFrame.SetRectangle(above_sec, 'C30', 30, 60)
    etabs.SapModel.FrameObj.SetSection(below_col, below_sec)
    etabs.SapModel.FrameObj.SetSection(above_col, above_sec)
    for angle in range(-1000, 1000, 10):
        etabs.SapModel.FrameObj.SetLocalAxes(above_col, angle)
        etabs.SapModel.FrameObj.SetLocalAxes(below_col, angle + 90)
        ret = etabs.prop_frame.check_if_dimention_of_above_column_is_greater_than_below_column(below_col, above_col)
        assert not ret[0]
        etabs.SapModel.FrameObj.SetLocalAxes(below_col, angle)
        ret = etabs.prop_frame.check_if_dimention_of_above_column_is_greater_than_below_column(below_col, above_col)
        assert ret[0]

@open_etabs_file("rashidzadeh.EDB")
def test_get_material():
    mat = etabs.prop_frame.get_material('404')
    assert mat == "STEEL"
    mat = etabs.prop_frame.get_material('411')
    assert mat == "C30"
    



if __name__ == '__main__':
    test_create_steel_tube()
