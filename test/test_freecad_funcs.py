import sys
from pathlib import Path

import numpy as np

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)
etabs_api_path = Path(__file__).parent.parent

import freecad_funcs
import FreeCAD
freecad_model = etabs_api_path / 'test' / 'files' / 'freecad' / 'shayesteh.FCStd'
shayesteh_doc = FreeCAD.openDocument(str(freecad_model))


def test_equivalent_height_in_meter():
    height, percent = freecad_funcs.equivalent_height_in_meter(shayesteh_doc.Wall007)
    np.testing.assert_allclose(height, 1.812, atol=.001)
    np.testing.assert_allclose(percent, 0.4, atol=.001)
    height, percent = freecad_funcs.equivalent_height_in_meter(shayesteh_doc.Wall003)
    np.testing.assert_allclose(height, 3.02, atol=.001)
    np.testing.assert_allclose(percent, 0, atol=.001)

def test_get_relative_dists():
    for wall in (shayesteh_doc.Wall007, shayesteh_doc.Wall003):
        dist1, dist2 = freecad_funcs.get_relative_dists(wall)
        np.testing.assert_allclose(dist1, 0, atol=.001)
        np.testing.assert_allclose(dist2, 1, atol=.001)
    dist1, dist2 = freecad_funcs.get_relative_dists(shayesteh_doc.Wall017)
    np.testing.assert_allclose(dist1, 0.1, atol=.001)
    np.testing.assert_allclose(dist2, .87, atol=.001)
