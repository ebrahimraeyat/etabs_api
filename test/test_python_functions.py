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

def test_is_text_in_list_elements():
    text_list = ["apple", "banana", "orange", "grape", "pineapple"]
    # Partial text to search for
    partial_text = "app"
    # Search for partial text in the list elements
    matching_elements = [text for text in text_list if partial_text in text]
    assert set(matching_elements) == {'apple', 'pineapple'}
