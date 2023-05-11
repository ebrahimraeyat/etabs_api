import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh

def test_set_concrete_framing_type(shayesteh):
    shayesteh.design.set_concrete_framing_type()
    beam_names, column_names = shayesteh.frame_obj.get_beams_columns(type_=2)
    shayesteh.SapModel.DesignConcrete.SetCode("ACI 318-19")
    shayesteh.design.set_concrete_framing_type()
    for name in beam_names + column_names:
        ret = shayesteh.SapModel.DesignConcrete.ACI318_19.GetOverwrite(name,1)
        assert ret[0] == 2
    shayesteh.design.set_concrete_framing_type(type_=1)
    for name in beam_names + column_names:
        ret = shayesteh.SapModel.DesignConcrete.ACI318_19.GetOverwrite(name,1)
        assert ret[0] == 1
