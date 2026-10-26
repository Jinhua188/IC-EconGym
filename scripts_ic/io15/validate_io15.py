"""Check that the derived IO15 files still match the three supplied workbooks."""
from pathlib import Path
import csv
import hashlib
import json
import math
import os

import numpy as np

ROOT = Path(os.environ.get("IC_ECONGYM_SOURCE_DIR", Path(__file__).resolve().parents[3]))
OUT = Path(os.environ.get("IC_ECONGYM_IO15_DIR", ROOT / "outputs" / "io_15_2018_2020_2023"))
audit = json.loads((OUT / "audit.json").read_text(encoding="utf-8"))
with (OUT / "metrics_by_year.csv").open(encoding="utf-8-sig", newline="") as stream:
    metrics = {int(row["year"]): row for row in csv.DictReader(stream)}
assert set(metrics) == {2018, 2020, 2023}
for key, meta in audit.items():
    year = int(key)
    source = ROOT / meta["source"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == meta["sha256"], source
    with np.load(OUT / f"io57_{year}.npz") as data:
        z, x, va = data["z_competitive"], data["gross_output"], data["value_added"]
        intra = data["ic15_intermediate"]
        assert z.shape == (57, 57) and x.shape == (57,) and intra.shape == (15, 15)
        assert np.array_equal(z[:15, :15], intra)
        assert np.max(np.abs(z.sum(axis=0) + va - x)) < 2e-5
        assert math.isclose(float(x[:15].sum()), float(metrics[year]["ic_gross_output_wanyuan"]), rel_tol=1e-12)
        assert math.isclose(float(intra.sum()), float(metrics[year]["ic_to_ic_intermediate_wanyuan"]), rel_tol=1e-12)
print("PASS: three source hashes, 57×57/15×15 shapes, column balances and published totals")
