import sys
from pathlib import Path
import pytest

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file, version

@open_etabs_file('two_earthquakes.EDB')
def test_set_modifiers():
    etabs.shearwall.set_modifiers()
    names = etabs.SapModel.AreaObj.GetLabelNameList()[1]
    for label in names:
        if etabs.SapModel.AreaObj.GetDesignOrientation(label)[0] == 1:
            curr_modifiers = list(etabs.SapModel.AreaObj.GetModifiers(label)[0])
            assert set(curr_modifiers[:6]) == {.01}

def test_create_25percent_file():
    main_file_path, filename = etabs.shearwall.create_25percent_file()
    assert filename.exists()
    assert main_file_path == etabs.get_filename()

@open_etabs_file('two_earthquakes.EDB')
def test_start_design():
    df = etabs.shearwall.start_design()
    assert "DCRatio" in df.columns
    assert df.shape[0] == 14

@open_etabs_file('two_earthquakes.EDB')
def test_set_design_type():
    etabs.shearwall.set_design_type(type_="Design")
    table_key = 'Shear Wall Pier Design Overwrites - ACI 318-14'
    df = etabs.database.read(table_key, to_dataframe=True)
    assert df['DesignCheck'].iloc[0] == 'Design'
    etabs.shearwall.set_design_type()
    df = etabs.database.read(table_key, to_dataframe=True)
    assert df['DesignCheck'].iloc[0] == 'Program Determined'

@open_etabs_file('two_earthquakes.EDB')
def test_get_wall_ratios():
    # etabs.shearwall.set_design_type(type_="Program Determined")
    df = etabs.shearwall.get_wall_ratios()
    assert "DCRatio" in df.columns
    assert df.shape[0] == 5
    
if __name__ == '__main__':
    test_get_wall_ratios()





