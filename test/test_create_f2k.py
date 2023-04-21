import pytest
import shutil
import tempfile
from pathlib import Path
import sys

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

import create_f2k


@pytest.mark.setmethod
def test_add_point_coordinates(shayesteh):
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    writer = create_f2k.CreateF2kFile(
        input_f2k=temp_f2k,
        etabs=shayesteh,
        load_cases=[],
        case_types=[],
        model_datum=0,
        append=False,
        )
    shayesteh.run_analysis()
    writer.add_point_coordinates()
    writer.write()
    points = writer.get_points_coordinates()
    assert len(points) == 11

def test_add_load_patterns(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_load_patterns()
    safe.write()
    assert  'LoadPat=DEAD' in content

def test_add_loadcase_general(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_loadcase_general()
    safe.write()
    assert  'LoadCase=DEAD' in content

def test_add_modal_loadcase_definitions(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_modal_loadcase_definitions()
    safe.write()
    assert  'LoadCase=Modal' in content

def test_add_loadcase_definitions(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_loadcase_definitions()
    safe.write()
    assert  'LoadCase=DEAD' in content

def test_add_point_loads(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    content = safe.add_point_loads()
    safe.write()
    # assert  'LoadCase=DEAD' in content


def test_create_f2k(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    safe.create_f2k()

def test_add_grids(shayesteh):
    safe = create_f2k.CreateF2kFile(
        Path('~\\test.f2k').expanduser(),
        shayesteh,
        )
    safe.add_grids()
    safe.write()

@pytest.mark.setmethod
def test_add_load_combinations(shayesteh):
    f2k = Path(__file__).parent / 'files' / 'shayesteh.F2K'
    temp_f2k = Path(tempfile.gettempdir()) / f2k.name
    shutil.copy(f2k, temp_f2k)
    writer = create_f2k.CreateF2kFile(
        input_f2k=temp_f2k,
        etabs=shayesteh,
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
    # from pathlib import Path
    import etabs_obj
    etabs_api = Path(__file__).parent.parent
    import sys
    sys.path.insert(0, str(etabs_api))
    from etabs_obj import EtabsModel
    etabs = EtabsModel(backup=False)
    test_add_point_loads(etabs)