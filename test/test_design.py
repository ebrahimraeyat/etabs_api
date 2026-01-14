import sys
from pathlib import Path
import pytest

import pandas as pd

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import etabs, open_etabs_file, get_temp_filepath

@open_etabs_file('shayesteh.EDB')
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

@open_etabs_file('shayesteh.EDB')
def test_get_code_string():
    code = "ACI 318-08"
    code_string = etabs.design.get_code_string(code=code)
    assert code_string == "ACI318_08_IBC2009"

@open_etabs_file('shayesteh.EDB')
def test_set_phi_joint_shear_aci19():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-19")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_19.GetPreference(15)
    assert ret[0] == phi_joint_shear

@open_etabs_file('shayesteh.EDB')
def test_set_phi_joint_shear_aci14():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-14")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_14.GetPreference(15)
    assert ret[0] == phi_joint_shear

@open_etabs_file('shayesteh.EDB')
def test_set_phi_joint_shear_aci11():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-11")
    with pytest.raises(AttributeError) as err:
        etabs.design.set_phi_joint_shear(value=phi_joint_shear)
        ret = etabs.SapModel.DesignConcrete.ACI318_11.GetPreference(15)
        assert ret[0] == phi_joint_shear

@open_etabs_file('shayesteh.EDB')
def test_set_phi_joint_shear_aci08():
    phi_joint_shear = 0.87
    etabs.SapModel.DesignConcrete.SetCode("ACI 318-08")
    etabs.design.set_phi_joint_shear(value=phi_joint_shear)
    ret = etabs.SapModel.DesignConcrete.ACI318_08_IBC2009.GetPreference(10)
    assert ret[0] == phi_joint_shear

@open_etabs_file('shayesteh.EDB')
def test_get_rho_of_beams():
    rhos, texts = etabs.design.get_rho_of_beams(['130'], distances=[0])
    assert len(rhos) == len(texts)
    assert isinstance(texts[0], str)
    print(texts[0])
    assert pytest.approx(rhos[0], abs=.001) == .014598

@open_etabs_file('madadi.EDB')
def test_get_deflection_of_beams():
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'beam_deflection_madadi_157.csv'
    df = pd.read_csv(filename)
    df.Name = df.Name.astype(str)
    dead = etabs.load_patterns.get_special_load_pattern_names(1)
    supper_dead = etabs.load_patterns.get_special_load_pattern_names(2)
    l1 = etabs.load_patterns.get_special_load_pattern_names(3)
    l2 = etabs.load_patterns.get_special_load_pattern_names(4)
    l3 = etabs.load_patterns.get_special_load_pattern_names(11)
    lives = l1 + l2 + l3
    defs1, defs2, *_ = etabs.design.get_deflection_of_beams(
        dead=dead,
        supper_dead=supper_dead,
        lives=lives,
        beam_names=df,
        distances_for_calculate_rho=['middle'],
    )
    assert pytest.approx(defs1[0], abs=.01) == 0.3496
    assert pytest.approx(defs2[0], abs=.01) == 2.2288

@open_etabs_file('madadi.EDB')
def test_get_deflection_of_beams_console():
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'beam_deflection_madadi_10.csv'
    df = pd.read_csv(filename)
    df.Name = df.Name.astype(str)
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
        beam_names=df,
        distances_for_calculate_rho=['start'],
        rhos=[0.002533],
    )
    assert True

# @open_etabs_file('madadi.EDB')
@open_etabs_file('rashidzadeh.EDB')
def test_get_deflection_of_beams_console2():
    filename = Path(__file__).absolute().parent / 'files' / 'dataframe' / 'beam_deflection_rashidzadeh_console2.csv'
    df = pd.read_csv(filename)
    df.Name = df.Name.astype(str)
    dead = etabs.load_patterns.get_special_load_pattern_names(1)
    supper_dead = etabs.load_patterns.get_special_load_pattern_names(2)
    l1 = etabs.load_patterns.get_special_load_pattern_names(3)
    l2 = etabs.load_patterns.get_special_load_pattern_names(4)
    l3 = etabs.load_patterns.get_special_load_pattern_names(11)
    lives = l1 + l2 + l3
    defs1, defs2, texts = etabs.design.get_deflection_of_beams(
        dead=dead,
        supper_dead=supper_dead,
        lives=lives,
        beam_names=df,
        distances_for_calculate_rho='start', #The frame is reverse
    )
    # print(f'{defs1=}\n\n\n')
    # print(f'{defs2=}')
    # print(f'{texts=}')
    assert True

@open_etabs_file('madadi.EDB')
def test_get_deflection_check_result():
    import design
    text = design.get_deflection_check_result(
        -1.8,
        -2.4,
        800,
    )
    print(text)
    assert isinstance(text, str)

@open_etabs_file('madadi.EDB')
def test_model_designed():
    assert not etabs.design.model_designed()
    etabs.run_analysis()
    assert not etabs.design.model_designed()
    etabs.start_design()
    assert etabs.design.model_designed()
    assert not etabs.design.model_designed(type_='Steel')

@open_etabs_file('madadi.EDB')
def test_get_concrete_columns_pmm_table():
    df = etabs.design.get_concrete_columns_pmm_table()
    assert df is not None
    assert isinstance(df, pd.DataFrame)

if __name__ == '__main__':
    test_get_deflection_of_beams_console()

