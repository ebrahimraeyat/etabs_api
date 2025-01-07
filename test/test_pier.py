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

    
if __name__ == '__main__':
    test_get_lateral_bracing()





