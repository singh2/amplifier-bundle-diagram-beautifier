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

import argparse
import json
from dataclasses import dataclass, field
from html import escape
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


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------


def score_color(score: float) -> str:
    """Return a color name based on the quality score threshold."""
    if score >= 4.0:
        return "green"
    if score >= 3.0:
        return "yellow"
    return "red"


def _pct(value: float) -> str:
    """Format a 0.0–1.0 fraction as an integer percentage string."""
    return f"{int(value * 100)}"


# ---------------------------------------------------------------------------
# Grid view
# ---------------------------------------------------------------------------


def generate_grid_html(run: RunData) -> str:
    """Generate a card-grid HTML fragment for all diagrams in a run."""
    parts: list[str] = []

    # Sort/filter controls
    parts.append('<div class="controls">')
    parts.append('<select id="sort-by">')
    parts.append('<option value="score">Sort by Score</option>')
    parts.append('<option value="name">Sort by Name</option>')
    parts.append('<option value="complexity">Sort by Complexity</option>')
    parts.append('<option value="format">Sort by Format</option>')
    parts.append("</select>")
    parts.append('<select id="filter-format">')
    parts.append('<option value="all">All Formats</option>')
    formats = sorted({d.fmt for d in run.diagrams})
    for fmt in formats:
        parts.append(f'<option value="{escape(fmt)}">{escape(fmt)}</option>')
    parts.append("</select>")
    parts.append("</div>")

    # Card grid
    parts.append('<div class="grid">')
    for diagram in run.diagrams:
        name = escape(diagram.name)
        avg = diagram.average_score
        color = score_color(avg)
        complexity = diagram.node_count + diagram.edge_count
        label_pct = _pct(diagram.verification.get("label_completeness", 0.0))
        edge_pct = _pct(diagram.verification.get("edge_completeness", 0.0))

        parts.append(
            f'<div class="card"'
            f' data-name="{name}"'
            f' data-score="{avg}"'
            f' data-format="{escape(diagram.fmt)}"'
            f' data-complexity="{complexity}">'
        )

        # Thumbnail (darkmode variant)
        thumb = f"./{name}/{name}_darkmode.png"
        parts.append(f'<img src="{thumb}" alt="{name} darkmode">')

        # Diagram name
        parts.append(f"<h3>{name}</h3>")

        # Format badge
        parts.append(f'<span class="badge">{escape(diagram.fmt)}</span>')

        # Average score, color-coded
        parts.append(f'<span class="score {color}">{avg}</span>')

        # Verification bars
        parts.append('<div class="verification">')
        parts.append(
            f'<div class="bar" style="width:{label_pct}%">Labels {label_pct}%</div>'
        )
        parts.append(
            f'<div class="bar" style="width:{edge_pct}%">Edges {edge_pct}%</div>'
        )
        parts.append("</div>")

        # Complexity indicator
        parts.append(
            f'<span class="complexity">'
            f"{diagram.node_count}n / {diagram.edge_count}e</span>"
        )

        parts.append("</div>")  # close card

    parts.append("</div>")  # close grid
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------


def _dimension_display_name(dim: str) -> str:
    """Convert a dimension key like 'label_fidelity' to 'Label Fidelity'."""
    return dim.replace("_", " ").title()


