"""Render the current 57-sector / 15-agent architecture diagram."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"


def main():
    fig, ax = plt.subplots(figsize=(12, 5.5), layout="constrained")
    fig.patch.set_facecolor("white")
    ax.set(xlim=(0, 12), ylim=(0, 5.5))
    ax.axis("off")
    boxes = [
        (0.25, 3.25, "2020 IO accounting\n57-sector structure"),
        (4.25, 3.25, "15 sector agents\n+ government agent"),
        (8.25, 3.25, "15 configured tasks\nE1–E5 / R1–R5 / G1–G5"),
        (0.25, 0.65, "Explicit boundaries\n42 domestic sectors\nImports / final demand"),
        (4.25, 0.65, "State transition\nOrders → arrivals → production\nAllocation → settlement"),
        (8.25, 0.65, "Evaluation & replay\nMatched-seed comparisons\nSensitivity / runtime"),
    ]
    for x, y, label in boxes:
        ax.add_patch(FancyBboxPatch((x, y), 3.5, 1.55, boxstyle="round,pad=0.04,rounding_size=0.08",
                                    facecolor="#eaf0fb", edgecolor="#8eaff0", linewidth=1.4))
        ax.text(x + 1.75, y + 0.775, label, ha="center", va="center", fontsize=11, color="#192331")
    for a, b in [((3.78, 4.025), (4.2, 4.025)), ((7.78, 4.025), (8.2, 4.025)),
                 ((3.78, 1.425), (4.2, 1.425)), ((7.78, 1.425), (8.2, 1.425)),
                 ((6, 3.22), (6, 2.27))]:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="->", mutation_scale=14,
                                     linewidth=2.0, color="#526d86"))
    for extension in ("svg", "png"):
        fig.savefig(OUT / f"architecture.{extension}", dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
