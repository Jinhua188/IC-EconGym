"""Compare a genuinely independent 2020 sector output source with the IO baseline.

Required CSV columns: sector_id, observed_annual_output_wanyuan, source_name,
source_year, measurement_scope. The CSV must be independent of the source IO
workbook and use the same 13-sector definitions. No fallback observations are
fabricated when these conditions cannot be met.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from ic_extension.entrypoint import load_task
from ic_extension.model import ICEnvironment, N


REQUIRED = {"sector_id", "observed_annual_output_wanyuan", "source_name",
            "source_year", "measurement_scope"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    with args.observed.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED <= set(reader.fieldnames or []):
            parser.error(f"missing required columns: {sorted(REQUIRED - set(reader.fieldnames or []))}")
        records = list(reader)
    ids = [int(r["sector_id"]) for r in records]
    if sorted(ids) != list(range(1, N + 1)):
        parser.error("all 13 sector IDs must appear exactly once")
    if any(int(r["source_year"]) != 2020 for r in records):
        parser.error("source_year must be 2020 for baseline comparison")
    if any(not r["source_name"].strip() or not r["measurement_scope"].strip() for r in records):
        parser.error("source name and measurement scope must be documented")
    records = sorted(records, key=lambda x: int(x["sector_id"]))
    observed = np.array([float(r["observed_annual_output_wanyuan"]) for r in records])
    if not np.all(np.isfinite(observed)) or np.any(observed <= 0):
        parser.error("observed output must be finite and positive")
    env = ICEnvironment(load_task("ic_r1"))
    modeled = env.q0 * 4
    rows = [{"sector_id": i + 1, "sector_label": env.labels[i],
             "modeled_annual_output_wanyuan": float(modeled[i]),
             "observed_annual_output_wanyuan": float(observed[i]),
             "absolute_percentage_error": float(abs(modeled[i] - observed[i]) / observed[i]),
             "source_name": records[i]["source_name"],
             "measurement_scope": records[i]["measurement_scope"]}
            for i in range(N)]
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "external_baseline_comparison.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"source_path": str(args.observed.resolve()), "source_year": 2020,
              "mean_absolute_percentage_error": float(np.mean([r["absolute_percentage_error"] for r in rows])),
              "comparability_warning": "This statistic is meaningful only if the external sector definitions and output valuation match the IO sectors; the script checks schema, not source independence."}
    (args.out / "comparison_metadata.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
