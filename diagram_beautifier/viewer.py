"""Eval report viewer -- generates static HTML reports from eval run directories.

Scans eval-results directories for per-diagram quality.json files and variant PNGs,
then generates a self-contained HTML report with Grid, Detail, and Dashboard views.

Usage:
    # Single run -- generates report.html inside the run directory
    python -m diagram_beautifier.viewer eval-results/2026-04-08_160419-diagrams/

    # Multiple runs -- generates comparison.html in eval-results/
    python -m diagram_beautifier.viewer eval-results/run-A/ eval-results/run-B/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VARIANT_NAMES: tuple[str, ...] = ("darkmode", "minimal", "sketchnote", "claymation")

ALL_DIMENSIONS: tuple[str, ...] = (
    "content_accuracy",
    "layout_quality",
    "visual_clarity",
    "prompt_fidelity",
    "aesthetic_fidelity",
    "label_fidelity",
    "structural_accuracy",
    "color_category_fidelity",
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DiagramData:
    """Loaded data for a single diagram within a run."""

    name: str
    fmt: str
    node_count: int
    edge_count: int
    variants: dict[str, dict[str, int]]
    verification: dict
    variant_images: dict[str, Path] = field(default_factory=dict)
    source_image: Path | None = None

    @property
    def average_score(self) -> float:
        """Average score across all variants and all available dimensions."""
        scores: list[float] = []
        for variant_scores in self.variants.values():
            variant_vals = [
                v for v in variant_scores.values() if isinstance(v, (int, float))
            ]
            if variant_vals:
                scores.append(mean(variant_vals))
        return round(mean(scores), 2) if scores else 0.0


@dataclass
class RunData:
    """Loaded data for an entire eval run."""

    run_dir: Path
    diagrams: list[DiagramData] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_diagram_data(diagram_dir: Path) -> DiagramData | None:
    """Load quality data and discover images for a single diagram directory.

    Returns None if quality.json is missing.
    """
    quality_path = diagram_dir / "quality.json"
    if not quality_path.exists():
        return None

    with open(quality_path) as f:
        data = json.load(f)

    name = data["diagram"]
    fmt = data.get("format", "unknown")
    node_count = data.get("node_count", 0)
    edge_count = data.get("edge_count", 0)
    variants = data.get("variants", {})
    verification = data.get("verification", {})

    # Discover variant PNGs
    variant_images: dict[str, Path] = {}
    for variant in VARIANT_NAMES:
        png_path = diagram_dir / f"{name}_{variant}.png"
        if png_path.exists():
            variant_images[variant] = png_path

    # Discover source image
    source_path = diagram_dir / f"{name}_source.png"
    source_image = source_path if source_path.exists() else None

    return DiagramData(
        name=name,
        fmt=fmt,
        node_count=node_count,
        edge_count=edge_count,
        variants=variants,
        verification=verification,
        variant_images=variant_images,
        source_image=source_image,
    )


def load_run_data(run_dir: Path) -> RunData:
    """Load all diagram data from an eval run directory."""
    diagrams: list[DiagramData] = []
    for entry in sorted(run_dir.iterdir()):
        if not entry.is_dir():
            continue
        diagram = load_diagram_data(entry)
        if diagram is not None:
            diagrams.append(diagram)
    return RunData(run_dir=run_dir, diagrams=diagrams)
