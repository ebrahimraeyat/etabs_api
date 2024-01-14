import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version, get_temp_filepath


def test_set_load_cases_to_analyze():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    etabs.analyze.set_load_cases_to_analyze()
    flags = etabs.SapModel.Analyze.GetRunCaseFlag()[2]
    assert set(flags) == {True}