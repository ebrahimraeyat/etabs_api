from pathlib import Path
import tempfile

import etabs_obj

global etabs
global open_model
version = 20

def etabs_model(
        edb: str="shayesteh.EDB",
        version: int=0, # 19, 20
        ):
    '''
    version 0 means that we can connect to register and openning etabs, it is not
    matter what version it is
    '''
    if version == 21:
        return None, None
    suffix = edb.split('.')[1]
    if suffix == 'EDB':
        software = 'ETABS'
    elif suffix == 'FDB':
        software = 'SAFE'
    new_instance = False
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            if version != 0 and etabs.etabs_main_version != version:
                raise FileNotFoundError
            filename = etabs.SapModel.GetModelFilename()
            if not filename:
                open_model(etabs, edb)
                filename = etabs.SapModel.GetModelFilename()
            filepath = Path(filename)
            if 'test.' in filepath.name:
                return etabs, new_instance
            else:
                return create_test_file(etabs, suffix=suffix), new_instance
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        etabs = etabs_obj.EtabsModel(
                attach_to_instance=False,
                backup = False,
                model_path = Path(__file__).parent / 'files' / edb,
                software_exe_path=rf'G:\program files\Computers and Structures\{software} {version}\{software}.exe'
            )
        new_instance = True
        return create_test_file(etabs, suffix=suffix), new_instance

# def shayesteh_safe(edb="shayesteh.FDB"):
# def two_earthquakes(edb="etabs.EDB"):
# def khiabani(edb="khiabani.EDB"):
# def steel(edb="steel.EDB"):
def open_model(
        etabs,
        filename: str, # "madadi.EDB"
        ):
    model_path = Path(__file__).parent / 'files' / filename
    etabs.SapModel.File.OpenFile(str(model_path))
    suffix = filename.split('.')[1]
    create_test_file(etabs, suffix)
    
def create_test_file(etabs, suffix='EDB', filename='test'):
    temp_path = Path(tempfile.gettempdir())
    version = etabs.etabs_main_version
    test_file_path = temp_path / f"{filename}{version}.{suffix}"
    etabs.SapModel.File.Save(str(test_file_path))
    return etabs

def get_temp_filepath(suffix='EDB', filename='test') -> Path:
    temp_path = Path(tempfile.gettempdir())
    temp_file_path = temp_path / f"{filename}.{suffix}"
    return temp_file_path

def get_all_open_software(
        software: str='ETABS',
        ):
    import psutil
    import comtypes
    softwares = []
    helper = comtypes.client.CreateObject('ETABSv1.Helper')
    helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
    if hasattr(helper, 'GetObjectProcess'):
        for proc in psutil.process_iter():
            if software in proc.name().lower():
                pid = proc.pid
                etabs = helper.GetObjectProcess(f"CSI.{software}.API.ETABSObject", pid)
                softwares.append(etabs)
    return softwares
                        


etabs, new_instance = etabs_model(version=version)
# register_version = etabs.etabs_main_version

# if register_version == 19:
#     etabs19 = etabs
#     etabs20, new_instance = etabs_model(version=20)
#     etabs21, new_instance = etabs_model(version=21)
# elif register_version == 20:
#     etabs19, new_instance = etabs_model(version=19)
#     etabs20 = etabs
#     etabs21, new_instance = etabs_model(version=21)
# elif register_version == 21:
#     etabs19, new_instance = etabs_model(version=19)
#     etabs20, new_instance = etabs_model(version=20)
#     etabs21 = etabs