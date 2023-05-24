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

def test_set_phi_joint_shear_aci19(shayesteh):
    phi_joint_shear = 0.87
    shayesteh.SapModel.DesignConcrete.SetCode("ACI 318-19")
    shayesteh.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = shayesteh.SapModel.DesignConcrete.ACI318_19.GetPreference(15)
    assert ret[0] == phi_joint_shear

def test_set_phi_joint_shear_aci14(shayesteh):
    phi_joint_shear = 0.87
    shayesteh.SapModel.DesignConcrete.SetCode("ACI 318-14")
    shayesteh.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = shayesteh.SapModel.DesignConcrete.ACI318_14.GetPreference(15)
    assert ret[0] == phi_joint_shear

def test_set_phi_joint_shear_aci11(shayesteh):
    phi_joint_shear = 0.87
    shayesteh.SapModel.DesignConcrete.SetCode("ACI 318-11")
    shayesteh.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = shayesteh.SapModel.DesignConcrete.ACI318_11.GetPreference(15)
    assert ret[0] == phi_joint_shear

def test_set_phi_joint_shear_aci08(shayesteh):
    phi_joint_shear = 0.87
    shayesteh.SapModel.DesignConcrete.SetCode("ACI 318-08/IBC 2009")
    shayesteh.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = shayesteh.SapModel.DesignConcrete.ACI318_08_IBC2009.GetPreference(10)
    assert ret[0] == phi_joint_shear

def test_get_rho(shayesteh):
    rho = shayesteh.design.get_rho('130', distance=0)
    assert pytest.approx(rho, abs=.0001) == .01517
