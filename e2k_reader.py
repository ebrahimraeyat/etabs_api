from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import re

import pandas as pd


_QUOTED_TOKEN_RE = re.compile(r'"(?:[^"]|"")*"')


def _unquote_etabs(token: str) -> str:
    token = token.strip()
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        inner = token[1:-1]
        # ETABS doubles quotes inside strings: "" -> "
        return inner.replace('""', '"')
    return token


def tokenize_e2k_line(line: str) -> List[str]:
    """Tokenize a single E2K line.

    Handles quoted strings that may contain escaped quotes via doubled quotes.
    Examples:
      MATERIAL  "C30"  TYPE "Concrete"  WEIGHTPERVOLUME 2500
      TITLE1  "{\"\"key\"\": 1}"  (very long JSON-like text)
    """
    s = line.strip()
    if not s or s.startswith('$'):
        return []

    out: List[str] = []
    i = 0
    n = len(s)
    while i < n:
        # skip spaces
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break

        if s[i] == '"':
            m = _QUOTED_TOKEN_RE.match(s, i)
            if not m:
                # fall back: take until next quote
                j = i + 1
                while j < n and s[j] != '"':
                    j += 1
                out.append(s[i:j + 1] if j < n else s[i:])
                i = j + 1
            else:
                out.append(m.group(0))
                i = m.end()
        else:
            j = i
            while j < n and not s[j].isspace():
                j += 1
            out.append(s[i:j])
            i = j

    return out


def _try_float(s: str) -> Any:
    try:
        if s.lower() in {'nan', '+nan', '-nan'}:
            return float('nan')
        return float(s)
    except Exception:
        return s


def parse_key_value_tokens(tokens: List[str], start_index: int) -> Dict[str, Any]:
    """Parse tokens of the form KEY VALUE KEY VALUE ... into a dict.

    If an odd token remains at the end, it is interpreted as a boolean flag set to True.
    """
    d: Dict[str, Any] = {}
    i = start_index
    while i < len(tokens):
        key = tokens[i]
        if i + 1 >= len(tokens):
            d[key] = True
            break
        val = _unquote_etabs(tokens[i + 1])
        d[key] = _try_float(val)
        i += 2
    return d


