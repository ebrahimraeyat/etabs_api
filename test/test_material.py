import sys
from pathlib import Path
import pytest
import math

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file


@open_etabs_file('shayesteh.EDB')
def test_get_material_of_type():
    rebars = etabs.material.get_material_of_type(6)
    assert len(rebars) == 3

@open_etabs_file('shayesteh.EDB')
def test_get_all_rebars():
    rebars = etabs.material.get_all_rebars()
    assert len(rebars) == 32

@open_etabs_file('shayesteh.EDB')
def test_get_S340_S400_rebars():
    s340, s400 = etabs.material.get_S340_S400_rebars()
    assert set(s340) == {'RMAT-1'}
    assert set(s400) == {'A615Gr60', 'RMAT'}

@open_etabs_file('shayesteh.EDB')
def test_get_tie_main_rebar_all_sizes():
    ties, mains, _all = etabs.material.get_tie_main_rebar_all_sizes()
    assert len(ties) == 2
    assert len(mains) == 7
    assert len(_all) == 9

@open_etabs_file('shayesteh.EDB')
def test_get_fc():
    fc = etabs.material.get_fc('CONC')
    assert fc == 25

@open_etabs_file('shayesteh.EDB')
def test_get_unit_weight_of_materials():
    etabs.set_current_unit('kgf', 'm')
    ret = etabs.material.get_unit_weight_of_materials()
    assert ret['CONC'] == 2400

@open_etabs_file('shayesteh.EDB')
def test_add_AIII_rebar():
    etabs.set_current_unit('kgf', 'm')
    rebar_aiii = 'rebar_aiii'
    ret = etabs.material.add_AIII_rebar(name=rebar_aiii)
    rebars = etabs.material.get_material_of_type(6)
    assert rebar_aiii in rebars
    etabs.set_current_unit('N', 'mm')
    fy, _ = etabs.material.get_rebar_fy_fu(rebar_aiii)
    assert fy == 400

@open_etabs_file('shayesteh.EDB')
def test_add_AII_rebar():
    etabs.set_current_unit('kgf', 'm')
    rebar_aii = 'rebar_aii'
    etabs.material.add_AII_rebar(name=rebar_aii)
    rebars = etabs.material.get_material_of_type(6)
    assert rebar_aii in rebars
    etabs.set_current_unit('N', 'mm')
    fy, _ = etabs.material.get_rebar_fy_fu(rebar_aii)
    assert fy == 300

@open_etabs_file('shayesteh.EDB')
def test_add_concrete():
    name = 'concrete'
    fc = 40
    etabs.set_current_unit('kgf', 'm')
    etabs.material.add_concrete(name=name, fc=fc)
    concretes = etabs.material.get_material_of_type(2)
    assert name in concretes
    etabs.set_current_unit('N', 'mm')
    fcc = etabs.material.get_fc(name)
    assert math.isclose(fcc, fc)

@open_etabs_file('shayesteh.EDB')
def test_add_rebar():
    name = 'rebarIII'
    fy = 400
    fu = 600
    etabs.set_current_unit('kgf', 'm')
    etabs.material.add_rebar(name=name, fy=fy, fu=fu)
    rebars = etabs.material.get_material_of_type(6)
    assert name in rebars
    etabs.set_current_unit('N', 'mm')
    fya, fua = etabs.material.get_rebar_fy_fu(name)
    assert math.isclose(fya, fy)
    assert math.isclose(fua, fu)

@open_etabs_file('shayesteh.EDB')
def test_add_steel():
    name = 'STEEL_AIII'
    fy = 240
    fu = 360
    etabs.set_current_unit('kgf', 'm')
    etabs.material.add_steel(name=name, fy=fy, fu=fu)
    steels = etabs.material.get_material_of_type(1)
    assert name in steels
    etabs.set_current_unit('N', 'mm')
    fya, fua = etabs.material.get_steel_fy_fu(name)
    assert math.isclose(fya, fy)
    assert math.isclose(fua, fu)



if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
    test_get_rebar_sizes(etabs)
