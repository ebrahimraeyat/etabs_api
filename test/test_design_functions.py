import sys
from pathlib import Path
import math

import pandas as pd
import numpy as np

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

def test_save_overwrites_of_frames_mixed_names_not_various():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options', '1', '2'],
        ['Set Restrain', '[]', '', '[]', '[]'],
        ['Structural Category', '1', '1,2,3,4', '4', '3'],
        ['Design Type', 'Column', 'Beam,Column', 'Beam', 'Beam'],
        ['SDL+LL Ratio', '0', '', '240', '240']
    ]
    original_df = pd.DataFrame(data[1:], columns=data[0])

    data2 = [
        ['Item', 'Value', 'Options'],
        ['Set Restrain', '[]', ''],
        ['Structural Category', '1', '1,2,3,4'],
        ['Design Type', 'Column', 'Beam,Column'],
        ['SDL+LL Ratio', '0', '']
    ]
    updated_df = pd.DataFrame(data2[1:], columns=data2[0])

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.save_overwrites_of_frames(
        updated_df=updated_df,
        original_df=original_df,
        relevant_columns=['1', '2', '3']
        )
    assert len(df.columns) == 6
    for i in range(len(df)):
        row_values = df.loc[i, ['1', '2', '3']]
        assert row_values.unique() == updated_df['Value'][i]

def test_save_overwrites_of_frames_mixed_names_various():
    import csv

    # Define the data as a list of lists
    data = [
        ['Item', 'Value', 'Options', '1', '2'],
        ['Set Restrain', '[]', '', '[]', '[]'],
        ['Structural Category', '1', '1,2,3,4', '4', '3'],
        ['Design Type', 'Column', 'Beam,Column', 'Beam', 'Beam'],
        ['SDL+LL Ratio', '0', '', '240', '240']
    ]
    original_df = pd.DataFrame(data[1:], columns=data[0])

    data2 = [
        ['Item', 'Value', 'Options'],
        ['Set Restrain', '[]', ''],
        ['Structural Category', 'various', '1,2,3,4'],
        ['Design Type', 'Column', 'Beam,Column'],
        ['SDL+LL Ratio', '0', '']
    ]
    updated_df = pd.DataFrame(data2[1:], columns=data2[0])

    # Open a file and write the data
    csv_file = get_temp_filepath('csv', 'test')
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)  # Write all rows at once
    df = design_functions.save_overwrites_of_frames(
        updated_df=updated_df,
        original_df=original_df,
        relevant_columns=['1', '2', '3']
        )
    assert len(df.columns) == 6
    for i in (0, 2, 3):
        row_values = df.loc[i, ['1', '2', '3']]
        assert row_values.unique() == updated_df['Value'][i]
    row_values = df.loc[1, ['1', '2', '3']]
    assert len(row_values.unique()) == 3
    assert set(row_values) == {'1', '3', '4'}

def test_get_point_and_bounds_restraints():
    test_cases = [
        ([(2, 'LL'), ((3, 5), 'LL'), (0.5, 'LL'), (4, 'LL'), ((6, 7), 'LL')]),
        ([(1, 'LL'), ((2, 3), 'LL'), (2.5, 'LL'), (3, 'LL'), ((4, 5), 'LL')]),
        ([(1.5, 'LL'), ((1, 2), 'LL'), (3, 'LL'), ((3, 4), 'LL'), (2.5, 'LL')]),
        ([(5, 'LL'), ((1, 6), 'LL'), (2, 'LL'), (4, 'LL'), ((7, 8), 'LL')]),
        ([(0, 'FF'), ((1, 2), 'LL'), (1, 'LL'), ((3, 4), 'FF')]),
        ([(0, 'FF'), ((1, 2), 'LL'), (1, 'LL'), ((3, 4), 'LL'), ((1.5, 3), 'LL')]),
        ([(0, 'LL'), ((1, 2), 'LL'), (0.5, 'LU'), ((3, 4), 'LL'), ((1.5, 3), 'LL')]),
    ]
    expected = (
    ([0.5, 2, 4], [(3, 5), (6, 7)]),
    ([1, 2.5, 3], [(2, 3), (4, 5)]),
    ([2.5, 3, 1.5], [(1, 2), (3, 4)]),
    ([2, 4, 5], [(1, 6), (7, 8)]),
    ([0, 1], [(1,2), (3, 4)]),
    ([0, 1], [(1, 2), (1.5, 3), (3,4)]),
    ([0, 0.5], [(1, 2), (1.5, 3), (3,4)]),
    )
    for i in range(len(test_cases)):
        input_data = test_cases[i]
        result = design_functions.get_point_and_bounds_restraints(input_data)
        assert len(result[0]) == len(expected[i][0]), f"Test case {i + 1} failed: expected {expected[i][0]}, got {result}"
        assert len(result[1]) == len(expected[i][1]), f"Test case {i + 1} failed: expected {expected[i][0]}, got {result}"
   
