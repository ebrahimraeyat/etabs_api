import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'shayesteh19' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

@pytest.mark.getmethod
def test_set_load_cases_to_analyze():
    etabs.analyze.set_load_cases_to_analyze()
    flags = etabs.SapModel.Analyze.GetRunCaseFlag()[2]
    assert set(flags) == {True}