import pytest
import comtypes.client
from pathlib import Path
import sys

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
import FreeCAD

filename = Path(__file__).absolute().parent.parent / 'etabs_api' / 'test_files' / 'freecad' / 'strip.FCStd'
filename_mat = Path(__file__).absolute().parent.parent / 'etabs_api' / 'test_files' / 'freecad' / 'mat.FCStd'
document= FreeCAD.openDocument(str(filename))

civil_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(civil_path))
from etabs_api import etabs_obj

@pytest.fixture
def shayesteh_safe(edb="shayesteh.FDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False, software='SAFE')
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                raise NameError
    except:
        helper = comtypes.client.CreateObject('SAFEv1.Helper') 
        helper = helper.QueryInterface('comtypes.gen.SAFEv1.cHelper')
        ETABSObject = helper.CreateObjectProgID("CSI.SAFE.API.ETABSObject")
        ETABSObject.ApplicationStart()
        SapModel = ETABSObject.SapModel
        SapModel.InitializeNewModel()
        SapModel.File.OpenFile(str(Path(__file__).parent / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.FDB"
        SapModel.File.Save(str(test_file_path))
        etabs = etabs_obj.EtabsModel(backup=False)
        return etabs

def test_export_freecad_slabs(shayesteh_safe):
    slabs = shayesteh_safe.area.export_freecad_slabs(document)
    assert shayesteh_safe.SapModel.AreaObj.GetNameList()[0] == 7
    shayesteh_safe.SapModel.View.RefreshView()

def test_export_freecad_slabs_mat(shayesteh_safe):
    document_mat= FreeCAD.openDocument(str(filename_mat))
    slabs = shayesteh_safe.area.export_freecad_slabs(
        document_mat,
        )
    shayesteh_safe.SapModel.View.RefreshView()
    assert shayesteh_safe.SapModel.AreaObj.GetNameList()[0] == len(slabs)

def test_export_freecad_strips(shayesteh_safe):
    shayesteh_safe.area.export_freecad_strips(document)
    shayesteh_safe.SapModel.View.RefreshView()

def test_export_freecad_stiff_elements(shayesteh_safe):
    shayesteh_safe.area.export_freecad_stiff_elements(document)

def test_set_uniform_gravity_load(shayesteh_safe):
    shayesteh_safe.area.set_uniform_gravity_load(
        ['1'], 'DEAD', 350
    )
    ret = shayesteh_safe.SapModel.AreaObj.GetLoadUniform('1')
    assert ret[2][0] == 'DEAD'
    assert ret[4][0] == 6
    assert ret[5][0] == -350

def test_export_freecad_wall_loads(shayesteh_safe):
    shayesteh_safe.area.export_freecad_wall_loads(document)
    

if __name__ == '__main__':
    test_export_freecad_stiff_elements(shayesteh_safe)