# def test_get_segments_of_frame():
#     # Define the parameters
#     x_values = [0, 1, 5, 6]
#     m_values = [-1, 0, 0, 1]
#     top_restraint = [(0, 6)]
#     bot_restraint = []
#     segments = design_functions.get_segments_of_frame(top_restraint, bot_restraint, x_values, m_values)
#     assert segments == [(0, 1), (5, 6)]

def test_convert_bounding_restraints_to_point_restraints():
    bounds_restraints = [
        [((1, 2.5), 'LL'), ((3, 7), 'LU')],
        [],
        [((1, 2.5), 'LL')],
        [((3, 7), 'LU')],
        [((2, 4), 'LU')],
    ]
    period = 6  # Period of the cosine function
    x_values = np.arange(0, 6, 0.1)  # Generate x values from 0 to 6 with a step of 0.1
    m_values = -np.cos((2 * np.pi / period) * x_values)

    points_restraints = design_functions.convert_bounding_restraints_to_point_restraints(
        bounds_restraints, x_values, m_values)
    desired_number_of_points = (6, 0, 3, 3, 2)
    for i, n in enumerate(desired_number_of_points):
        assert len(points_restraints[i]) == n

def test_convert_beam_restraints_to_points():
    restraints = [(0.5, 'LU'), ((1, 2.5), 'LU'),
                ((3, 7), 'LU'), (4, 'UL'), ((4.5, 5.5), 'UL')]
    period = 8  # Period of the cosine function
    x_values = np.arange(0, period + 0.1, 0.1)  # Generate x values from 0 to period with a step of 0.1
    m_values = -np.cos((2 * np.pi / period) * x_values)

    point_restraints = design_functions.convert_beam_restraints_to_points(
        restraints, x_values, m_values)[0]
    assert len(point_restraints) == 10
    assert set([ps.flange_restraints for ps in point_restraints]) == {'LU', 'UL'}

def test_get_beam_point_restraints_with_respect_to_supports_and_remove_duplicates():
    point_restraints = [(0.0, 'FF'), (0, 'LU'), (2.0, 'LU'), (8, 'LU'), (6.0, 'LU')]
    start_support = (0, 'FF')
    end_support = (8.0, 'FF')
    period = 8  # Period of the cosine function
    x_values = np.arange(0, period + 0.1, 0.1)  # Generate x values from 0 to period with a step of 0.1
    m_values = -np.cos((2 * np.pi / period) * x_values)
    rets = design_functions.get_beam_point_restraints_with_respect_to_supports_and_remove_duplicates(
        point_restraints,
        start_support,
        end_support,
        x_values,
        m_values,
    )
    assert len(rets) == 4
    assert rets[0].location == start_support[0]
    assert rets[0].flange_restraints == start_support[1]
    assert rets[-1].location == end_support[0]
    assert rets[-1].flange_restraints == end_support[1]

