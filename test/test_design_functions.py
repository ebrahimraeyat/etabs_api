import sys
from pathlib import Path
import pytest

import pandas as pd

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from python_functions import get_temp_filepath
import design_functions



def test_get_overwrites_of_frames():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options'],
        ['Set Restrain', '[]', ''],
        ['Structural Category', '1', '1,2,3,4'],
        ['Design Type', 'Column', 'Beam,Column'],
        ['SDL+LL Ratio', '0', '']
    ]

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.get_overwrites_of_frames(csv_file, [])
    df2 = pd.read_csv(csv_file)
    pd.testing.assert_frame_equal(df, df2)

def test_get_overwrites_of_frames_exist_names():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options', '1', '2'],
        ['Set Restrain', '[]', '', '[]', '[]'],
        ['Structural Category', '1', '1,2,3,4', '4', '3'],
        ['Design Type', 'Column', 'Beam,Column', 'Beam', 'Beam'],
        ['SDL+LL Ratio', '0', '', '240', '240']
    ]

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.get_overwrites_of_frames(csv_file, ['1', '2'])
    assert df['Value'][1] == 'various'
    for i in (0, 2, 3):
        assert df['Value'][i] != 'various'

def test_get_overwrites_of_frames_new_name():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options', '1', '2'],
        ['Set Restrain', '[]', '', '[]', '[]'],
        ['Structural Category', '1', '1,2,3,4', '4', '3'],
        ['Design Type', 'Column', 'Beam,Column', 'Beam', 'Beam'],
        ['SDL+LL Ratio', '0', '', '240', '240']
    ]

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.get_overwrites_of_frames(csv_file, ['3'])
    df2 = pd.read_csv(csv_file)
    pd.testing.assert_frame_equal(df, df2)

def test_get_overwrites_of_frames_mixed_names_not_various():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options', '1', '2'],
        ['Set Restrain', '[]', '', '[]', '[]'],
        ['Structural Category', '1', '1,2,3,4', '4', '3'],
        ['Design Type', 'Column', 'Beam,Column', 'Beam', 'Beam'],
        ['SDL+LL Ratio', '0', '', '240', '240']
    ]

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.get_overwrites_of_frames(csv_file, ['1', '3'])
    df2 = pd.read_csv(csv_file)
    df2 = df2[['Item', '1', 'Options']]
    df2.columns = ['Item', 'Value', 'Options']
    pd.testing.assert_frame_equal(df, df2)

def test_get_overwrites_of_frames_mixed_names_various():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options', '1', '2'],
        ['Set Restrain', '[]', '', '[]', '[]'],
        ['Structural Category', '1', '1,2,3,4', '4', '3'],
        ['Design Type', 'Column', 'Beam,Column', 'Beam', 'Beam'],
        ['SDL+LL Ratio', '0', '', '240', '240']
    ]

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.get_overwrites_of_frames(csv_file, ['1', '2', '3'])
    assert df['Value'][1] == 'various'
    df2 = pd.read_csv(csv_file)
    for i in (0, 2, 3):
        assert df['Value'][i] == df2['1'][i]
        assert df['Value'][i] == df2['2'][i]

if __name__ == '__main__':
    test_get_overwrites_of_frames_mixed_names_not_various()



