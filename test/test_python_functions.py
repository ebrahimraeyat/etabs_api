import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

import python_functions


def test_flatten_list():
    nested_list = [[1, 2, [3, 4]], [5, 6], 7, [8, [9, 10]]]
    ret = python_functions.flatten_list(nested_list)
    assert set(ret) == {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}