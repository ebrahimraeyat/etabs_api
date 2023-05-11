import sys
from pathlib import Path
import pytest
from unittest.mock import Mock

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

from shayesteh import shayesteh, get_temp_filepath

Tx_drift, Ty_drift = 1.085, 1.085

# def close_etabs(ETABS):
#     SapModel = ETABS.SapModel
#     test_file_path = Path(SapModel.GetModelFilename())
#     etabs.close_etabs(ETABS)
#     test_files = test_file_path.parent.glob('test.*')
#     for f in test_files:
#         f.unlink()

def create_building():
    building = Mock()
    building.results = [True, .123, .108]
    building.kx, building.ky = 1.18, 1.15
    building.results_drift = [True, .89, .98]
    building.kx_drift, building.ky_drift = 1.15, 1.2
    return building

def test_get_from_list_table(shayesteh):
    data = [['STORY5', 'QX', 'LinStatic', None, None, None, 'Top', '0', '0'],
            ['STORY5', 'QX', 'LinStatic', None, None, None, 'Bottom', '0', '0'],
            ['STORY4', 'QX', 'LinRespSpec', 'Max', None, None, 'Bottom', '0', '25065.77']]
    columns = (1, 6)
    values = ('QX', 'Bottom')
    result = shayesteh.get_from_list_table(data, columns, values)
    assert list(result) == [['STORY5', 'QX', 'LinStatic', None, None, None, 'Bottom', '0', '0'],
            ['STORY4', 'QX', 'LinRespSpec', 'Max', None, None, 'Bottom', '0', '25065.77']]
    # len columns = 1
    columns = (6,)
    values = ('Bottom',)
    result = shayesteh.get_from_list_table(data, columns, values)
    assert list(result) == [['STORY5', 'QX', 'LinStatic', None, None, None, 'Bottom', '0', '0'],
            ['STORY4', 'QX', 'LinRespSpec', 'Max', None, None, 'Bottom', '0', '25065.77']]

@pytest.mark.slow
def test_get_drift_periods(shayesteh):
    Tx_drift, Ty_drift, file_name = shayesteh.get_drift_periods()
    # close_etabs(shayesteh)
    # assert pytest.approx(Tx_drift, .01) == 0.888
    # assert pytest.approx(Ty_drift, .01) == 0.738
    assert pytest.approx(Tx_drift, .01) == 1.085
    assert pytest.approx(Ty_drift, .01) == 1.085
    assert file_name.name == "test.EDB"

@pytest.mark.slow
def test_apply_cfactor_to_edb(shayesteh):
    building = create_building()
    NumFatalErrors = shayesteh.apply_cfactor_to_edb(building)
    ret = shayesteh.SapModel.Analyze.RunAnalysis()
    assert NumFatalErrors == 0
    assert ret == 0



@pytest.mark.getmethod
def test_get_diaphragm_max_over_avg_drifts(shayesteh):
    table = shayesteh.get_diaphragm_max_over_avg_drifts()
    assert len(table) == 20

@pytest.mark.getmethod
def test_get_magnification_coeff_aj(shayesteh):
    df = shayesteh.get_magnification_coeff_aj()
    assert len(df) == 20

def test_get_story_forces_with_percentages(shayesteh):
    forces, _ = shayesteh.get_story_forces_with_percentages()
    assert len(forces) == 10

def test_get_drifts(shayesteh):
    no_story, cdx, cdy = 4, 4.5, 4.5
    drifts, headers = shayesteh.get_drifts(no_story, cdx, cdy)
    assert len(drifts[0]) == len(headers)
    assert len(drifts) == 30

def test_calculate_drifts(shayesteh, mocker):
    mocker.patch(
        'etabs_api.etabs_obj.EtabsModel.get_drift_periods_calculate_cfactor_and_apply_to_edb',
        return_value = 0
    )
    no_story = 4
    widget = Mock()
    widget.final_building.x_system.cd = 4.5
    widget.final_building.y_system.cd = 4.5
    drifts, headers = shayesteh.calculate_drifts(
        widget, no_story, auto_no_story=False,auto_height=False)
    assert len(drifts[0]) == len(headers)

def test_get_irregularity_of_mass(shayesteh):
    iom, fields = shayesteh.get_irregularity_of_mass()
    assert len(iom) == 5
    assert len(iom[0]) == len(fields)

@pytest.mark.slow
def test_get_story_stiffness_modal_way(shayesteh, mocker):
    # dx = dy = {
    #             'STORY5' : 5,
    #             'STORY4' : 4,
    #             'STORY3' : 3,
    #             'STORY2' : 2,
    #             'STORY1' : 1,
    #         }
    # wx = wy = 1
    # mocker.patch(
    #     'etabs_api.database.DataBaseTables.get_stories_displacement_in_xy_modes',
    #     return_value = (dx, dy, wx, wy))
    # mocker.patch(
    #     'etabs_api.etabs_obj.EtabsModel.get_story_stiffness_modal_way',
    #     return_value = (
    #         ('STORY1', '1'),
    #         ('STORY2', '1'),
    #         ('STORY3', '1'),
    #         ('STORY4', '1'),
    #         ('STORY5', '1'),
    #         ))
    story_stiffness = shayesteh.get_story_stiffness_modal_way()
    assert len(story_stiffness) == 5
    assert story_stiffness == {
                            'STORY5':[4, 4],
                            'STORY4': [7, 7],
                            'STORY3': [9, 9],
                            'STORY2': [10, 10],
                            'STORY1': [15, 15],
                            }

def test_set_current_unit(shayesteh):
    shayesteh.set_current_unit('kgf', 'm')
    assert shayesteh.SapModel.GetPresentUnits_2()[:-1] == [5, 6, 2]
    assert shayesteh.SapModel.GetPresentUnits() == 8

def test_add_prefix_suffix_name(shayesteh):
    path = shayesteh.add_prefix_suffix_name(prefix='asli_', suffix='_x', open=False)
    assert path.name == 'asli_test_x.EDB'

def test_create_joint_shear_file(shayesteh):
    filename = get_temp_filepath(filename='js')
    df = shayesteh.create_joint_shear_file(file_name=filename.name, open_main_file=True)
    assert len(df) > 0


if __name__ == '__main__':
    import pandas as pd
    etabs = etabs_obj.EtabsModel(backup=False)
    etabs.test_write_aj()