@dataclass
class E2KModel:
    """Lightweight reader for ETABS .e2k text exports.

    This is NOT a full semantic ETABS model. It is a structured view of key
    tables (stories, points, lines, frame sections, materials) that is useful
    for offline QA and geometry/metadata queries.

    Limitations:
    - Design/analysis results are not in .e2k in a way that replaces running ETABS.
    - Some advanced tables are not parsed (yet).
    """

    e2k_path: Path

    # parsed outputs
    units: Optional[Tuple[str, str, str]] = None
    stories: pd.DataFrame = field(default_factory=pd.DataFrame)
    points: pd.DataFrame = field(default_factory=pd.DataFrame)
    point_assigns: pd.DataFrame = field(default_factory=pd.DataFrame)
    lines: pd.DataFrame = field(default_factory=pd.DataFrame)
    line_assigns: pd.DataFrame = field(default_factory=pd.DataFrame)
    areas: pd.DataFrame = field(default_factory=pd.DataFrame)
    frame_sections: pd.DataFrame = field(default_factory=pd.DataFrame)
    materials: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self) -> None:
        self.e2k_path = Path(self.e2k_path)
        self._parse()

    def _parse(self) -> None:
        stories: List[Dict[str, Any]] = []
        points: List[Dict[str, Any]] = []
        point_assigns: List[Dict[str, Any]] = []
        lines: List[Dict[str, Any]] = []
        line_assigns: List[Dict[str, Any]] = []
        areas: List[Dict[str, Any]] = []
        frame_sections: List[Dict[str, Any]] = []
        materials: List[Dict[str, Any]] = []

        current_block: Optional[str] = None

        with self.e2k_path.open('r', encoding='utf-8', errors='replace') as f:
            for raw in f:
                line = raw.rstrip('\n')
                if not line.strip():
                    continue

                if line.lstrip().startswith('$'):
                    current_block = line.strip().lstrip('$').strip()
                    continue

                tokens = tokenize_e2k_line(line)
                if not tokens:
                    continue

                rec = tokens[0].upper()

                # Controls / units
                if rec == 'UNITS' and len(tokens) >= 4:
                    self.units = (
                        _unquote_etabs(tokens[1]),
                        _unquote_etabs(tokens[2]),
                        _unquote_etabs(tokens[3]),
                    )
                    continue

                # Stories
                if rec == 'STORY' and len(tokens) >= 2:
                    name = _unquote_etabs(tokens[1])
                    row: Dict[str, Any] = {'Story': name}
                    row.update(parse_key_value_tokens(tokens, 2))
                    stories.append(row)
                    continue

                # Points
                if rec == 'POINT' and len(tokens) >= 4:
                    # POINT "id"  x  y  [z]
                    pid = _unquote_etabs(tokens[1])
                    x = _try_float(_unquote_etabs(tokens[2]))
                    y = _try_float(_unquote_etabs(tokens[3]))
                    z = _try_float(_unquote_etabs(tokens[4])) if len(tokens) >= 5 else 0.0
                    points.append({'Point': pid, 'X': x, 'Y': y, 'Z': z})
                    continue

                # Point assigns (per story)
                if rec == 'POINTASSIGN' and len(tokens) >= 3:
                    # POINTASSIGN "1" "Roof" USERJOINT "Yes" ...
                    pid = _unquote_etabs(tokens[1])
                    story = _unquote_etabs(tokens[2])
                    row = {'Point': pid, 'Story': story}
                    row.update(parse_key_value_tokens(tokens, 3))
                    point_assigns.append(row)
                    continue

                # Line connectivities
                if rec == 'LINE' and len(tokens) >= 6:
                    # LINE "B1" BEAM "2" "7" 0
                    lname = _unquote_etabs(tokens[1])
                    ltype = tokens[2].upper()  # BEAM/COLUMN/BRACE/etc.
                    pi = _unquote_etabs(tokens[3])
                    pj = _unquote_etabs(tokens[4])
                    try:
                        extra = int(float(tokens[5]))
                    except Exception:
                        extra = tokens[5]
                    lines.append({'Line': lname, 'Type': ltype, 'PointI': pi, 'PointJ': pj, 'Extra': extra})
                    continue

                # Line assigns (per story)
                if rec == 'LINEASSIGN' and len(tokens) >= 3:
                    # LINEASSIGN "B2" "Roof" SECTION "B40X40" PROPMODI22 0.35 ...
                    lname = _unquote_etabs(tokens[1])
                    story = _unquote_etabs(tokens[2])
                    row = {'Line': lname, 'Story': story}
                    row.update(parse_key_value_tokens(tokens, 3))
                    line_assigns.append(row)
                    continue

                # Area connectivities
                if rec == 'AREA' and len(tokens) >= 5:
                    # AREA "F1" FLOOR 5 "2" "10" ...
                    aname = _unquote_etabs(tokens[1])
                    atype = tokens[2].upper()
                    # the rest is variable-length; store as raw tokens
                    areas.append({'Area': aname, 'Type': atype, 'Tokens': [ _unquote_etabs(t) for t in tokens[3:] ]})
                    continue

                # Frame sections
                if rec == 'FRAMESECTION' and len(tokens) >= 2:
                    sec = _unquote_etabs(tokens[1])
                    row = {'Section': sec}
                    row.update(parse_key_value_tokens(tokens, 2))
                    frame_sections.append(row)
                    continue

                # Materials
                if rec == 'MATERIAL' and len(tokens) >= 2:
                    mname = _unquote_etabs(tokens[1])
                    row = {'Material': mname}
                    row.update(parse_key_value_tokens(tokens, 2))
                    materials.append(row)
                    continue

                # Everything else: ignore.
                _ = current_block

        self.stories = pd.DataFrame(stories)
        self.points = pd.DataFrame(points)
        self.point_assigns = pd.DataFrame(point_assigns)
        self.lines = pd.DataFrame(lines)
        self.line_assigns = pd.DataFrame(line_assigns)
        self.areas = pd.DataFrame(areas)
        self.frame_sections = pd.DataFrame(frame_sections)
        self.materials = pd.DataFrame(materials)

    # Convenience APIs -------------------------------------------------

    def get_point(self, point_id: str) -> Tuple[float, float, float]:
        df = self.points
        if df.empty:
            raise KeyError(f'No points parsed: {point_id}')
        row = df.loc[df['Point'] == str(point_id)]
        if row.empty:
            raise KeyError(f'Point not found: {point_id}')
        r0 = row.iloc[0]
        return float(r0['X']), float(r0['Y']), float(r0['Z'])

    def get_line_endpoints(self, line_name: str) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        df = self.lines
        row = df.loc[df['Line'] == str(line_name)]
        if row.empty:
            raise KeyError(f'Line not found: {line_name}')
        r0 = row.iloc[0]
        p1 = self.get_point(str(r0['PointI']))
        p2 = self.get_point(str(r0['PointJ']))
        return p1, p2

    def iter_beams(self) -> Iterable[str]:
        if self.lines.empty:
            return iter(())
        return (str(x) for x in self.lines.loc[self.lines['Type'] == 'BEAM', 'Line'].tolist())

    def iter_columns(self) -> Iterable[str]:
        if self.lines.empty:
            return iter(())
        return (str(x) for x in self.lines.loc[self.lines['Type'] == 'COLUMN', 'Line'].tolist())
