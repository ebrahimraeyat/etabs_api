import sys
from pathlib import Path

import pytest
import comtypes.client


etabs_api_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(etabs_api_path))

from safe.create_f2k import CreateF2kFile
import etabs_obj

@pytest.fixture
def shayesteh(edb="shayesteh.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                raise FileNotFoundError
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        helper = comtypes.client.CreateObject('ETABSv1.Helper') 
        helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
        ETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
        ETABSObject.ApplicationStart()
        SapModel = ETABSObject.SapModel
        # SapModel.InitializeNewModel()
        SapModel.File.OpenFile(str(Path(__file__).parent.parent / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.EDB"
        SapModel.File.Save(str(test_file_path))
        etabs = etabs_obj.EtabsModel(backup=False)
        return etabs

def test_add_point_coordinates(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_point_coordinates()
    safe.write()
    id_ = safe.is_point_exist([2820, 0, 0], content)
    assert id_ == '115'
    id_ = safe.is_point_exist([2820, 20, 0], content)
    assert not id_

def test_add_load_patterns(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_load_patterns()
    safe.write()
    assert  'LoadPat=DEAD' in content

def test_add_loadcase_general(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_loadcase_general()
    safe.write()
    assert  'LoadCase=DEAD' in content

def test_add_modal_loadcase_definitions(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_modal_loadcase_definitions()
    safe.write()
    assert  'LoadCase=Modal' in content

def test_add_loadcase_definitions(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_loadcase_definitions()
    safe.write()
    assert  'LoadCase=DEAD' in content

def test_add_point_loads(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_point_loads()
    safe.write()
    # assert  'LoadCase=DEAD' in content

def test_add_load_combinations(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_load_combinations()
    safe.write()
    assert  'Combo=COMB1   Load=DEAD Type="Linear Add"  SF=1.2' in content

def test_create_f2k(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    safe.create_f2k()

def test_add_grids(shayesteh):
    safe = CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    safe.add_grids()
    safe.write()

if __name__ == '__main__':
    etabs = etabs_obj.EtabsModel(backup=False)
    test_add_grids(etabs)
