"""Allocate competitive-table imports to uses under three explicit scenarios.

The source tables identify imports by product, not by purchaser.  These
allocations are assumptions and are never treated as observed transactions.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(os.environ.get("IC_ECONGYM_IO15_DIR", Path(__file__).resolve().parents[3] / "outputs" / "io_15_2018_2020_2023"))
CASES = ("proportional", "intermediate_first", "final_first")


def allocate_pool(remaining: float, capacity: np.ndarray) -> np.ndarray:
    amount = min(remaining, float(capacity.sum()))
    if amount <= 0:
        return np.zeros_like(capacity)
    return capacity * (amount / capacity.sum())


def split_row(z: np.ndarray, y: np.ndarray, imported: float, mode: str):
    # Negative inventory changes are stock withdrawals, not import demand.
    # Exports are reserved for domestic production in these scenarios.
    eligible_y = np.maximum(y[:3], 0.0)
    if mode == "proportional":
        pool = np.r_[z, eligible_y]
        take = allocate_pool(imported, pool)
        mz, my = take[:len(z)], np.r_[take[len(z):], 0.0]
    else:
        first, second = (z, eligible_y) if mode == "intermediate_first" else (eligible_y, z)
        a = allocate_pool(imported, first)
        b = allocate_pool(imported - float(a.sum()), second)
        if mode == "intermediate_first":
            mz, my = a, np.r_[b, 0.0]
        else:
            mz, my = b, np.r_[a, 0.0]
    if not np.isclose(mz.sum() + my.sum(), imported, rtol=0, atol=1e-5):
        raise ValueError("Import volume exceeds eligible uses")
    return mz, my


def build(year: int, mode: str) -> dict:
    with np.load(HERE / f"io57_{year}.npz") as source:
        z = source["z_competitive"]
        y = source["final_use"]
        imports = source["imports"]
        x = source["gross_output"]
        va = source["value_added"]
    zm = np.empty_like(z)
    ym = np.empty_like(y)
    for i in range(57):
        zm[i], ym[i] = split_row(z[i], y[i], float(imports[i]), mode)
    zd, yd = z - zm, y - ym
    checks = {
        "competitive_z": float(np.max(np.abs(zd + zm - z))),
        "competitive_y": float(np.max(np.abs(yd + ym - y))),
        "import_rows": float(np.max(np.abs(zm.sum(axis=1) + ym.sum(axis=1) - imports))),
        "domestic_rows": float(np.max(np.abs(zd.sum(axis=1) + yd.sum(axis=1) - x))),
        "input_columns": float(np.max(np.abs(zd.sum(axis=0) + zm.sum(axis=0) + va - x))),
    }
    if max(checks.values()) > 1e-3 or np.any(zd < -1e-5) or np.any(zm < -1e-5) or np.any(ym < -1e-5):
        raise ValueError(f"Accounting check failed: {year} {mode} {checks}")
    path = HERE / f"io_use_15_{year}_{mode}.npz"
    np.savez_compressed(path, z_domestic=zd, z_import=zm, y_domestic=yd,
                        y_import=ym, x=x, value_added=va, imports=imports)
    return {"year": year, "case": mode, "checks_max_abs_wanyuan": checks,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    results = [build(year, mode) for year in (2018, 2020, 2023) for mode in CASES]
    (HERE / "dynamic_input_audit.json").write_text(json.dumps({
        "allocation_status": "scenario assumption; product imports are observed but purchaser uses are unidentified",
        "export_rule": "zero assigned imports to exports",
        "negative_inventory_rule": "domestic stock withdrawal; excluded from eligible import uses",
        "units": "current-price RMB 10,000 per year",
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(results), "max_residual": max(max(r["checks_max_abs_wanyuan"].values()) for r in results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
