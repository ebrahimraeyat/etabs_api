# AGENTS.md

Python package that drives **CSI ETABS / SAFE / SAP2000** structural-analysis software over COM (Windows-only). It ships as a [FreeCAD](https://www.freecad.org/) workbench dependency and as a pip package (`etabs-api`). See [README.md](README.md) for the public quick-start.

## Architecture

- **`EtabsModel` in [etabs_obj.py](etabs_obj.py) is the central facade.** Its `__init__` opens the COM connection (`self.SapModel = self.etabs.SapModel`) and composes ~20 domain modules as attributes: `self.database`, `self.load_patterns`, `self.load_cases`, `self.load_combinations`, `self.frame_obj`, `self.points`, `self.story`, `self.area`, `self.material`, `self.design`, `self.group`, etc.
- **One manager class per source file.** Each class takes the `EtabsModel` in its constructor and caches `self.etabs` (back-reference) and `self.SapModel` (raw COM handle). Modules cross-call each other through the facade, e.g. `self.etabs.database.read(...)` from inside another module.
- **Two constructor signatures coexist.** Legacy modules use `__init__(self, SapModel=None, etabs=None)` — that is why `EtabsModel` instantiates them as `DatabaseTables(None, self)`. Newer modules use `__init__(self, etabs=None)`. Match the existing signature of the file you edit.
- **One class serves ETABS/SAFE/SAP2000.** Software type is `self.software`; branch with `if self.software == "ETABS": ... elif self.software == "SAP2000": ...`. The COM helper interface is built dynamically via `exec()` / `QueryInterface` so a single code path serves all three.
- **[find_etabs.py](find_etabs.py)** (`find_etabs.find_etabs(run, backup)`) is the real entry point used by FreeCAD — it reconnects to a running instance via a stored PID/moniker, then falls back to attach/browse. This is the canonical way to obtain an `etabs` object.
- **[csi_safe/safe.py](csi_safe/safe.py)** is separate: a text parser/writer for SAFE `.f2k` files (no COM). [create_f2k.py](create_f2k.py) subclasses it to export a live ETABS model to SAFE.

## Critical conventions

- **Flat absolute imports only.** There are NO `__init__.py` files; modules import siblings by bare name (`import etabs_obj`, `from csi_safe import safe`). Scripts and tests must `sys.path.insert(0, <repo-root>)`. **Edit the root-level `*.py` files — `src/etabs_api/` is vestigial scaffolding, not the real package.**
- **Set units before numeric read/write:** `etabs.set_current_unit('kgf', 'm')` (or `'N', 'mm'`). Most data methods call this first.
- **Bulk data goes through DatabaseTables** ([database.py](database.py)): `etabs.database.read(table_key, to_dataframe=True)` / `etabs.database.write(table_key, df)`. Data is reshaped between flat COM arrays and pandas DataFrames.
- **Respect version-dependent column names.** `set_special_values_according_to_software_and_version()` sets attributes for table column names that differ across ETABS versions (e.g. `'Is Auto Load'` vs `'IsAuto'`). Use those attributes — never hardcode the strings.
- **COM return values** are tuples/lists where the **last element is a status code** (`0` = success), e.g. `read_table` returns `(_, _, fields, _, data, _)`. Catch `comtypes.COMError` / `OSError` around connection code.
- **Model lock state matters:** writes auto-unlock; analysis checks `GetModelIsLocked()` first. Helpers: `lock_model`, `unlock_model`, `lock_and_unlock_model`.
- **Defensive optional imports.** FreeCAD / `Part` / `PySide` and tools like `pywinauto` may be absent; guard them with `try/except ModuleNotFoundError` (existing pattern). [freecad_funcs.py](freecad_funcs.py) holds the FreeCAD geometry/UI helpers.
- **Style:** `snake_case` functions, `PascalCase` classes, pandas-heavy, type hints in newer/pure modules (`e2k_reader.py`, `frame_obj.py`) but sparse in older COM wrappers. Don't add annotations/docstrings to code you didn't change.

## Testing

- Tests live in [test/](test/) (one `test_*.py` per module). Config is [test/pytest.ini](test/pytest.ini); markers: `getmethod`, `slow`, `section`, `selectmethod`. There is **no `conftest.py`** — [test/shayesteh.py](test/shayesteh.py) is the shared fixture helper.
- **Most tests require a live ETABS install on Windows.** Importing `shayesteh` immediately attaches/launches ETABS. Tests use the `@open_etabs_file('shayesteh.EDB')` decorator (software inferred from extension) and a global `etabs` object; originals in `test/files/` are never mutated (a `test{version}.<ext>` copy is saved to temp).
- Run from the `test/` directory: `pytest` or `pytest test_database.py`. Env knobs: `software_version` (default `21`), `software_name` (default `ETABS`).
- **Offline tests** (no ETABS, cross-platform) import pure functions directly and skip `shayesteh`: [test/test_load_combinations_without_etabs.py](test/test_load_combinations_without_etabs.py) and [test/test_e2k_reader.py](test/test_e2k_reader.py). Use these patterns when adding logic that doesn't need COM. Assert floats with `pytest.approx`.

## Gotchas

- Run [clear_comtypes_cache.py](clear_comtypes_cache.py) when comtypes import/interface errors appear after an ETABS version change (stale generated `gen` cache).
- Hard-coded absolute paths exist in test/setup helpers (`G:\program files\...` for ETABS and FreeCAD) — environment-specific.
- Dependencies: `comtypes`, `pandas`, `psutil`, `numpy`, `math2docx` (see [pyproject.toml](pyproject.toml)); Python `>=3.8`, Windows only. `pytest`/`FreeCAD` are assumed-present, not declared deps.
