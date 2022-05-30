import pytest
from pathlib import Path
# import sys
import tempfile


# etabs_api_path = Path(__file__).parent.parent
# sys.path.insert(0, str(etabs_api_path))

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
