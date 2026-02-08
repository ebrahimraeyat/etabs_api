from pathlib import Path

import pandas as pd

from e2k_reader import E2KModel, tokenize_e2k_line


def test_tokenize_handles_double_quotes():
    line = 'TITLE1  "{""key"": 1, ""text"": ""a""}"'
    tokens = tokenize_e2k_line(line)
    assert tokens[0] == 'TITLE1'
    assert tokens[1].startswith('"') and tokens[1].endswith('"')


def test_parse_minimal_e2k(tmp_path: Path):
    content = '\n'.join([
        '$ CONTROLS',
        '  UNITS  "KGF"  "M"  "C"',
        '$ STORIES - IN SEQUENCE FROM TOP',
        '  STORY "Roof" HEIGHT 3.6 MASTERSTORY "Yes"',
        '  STORY "Base" ELEV 0',
        '$ POINT COORDINATES',
        '  POINT "1"  0 0',
        '  POINT "2"  1 0',
        '$ POINT ASSIGNS',
        '  POINTASSIGN  "1"  "Roof"  USERJOINT  "Yes"',
        '  POINTASSIGN  "2"  "Roof"  USERJOINT  "Yes"',
        '$ LINE CONNECTIVITIES',
        '  LINE "B1"  BEAM  "1"  "2"  0',
        '$ LINE ASSIGNS',
        '  LINEASSIGN "B1" "Roof" SECTION "B30X40" PROPMODI22 0.35',
        '$ FRAME SECTIONS',
        '  FRAMESECTION "B30X40"  MATERIAL "C30"  SHAPE "Concrete Rectangular"  D 0.4 B 0.3',
        '$ MATERIAL PROPERTIES',
        '  MATERIAL  "C30"    TYPE "Concrete"    WEIGHTPERVOLUME 2500',
        '  MATERIAL  "C30"    FC 30000000',
        '',
    ])

    p = tmp_path / 'm.e2k'
    p.write_text(content, encoding='utf-8')

    m = E2KModel(p)
    assert m.units == ('KGF', 'M', 'C')

    assert not m.stories.empty
    assert set(m.stories['Story']) == {'Roof', 'Base'}

    assert not m.points.empty
    assert m.get_point('1') == (0.0, 0.0, 0.0)

    assert not m.lines.empty
    assert list(m.iter_beams()) == ['B1']

    assert not m.point_assigns.empty
    assert set(m.point_assigns['Story']) == {'Roof'}

    assert not m.line_assigns.empty
    la = m.line_assigns.iloc[0]
    assert la['Line'] == 'B1'
    assert la['Story'] == 'Roof'
    assert la['SECTION'] == 'B30X40'

    assert not m.frame_sections.empty
    sec = m.frame_sections.loc[m.frame_sections['Section'] == 'B30X40'].iloc[0]
    assert sec['MATERIAL'] == 'C30'
    assert float(sec['D']) == 0.4
    assert float(sec['B']) == 0.3

    assert not m.materials.empty
    assert 'C30' in set(m.materials['Material'])
