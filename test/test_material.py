import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh


@pytest.mark.getmethod
def test_get_material_of_type(shayesteh):
    rebars = shayesteh.material.get_material_of_type(6)
    assert len(rebars) == 3

@pytest.mark.getmethod
def test_get_S340_S400_rebars(shayesteh):
    s340, s400 = shayesteh.material.get_S340_S400_rebars()
    assert len(s340) == 1
    assert len(s400) == 1

@pytest.mark.getmethod
def test_get_standard_rebar_size(shayesteh):
    shayesteh.set_current_unit('N', 'mm')
    rebars = shayesteh.material.get_standard_rebar_size()
    assert len(rebars) == 11

@pytest.mark.getmethod
def test_get_tie_main_rebars(shayesteh):
    ties, mains = shayesteh.material.get_tie_main_rebars()
    assert len(ties) == 2
    assert len(mains) == 8

@pytest.mark.getmethod
def test_get_fc(shayesteh):
    fc = shayesteh.material.get_fc('CONC')
    assert fc == 25


if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    SapModel = etabs.SapModel
    test_get_rebar_sizes(etabs)