def generate_detail_html(diagram: DiagramData) -> str:
    """Generate detail view HTML for a single diagram.

    Contains three sections:
    - Image comparison strip (source + 4 variants)
    - Score heatmap (ALL_DIMENSIONS × VARIANT_NAMES)
    - Topology diff (completeness stats + missing labels/edges)
    """
    name = escape(diagram.name)
    parts: list[str] = []

    # --- Section A: Image comparison strip ---
    parts.append('<div class="image-strip">')

    # Source image
    if diagram.source_image is not None:
        src = f"./{name}/{name}_source.png"
        parts.append(f'<img src="{src}" alt="{name} source">')
    else:
        parts.append('<div class="no-source">Source not available</div>')

    # Variant images
    for variant in VARIANT_NAMES:
        img_path = f"./{name}/{name}_{variant}.png"
        if variant in diagram.variant_images:
            parts.append(
                f'<div class="variant">'
                f'<img src="{img_path}" alt="{name} {variant}"'
                f' onclick="openLightbox(this.src)">'
                f"<label>{variant.title()}</label>"
                f"</div>"
            )
        else:
            parts.append(
                f'<div class="variant placeholder">'
                f"<label>{variant.title()}</label>"
                f"</div>"
            )

    parts.append("</div>")  # close image-strip

    # --- Section B: Score heatmap ---
    parts.append('<table class="heatmap">')

    # Header row
    parts.append("<tr><th></th>")
    for variant in VARIANT_NAMES:
        parts.append(f"<th>{variant.title()}</th>")
    parts.append("</tr>")

    # Dimension rows
    for dim in ALL_DIMENSIONS:
        display = _dimension_display_name(dim)
        parts.append(f"<tr><th>{display}</th>")
        for variant in VARIANT_NAMES:
            score = diagram.variants.get(variant, {}).get(dim)
            if score is not None:
                color = score_color(score)
                parts.append(f'<td class="score {color}">{score}</td>')
            else:
                parts.append('<td class="score-na">N/A</td>')
        parts.append("</tr>")

    parts.append("</table>")

    # --- Section C: Topology diff ---
    verification = diagram.verification
    label_pct = _pct(verification.get("label_completeness", 0.0))
    edge_pct = _pct(verification.get("edge_completeness", 0.0))

    parts.append('<div class="topology-diff">')
    parts.append(f"<p>Label completeness: {label_pct}%</p>")
    parts.append(f"<p>Edge completeness: {edge_pct}%</p>")

    # Missing labels
    missing_labels = verification.get("missing_labels", [])
    if missing_labels:
        parts.append("<h4>Missing labels</h4><ul>")
        for label in missing_labels:
            parts.append(f"<li>{escape(str(label))}</li>")
        parts.append("</ul>")

    # Missing edges
    missing_edges = verification.get("missing_edges", [])
    if missing_edges:
        parts.append("<h4>Missing edges</h4><ul>")
        for edge in missing_edges:
            parts.append(f"<li>{escape(str(edge))}</li>")
        parts.append("</ul>")

    parts.append("</div>")  # close topology-diff

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Dashboard view
# ---------------------------------------------------------------------------


def _complexity_band(node_count: int) -> str:
    """Classify a diagram by node count into a complexity band."""
    if node_count <= 10:
        return "small (≤10)"
    if node_count <= 25:
        return "medium (11-25)"
    if node_count <= 40:
        return "large (26-40)"
    return "very_large (41+)"


