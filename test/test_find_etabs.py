import sys
from pathlib import Path

FREECADPATH = 'G:\\program files\\FreeCAD 0.19\\bin'
sys.path.append(FREECADPATH)

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))
import FreeCAD
import find_etabs

def test_find_etabs():
    find_etabs.find_etabs()

if __name__ == '__main__':
    test_find_etabs()