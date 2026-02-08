"""Entry point to run your DGBM optimization on an ETABS model.

This script lives inside the `etabs_api` mod folder, but it can import your
external optimization script (e.g. `DGBM.py`) from anywhere.

Typical usage (PowerShell):

  & "G:/Program Files/FreeCAD 0.19/bin/python.exe" run_optimization.py `
      --dgbm "G:/my_software/projects/optimization/DGBM.py" `
      --model "C:/path/to/model.EDB" `
      --software ETABS `
      --algo DGBM --popsize 20 --maxiter 50 --rounds 10

Notes / assumptions
- This script opens the model in a new ETABS instance by default.
- Your DGBM module is imported with `DGBM_SKIP_ETABS=1` to prevent it from
  auto-running at import time.
- If your DGBM code always creates its own EtabsModel instance internally, you
  may need to edit it to accept an existing `EtabsModel` (see message printed
  by this script if injection is not supported).
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Optional, Tuple


def _import_module_from_path(path: Path):
    """Import a module given a file path or folder containing it."""
    if path.is_dir():
        # Expect DGBM.py inside the folder
        candidate = path / "DGBM.py"
        if not candidate.exists():
            raise FileNotFoundError(f"Expected DGBM.py in folder: {path}")
        sys.path.insert(0, str(path))
        module_name = "DGBM"
    else:
        sys.path.insert(0, str(path.parent))
        module_name = path.stem

    # Prevent DGBM.py from auto-instantiating ETABS on import (if supported)
    os.environ.setdefault("DGBM_SKIP_ETABS", "1")
    return importlib.import_module(module_name)


def _guess_bounds(mod) -> Tuple[Any, Any]:
    """Try common global names for lower/upper bounds in the DGBM module."""
    candidates = [
        ("upper_bound", "lower_bound"),
        ("ub", "lb"),
        ("UB", "LB"),
    ]
    for ub_name, lb_name in candidates:
        if hasattr(mod, ub_name) and hasattr(mod, lb_name):
            return getattr(mod, ub_name), getattr(mod, lb_name)
    raise AttributeError(
        "Could not find bounds arrays in DGBM module. Expected one of: "
        "(upper_bound, lower_bound) or (ub, lb)."
    )


def _build_etabs_object(model_path: Optional[str], software: str, attach: bool):
    # Import locally so this script can be used outside FreeCAD too (if needed)
    import etabs_obj

    if attach:
        etabs = etabs_obj.EtabsModel(attach_to_instance=True, backup=False, software=software)
        if model_path:
            # If attaching and model_path given, open it in the attached instance.
            etabs.SapModel.File.OpenFile(str(model_path))
        return etabs

    return etabs_obj.EtabsModel(
        attach_to_instance=False,
        backup=False,
        software=software,
        model_path=model_path or "",
    )


def _instantiate_objective(mod, etabs) -> Any:
    if not hasattr(mod, "ETABSObjectiveFunction"):
        raise AttributeError("DGBM module has no ETABSObjectiveFunction class.")

    cls = mod.ETABSObjectiveFunction
    sig = inspect.signature(cls)

    # Try common injection styles
    kwargs = {}
    for param_name in sig.parameters:
        if param_name in ("etabs", "etabs_obj", "model", "etabsModel"):
            kwargs[param_name] = etabs
        elif param_name in ("SapModel", "sapModel", "sap_model"):
            kwargs[param_name] = etabs.SapModel

    try:
        return cls(**kwargs) if kwargs else cls()
    except TypeError as e:
        # Provide a helpful hint
        raise TypeError(
            "Failed to instantiate ETABSObjectiveFunction. "
            "Your DGBM.py likely creates/attaches to ETABS internally and does not accept an existing EtabsModel. "
            "Recommended minimal edit: change ETABSObjectiveFunction.__init__ to accept an optional `etabs` "
            "and use it instead of creating a new instance.\n\n"
            f"Original error: {e}"
        )


def run_from_python(
    *,
    dgbm_path: str,
    model_path: Optional[str] = None,
    software: str = "ETABS",
    attach: bool = True,
    algo: str = "DGBM",
    popsize: int = 20,
    maxiter: int = 50,
    rounds: int = 10,
    parasite: bool = False,
    objective_name: str = "objFunc_plus",
) -> int:
    """Run optimization programmatically (no argparse).

    This is intended for VS Code debug runs where you want to execute the file
    directly as Python (F5) without providing CLI arguments.

    Args are intentionally similar to the CLI flags.
    """

    dgbm_p = Path(dgbm_path).expanduser()
    if not dgbm_p.exists():
        raise FileNotFoundError(f"DGBM path not found: {dgbm_p}")

    model_p = str(Path(model_path).expanduser()) if model_path else None

    print(f"Opening model: {model_p or '(current open model)'}")
    etabs = _build_etabs_object(model_path=model_p, software=software, attach=attach)
    if not getattr(etabs, "success", False):
        print("ERROR: Failed to connect to ETABS")
        return 3

    print(f"Importing DGBM module from: {dgbm_p}")
    mod = _import_module_from_path(dgbm_p)

    print("Instantiating ETABSObjectiveFunction...")
    etabs_class = _instantiate_objective(mod, etabs)
    setattr(mod, "etabsClass", etabs_class)

    if hasattr(mod, "auto_config_from_etabs_model"):
        try:
            print("Running auto_config_from_etabs_model(etabs_obj=...)...")
            mod.auto_config_from_etabs_model(etabs_obj=etabs_class)
        except TypeError:
            mod.auto_config_from_etabs_model(etabs_class)

    # Rebuild bounds & module-level globals (names, beams_idx, etc.)
    # They were empty at import time because DGBM_SKIP_ETABS was set.
    if hasattr(mod, "setup_optimization_globals"):
        print("Rebuilding bounds & globals via setup_optimization_globals()...")
        mod.setup_optimization_globals(etabs_class)

    ub, lb = _guess_bounds(mod)

    if not hasattr(mod, objective_name):
        print(f"ERROR: objective function not found in DGBM module: {objective_name}")
        return 4
    objective = getattr(mod, objective_name)

    print(f"Running {algo}: popsize={popsize}, maxiter={maxiter}")
    if algo == "SOS":
        if not hasattr(mod, "SOS"):
            print("ERROR: DGBM module has no SOS()")
            return 5
        mod.SOS(popsize, maxiter, ub, lb, objective, verbose=True)
    else:
        if not hasattr(mod, "DGBM"):
            print("ERROR: DGBM module has no DGBM()")
            return 6
        mod.DGBM(popsize, maxiter, ub, lb, objective, rounds, boolParasite=parasite)

    print("Done.")
    return 0


def run_from_env_defaults(
    *,
    dgbm_path: str,
    model_path: Optional[str] = None,
    software: str = "ETABS",
    attach: bool = True,
    algo: str = "DGBM",
    popsize: int = 20,
    maxiter: int = 50,
    rounds: int = 10,
    parasite: bool = False,
    objective_name: str = "objFunc_plus",
) -> int:
    """Run with explicit arguments (debug-friendly helper).

    Despite the legacy name, this function does NOT read from `os.environ`.
    It is meant to be called directly from Python (e.g. when you press F5).
    """

    return run_from_python(
        dgbm_path=dgbm_path,
        model_path=model_path,
        software=software,
        attach=attach,
        algo=algo,
        popsize=popsize,
        maxiter=maxiter,
        rounds=rounds,
        parasite=parasite,
        objective_name=objective_name,
    )


def main(argv: Optional[list[str]] = None, in_command: bool = False) -> int:
    parser = argparse.ArgumentParser(description="Run DGBM optimization on an ETABS model")
    parser.add_argument("--dgbm", required=False, help="Path to DGBM.py or folder containing it")
    parser.add_argument(
        "--model",
        default=None,
        help="Path to model file (.EDB/.SDB/.FDB). If omitted, uses current open model when --attach",
    )
    parser.add_argument("--software", default="ETABS", choices=["ETABS", "SAP2000", "SAFE"], help="Target CSI software")
    # Default attach=True (debug-friendly). Use --no-attach to force starting a new instance.
    parser.add_argument(
        "--attach",
        dest="attach",
        action="store_true",
        default=True,
        help="Attach to an already running instance (default: true)",
    )
    parser.add_argument(
        "--no-attach",
        dest="attach",
        action="store_false",
        help="Start a new instance instead of attaching",
    )

    parser.add_argument("--algo", default="DGBM", choices=["DGBM", "SOS"], help="Which optimizer function to call")
    parser.add_argument("--popsize", type=int, default=20)
    parser.add_argument("--maxiter", type=int, default=50)
    parser.add_argument("--rounds", type=int, default=10, help="n_round (for DGBM screening)")
    parser.add_argument("--parasite", action="store_true", help="Enable parasite phase in DGBM")
    parser.add_argument("--objective", default="objFunc", help="Objective function name inside DGBM module")

    args = parser.parse_args(argv)

    # Debug-friendly defaults via environment variables.
    # This avoids argparse exiting early when running under VS Code debugger with no args.
    if not args.dgbm:
        args.dgbm = os.environ.get("DGBM_PATH")
    if not args.model:
        args.model = os.environ.get("ETABS_MODEL_PATH")
    if args.software == "ETABS":
        args.software = os.environ.get("ETABS_SOFTWARE", args.software)

    # Allow env override only when user didn't explicitly disable attach.
    if args.attach:
        env_attach = (os.environ.get("ETABS_ATTACH") or "").strip().lower()
        if env_attach in ("0", "false", "no", "n", "off"):
            args.attach = False

    if in_command and not args.dgbm:
        parser.error("--dgbm is required (or set DGBM_PATH env var)")

    if not args.dgbm:
        print("ERROR: Missing DGBM path.")
        print("Provide --dgbm on the command line, or set env var DGBM_PATH.")
        print("Example:")
        print('  $env:DGBM_PATH = "G:/my_software/projects/optimization/DGBM.py"')
        print('  $env:ETABS_MODEL_PATH = "C:/path/to/model.EDB"')
        print('  & "G:/Program Files/FreeCAD 0.19/bin/python.exe" run_optimization.py --algo DGBM --popsize 20 --maxiter 50 --rounds 10')
        return 2

    dgbm_path = Path(args.dgbm).expanduser()
    if not dgbm_path.exists():
        print(f"ERROR: DGBM path not found: {dgbm_path}")
        return 2

    model_path = None
    if args.model:
        model_path = str(Path(args.model).expanduser())

    # 1) Open/attach ETABS model
    print(f"Opening model: {model_path or '(current open model)'}")
    etabs = _build_etabs_object(model_path=model_path, software=args.software, attach=args.attach)
    if not getattr(etabs, "success", False):
        print("ERROR: Failed to connect to ETABS")
        return 3

    # 2) Import DGBM module (without auto-running)
    print(f"Importing DGBM module from: {dgbm_path}")
    mod = _import_module_from_path(dgbm_path)

    # 3) Build objective wrapper (etabsClass)
    print("Instantiating ETABSObjectiveFunction...")
    etabs_class = _instantiate_objective(mod, etabs)
    setattr(mod, "etabsClass", etabs_class)

    # 4) Auto-config if available (fills names, bounds, etc.)
    if hasattr(mod, "auto_config_from_etabs_model"):
        try:
            print("Running auto_config_from_etabs_model(etabs_obj=...)...")
            mod.auto_config_from_etabs_model(etabs_obj=etabs)
        except TypeError:
            # Some versions might not accept keyword
            mod.auto_config_from_etabs_model(etabs)

    # 5) Resolve bounds & objective
    ub, lb = _guess_bounds(mod)

    if not hasattr(mod, args.objective):
        print(f"ERROR: objective function not found in DGBM module: {args.objective}")
        return 4
    objective = getattr(mod, args.objective)

    # 6) Run
    print(f"Running {args.algo}: popsize={args.popsize}, maxiter={args.maxiter}")
    if args.algo == "SOS":
        if not hasattr(mod, "SOS"):
            print("ERROR: DGBM module has no SOS()")
            return 5
        mod.SOS(args.popsize, args.maxiter, ub, lb, objective, verbose=True)
    else:
        if not hasattr(mod, "DGBM"):
            print("ERROR: DGBM module has no DGBM()")
            return 6
        mod.DGBM(args.popsize, args.maxiter, ub, lb, objective, args.rounds, boolParasite=args.parasite)

    print("Done.")
    return 0


if __name__ == "__main__":
    # If called with CLI args, behave like a normal command.
    # If called with no args (common in debug runs), run from the config below.
    if sys.argv[1:]:
        raise SystemExit(main(in_command=True))

    # Edit these values for VS Code debug runs (F5).
    DEBUG_CONFIG = dict(
        dgbm_path=r"G:\my_software\projects\optimization\DGBM.py",
        model_path=None,
        software="ETABS",
        attach=True,
        algo="DGBM",
        popsize=20,
        maxiter=50,
        rounds=10,
        parasite=False,
        objective_name="objFunc_plus",
    )

    if not DEBUG_CONFIG["dgbm_path"]:
        print("ERROR: DEBUG_CONFIG['dgbm_path'] is empty.")
        print("- For debug runs: edit DEBUG_CONFIG in run_optimization.py")
        print("- For CLI runs: pass --dgbm ... (argparse)")
        raise SystemExit(2)

    raise SystemExit(run_from_env_defaults(**DEBUG_CONFIG))