def generate_dashboard_html(run: RunData) -> str:
    """Generate dashboard tab HTML with aggregate metrics for a run."""
    parts: list[str] = []
    diagrams = run.diagrams

    # --- Key metrics row ---
    total = len(diagrams)

    all_avg_scores = [d.average_score for d in diagrams]
    overall_avg = round(mean(all_avg_scores), 2) if all_avg_scores else 0.0

    # Collect per-dimension averages across all diagrams and variants
    dim_averages: dict[str, float] = {}
    for dim in ALL_DIMENSIONS:
        scores: list[float] = []
        for d in diagrams:
            for variant_scores in d.variants.values():
                val = variant_scores.get(dim)
                if val is not None and isinstance(val, (int, float)):
                    scores.append(float(val))
        if scores:
            dim_averages[dim] = round(mean(scores), 2)

    # Verification averages
    label_comps = [d.verification.get("label_completeness", 0.0) for d in diagrams]
    edge_comps = [d.verification.get("edge_completeness", 0.0) for d in diagrams]
    avg_label_comp = round(mean(label_comps), 2) if label_comps else 0.0
    avg_edge_comp = round(mean(edge_comps), 2) if edge_comps else 0.0

    parts.append('<div class="key-metrics">')
    parts.append(f"<div><strong>Total Diagrams</strong><span>{total}</span></div>")
    parts.append(f"<div><strong>Avg Score</strong><span>{overall_avg}</span></div>")

    # Show avg structural_accuracy and label_fidelity if available
    for key_dim in ("structural_accuracy", "label_fidelity"):
        if key_dim in dim_averages:
            display = _dimension_display_name(key_dim)
            parts.append(
                f"<div><strong>Avg {display}</strong>"
                f"<span>{dim_averages[key_dim]}</span></div>"
            )

    parts.append(
        f"<div><strong>Avg Label Completeness</strong>"
        f"<span>{_pct(avg_label_comp)}%</span></div>"
    )
    parts.append(
        f"<div><strong>Avg Edge Completeness</strong>"
        f"<span>{_pct(avg_edge_comp)}%</span></div>"
    )
    parts.append("</div>")  # close key-metrics

    # --- Dimension breakdown bar chart ---
    parts.append('<div class="dimension-chart bar-chart">')
    parts.append("<h3>Dimension Averages</h3>")

    # Determine weakest dimension
    weakest_dim: str | None = None
    weakest_val: float = 6.0
    for dim in ALL_DIMENSIONS:
        if dim in dim_averages and dim_averages[dim] < weakest_val:
            weakest_val = dim_averages[dim]
            weakest_dim = dim

    for dim in ALL_DIMENSIONS:
        if dim not in dim_averages:
            continue
        avg_val = dim_averages[dim]
        color = score_color(avg_val)
        display = _dimension_display_name(dim)
        width_pct = int(avg_val / 5.0 * 100)
        parts.append('<div class="bar-row">')
        parts.append(f'<span class="bar-label">{escape(display)}</span>')
        parts.append('<span class="bar-track">')
        parts.append(
            f'<span class="bar-fill {color}" style="width:{width_pct}%"></span>'
        )
        parts.append("</span>")
        parts.append(f'<span class="bar-value">{avg_val}</span>')
        parts.append("</div>")

    parts.append("</div>")  # close dimension-chart

    # --- Weakest dimension note ---
    if weakest_dim is not None:
        display = _dimension_display_name(weakest_dim)
        parts.append(
            f'<p class="weakest-note">Weakest dimension: '
            f"<strong>{escape(display)}</strong> ({weakest_val})</p>"
        )

    # --- Complexity band table ---
    band_data: dict[str, list[DiagramData]] = {}
    for d in diagrams:
        band = _complexity_band(d.node_count)
        band_data.setdefault(band, []).append(d)

    band_order = [
        "small (≤10)",
        "medium (11-25)",
        "large (26-40)",
        "very_large (41+)",
    ]

    parts.append('<table class="complexity-table">')
    parts.append("<tr><th>Complexity Band</th><th>Count</th><th>Avg Score</th></tr>")
    for band in band_order:
        band_diagrams = band_data.get(band, [])
        if not band_diagrams:
            continue
        count = len(band_diagrams)
        band_avg = round(mean([d.average_score for d in band_diagrams]), 2)
        parts.append(
            f"<tr><td>{escape(band)}</td><td>{count}</td><td>{band_avg}</td></tr>"
        )
    parts.append("</table>")

    # --- Worst 5 performers ---
    sorted_diagrams = sorted(diagrams, key=lambda d: d.average_score)
    worst_5 = sorted_diagrams[:5]

    parts.append('<div class="worst-performers">')
    parts.append("<h3>Worst 5 Performers</h3>")
    parts.append("<ol>")
    for d in worst_5:
        name = escape(d.name)
        avg = d.average_score
        color = score_color(avg)
        parts.append(
            f'<li><a href="#{name}">{name}</a> '
            f'<span class="score {color}">{avg}</span></li>'
        )
    parts.append("</ol>")
    parts.append("</div>")  # close worst-performers

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CSS & JS constants for the full report
# ---------------------------------------------------------------------------

