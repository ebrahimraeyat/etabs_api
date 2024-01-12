import sys
from pathlib import Path
import pytest

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

if 'etabs' not in dir(__builtins__):
    from shayesteh import etabs, open_model, version

def test_set_concrete_framing_type():
    etabs.design.set_concrete_framing_type()
    beam_names, column_names = etabs.frame_obj.get_beams_columns(type_=2)
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-19")
    etabs.design.set_concrete_framing_type()
    for name in beam_names + column_names:
        ret = etabs.SapModel.DesignConcrete.ACI318_19.GetOverwrite(name,1)
        assert ret[0] == 2
    etabs.design.set_concrete_framing_type(type_=1)
    for name in beam_names + column_names:
        ret = etabs.SapModel.DesignConcrete.ACI318_19.GetOverwrite(name,1)
        assert ret[0] == 1

def test_get_code_string():
    code = "ACI 318-08"
    code_string = etabs.design.get_code_string(code=code)
    assert code_string == "ACI318_08_IBC2009"

def test_set_phi_joint_shear_aci19():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-19")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_19.GetPreference(15)
    assert ret[0] == phi_joint_shear

def test_set_phi_joint_shear_aci14():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-14")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_14.GetPreference(15)
    assert ret[0] == phi_joint_shear

def test_set_phi_joint_shear_aci11():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-11")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_11.GetPreference(15)
    assert ret[0] == phi_joint_shear

def test_set_phi_joint_shear_aci08():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-08/IBC 2009")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_08_IBC2009.GetPreference(10)
    assert ret[0] == phi_joint_shear

def test_get_rho_of_beams():
    open_model(etabs=etabs, filename='shayesteh.EDB')
    rhos, _ = etabs.design.get_rho_of_beams(['130'], distances=[0])
    assert pytest.approx(rhos[0], abs=.0001) == .01517

def test_get_deflection_of_beams():
    open_model(etabs=etabs, filename='madadi.EDB')
    dead = etabs.load_patterns.get_special_load_pattern_names(1)
    supper_dead = etabs.load_patterns.get_special_load_pattern_names(2)
    l1 = etabs.load_patterns.get_special_load_pattern_names(3)
    l2 = etabs.load_patterns.get_special_load_pattern_names(4)
    l3 = etabs.load_patterns.get_special_load_pattern_names(11)
    lives = l1 + l2 + l3
    defs1, defs2, _ = etabs.design.get_deflection_of_beams(
        dead=dead,
        supper_dead=supper_dead,
        lives=lives,
        beam_names=['157'],
        distances_for_calculate_rho=['middle'],
    )
    assert pytest.approx(defs1[0], abs=.001) == 0.3975
    assert pytest.approx(defs2[0], abs=.001) == 2.21168

def test_get_deflection_of_beams_console():
    open_model(etabs=etabs, filename='madadi.EDB')
    dead = etabs.load_patterns.get_special_load_pattern_names(1)
    supper_dead = etabs.load_patterns.get_special_load_pattern_names(2)
    l1 = etabs.load_patterns.get_special_load_pattern_names(3)
    l2 = etabs.load_patterns.get_special_load_pattern_names(4)
    l3 = etabs.load_patterns.get_special_load_pattern_names(11)
    lives = l1 + l2 + l3
    etabs.design.get_deflection_of_beams(
        dead=dead,
        supper_dead=supper_dead,
        lives=lives,
        beam_names=['129'],
        distances_for_calculate_rho=['end'], #The frame is reverse
        is_consoles=[True],
        rhos=[0.00579],
    )
    assert True

def test_get_deflection_of_beams_console2():
    # open_model(etabs=etabs, filename='rashidzadeh.EDB')
    dead = etabs.load_patterns.get_special_load_pattern_names(1)
    supper_dead = etabs.load_patterns.get_special_load_pattern_names(2)
    l1 = etabs.load_patterns.get_special_load_pattern_names(3)
    l2 = etabs.load_patterns.get_special_load_pattern_names(4)
    l3 = etabs.load_patterns.get_special_load_pattern_names(11)
    lives = l1 + l2 + l3
    beam_names=['97', '80', '63', '46', '29', '12', '11', '28', '45', '62', '79', '96']
    defs1, defs2, texts = etabs.design.get_deflection_of_beams(
        dead=dead,
        supper_dead=supper_dead,
        lives=lives,
        beam_names=beam_names,
        distances_for_calculate_rho='start', #The frame is reverse
        is_consoles=True,
    )
    print(f'{defs1=}\n\n\n')
    print(f'{defs2=}')
    # print(f'{texts=}')
    assert True

def test_get_deflection_check_result():
    open_model(etabs=etabs, filename='madadi.EDB')
    import design
    text = design.get_deflection_check_result(
        -1.8,
        -2.4,
        800,
    )
    print(text)
    assert isinstance(text, str)

def test_model_designed():
    open_model(etabs=etabs, filename='madadi.EDB')
    assert not etabs.design.model_designed()
    etabs.run_analysis()
    assert not etabs.design.model_designed()
    etabs.start_design()
    assert etabs.design.model_designed()
    assert not etabs.design.model_designed(type_='Steel')

