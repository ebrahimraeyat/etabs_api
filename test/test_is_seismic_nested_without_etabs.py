import sys
from pathlib import Path

etabs_api_path = Path(__file__).parent.parent
sys.path.insert(0, str(etabs_api_path))

import load_combinations


class RespCombo:
    def __init__(self, combos):
        self.combos = combos

    def GetNameList(self):
        names = tuple(self.combos)
        return (len(names), names, 0)

    def GetCaseList(self, name):
        types, names, sf = self.combos[name]
        return (len(names), types, names, sf, 0)

    def Add(self, name, type_):
        self.combos[name] = ((), (), ())
        return 0

    def SetCaseList(self, combo, cname_type, case_name, sf):
        types, names, sfs = self.combos.get(combo, ((), (), ()))
        self.combos[combo] = (
            types + (cname_type,),
            names + (case_name,),
            sfs + (sf,),
        )
        return 0


class LoadPatterns:
    def GetLoadType(self, name):
        return ({'QX': 5, 'DEAD': 1, 'LIVE': 3}.get(name, 0), 0)


class StaticLinear:
    def __init__(self, static_loads):
        self.static_loads = static_loads

    def GetLoads(self, name):
        pats = self.static_loads.get(name, [])
        return (
            len(pats),
            tuple('Load' for _ in pats),
            tuple(pats),
            tuple(1.0 for _ in pats),
            0,
        )


class LoadCases:
    def __init__(self, case_types, static_loads):
        self._case_types = case_types
        self.StaticLinear = StaticLinear(static_loads)
        self.StaticNonlinear = self.StaticLinear

    def GetTypeOAPI(self, name):
        t = self._case_types.get(name)
        if t is None:
            return (0, 0, 1)
        return (t, 0, 0, 0, 0, 0)


class SapModel:
    def __init__(self, combos, case_types, static_loads):
        self.RespCombo = RespCombo(combos)
        self.LoadCases = LoadCases(case_types, static_loads)
        self.LoadPatterns = LoadPatterns()


class FakeEtabs:
    def __init__(self, sap):
        self.SapModel = sap


def _make_lc(combos, seismic_cases=None):
    case_types = {'DEAD': 1, 'SDL': 1, 'QX': 1, 'LIVE': 1}
    static_loads = {
        'DEAD': ['DEAD'],
        'SDL': ['DEAD'],
        'QX': ['QX'],
        'LIVE': ['LIVE'],
    }
    lc = load_combinations.LoadCombination(
        FakeEtabs(SapModel(combos, case_types, static_loads))
    )

    class LoadCasesFacade:
        def get_seismic_load_cases(self):
            return list(seismic_cases or [])

    lc.etabs.load_cases = LoadCasesFacade()
    return lc


def test_nested_seismic_and_gravity():
    # Mirrors user model: parent = gravity child + seismic child
    combos = {
        'G + 0.15Q': ((0, 0), ('DEAD', 'LIVE'), (1.0, 0.15)),
        '-100X30Y': ((0, 0), ('QX', 'DEAD'), (-1.0, 0.3)),
        '-100X30Y + G + 0.15Q': ((1, 1), ('G + 0.15Q', '-100X30Y'), (1.0, 1.0)),
        'NESTED_GRAV': ((1,), ('G + 0.15Q',), (1.0,)),
        # Mis-tagged nested member as load case type 0, but name is a combo.
        'MIS_TAGGED': ((0, 0), ('G + 0.15Q', '-100X30Y'), (1.0, 1.0)),
    }
    lc = _make_lc(combos)
    assert lc.is_seismic('G + 0.15Q') is False
    assert lc.is_seismic('-100X30Y') is True
    assert lc.is_seismic('-100X30Y + G + 0.15Q') is True
    assert lc.is_seismic('NESTED_GRAV') is False
    assert lc.is_seismic('MIS_TAGGED') is True


def test_known_seismic_combo_short_circuits_parent():
    combos = {
        'CHILD_SEIS': ((0,), ('QX',), (1.0,)),
        'PARENT': ((1,), ('CHILD_SEIS',), (1.0,)),
    }
    lc = _make_lc(combos)
    known = {'CHILD_SEIS'}
    assert lc.is_seismic('PARENT', seismic_load_combos=known) is True
    assert 'PARENT' in known


def test_add_load_combination_marks_nested_members():
    combos = {
        'G': ((0,), ('DEAD',), (1.0,)),
        'EQ': ((0,), ('QX',), (1.0,)),
    }
    lc = _make_lc(combos)
    lc.add_load_combination('PUSH', ['G', 'EQ'], 1.0, type_=1)
    assert combos['PUSH'][0] == (1, 1)
    assert combos['PUSH'][1] == ('G', 'EQ')
    assert lc.is_seismic('PUSH') is True


def test_get_load_combinations_of_type_nested():
    combos = {
        'G + 0.15Q': ((0,), ('DEAD',), (1.0,)),
        '-100X30Y': ((0,), ('QX',), (1.0,)),
        '-100X30Y + G + 0.15Q': ((1, 1), ('G + 0.15Q', '-100X30Y'), (1.0, 1.0)),
        'NESTED_GRAV': ((1,), ('G + 0.15Q',), (1.0,)),
    }
    lc = _make_lc(combos)
    all_names = list(combos)
    seismic = lc.get_load_combinations_of_type('SEISMIC', all_names)
    gravity = lc.get_load_combinations_of_type('GRAVITY', all_names)
    assert set(seismic) == {'-100X30Y', '-100X30Y + G + 0.15Q'}
    assert set(gravity) == {'G + 0.15Q', 'NESTED_GRAV'}


def test_get_seismic_load_combinations_memoizes_children():
    combos = {
        'G + 0.15Q': ((0,), ('DEAD',), (1.0,)),
        '-100X30Y': ((0,), ('QX',), (1.0,)),
        '-100X30Y + G + 0.15Q': ((1, 1), ('G + 0.15Q', '-100X30Y'), (1.0, 1.0)),
        'Max Env': ((1,), ('-100X30Y + G + 0.15Q',), (1.0,)),
    }
    lc = _make_lc(combos)
    seismic = lc.get_seismic_load_combinations(list(combos))
    assert seismic == {
        '-100X30Y',
        '-100X30Y + G + 0.15Q',
        'Max Env',
    }
