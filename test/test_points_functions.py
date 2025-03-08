import sys
from pathlib import Path
import tempfile

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

import etabs_obj
import points_functions
# from python_functions import get_temp_filepath

def create_test_file(etabs, suffix='EDB', filename='test'):
    temp_path = Path(tempfile.gettempdir())
    version = etabs.etabs_main_version
    test_file_path = temp_path / f"{filename}{version}.{suffix}"
    etabs.SapModel.File.Save(str(test_file_path))
    return etabs


def test_get_similar_points_in_two_models():
    filename = Path(etabs_api_path) / 'test' / 'files' / "shayesteh.EDB"
    print(filename)
    model1 = etabs_obj.EtabsModel(
            attach_to_instance=False,
            backup=False,
            software="ETABS",
            model_path=filename,
            )
    model1 = create_test_file(model1)
    model2 = etabs_obj.EtabsModel(
            attach_to_instance=False,
            backup=False,
            software="ETABS",
            model_path=filename,
            )
    model2 = create_test_file(model2)
    storyname_and_levels = model1.story.storyname_and_levels()
    for story, level in storyname_and_levels.items():
        ret = points_functions.get_similar_points_in_two_models(model1, model2, level, level)
        for p1, p2 in ret.items():
            assert p1 == p2
    model1.close_etabs()
    model2.close_etabs()

def test_transfer_loads_between_two_models():
    filename = Path(etabs_api_path) / 'test' / 'files' / "shayesteh.EDB"
    print(filename)
    model1 = etabs_obj.EtabsModel(
            attach_to_instance=False,
            backup=False,
            software="ETABS",
            model_path=filename,
            )
    model1 = create_test_file(model1)
    loadcase = model1.load_cases.get_loadcase_withtype(1)
    model2 = etabs_obj.EtabsModel(
            attach_to_instance=False,
            backup=False,
            software="ETABS",
            model_path=filename,
            )
    model2 = create_test_file(model2, filename='test2')
    storyname_and_levels = model1.story.storyname_and_levels()
    map_dict = {k: v for k, v in zip(loadcase, loadcase)}
    for story, level in storyname_and_levels.items():
        ret = points_functions.transfer_loads_between_two_models(model1, model2, level, level, map_dict)
        assert len(ret) == 0
    model1.close_etabs()
    model2.close_etabs()


if __name__ == '__main__':
    test_get_similar_points_in_two_models()



