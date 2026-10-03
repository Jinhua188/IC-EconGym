"""Idempotently install this overlay into a local EconGym checkout.

Usage: python install_into_econgym.py PATH_TO_ECONGYM
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

MARKER = "# IC_ECONGYM_EXTENSION_DISPATCH_V1"
DISPATCH = '''# IC_ECONGYM_EXTENSION_DISPATCH_V1
if __name__ == "__main__":
    import sys as _ic_sys
    if any(arg == "--problem_scene" and i + 1 < len(_ic_sys.argv) and
           _ic_sys.argv[i + 1].startswith("ic_")
           for i, arg in enumerate(_ic_sys.argv)):
        from ic_extension.entrypoint import main as _ic_main
        _ic_sys.exit(_ic_main())

'''


def install(root: Path, include_upgrade: bool = False):
    source = Path(__file__).resolve().parent
    root = root.resolve()
    main = root / "main.py"
    if not main.is_file() or not (root / "env" / "env_core.py").is_file():
        raise FileNotFoundError(f"Not an EconGym checkout: {root}")
    for name in ("ic_extension", "cfg_ic", "scripts_ic"):
        destination = root / name
        shutil.copytree(source / name, destination, dirs_exist_ok=True)
    if include_upgrade:
        for name in ("learning", "calibration", "benchmark_splits"):
            shutil.copytree(source / name, root / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "training_scenarios.json", "locked_scenarios.json"))
        for name in ("requirements_learning.txt", "requirements_learning.lock.txt", "EXPERIMENT_UPGRADE.md"):
            shutil.copy2(source / name, root / name)
    original = main.read_text(encoding="utf-8")
    if MARKER not in original:
        main.write_text(DISPATCH + original, encoding="utf-8")
    print(f"IC extension installed in {root}")
    print("Run: python main.py --problem_scene ic_e1 --ic_periods 8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("econgym_root", type=Path)
    p.add_argument("--include-upgrade", action="store_true", help="Copy v0.3 learning checkpoints, proxies and locked splits")
    args = p.parse_args()
    install(args.econgym_root, args.include_upgrade)
