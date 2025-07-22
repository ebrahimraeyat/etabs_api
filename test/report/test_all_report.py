import sys
from pathlib import Path
import json


etabs_api_path = Path(__file__).absolute().parent.parent.parent
sys.path.insert(0, str(etabs_api_path))
from report import all_report as report

from freecad_funcs import open_file
from test.shayesteh import get_temp_filepath


def test_model_settings_report():
    # Path to your manually provided JSON
    json_file = etabs_api_path / 'test' / 'files' / 'json' / 'des27_model_settings.json'
    filename = get_temp_filepath(suffix='docx', filename='test_model_settings')
    doc = report.create_doc()
    report.add_model_settings_report(doc, json_file)
    doc.save(filename)
    assert filename.exists()
    open_file(filename)


def test_add_json_table_to_doc():
    json_file = etabs_api_path / 'test' / 'files' / 'json' / 'IrregularityOfMassModel.json'
    filename = get_temp_filepath(suffix='docx', filename='test')
    doc = report.add_json_table_to_doc(json_file=json_file)
    doc.save(filename)
    assert filename.exists()
    open_file(filename)

def test_add_earthquake_factor_formulation_section():
    doc = report.add_earthquake_factor_formulation_section()
    filename = get_temp_filepath(suffix='docx', filename='test')
    doc.save(filename)
    assert filename.exists()
    open_file(filename)

def test_add_earthquake_factor_explanations_section():
    json_file = etabs_api_path / 'test' / 'files' / 'json' / 'des27_model_settings.json'
    d = json.loads(json_file.read_text())
    from exporter import civiltools_config
    building = civiltools_config.current_building_from_config(d)
    filename = get_temp_filepath(suffix='docx', filename='test')
    doc = report.create_doc()
    doc = report.add_earthquake_factor_explanations_section(doc, building)
    doc.save(filename)
    assert filename.exists()
    open_file(filename)

def test_create_report():
    results_path = etabs_api_path / 'test' / 'files' / 'json'
    filename = get_temp_filepath(suffix='docx', filename='test1')
    report.create_report(
        filename=filename,
        results_path=results_path,
    )
    assert filename.exists()
    open_file(filename)

    
if __name__ == "__main__":
    test_add_html_explanations_section()