def test_point_restraint():
    # Beam with fix ends and gravity load
    period = 8  # Period of the cosine function
    x_values = np.arange(0, period + 0.1, 0.1)  # Generate x values from 0 to period with a step of 0.1
    m_values = -np.cos((2 * np.pi / period) * x_values)
    for x_value in (0, period):
        restraint = design_functions.PointRestraint(
            None,
            x_value,
            'LL',
            x_values, 
            m_values,
        )
        assert restraint.moment_sign == '--'
        assert restraint.critical_flang == 'Botton'
        assert restraint.cf_restraint == 'F'
    for x_value in (2, 6):
        restraint = design_functions.PointRestraint(
            None,
            x_value,
            'LU',
            x_values, 
            m_values,
            middle_of_bounding_restraint=False,
        )
        assert restraint.moment_sign == '0'
        assert restraint.critical_flang == 'Both'
        assert restraint.cf_restraint == 'U'
        restraint = design_functions.PointRestraint(
            None,
            x_value,
            'LU',
            x_values, 
            m_values,
            middle_of_bounding_restraint=True,
        )
        if x_value == 2:
            assert restraint.moment_sign == '-0+'
        elif x_value == 6:
            assert restraint.moment_sign == '+0-'
        assert restraint.critical_flang == 'Either'
        assert restraint.cf_restraint == 'L'
    # 
    # Beam with fix ends and wind load
    m_values = -m_values
    for x_value in (0, period):
        restraint = design_functions.PointRestraint(
            None,
            x_value,
            'LL',
            x_values, 
            m_values,
        )
        assert restraint.moment_sign == '++'
        assert restraint.critical_flang == 'Top'
        assert restraint.cf_restraint == 'F'
    for x_value in (2, 6):
        restraint = design_functions.PointRestraint(
            None,
            x_value,
            'LU',
            x_values, 
            m_values,
            middle_of_bounding_restraint=False,
        )
        assert restraint.moment_sign == '0'
        assert restraint.critical_flang == 'Both'
        assert restraint.cf_restraint == 'U'
        restraint = design_functions.PointRestraint(
            None,
            x_value,
            'LU',
            x_values, 
            m_values,
            middle_of_bounding_restraint=True,
        )
        if x_value == 2:
            assert restraint.moment_sign == '+0-'
        elif x_value == 6:
            assert restraint.moment_sign == '-0+'
        assert restraint.critical_flang == 'Either'
        assert restraint.cf_restraint == 'L'


    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print("\n", segments)
    # assert len(segments) == 2
    # # wind load
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, -m_values)
    # print(segments)
    # assert len(segments) == 1

    # restraints = [((0, period), 'UL')]
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, -m_values)
    # print(segments)
    # assert len(segments) == 2
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print(segments)
    # assert len(segments) == 1
    # # memdes example
    # restraints = [(4, 'LP')]
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print(segments)
    # assert len(segments) == 2

    # restraints = [(2.5, 'UL')]
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print(segments)
    # assert len(segments) == 1
    # restraints = [(2.5, 'LU')]
    # x_values = np.arange(0, 5.5, .50)
    # m_values = np.array([-170, -92, -27, 24,61,85,95,92,75,44,0])
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print(segments)
    # assert len(segments) == 2
    
    # restraints = [(2.5, 'PL')]
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print(segments)
    # assert len(segments) == 2
    
    # x_values = np.array([0, .5,1,1.25,1.5,2,2.5,3,3.5,3.75,4,4.5,5])
    # m_values = np.array([-170, -92, -27, 0,24,61,85,95,92, 85, 75,44,0])
    # restraints = [(1.25 * i, 'LU') for i in (1,2,3)]
    # segments = design_functions.get_segments_of_frame(
    #     restraints, x_values, m_values)
    # print(segments)
    # assert len(segments) == 3


def test_get_segments_of_frame():
    period = 8  # Period of the cosine function
    restraints = [((0, period), 'LU')]
    x_values = np.arange(0, period + 0.1, 0.1)  # Generate x values from 0 to period with a step of 0.1
    m_values = -np.cos((2 * np.pi / period) * x_values)

    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print("\n", segments)
    assert len(segments) == 2
    # wind load
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, -m_values)
    print(segments)
    assert len(segments) == 1

    restraints = [((0, period), 'UL')]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, -m_values)
    print(segments)
    assert len(segments) == 2
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print(segments)
    assert len(segments) == 1
    # memdes example
    restraints = [(4, 'LP')]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print(segments)
    assert len(segments) == 2

    restraints = [(2.5, 'UL')]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print(segments)
    assert len(segments) == 1
    restraints = [(2.5, 'LU')]
    x_values = np.arange(0, 5.5, .50)
    m_values = np.array([-170, -92, -27, 24,61,85,95,92,75,44,0])
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print(segments)
    assert len(segments) == 2
    
    restraints = [(2.5, 'PL')]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print(segments)
    assert len(segments) == 2
    
    x_values = np.array([0, .5,1,1.25,1.5,2,2.5,3,3.5,3.75,4,4.5,5])
    m_values = np.array([-170, -92, -27, 0,24,61,85,95,92, 85, 75,44,0])
    restraints = [(1.25 * i, 'LU') for i in (1,2,3)]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values)
    print(segments)
    assert len(segments) == 3
    assert math.isclose(segments[0].end_restraint.location, 2.5)
    
    x_values = np.array([0, .5,1,1.25,1.5,2,2.5,3,3.5,3.75,4,4.5,5])
    m_values = np.array([0,32,54,62,66,69,62,44,17,0,-20,-66,-123])
    restraints = [(1.25 * i, 'LU') for i in (1,2,3)]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values, start_support='LL', end_support='LL')
    print(segments)
    assert len(segments) == 3
    names = ('A-1', '1-2', '2-B')
    for i, segment in enumerate(segments):
        assert segment.name == names[i]
    assert math.isclose(segments[0].end_restraint.location, 1.25)
    
    x_values = np.array([0, .5,1,1.25,1.5,2,2.5,3,3.5,3.75,4,4.5,5])
    m_values = np.array([0,-19,-32,-37,-40,-41,-37,-27,-10,0,12,40,74])
    restraints = [(1.25 * i, 'LU') for i in (1,2,3)]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values, start_support='LL', end_support='LL')
    print(segments)
    assert len(segments) == 1
    names = ('A-B',)
    for i, segment in enumerate(segments):
        assert segment.name == names[i]
    assert math.isclose(segments[0].end_restraint.location, 5)
    
    # real example
    x_values = np.array([ 101.5 ,  595.16, 1088.81, 1582.47, 2076.13, 2569.78, 3063.44,
       3557.09, 4050.75, 4544.41, 5038.06, 5531.72, 6025.38, 6519.03,
       7012.69, 7506.34, 8000.  ])
    m_values = np.array([-264746.66, -170825.47,  -89156.74,  -19740.47,   37423.33,
         82334.67,  114993.55,  135399.97,  143553.92,  139455.41,
        123104.43,   94500.99,   53645.09,     536.73,  -64824.1 ,
       -142437.39, -232303.14])
    restraints = [(4000, 'LL')]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values, start_support='LL', end_support='LL')
    print(segments)
    assert len(segments) == 2
    names = ('A-1', '1-B')
    for i, segment in enumerate(segments):
        assert segment.name == names[i]
    assert math.isclose(segments[0].end_restraint.location, 4000)
    # composite
    restraints = [((x_values[0], x_values[-1]), 'LU')]
    segments = design_functions.get_segments_of_frame(
        restraints, x_values, m_values, start_support='LL', end_support='LL')
    print(segments)
    assert len(segments) == 2
    names = ('A-1', '2-B')
    for i, segment in enumerate(segments):
        assert segment.name == names[i]
    assert math.isclose(segments[0].end_restraint.location, 1752, abs_tol=1)

    # assert set([ps[1] for ps in point_restraints]) == {'LU', 'UL'}

