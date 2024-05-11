import sys
from pathlib import Path


etabs_api_path = Path(__file__).absolute().parent.parent.parent
sys.path.insert(0, str(etabs_api_path))
from report import all_report as report

from freecad_funcs import open_file
from test.shayesteh import get_temp_filepath


def test_add_json_table_to_doc():
    json_file = etabs_api_path / 'test' / 'files' / 'json' / 'model_IrregularityOfMassModel.json'
    filename = get_temp_filepath(suffix='docx', filename='test')
    doc = report.add_json_table_to_doc(json_file=json_file)
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
    test_add_json_table_to_doc()