REPORT_CSS = """\
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#c9d1d9;font-family:system-ui,-apple-system,sans-serif;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:1rem}
h1{color:#f0f6fc;font-size:1.8rem;margin-bottom:.5rem}
h2{color:#f0f6fc;font-size:1.4rem;margin:1rem 0 .5rem}
h3{color:#e6edf3;font-size:1.1rem;margin:.5rem 0}
h4{color:#c9d1d9;font-size:.95rem;margin:.5rem 0}

/* Tabs */
.tabs{display:flex;gap:.5rem;border-bottom:1px solid #30363d;margin-bottom:1rem;padding-bottom:0}
.tab{padding:.5rem 1rem;cursor:pointer;border:1px solid transparent;border-bottom:none;
     border-radius:6px 6px 0 0;background:transparent;color:#8b949e;font-size:.9rem}
.tab:hover{color:#c9d1d9}
.tab.active{background:#161b22;color:#f0f6fc;border-color:#30363d}
.tab-content{display:none}
.tab-content.active{display:block}

/* Controls */
.controls{display:flex;gap:.5rem;margin-bottom:1rem}
.controls select{background:#161b22;color:#c9d1d9;border:1px solid #30363d;padding:.4rem .6rem;
                  border-radius:6px;font-size:.85rem}

/* Grid */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden;
      cursor:pointer;transition:border-color .2s}
.card:hover{border-color:#58a6ff}
.card img,.card-thumb{width:100%;height:180px;object-fit:cover;background:#0d1117}
.card-body{padding:.75rem}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:12px;font-size:.75rem;
       background:#30363d;color:#8b949e;margin-right:.5rem}
.score{font-weight:bold;font-size:1rem}
.score.green,.score-green{color:#3fb950}
.score.yellow,.score-yellow{color:#d29922}
.score.red,.score-red{color:#f85149}
.verification-bars,.verification{margin-top:.4rem}
.vbar,.bar{height:16px;border-radius:3px;background:#21262d;margin-bottom:.25rem;
           font-size:.7rem;color:#c9d1d9;line-height:16px;padding-left:4px;overflow:hidden}
.vbar-fill{height:100%;border-radius:3px}
.complexity{font-size:.8rem;color:#8b949e}

/* Detail */
.detail-view{margin-bottom:2rem;padding:1rem;background:#161b22;border:1px solid #30363d;
             border-radius:8px}
.image-strip{display:flex;gap:.75rem;overflow-x:auto;padding:.5rem 0}
.image-strip img,.strip-img{max-height:220px;border-radius:6px;cursor:pointer;
                            border:1px solid #30363d}
.strip-label{text-align:center;font-size:.8rem;color:#8b949e;margin-top:.25rem}
.placeholder{width:200px;height:200px;background:#21262d;border-radius:6px;display:flex;
             align-items:center;justify-content:center;color:#484f58;font-size:.85rem}
.no-source{width:200px;height:200px;background:#21262d;border-radius:6px;display:flex;
           align-items:center;justify-content:center;color:#484f58;font-size:.85rem}
.variant{text-align:center}
.variant label{display:block;font-size:.8rem;color:#8b949e;margin-top:.25rem}
.heatmap{width:100%;border-collapse:collapse;margin:1rem 0}
.heatmap th,.heatmap td{padding:.4rem .6rem;border:1px solid #30363d;text-align:center;
                        font-size:.85rem}
.heatmap th{background:#21262d;color:#8b949e}
.score-cell{font-weight:bold}
.score-na{color:#484f58;font-style:italic}
.topology-diff{margin-top:1rem;padding:.75rem;background:#0d1117;border-radius:6px}
.topology-diff p{margin:.25rem 0}
.topology-diff ul{margin-left:1.2rem;margin-top:.25rem}
.topology-diff li{font-size:.85rem;color:#f85149}
.diff-stats{display:flex;gap:1rem;margin-bottom:.5rem}
.diff-tables{display:flex;gap:1rem;flex-wrap:wrap}
.diff-table{flex:1;min-width:200px}
.missing-list{list-style:disc;padding-left:1.2rem}

/* Dashboard */
.key-metrics{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:1.5rem}
.key-metrics>div,.key-metric{flex:1;min-width:140px;background:#161b22;
                              border:1px solid #30363d;border-radius:8px;
                              padding:.75rem;text-align:center}
.key-metrics strong,.metric-label{display:block;font-size:.8rem;color:#8b949e;
                                  margin-bottom:.25rem}
.key-metrics span,.metric-value{font-size:1.3rem;font-weight:bold;color:#f0f6fc}
.bar-chart{margin:1rem 0}
.bar-row{display:flex;align-items:center;margin-bottom:.5rem}
.bar-label{width:180px;font-size:.85rem;color:#8b949e;flex-shrink:0}
.bar-track{flex:1;height:20px;background:#21262d;border-radius:4px;overflow:hidden;
           margin:0 .5rem}
.bar-fill{height:100%;border-radius:4px;transition:width .3s}
.bar-fill.green,.bar-green{background:#238636}
.bar-fill.yellow,.bar-yellow{background:#9e6a03}
.bar-fill.red,.bar-red{background:#da3633}
.bar-value{width:40px;font-size:.85rem;color:#c9d1d9;text-align:right}
.weakest-note{margin:1rem 0;padding:.5rem .75rem;background:#2d1b00;
              border:1px solid #9e6a03;border-radius:6px;font-size:.9rem}
.complexity-table{width:100%;border-collapse:collapse;margin:1rem 0}
.complexity-table th,.complexity-table td{padding:.5rem .75rem;border:1px solid #30363d;
                                          text-align:left;font-size:.85rem}
.complexity-table th{background:#21262d;color:#8b949e}
.worst-performers{margin-top:1rem}
.worst-performers ol{margin-left:1.5rem}
.worst-performers li{margin:.3rem 0}
.worst-performers a{color:#58a6ff;text-decoration:none}
.worst-performers a:hover{text-decoration:underline}

/* Lightbox */
.lightbox{display:none;position:fixed;top:0;left:0;width:100%;height:100%;
          background:rgba(0,0,0,.85);z-index:1000;align-items:center;
          justify-content:center;cursor:pointer}
.lightbox.active{display:flex}
.lightbox img{max-width:90%;max-height:90%;border-radius:8px}

/* Detail navigation */
.detail-nav{display:flex;align-items:center;gap:.5rem;margin:1rem 0;flex-wrap:wrap}
.detail-nav button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;
                   padding:.4rem .8rem;border-radius:6px;cursor:pointer;font-size:.85rem}
.detail-nav button:hover{background:#30363d}
.detail-nav select{background:#161b22;color:#c9d1d9;border:1px solid #30363d;
                   padding:.4rem .6rem;border-radius:6px;font-size:.85rem}
"""

