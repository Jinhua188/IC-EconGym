"""Refresh the static replay and paper from published sources; no simulation runs.

Run: python -m scripts_ic.build_project_site
Additional build dependencies: requirements_site.txt
"""
from pathlib import Path
import csv
import html
import json
import re
import shutil
import hashlib
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from markdown_it import MarkdownIt
from scripts_ic.build_dashboard import build_dashboard

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def build(refresh_figures=False):
    docs = ROOT / "docs"
    demo = ROOT / "demo_results_v2"
    index = json.loads((demo / "run_index.json").read_text(encoding="utf-8"))
    build_dashboard(index, demo / "dashboard.html")
    shutil.copy2(demo / "dashboard.html", docs / "demo.html")
    observer = {"seeds": index["seeds"], "periods": index["periods"], "tasks": []}
    for task in index["tasks"]:
        item = {k: v for k, v in task.items() if k != "series"}
        item["runs"] = {}
        for arm in task["variants"]:
            item["runs"][arm] = {}
            for seed in index["seeds"]:
                folder = demo / "runs" / task["id"] / arm / f"seed_{seed}"
                item["runs"][arm][str(seed)] = {
                    "nodes": read_csv(folder / "node_panel.csv"),
                    "aggregate": read_csv(folder / "trajectory.csv"),
                }
        observer["tasks"].append(item)
    (docs / "observer-data.json").write_text(json.dumps(observer, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    figures = ROOT / "paper" / "figures"
    expected_figures = ["final_demand_comparison.svg", "final_demand_comparison.png", "runtime_15tasks.svg", "runtime_15tasks.png"]
    if refresh_figures or not all((figures / name).exists() for name in expected_figures):
        plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                             "axes.spines.right": False, "svg.fonttype": "none"})
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
        for ax, folder, policies, labels, title in [
            (axes[0], "r1_v2", ["rule", "demand_tracking", "buffered_smoothing"], ["Rule", "Demand tracking", "Buffered"], "R1: sector policies"),
            (axes[1], "g5_v2", ["uniform", "linkage", "stress"], ["Uniform", "Linkage", "Stress"], "G5: government targeting"),
        ]:
            rows = read_csv(ROOT / "benchmark_results" / folder / "run_metrics.csv")
            for i, policy in enumerate(policies):
                values = [100 * float(r["final_fill_rate"]) for r in rows if r["case"] == "base" and r["policy"] == policy]
                color = ["#2563eb", "#f97316", "#059669"][i]
                ax.scatter([i] * len(values), values, color=color, s=16, alpha=.55)
                ax.scatter(i, statistics.mean(values), color=color, marker="_", s=500, linewidths=3)
            ax.set_xticks(range(3), labels)
            ax.set_ylabel("Final-demand fill rate (%)")
            ax.set_title(title)
            ax.grid(axis="y", alpha=.15)
        fig.savefig(figures / "final_demand_comparison.svg")
        fig.savefig(figures / "final_demand_comparison.png", dpi=180)
        plt.close(fig)
        rows = read_csv(ROOT / "benchmark_results/runtime_v2/runtime_summary.csv")
        fig, ax = plt.subplots(figsize=(10, 3.8), layout="constrained")
        ax.bar([r["task"].replace("ic_", "").upper() for r in rows], [float(r["median_ms_per_step"]) for r in rows], color=["#2563eb"] * 5 + ["#f97316"] * 5 + ["#059669"] * 5)
        ax.set_ylabel("Median milliseconds / step")
        ax.set_title("Fixed 13-sector + government rollout")
        ax.grid(axis="y", alpha=.15)
        fig.savefig(figures / "runtime_15tasks.svg")
        fig.savefig(figures / "runtime_15tasks.png", dpi=180)
        plt.close(fig)
    (docs / "figures").mkdir(exist_ok=True)
    for file in figures.iterdir():
        shutil.copy2(file, docs / "figures" / file.name)

    paper = (ROOT / "paper/manuscript_zh.md").read_text(encoding="utf-8")
    math = {}
    def protect(match):
        key = "MATHPLACEHOLDER" + str(len(math)) + "END"
        math[key] = match.group(0)
        return key
    protected = re.sub(r"\\\[.*?\\\]|\$[^$\n]+\$", protect, paper, flags=re.S)
    body = MarkdownIt("commonmark", {"html": False}).enable("table").render(protected)
    for key, value in math.items():
        body = body.replace(key, html.escape(value))
    body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', body, flags=re.S)
    body = body.replace('href="../', 'href="')
    template = (docs / "paper.html").read_text(encoding="utf-8")
    start = template.index('<article class="paper">')
    end = template.index("</article>", start) + len("</article>")
    buttons = '<div class="actions"><button onclick="window.print()">打印或保存 PDF</button><a href="paper/IC-EconGym_中文论文完善稿.pdf">下载本版 PDF</a><a href="paper/manuscript_zh.md">下载 Markdown 源稿</a></div>'
    (docs / "paper.html").write_text(template[:start] + '<article class="paper">' + buttons + body + '</article>' + template[end:], encoding="utf-8")
    for relative in ["paper/manuscript_zh.md", "paper/references.bib", "paper/reference_evidence.json", "paper/CITATION_REVISION.md", "paper/results_summary.json", "paper/SUBMISSION_EVIDENCE.md", "DATA_PROVENANCE.json", "MECHANISMS.md", "IEWM13_ADAPTATION.md", "README.md", "README_zh.md", "REPRODUCIBILITY.md", "reference/iewm13_source_audit.json", "RELEASE_CHECKS.json", "ic_extension/iewm13.py", "ic_extension/data/io_preparation_audit.json", "scripts_ic/compare_external_baseline.py"]:
        target = docs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    for relative in ["LICENSE", "LICENSE_SCOPE.md", "NOTICE", "THIRD_PARTY_NOTICES.md", "CITATION.cff", "CONTRIBUTING.md", "GOVERNANCE.md", "ROADMAP.md", "SECURITY.md", "PUBLISHING.md", "RELEASE_v0.3.0.md", "ZENODO_RELEASE_GUIDE.md", "GITHUB_SETTINGS_CHECKLIST.md", "RIGHTS_REGISTRY.csv", "RELEASE_READINESS.json", "RELEASE_PREPARATION.md", "AUTHOR_METADATA.md", "TASKS.md", "CHANGELOG.md"]:
        source = ROOT / relative
        if source.exists():
            shutil.copy2(source, docs / relative)
    for folder in ["r1_v2", "g5_v2", "runtime_v2", "manuscript_diagnostics"]:
        shutil.copytree(ROOT / "benchmark_results" / folder, docs / "benchmark_results" / folder, dirs_exist_ok=True)
    if (ROOT / "EXPERIMENT_UPGRADE.md").exists():
        shutil.copy2(ROOT / "EXPERIMENT_UPGRADE.md", docs / "EXPERIMENT_UPGRADE.md")
        shutil.copy2(ROOT / "DATA_CARD.md", docs / "DATA_CARD.md")
        for folder in ["calibration", "external_validation", "benchmark_splits", "robustness"]:
            target = docs / folder
            target.mkdir(parents=True, exist_ok=True)
            for file in (ROOT / folder).iterdir():
                if file.is_file() and file.name != "locked_scenarios.json":
                    shutil.copy2(file, target / file.name)
        for folder in ["p0_v3", "p1_v3", "p4_v3", "upgrade_summary"]:
            shutil.copytree(ROOT / "benchmark_results" / folder, docs / "benchmark_results" / folder, dirs_exist_ok=True)
    pdf = ROOT / "paper/IC-EconGym_中文论文完善稿.pdf"
    if pdf.exists():
        shutil.copy2(pdf, docs / "paper" / pdf.name)
    import subprocess
    manifest = []
    public = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0")
    for relative in sorted(set(public)):
        file = ROOT / relative
        if relative and file.is_file() and file.name != "MANIFEST.sha256":
            manifest.append(hashlib.sha256(file.read_bytes()).hexdigest() + "  " + file.relative_to(ROOT).as_posix())
    (ROOT / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(index["tasks"]), "site": "docs", "files": len(manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-figures", action="store_true", help="Explicitly regenerate research figures and update their artifact hashes")
    build(refresh_figures=parser.parse_args().refresh_figures)
