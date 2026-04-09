# Eval Viewer Design

## Goal

Build a static HTML eval report viewer that serves as a one-stop shop for reviewing diagram beautification eval runs — replacing the current workflow of manually navigating directories and opening individual image/JSON files.

## Background

After an eval run completes, the results live as a tree of directories containing variant PNGs and `quality.json` files. Reviewing them requires manually opening each image, cross-referencing JSON scores, and mentally aggregating patterns across diagrams. There is no unified view for spotting trends, comparing variants, or identifying regressions. This friction slows down iteration on prompts, styles, and the beautification pipeline itself.

## Approach

**Standalone Python module + recipe integration.** A new `diagram_beautifier/viewer.py` module generates the HTML. The eval recipe calls it as its final step (`python -m diagram_beautifier.viewer {run_dir}`). It can also be run independently — point it at any eval-results directory to regenerate a report, or pass multiple run directories for cross-run comparison.

This was chosen over embedding generation logic in the recipe YAML because the viewer logic is non-trivial (HTML templating, data aggregation, cross-run diffing) and deserves to be a proper Python module — testable, maintainable, and reusable alongside `parser.py`, `renderer.py`, `verify.py`, etc. The recipe stays lean.

## Architecture

### Data Model — quality.json Expansion (2 → 8 Dimensions)

Currently `quality.json` stores only 2 VLM scores per variant (`label_fidelity`, `structural_accuracy`). The agent's review step already evaluates 8 dimensions but only persists 2. Expand to persist all 8.

**The 8 dimensions** (each scored 1-5):

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 1 | `content_accuracy` | All source content preserved |
| 2 | `layout_quality` | Spatial arrangement and flow |
| 3 | `visual_clarity` | Readability and legibility |
| 4 | `prompt_fidelity` | Adherence to the style prompt |
| 5 | `aesthetic_fidelity` | Visual polish and coherence |
| 6 | `label_fidelity` | Text labels accurate and readable |
| 7 | `structural_accuracy` | Nodes and edges structurally correct |
| 8 | `color_category_fidelity` | Color usage matches category semantics |

**Changes required:**

- `agents/diagram-beautifier.md` — update Step 6 to write all 8 scores per variant
- `recipes/evaluate-diagrams.yaml` — update aggregate computation to average all 8 dimensions

**Expanded quality.json schema:**

```json
{
  "diagram": "amplifier-session-loop",
  "format": "dot",
  "node_count": 21,
  "edge_count": 23,
  "variants": {
    "darkmode": {
      "content_accuracy": 4,
      "layout_quality": 3,
      "visual_clarity": 4,
      "prompt_fidelity": 5,
      "aesthetic_fidelity": 4,
      "label_fidelity": 3,
      "structural_accuracy": 5,
      "color_category_fidelity": 4
    },
    "minimal": { "...same 8 dimensions..." },
    "sketchnote": { "...same 8 dimensions..." },
    "claymation": { "...same 8 dimensions..." }
  },
  "verification": {
    "label_completeness": 0.917,
    "edge_completeness": 0.75,
    "missing_labels": ["HookResult.action == deny?"],
    "missing_edges": ["yes (no tools)", "no (has tools)"]
  }
}
```

The verification block stays the same — it's already good.

### Source Image Handling

Three input formats need different treatment for the topology comparison view:

| Format | Source image for comparison |
|--------|---------------------------|
| `.dot` | Plain-rendered PNG from Graphviz (`dot -Tpng`) — the agent already generates this in Step 2 |
| `.mmd` | Plain-rendered PNG from Mermaid CLI (`mmdc`) — same, Step 2 |
| `.png` | The input PNG itself |

The agent should save the source render as `{diagram_name}_source.png` in the diagram's output directory, alongside the 4 variants. This makes discovery trivial for the viewer.

## Components

### `diagram_beautifier/viewer.py`

**CLI interface:**

```bash
# Single run — generates report.html inside the run directory
python -m diagram_beautifier.viewer eval-results/2026-04-08_160419-diagrams/

# Multiple runs — generates comparison.html in eval-results/
python -m diagram_beautifier.viewer eval-results/run-A/ eval-results/run-B/ eval-results/run-C/
```

**What it does:**

1. Scans the run directory for per-diagram subdirectories
2. Reads each `quality.json` + discovers variant PNGs + finds the source input in `eval/diagrams/`
3. For `.dot` and `.mmd` sources, also looks for the plain-rendered source PNG. For `.png` inputs, the source IS an image already.
4. Generates a single `report.html` using Python string templating (no external dependencies — just `json`, `pathlib`, `html` stdlib modules)
5. All image references are relative paths (e.g., `./amplifier-session-loop/amplifier-session-loop_darkmode.png`)

**No external dependencies.** The HTML includes inline CSS and vanilla JS. No React, no build step, no npm.

**Backward compatibility:** The viewer handles both old-format `quality.json` (2 dimensions: `label_fidelity`, `structural_accuracy`) and new-format (all 8 dimensions) gracefully. It displays what's available and shows "N/A" for missing dimensions.

### Tab 1: Grid View (Landing)

A responsive card grid, one card per diagram:

