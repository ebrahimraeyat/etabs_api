import sys
from pathlib import Path

import matplotlib.pyplot as plt

import numpy as np


etabs_api_path = Path(__file__).absolute().parent.parent.parent
sys.path.insert(0, str(etabs_api_path))
from report import beam_deflection_report as report

from test.shayesteh import etabs, open_etabs_file, get_temp_filepath


def test_add_lines_to_ax():
    fig, ax = plt.subplots()
    plt.axis('off')
    x = .3
    y1 = .3
    y2 = .6
    line_coords = [([0, x], [y1, y2]), ([x, x], [y2, y1])]
    report.add_lines_to_ax(line_coords, ax)
    x_plot, y_plot = ax.lines[0].get_xydata().T
    np.testing.assert_array_equal(x_plot, np.array([0, x]))
    np.testing.assert_array_equal(y_plot, np.array([y1, y2]))
    x_plot, y_plot = ax.lines[1].get_xydata().T
    np.testing.assert_array_equal(x_plot, np.array([x, x]))
    np.testing.assert_array_equal(y_plot, np.array([y2, y1]))
    filename = get_temp_filepath(suffix='jpg', filename='test')
    fig.savefig(filename)
    assert filename.exists()

@open_etabs_file('shayesteh.EDB')
def test_get_beam_column_ax():
    report.get_beam_column_ax(etabs, beam_name='115')
    assert True

@open_etabs_file('shayesteh.EDB')
def test_get_picture():
    filename_path = report.get_picture(etabs, beam_name='115')
    assert filename_path.exists()

@open_etabs_file('shayesteh.EDB')
def test_get_beam_columns_coords():
    beam_coords, polygons = report.get_beam_columns_coords(etabs, '115')
    assert len(beam_coords) == 38
    assert len(polygons) == 11

@open_etabs_file('shayesteh.EDB')
def test_create_report():
    filename = get_temp_filepath(suffix='docx', filename='test')
    report.create_report(etabs, 'x', 'y', '115', filename)
    assert filename.exists()

# @open_etabs_file('shayesteh.EDB')
# def test_create_beam_deflection_report():
#     filename = get_temp_filepath(suffix='docx', filename='test')
#     report.create_beam_deflection_report(etabs, results, filename)
#     assert filename.exists()



    
if __name__ == "__main__":
    test_get_beam_column_ax()