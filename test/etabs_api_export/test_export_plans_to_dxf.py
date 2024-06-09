import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from etabs_api_export import export_plans_to_dxf

from shayesteh import etabs, open_etabs_file
from python_functions import get_temp_filepath


@open_etabs_file('shayesteh.EDB')
def test_export_to_dxf():
    filename = get_temp_filepath(suffix='dxf', random=True)
    export_plans_to_dxf.export_to_dxf(etabs=etabs, filename=filename, Open_file=True)
    assert filename.exists()