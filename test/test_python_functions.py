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

def test_filter_and_sort():
    """
    Tests the filter_and_sort function with various cases.
    """
    # Test cases
    test_cases = [
        ([2, [3, 5], 0.5, 4, [6, 7]], [0.5, 2, [3, 5], [6, 7]]),
        ([1, [2, 3], 2.5, 3, [4, 5]], [1, [2, 3], [4, 5]]),
        ([1.5, [1, 2], 3, [3, 4], 2.5], [[1,2], 2.5, [3, 4]]),
        ([5, [1, 6], 2, 4, [7, 8]], [[1,6], [7, 8]]),
        ([0, [1, 2], 1, [3, 4]], [0, [1,2], [3, 4]])
    ]

    for i, (input_data, expected) in enumerate(test_cases):
        result = python_functions.filter_and_sort(input_data)
        assert result == expected, f"Test case {i + 1} failed: expected {expected}, got {result}"
    
if __name__ == "__main__":
    test_filter_and_sort()