import json
from pathlib import Path
from typing import Union


try:
    from docx.shared import Inches
except ImportError:
    import freecad_funcs
    package = 'python-docx'
    freecad_funcs.install_package(package)

import docx
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

etabs_api_path = Path(__file__).absolute().parent.parent


def add_table_figure(
        doc,
        caption: str,
        type_: str='Table ', # 'Figure '
        ):
    paragraph = doc.add_paragraph(type_, style='Caption')
    run = run = paragraph.add_run()
    r = run._r
    feild_charachter = OxmlElement('w:fldChar')
    feild_charachter.set(qn('w:fldCharType'), 'begin')
    r.append(feild_charachter)
    instr_text = OxmlElement('w:instrText')
    instr_text.text = f' SEQ {type_}\* ARABIC'
    r.append(instr_text)
    feild_charachter = OxmlElement('w:fldChar')
    feild_charachter.set(qn('w:fldCharType'), 'end')
    r.append(feild_charachter)
    paragraph.add_run(f': {caption} ')

def add_json_table_to_doc(
                          json_file: str,
                          doc=None,
                          caption: str='',
                       ):
    # create a new document
    if doc is None:
        doc = create_doc()
    try:
        with open(json_file, 'r') as file:
            json_table = json.load(file)
    except json.JSONDecodeError:
        return doc
    table_style = 'List Table 4 Accent 5'
    if isinstance(json_table, list):
        cols = json_table[-1].get('col') + 1
        rows = json_table[-1].get('row') + 1
        table_docx = doc.add_table(rows=rows, cols=cols)
        table_docx.style = table_style
        # write the the table to doc
        for d in json_table:
            row = d.get('row')
            col = d.get('col')
            text = d.get('text')
            color = d.get('color')
            cell = table_docx.cell(row, col)
            cell.text = text
            if row == 0:  # Set header text to bold
                run = cell.paragraphs[0].runs[0]
                run.bold = True
                run.italic = True
                shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), "#244061"))
                cell._tc.get_or_add_tcPr().append(shading_elm)
            elif color:   # write the data to the remaining rows of the table
                shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), color))
                cell._tc.get_or_add_tcPr().append(shading_elm)
    if isinstance(json_table, dict) and "settings" in str(json_file):
        pass

    add_table_figure(doc=doc, caption=caption, type_='Table ')
    return doc

def create_doc():
    filepath = etabs_api_path / 'report' / 'templates' / 'beam_deflections.docx'
    doc = docx.Document(str(filepath))
    return doc

def create_report(
                etabs=None,
                filename: str = None,
                doc: 'docx.Document' = None,
                results_path: Union[Path, None]=None,
                ):
    if etabs is None and results_path is None:
        return
    if etabs is not None:
        results_path = etabs.get_filepath() / "table_results"
        if not results_path.exists():
            return
    if doc is None:
        doc = create_doc()
    for file in results_path.glob('*.json'):
        doc.add_paragraph()
        caption = ''.join(file.name.split('_')[1:]).rstrip('.json')
        caption = caption.replace('Model', "").replace("Table", "")
        result = ""
        for i, char in enumerate(caption):
            if char.isupper() and i > 0:
                result += " " + char
            else:
                result += char
        doc = add_json_table_to_doc(json_file=file, doc=doc, caption=result)
    if filename is None:
        filename = results_path / 'all_reports.docx'
    doc.save(filename)
    return doc