REPORT_JS = """\
let diagramNames = [];
let currentIndex = 0;

function initDiagrams(names) {
    diagramNames = names;
}

function showTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(
        c => c.classList.remove('active')
    );
    const tab = document.querySelector('.tab[data-tab="' + name + '"]');
    const content = document.getElementById('tab-' + name);
    if (tab) tab.classList.add('active');
    if (content) content.classList.add('active');
}

function showDetail(name) {
    showTab('detail');
    const idx = diagramNames.indexOf(name);
    if (idx >= 0) currentIndex = idx;
    document.querySelectorAll('.detail-view').forEach(
        d => d.style.display = 'none'
    );
    const el = document.getElementById('detail-' + name);
    if (el) {
        el.style.display = 'block';
        el.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
    const sel = document.getElementById('detail-select');
    if (sel) sel.value = name;
}

function prevDetail() {
    if (diagramNames.length === 0) return;
    currentIndex = (currentIndex - 1 + diagramNames.length)
                   % diagramNames.length;
    showDetail(diagramNames[currentIndex]);
}

function nextDetail() {
    if (diagramNames.length === 0) return;
    currentIndex = (currentIndex + 1) % diagramNames.length;
    showDetail(diagramNames[currentIndex]);
}

function sortGrid(key) {
    const grid = document.querySelector('.grid');
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll('.card'));
    cards.sort((a, b) => {
        if (key === 'score')
            return parseFloat(b.dataset.score) - parseFloat(a.dataset.score);
        if (key === 'name')
            return a.dataset.name.localeCompare(b.dataset.name);
        if (key === 'complexity')
            return parseInt(b.dataset.complexity)
                   - parseInt(a.dataset.complexity);
        if (key === 'format')
            return a.dataset.format.localeCompare(b.dataset.format);
        return 0;
    });
    cards.forEach(c => grid.appendChild(c));
}

function filterGrid() {
    const sel = document.getElementById('filter-format');
    if (!sel) return;
    const val = sel.value;
    document.querySelectorAll('.card').forEach(c => {
        c.style.display = (val === 'all' || c.dataset.format === val)
                          ? '' : 'none';
    });
}

function openLightbox(src) {
    const lb = document.getElementById('lightbox');
    if (!lb) return;
    lb.querySelector('img').src = src;
    lb.classList.add('active');
}

function closeLightbox() {
    const lb = document.getElementById('lightbox');
    if (lb) lb.classList.remove('active');
}
"""


