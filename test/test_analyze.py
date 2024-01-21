import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file, get_temp_filepath


@open_etabs_file('shayesteh.EDB')
def test_set_load_cases_to_analyze():
    etabs.analyze.set_load_cases_to_analyze()
    flags = etabs.SapModel.Analyze.GetRunCaseFlag()[2]
    assert set(flags) == {True}