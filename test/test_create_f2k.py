import pytest
import shutil
import tempfile
from pathlib import Path
import sys

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file

import create_f2k


@open_etabs_file("shayesteh.EDB")
def test_add_point_coordinates():
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    writer = create_f2k.CreateF2kFile(
        input_f2k=temp_f2k,
        etabs=etabs,
        load_cases=[],
        case_types=[],
        model_datum=0,
        append=False,
        )
    etabs.run_analysis()
    writer.add_point_coordinates()
    writer.write()
    points = writer.get_points_coordinates()
    assert len(points) == 11

@open_etabs_file("shayesteh.EDB")
def test_add_load_patterns():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    content = safe.add_load_patterns()
    safe.write()
    assert  'LoadPat=DEAD' in content

@open_etabs_file("shayesteh.EDB")
def test_add_loadcase_general():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    content = safe.add_loadcase_general()
    safe.write()
    assert  'LoadCase=DEAD' in content

@open_etabs_file("shayesteh.EDB")
def test_add_modal_loadcase_definitions():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    content = safe.add_modal_loadcase_definitions()
    safe.write()
    assert  'LoadCase=Modal' in content

@open_etabs_file("shayesteh.EDB")
def test_add_loadcase_definitions():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    content = safe.add_loadcase_definitions()
    safe.write()
    assert  'LoadCase=DEAD' in content

@open_etabs_file("shayesteh.EDB")
def test_add_point_loads():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    content = safe.add_point_loads()
    safe.write()
    # assert  'LoadCase=DEAD' in content

@open_etabs_file("shayesteh.EDB")
def test_add_point_loads_modify_f2k():
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    safe = create_f2k.ModifyF2kFile(
        input_f2k=temp_f2k,
        etabs=etabs,
        load_cases=[],
        case_types=[],
        model_datum=0,
        )
    original_point_content = safe.get_points_contents()
    safe.add_point_loads()
    safe.write()
    assert temp_f2k.exists()
    point_contents = safe.get_points_contents()
    point_coordinates = safe.get_points_coordinates(content=point_contents)
    points=[115, 117 ,119 ,121 ,123 ,125 ,127 ,129 ,131 ,133 ,135]
    for p, coords in point_coordinates.items():
        assert int(p) in points
        assert safe.is_point_exist(coords, original_point_content)

@open_etabs_file("shayesteh.EDB")
def test_create_f2k():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    safe.create_f2k()

@open_etabs_file("shayesteh.EDB")
def test_add_grids():
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        etabs,
        )
    safe.add_grids()
    safe.write()

@open_etabs_file("shayesteh.EDB")
def test_add_load_combinations():
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    writer = create_f2k.CreateF2kFile(
        input_f2k=temp_f2k,
        etabs=etabs,
        load_cases=[],
        case_types=[],
        model_datum=0,
        append=False,
        )
    writer.add_load_combinations(ignore_dynamics=True)
    writer.write()
    with open(temp_f2k, 'r') as f:
        for line in f.readlines():
            for case in ('SX', 'SY', 'SPX', 'SPY'):
                if case in line:
                    assert False
    assert True

@open_etabs_file("shayesteh.EDB")
def test_add_load_combinations_envelope():
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    writer = create_f2k.CreateF2kFile(
        input_f2k=temp_f2k,
        etabs=etabs,
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
    # from pathlib import Path
    import etabs_obj
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    test_add_point_loads(etabs)