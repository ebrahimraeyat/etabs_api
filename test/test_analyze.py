import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

@pytest.mark.getmethod
def test_set_load_cases_to_analyze(shayesteh):
    shayesteh.analyze.set_load_cases_to_analyze()
    flags = shayesteh.SapModel.Analyze.GetRunCaseFlag()[2]
    assert set(flags) == {True}