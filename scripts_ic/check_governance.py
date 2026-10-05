"""Validate governance, public artifact integrity and explicit publication gates.

This command does not create tags, releases or DOIs, or perform a rights review.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = (
    "https://raw.githubusercontent.com/citation-file-format/citation-file-format/"
    "396f738fb025b1d8acdb02a56ffc923f95dc8999/schema.json"
)
SCHEMA_SHA256 = "0b8d22140da702d766df318dcff3a91af2f39521298dcf36d76315fd99cc169b"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def check_hashes(filename: str, full_public_snapshot: bool = False) -> int:
    entries = {}
    for line in (ROOT / filename).read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"Invalid hash: {relative}")
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT) and path.is_file(), f"Invalid artifact path: {relative}")
        require(relative not in entries, f"Duplicate hash entry: {relative}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"Hash mismatch: {relative}")
        entries[relative] = digest
    require(bool(entries), f"Empty manifest: {filename}")
    if full_public_snapshot:
        output = subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
        ).decode("utf-8")
        actual = {name for name in output.split("\0") if name and (ROOT / name).is_file()}
        actual.discard("MANIFEST.sha256")
        require(set(entries) == actual,
                f"Manifest coverage mismatch; missing={sorted(actual-set(entries))[:5]}, "
                f"extra={sorted(set(entries)-actual)[:5]}")
    return len(entries)


def engineering_checks(schema_file: Path | None) -> dict:
    required = [
        "README.md", "LICENSE", "LICENSE_SCOPE.md", "NOTICE", "CITATION.cff",
        "CONTRIBUTING.md", "GOVERNANCE.md", "ROADMAP.md", "SECURITY.md",
        "RELEASE_v0.3.0.md", "ZENODO_RELEASE_GUIDE.md", "GITHUB_SETTINGS_CHECKLIST.md",
        "RIGHTS_REGISTRY.csv", "RELEASE_READINESS.json", "AUTHOR_METADATA.md",
        "RESEARCH_SNAPSHOT.sha256", ".github/CODEOWNERS", ".github/PULL_REQUEST_TEMPLATE.md",
    ]
    require(all((ROOT / path).is_file() for path in required), "Missing governance files")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    require(re.fullmatch(r"\d+\.\d+\.\d+", version) is not None, "Invalid VERSION")
    # BaseLoader preserves date and numeric scalars as strings, matching CFF YAML semantics.
    cff = yaml.load((ROOT / "CITATION.cff").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if schema_file:
        schema_bytes = schema_file.read_bytes()
    else:
        with urlopen(SCHEMA_URL, timeout=30) as response:
            schema_bytes = response.read()
    require(hashlib.sha256(schema_bytes).hexdigest() == SCHEMA_SHA256, "CFF schema identity mismatch")
    schema = json.loads(schema_bytes)
    jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker()).validate(cff)
    require(cff["version"] == version, "CFF/VERSION mismatch")
    require(cff["license"] == "Apache-2.0", "Unexpected software-license metadata")
    readiness = read_json("RELEASE_READINESS.json")
    require(readiness["version"] == version, "Readiness/VERSION mismatch")
    require(not (ROOT / ".zenodo.json").exists(), "Conflicting Zenodo metadata source")
    with (ROOT / "RIGHTS_REGISTRY.csv").open(encoding="utf-8-sig", newline="") as stream:
        rights = list(csv.DictReader(stream))
    expected_categories = {
        "original_code", "operational_docs", "task_configuration", "processed_io",
        "ai_proxies", "source_registries", "external_series", "checkpoints",
        "simulation_artifacts", "manuscript", "generated_site", "raw_inputs",
    }
    require(expected_categories.issubset({row["category"] for row in rights}),
            "Missing artifact category in rights registry")
    require(len({row["category"] for row in rights}) == len(rights), "Duplicate rights category")
    require(all(row["status"] in {"covered", "pending", "confirmed", "not_distributed"}
                and row["evidence"] and row["paths"] for row in rights), "Invalid rights registry")
    require("* @Jinhua188" in (ROOT / ".github/CODEOWNERS").read_text(), "Owner routing mismatch")
    forms = ["bug", "research_question", "benchmark_proposal", "data_validation"]
    for form in forms:
        data = yaml.safe_load((ROOT / f".github/ISSUE_TEMPLATE/{form}.yml").read_text(encoding="utf-8"))
        require(bool(data.get("name") and data.get("description") and data.get("body")), f"Invalid form: {form}")
        ids = [item["id"] for item in data["body"] if "id" in item]
        require(len(ids) == len(set(ids)), f"Duplicate form field: {form}")
        for field in data["body"]:
            require(field["type"] in {"markdown", "input", "textarea", "dropdown", "checkboxes"},
                    f"Unsupported form type: {form}")
            if field["type"] != "markdown":
                require(bool(field.get("attributes", {}).get("label")), f"Missing form label: {form}")
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        data = yaml.load(workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        require(bool(data.get("on") and data.get("jobs")), f"Invalid workflow: {workflow.name}")
    # The recorded research snapshot preserves the source engine, configurations,
    # locked split, checkpoints and reported results of the pre-governance commit.
    research_count = check_hashes("RESEARCH_SNAPSHOT.sha256")
    public_count = check_hashes("MANIFEST.sha256", full_public_snapshot=True)
    return {"version": version, "cff_schema": "1.2.0", "issue_forms": len(forms),
            "research_artifacts_verified": research_count, "public_files_verified": public_count,
            "rights_pending": [row["category"] for row in rights if row["status"] == "pending"],
            "engineering_checks": "passed"}


def publication_pending() -> list[str]:
    readiness = read_json("RELEASE_READINESS.json")
    pending = []
    for key in ["authors", "artifact_rights", "zenodo_enabled", "publication_authorized"]:
        item = readiness.get("confirmations", {}).get(key, {})
        if item.get("confirmed") is not True or not item.get("evidence", "").strip():
            pending.append(key)
    with (ROOT / "RIGHTS_REGISTRY.csv").open(encoding="utf-8-sig", newline="") as stream:
        pending.extend(f"rights:{row['category']}" for row in csv.DictReader(stream) if row["status"] == "pending")
    cff = yaml.load((ROOT / "CITATION.cff").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if any(author.get("name") == "IC-EconGym Project" for author in cff["authors"]):
        pending.append("provisional_author")
    if not cff.get("date-released"):
        pending.append("actual_release_date")
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication", action="store_true", help="Fail if explicit release confirmations remain pending")
    parser.add_argument("--schema-file", type=Path, help="Offline copy of the exact pinned CFF schema")
    args = parser.parse_args()
    try:
        report = engineering_checks(args.schema_file)
        report["publication_pending"] = publication_pending()
        report["publication_ready"] = not report["publication_pending"]
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2 if args.publication and report["publication_pending"] else 0
    except (ValueError, KeyError, jsonschema.ValidationError, OSError) as error:
        print(json.dumps({"engineering_checks": "failed", "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
