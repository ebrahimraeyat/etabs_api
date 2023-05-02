import pytest
from pathlib import Path
import tempfile

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
                return create_test_file(etabs)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 19\ETABS.exe'
            )
        return create_test_file(etabs)

@pytest.fixture
def shayesteh_safe(edb="shayesteh.FDB"):
    try:
        safe = etabs_obj.EtabsModel(backup=False, software='SAFE')
        if safe.success:
            filepath = Path(safe.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return safe
            else:
                return create_test_file(safe, suffix='FDB')
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        safe = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\SAFE 20\SAFE.exe'
            )
        return create_test_file(safe, suffix='FDB')


@pytest.fixture
def two_earthquakes(edb="two_earthquakes.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                return create_test_file(etabs)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 19\ETABS.exe'
            )
        return create_test_file(etabs)

@pytest.fixture
def khiabani(edb="khiabani.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                return create_test_file(etabs)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 19\ETABS.exe'
            )
        return create_test_file(etabs)

@pytest.fixture
def steel(edb="steel.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                return create_test_file(etabs)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=r'G:\program files\Computers and Structures\ETABS 19\ETABS.exe'
            )
        return create_test_file(etabs)
        

def create_test_file(etabs, suffix='EDB'):
    temp_path = Path(tempfile.gettempdir())
    test_file_path = temp_path / f"test.{suffix}"
    etabs.SapModel.File.Save(str(test_file_path))
    return etabs