# def test_get_sorted_top_bot_beam_restraints_in_points_format():
#     top_restraints = [0.5, (1, 2.5), (3, 7)]
#     bot_restraints = [0.5, 4, (4.5, 5.5)]
#     period = 8  # Period of the cosine function
#     x_values = np.arange(0, period, 0.1)  # Generate x values from 0 to 6 with a step of 0.1
#     m_values = -np.cos((2 * np.pi / period) * x_values)

#     top_bot_point_restraints = design_functions.get_sorted_top_bot_beam_restraints_in_points_format(
#         top_restraints, bot_restraints, x_values, m_values)
#     assert len(top_bot_point_restraints) == 5
#     assert (0.5, 'top_bot') in top_bot_point_restraints
#     assert (4, 'bot') in top_bot_point_restraints

def test_segment():
    x_values = np.array([0, .5,1,1.25,1.5,2,2.5,3,3.5,3.75,4,4.5,5])
    m_values = np.array([0,-19,-32,-37,-40,-41,-37,-27,-10,0,12,40,74])
    start_restraint = design_functions.PointRestraint('A', x_values[0], 'FF', x_values, m_values)
    end_restraint = design_functions.PointRestraint('B', x_values[-1], 'FF', x_values, m_values)
    segment = design_functions.Segment(start_restraint, end_restraint)
    assert segment.name == 'A-B'
    assert segment.length == x_values[-1] - x_values[0]
    assert segment.restraints == 'FF'
    assert segment.kr == 1

def test_beam():
    x_values = np.array([0, .5,1,1.25,1.5,2,2.5,3,3.5,3.75,4,4.5,5])
    m_values = np.array([0,-19,-32,-37,-40,-41,-37,-27,-10,0,12,40,74])
    combos = {'comb1': (x_values, m_values)}
    beam = design_functions.Beam(
        '3', 8, None, '', '', [], 'FF', 'FF', 
        combos, is_composite=True, tolerance=.001
    )

def test_beam2():
    x_values = np.array([ 101.5 ,  595.16, 1088.81, 1582.47, 2076.13, 2569.78, 3063.44,
       3557.09, 4050.75, 4544.41, 5038.06, 5531.72, 6025.38, 6519.03,
       7012.69, 7506.34, 8000.  ])
    m_values = np.array([-264746.66, -170825.47,  -89156.74,  -19740.47,   37423.33,
         82334.67,  114993.55,  135399.97,  143553.92,  139455.41,
        123104.43,   94500.99,   53645.09,     536.73,  -64824.1 ,
       -142437.39, -232303.14])
    combo_name = '1.2G+1.5Q'
    combos = {combo_name: (x_values, m_values)}
    beam = design_functions.Beam(
        '25', 7898.5, None, '', '', [(4000, 'LL')], 'LL', 'LL', 
        combos, is_composite=True, tolerance=.001
    )
    assert beam.name == '25'
    assert len(beam.segments) == 1
    segments = beam.segments.get(combo_name)
    assert len(segments) == 2
    segments_name = ('A-1', '3-B')
    for name, segment in zip(segments_name, segments):
        assert segment.name == name


if __name__ == '__main__':
    test_beam2()



