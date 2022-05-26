import pytest
import comtypes.client
from pathlib import Path
import sys
import shutil
import tempfile


etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

import etabs_obj
import create_f2k


@pytest.fixture
def shayesteh(edb="shayesteh.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                raise NameError
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 19\ETABS.exe'
            )
        temp_path = Path(tempfile.gettempdir())
        test_file_path = temp_path / "test.EDB"
        etabs.SapModel.File.Save(str(test_file_path))
        return etabs

@pytest.mark.setmethod
def test_add_load_combinations_envelope(shayesteh):
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    writer = create_f2k.CreateF2kFile(
        input_f2k=temp_f2k,
        etabs=shayesteh,
        load_cases=[],
        case_types=[],
        model_datum=0,
        append=True,
        )
    types = ['Envelope']
    writer.add_load_combinations(types=tuple(types))
    writer.write()
    with open(temp_f2k, 'r') as f:
        for line in f.readlines():
            if 'PUSH' in line:
                assert True
                return
    assert False

if __name__ == '__main__':
    from pathlib import Path
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    test_add_load_combinations_envelope(etabs)