# ---------------------------------------------------------------------------
# Full report assembly
# ---------------------------------------------------------------------------


def generate_report(run_dir: Path, output_path: Path | None = None) -> Path:
    """Generate a self-contained HTML report for an eval run.

    Assembles Grid, Detail, and Dashboard views into one HTML file with
    inline CSS and JS.  All image paths are relative to *run_dir* so the
    report works when opened from that directory.
    """
    run = load_run_data(run_dir)

    if output_path is None:
        output_path = run_dir / "report.html"

    # Generate the three view fragments
    grid_html = generate_grid_html(run)
    detail_sections: list[str] = []
    for diagram in run.diagrams:
        detail_sections.append(
            f'<div id="detail-{escape(diagram.name)}" class="detail-view">'
            f"<h2>{escape(diagram.name)}</h2>"
            f"{generate_detail_html(diagram)}"
            f"</div>"
        )
    dashboard_html = generate_dashboard_html(run)

    diagram_names = [d.name for d in run.diagrams]
    names_js = ", ".join(f'"{escape(n)}"' for n in diagram_names)

    # Detail navigation: prev/next + dropdown
    options = "".join(
        f'<option value="{escape(n)}">{escape(n)}</option>' for n in diagram_names
    )
    detail_nav = (
        '<div class="detail-nav">'
        '<button onclick="prevDetail()">&larr; Prev</button>'
        '<select id="detail-select"'
        ' onchange="showDetail(this.value)">'
        f"{options}</select>"
        '<button onclick="nextDetail()">Next &rarr;</button>'
        "</div>"
    )

    run_name = escape(run_dir.name)

    html = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport"'
        ' content="width=device-width, initial-scale=1">\n'
        f"<title>Eval Report – {run_name}</title>\n"
        "<style>\n"
        f"{REPORT_CSS}"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="container">\n'
        f"<h1>Eval Report"
        f' <small style="color:#8b949e;font-size:.7em">'
        f"{run_name}</small></h1>\n"
        "\n"
        '<div class="tabs">\n'
        '<button class="tab active" data-tab="grid"'
        " onclick=\"showTab('grid')\">Grid</button>\n"
        '<button class="tab" data-tab="detail"'
        " onclick=\"showTab('detail')\">Detail</button>\n"
        '<button class="tab" data-tab="dashboard"'
        " onclick=\"showTab('dashboard')\">Dashboard</button>\n"
        "</div>\n"
        "\n"
        '<div id="tab-grid" class="tab-content active">\n'
        f"{grid_html}\n"
        "</div>\n"
        "\n"
        '<div id="tab-detail" class="tab-content">\n'
        f"{detail_nav}\n"
        f"{''.join(detail_sections)}\n"
        "</div>\n"
        "\n"
        '<div id="tab-dashboard" class="tab-content">\n'
        f"{dashboard_html}\n"
        "</div>\n"
        "\n"
        "</div><!-- /container -->\n"
        "\n"
        '<div id="lightbox" class="lightbox"'
        ' onclick="closeLightbox()">\n'
        '<img src="" alt="lightbox">\n'
        "</div>\n"
        "\n"
        "<script>\n"
        f"{REPORT_JS}"
        f"initDiagrams([{names_js}]);\n"
        "document.addEventListener('DOMContentLoaded', function() {\n"
        "    var sortSel = document.getElementById('sort-by');\n"
        "    if (sortSel) sortSel.addEventListener("
        "'change', function() { sortGrid(this.value); });\n"
        "    var filterSel = document.getElementById('filter-format');\n"
        "    if (filterSel) filterSel.addEventListener("
        "'change', filterGrid);\n"
        "    if (diagramNames.length > 0)"
        " showDetail(diagramNames[0]);\n"
        "});\n"
        "</script>\n"
        "</body>\n"
        "</html>"
    )

    output_path.write_text(html)
    return output_path


# ---------------------------------------------------------------------------
# Cross-run comparison
# ---------------------------------------------------------------------------


COMPARISON_CSS = ".flagged-delta { background: #2d1b00; }\n"


