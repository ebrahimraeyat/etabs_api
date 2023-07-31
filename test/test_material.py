import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version


@pytest.mark.getmethod
def test_get_material_of_type():
    rebars = etabs.material.get_material_of_type(6)
    assert len(rebars) == 3

@pytest.mark.getmethod
def test_get_S340_S400_rebars():
    s340, s400 = etabs.material.get_S340_S400_rebars()
    assert len(s340) == 1
    assert len(s400) == 1

# @pytest.mark.getmethod
# def test_get_standard_rebar_size():
#     etabs.set_current_unit('N', 'mm')
#     rebars = etabs.material.get_standard_rebar_size()
#     assert len(rebars) == 10

@pytest.mark.getmethod
def test_get_tie_main_rebar_all_sizes():
    ties, mains, _all = etabs.material.get_tie_main_rebar_all_sizes()
    assert len(ties) == 2
    assert len(mains) == 7
    assert len(_all) == 9

@pytest.mark.getmethod
def test_get_fc():
    fc = etabs.material.get_fc('CONC')
    assert fc == 25

@pytest.mark.getmethod
def test_get_unit_weight_of_materials():
    ret = etabs.material.get_unit_weight_of_materials()
    assert ret['CONC'] == 2400


if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
    test_get_rebar_sizes(etabs)
