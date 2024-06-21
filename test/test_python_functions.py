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

def test_get_unique_load_combinations():
    data = [
            'COMBO11', 'Linear Add', 'Dead', 1.4,
            'COMBO21', 'Linear Add', 'Dead', 1.2, 'COMBO21', 'Linear Add', 'Live', 1.6,
            'COMBO22', 'Linear Add', 'Dead', 1.2, 'COMBO22', 'Linear Add', 'Live', 1.6,
            'COMBO31', 'Linear Add', 'Dead', 1.2, 'COMBO31', 'Linear Add', 'Live', 1,
            'COMBO32', 'Linear Add', 'Dead', 1.2, 'COMBO32', 'Linear Add', 'Live', 1,
            'COMBO41', 'Linear Add', 'Dead', 1.2, 'COMBO41', 'Linear Add', 'Live', 1,
            'COMBO51', 'Linear Add', 'Dead', 1.2, 'COMBO51', 'Linear Add', 'Live', 1,
            'COMBO71', 'Linear Add', 'Dead', 0.9,
            'COMBO72', 'Linear Add', 'Dead', 0.9,
            ]
    
    ret = python_functions.get_unique_load_combinations(data)
    desired = [
             'COMBO11', 'Linear Add', 'Dead', '1.4',
             'COMBO21', 'Linear Add', 'Dead', '1.2', 'COMBO21', 'Linear Add', 'Live', '1.6',
             'COMBO31', 'Linear Add', 'Dead', '1.2', 'COMBO31', 'Linear Add', 'Live', '1',
             'COMBO71', 'Linear Add', 'Dead', '0.9',
             ]
    assert ret == desired
    ret = python_functions.get_unique_load_combinations(data, sequence_numbering=True, prefix='COMBO')
    desired = [
             'COMBO1', 'Linear Add', 'Dead', '1.4',
             'COMBO2', 'Linear Add', 'Dead', '1.2', 'COMBO2', 'Linear Add', 'Live', '1.6',
             'COMBO3', 'Linear Add', 'Dead', '1.2', 'COMBO3', 'Linear Add', 'Live', '1',
             'COMBO4', 'Linear Add', 'Dead', '0.9',
             ]
    assert ret == desired