def generate_comparison_report(run_dirs: list[Path], output_path: Path) -> Path:
    """Generate a cross-run comparison HTML report.

    Correlates diagrams by name across runs, computes score trends,
    flags diagrams with significant delta (>1 point between first and last),
    and writes a self-contained comparison.html.
    """
    # 1. Load RunData for each run directory
    runs = [load_run_data(d) for d in run_dirs]

    # 2. Correlate diagrams by name across runs
    #    Build {diagram_name: {run_index: DiagramData}}
    diagram_map: dict[str, dict[int, DiagramData]] = {}
    for i, run in enumerate(runs):
        for diagram in run.diagrams:
            diagram_map.setdefault(diagram.name, {})[i] = diagram

    # All diagram names across runs
    all_names = sorted(diagram_map.keys())

    # 3. Compute score trend per diagram across runs
    #    {diagram_name: [score_or_None per run]}
    score_trends: dict[str, list[float | None]] = {}
    for name in all_names:
        scores: list[float | None] = []
        for i in range(len(runs)):
            d = diagram_map[name].get(i)
            scores.append(d.average_score if d is not None else None)
        score_trends[name] = scores

    # 4. Compute aggregate average per run
    run_averages: list[float] = []
    for i, run in enumerate(runs):
        avg_scores = [d.average_score for d in run.diagrams]
        run_averages.append(round(mean(avg_scores), 2) if avg_scores else 0.0)

    # 5. Flag diagrams with significant delta (>1 point first vs last)
    flagged: set[str] = set()
    for name, scores in score_trends.items():
        actual = [s for s in scores if s is not None]
        if len(actual) >= 2:
            delta = abs(actual[-1] - actual[0])
            if delta > 1:
                flagged.add(name)

    # 6. Generate HTML
    run_names = [escape(d.name) for d in run_dirs]

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append("<title>Cross-Run Comparison</title>")
    parts.append("<style>")
    parts.append(REPORT_CSS)
    parts.append(COMPARISON_CSS)
    parts.append("</style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append('<div class="container">')
    parts.append("<h1>Cross-Run Comparison</h1>")

    # --- Aggregate Trend section ---
    parts.append('<div class="comparison-aggregate">')
    parts.append("<h2>Aggregate Trend</h2>")
    parts.append("<table>")
    parts.append("<tr><th>Run</th><th>Avg Score</th></tr>")
    for i, name in enumerate(run_names):
        parts.append(f"<tr><td>{name}</td><td>{run_averages[i]}</td></tr>")
    parts.append("</table>")
    parts.append("</div>")

    # --- Per-Diagram Trends section ---
    parts.append('<div class="comparison-diagrams">')
    parts.append("<h2>Per-Diagram Trends</h2>")
    parts.append("<table>")

    # Header: Diagram + run names
    parts.append("<tr><th>Diagram</th>")
    for name in run_names:
        parts.append(f"<th>{name}</th>")
    parts.append("<th>Delta</th></tr>")

    for diagram_name in all_names:
        scores = score_trends[diagram_name]
        is_flagged = diagram_name in flagged
        row_class = ' class="flagged-delta"' if is_flagged else ""
        parts.append(f"<tr{row_class}>")
        parts.append(f"<td>{escape(diagram_name)}</td>")
        for s in scores:
            if s is not None:
                color = score_color(s)
                parts.append(f'<td class="score {color}">{s}</td>')
            else:
                parts.append('<td class="score-na">-</td>')
        # Delta column
        actual = [s for s in scores if s is not None]
        if len(actual) >= 2:
            delta = round(actual[-1] - actual[0], 2)
            flag_text = " \u26a0 significant delta" if is_flagged else ""
            parts.append(f"<td>{delta:+.2f}{flag_text}</td>")
        else:
            parts.append("<td>-</td>")
        parts.append("</tr>")

    parts.append("</table>")
    parts.append("</div>")

    parts.append("</div><!-- /container -->")
    parts.append("</body>")
    parts.append("</html>")

    html = "\n".join(parts)
    output_path.write_text(html)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for generating eval reports."""
    parser = argparse.ArgumentParser(
        description="Generate an HTML eval report from a run directory.",
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to the eval run directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for the report (default: <run_dir>/report.html)",
    )
    args = parser.parse_args()
    result = generate_report(args.run_dir, args.output)
    print(f"Report generated: {result}")


if __name__ == "__main__":
    main()
