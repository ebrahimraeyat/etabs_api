import sys
from pathlib import Path
import pytest

import numpy as np

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file, version

@open_etabs_file('shayesteh.EDB')
def test_add_piers():
    names = etabs.pier.add_piers()
    assert set(names) == set(etabs.pier.get_names())

@open_etabs_file('two_earthquakes.EDB')
def test_get_columns_names_with_pier_label():
    '''
    {'P1': {'STORY1': ['181','190','199','208','217','226','235','244','253']},
    'P2': {'STORY1': ['10', '19', '28', '37', '46', '55', '64', '73']},
    'P3': {'STORY1': ['172', '1']}}
    '''
    ret = etabs.pier.get_columns_names_with_pier_label()
    assert len(ret) == 3
    assert set(ret['P1']['STORY1']) == {'181','190','199','208','217','226','235','244','253'}
    
if __name__ == '__main__':
    test_get_lateral_bracing()