- **Thumbnail:** the darkmode variant (first variant, good visual preview)
- **Diagram name** + format badge (`.dot` / `.mmd` / `.png`)
- **Average score** across all 8 dimensions, color-coded: green (>=4), yellow (3–3.9), red (<3)
- **Verification bar:** label completeness + edge completeness as thin colored bars
- **Complexity indicator:** node/edge count shown as "21n / 23e"

**Interactions:**

- Click any card → navigates to its Detail View
- Sort by: score (default, worst first), name, complexity, format
- Filter by: format type, complexity band, score threshold

### Tab 2: Detail View (Per Diagram)

Accessed by clicking a grid card or via prev/next navigation. Three sections stacked vertically:

**Section A — Image comparison strip:**

- Source image (plain-rendered) on the left
- 4 variant images in a row to the right
- Each image is clickable to open full-size in a lightbox
- Variant labels underneath (Darkmode, Minimal, Sketchnote, Claymation)

**Section B — Score heatmap:**

- An 8x4 grid (8 dimensions x 4 variants)
- Each cell shows the 1-5 score, color-coded (green >=4, yellow 3, red <=2)
- Row headers: dimension names
- Column headers: variant names
- Enables instant visual pattern detection (e.g., "sketchnote consistently scores low on label fidelity")

**Section C — Topology diff:**

- Summary stats: `label_completeness: 91.7%`, `edge_completeness: 75.0%`
- Missing labels table: list of expected labels not found in the generated images, each with a red indicator
- Missing edges table: same treatment for edges
- Data comes directly from the existing `verification` block in `quality.json`

**Navigation:** prev/next diagram buttons + a dropdown to jump to any diagram by name.

### Tab 3: Dashboard (Aggregate)

Run-level summary for quick assessment:

**Section A — Key metrics (top row of numbers):**

- Total diagrams processed / total expected
- Failed diagrams (if any)
- Average structural accuracy, average label fidelity (the two most critical scores)
- Average label completeness, average edge completeness

**Section B — Dimension breakdown:**

- Bar chart showing the average score for each of the 8 dimensions across all diagrams
- Highlights the weakest dimension (the bottleneck to overall quality)

**Section C — Complexity band table:**

- The existing band breakdown from `quality-report.json` (small / medium / large / very_large)
- Count, average structural accuracy, min structural accuracy per band
- Expanded to include all 8 dimensions

**Section D — Worst performers:**

- Bottom 5 diagrams by average score
- Direct links to their detail views

### Cross-Run Comparison (`comparison.html`)

When `viewer.py` is invoked with multiple run directories, it generates `comparison.html` in the parent `eval-results/` directory:

- **Run selector:** dropdown or tabs for each run (by timestamp)
- **Per-diagram trend:** for diagrams that appear in multiple runs, show score progression (improvement or regression)
- **Aggregate trend:** overall averages per run, plotted as a simple line/bar chart (vanilla JS canvas or SVG — no Chart.js dependency)
- **Diff highlights:** diagrams whose scores changed significantly (>1 point delta) between runs, flagged for attention

Diagrams are correlated across runs by name (the diagram slug from `quality.json`).

## Data Flow

```
eval run completes
    │
    ▼
per-diagram directories exist with:
    ├── quality.json (8 scores per variant + verification)
    ├── {name}_source.png
    ├── {name}_darkmode.png
    ├── {name}_minimal.png
    ├── {name}_sketchnote.png
    └── {name}_claymation.png
    │
    ▼
recipe invokes: python -m diagram_beautifier.viewer {run_dir}
    │
    ▼
viewer.py scans run directory
    ├── reads all quality.json files
    ├── discovers all PNGs (variants + source)
    ├── aggregates scores across diagrams
    └── generates report.html with relative image paths
    │
    ▼
report.html lives in {run_dir}/report.html
    └── open in any browser, no server needed
```

## Recipe Integration

Add one step at the end of `recipes/evaluate-diagrams.yaml`:

```yaml
- id: generate-viewer
  type: bash
  command: |
    python -m diagram_beautifier.viewer "{{run_dir}}"
    echo "Report generated: {{run_dir}}/report.html"
```

Runs after `generate-report`. Produces `report.html` in the same run directory.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Missing `quality.json` for a diagram | Show card in grid with a "no data" badge; skip from aggregates |
| Missing variant PNGs | Show placeholder in image strip; note which variants are missing |
| Old-format `quality.json` (2 dimensions) | Display available scores; show "N/A" for missing dimensions |
| Missing source render | Show "source not available" placeholder in detail view image strip |
| Empty run directory | Show an informative message instead of a blank page |

## Testing Strategy

- **Unit tests for data loading:** test `quality.json` parsing (both 2-dim and 8-dim formats), PNG discovery, source image resolution
- **Unit tests for HTML generation:** test that generated HTML contains expected elements for a known test fixture (a minimal eval-results directory with 2-3 diagrams)
- **Integration test:** generate `report.html` from the existing eval run (`2026-04-08_160419-diagrams`) and verify it's valid HTML and references existing image files
- **Cross-run test:** generate `comparison.html` from two mock run directories and verify trend data

## Out of Scope

- No server, no deployment, no authentication
- No real-time updating (it's a snapshot of a completed run)
- No image editing or annotation
- No database — all data comes from JSON files on disk
- No external JS/CSS dependencies (everything inline)
- No framework (React, Vue, etc.) — vanilla HTML/CSS/JS only

## Open Questions

None — design is fully validated.
