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
    test_add_load_combinations_envelope(etabs)