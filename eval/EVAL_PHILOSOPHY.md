# Evaluation Philosophy

## Purpose

This document defines how we think about evaluation coverage for the
diagram-beautifier system, why the eval set is structured the way it is,
and how to extend it without losing signal or creating redundancy.

The eval has three jobs:
1. **Regression detection** -- did a change to the agent, style guide, or
   pipeline break something that was working?
2. **Capability coverage** -- does the system handle all input formats and
   complexity levels we claim to support?
3. **Threshold detection** -- at what complexity level does the generation
   start dropping nodes, edges, or labels?

An eval input that does none of these is dead weight.

Unlike infographic-builder's scenario-based eval, diagram-beautifier's eval
is input-based: every file in `eval/diagrams/` is run through the full
pipeline (all four variants). There is no tier system -- all inputs run every
time.

---

## Dimension Space

### Dimension 1 -- Input Format

| Value | How it enters the pipeline |
|-------|--------------------------|
| `.dot` | Graphviz source -> topology manifest extract -> 4 variants |
| `.mmd` | Mermaid source -> topology manifest extract -> 4 variants |
| `.png` | Existing diagram image -> topology manifest extract (skip render) -> 4 variants |

**Coverage target:** At least 3 files per format. For `.mmd`, diversity of
diagram types: `flowchart`, `sequenceDiagram`, `classDiagram`, `erDiagram`.

---

### Dimension 2 -- Diagram Complexity

Controls panel decomposition behavior in `diagram_beautifier/decompose.py`.

| Range | Behavior |
|-------|---------|
| <=10 nodes | 1 panel |
| 11-25 nodes, multi-subgraph | Up to 3 panels |
| 26-40 nodes | Up to 4 panels |
| 41+ nodes | Up to 6 panels |

Also controls Claymation sub-mode:
- <=12 nodes, sequential workflow -> **Diorama mode** (characters in scene)
- 13+ nodes, or architectural/hierarchical -> **Normal Claymation**

**Coverage target:** At least one diagram in each complexity band. Both
Diorama and Normal Claymation must be triggered.

---

### Dimension 3 -- Topological Pattern

Tests different graph structures that stress different aspects of the pipeline.

| Pattern | What it stresses |
|---------|-----------------|
| Linear chain | Basic flow preservation |
| Hub-and-spoke | Central node with many connections |
| DAG with parallel branches + convergence | Fork/join topology |
| Cyclic (back-edges / loops) | Non-DAG representation |
| Entity-relationship | Non-flowchart structure |
| Class hierarchy | Inheritance/composition edges |
| Sequence/temporal | Participant-message structure |
| Dense mesh | High edge-to-node ratio (edge fidelity) |

---

### Dimension 4 -- Edge Density

Measures how many connections exist relative to the node count.

| Density | Description | Example |
|---------|-------------|---------|
| Sparse (< 0.1) | Tree-like, most nodes have 1-2 edges | Linear workflows |
| Medium (0.1-0.2) | Moderate cross-connections | Microservice architectures |
| Dense (> 0.2) | Many-to-many relationships | Module dependency graphs |

**Coverage target:** At least one diagram in each density band.

---

## Evaluation Criteria

### Quality Review (VLM-based, per variant)

8 dimensions scored 1-5 by VLM via `nano-banana analyze`:

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 1 | Content accuracy | Correct content representation |
| 2 | Layout quality | Spatial arrangement and readability |
| 3 | Visual clarity | Legibility and contrast |
| 4 | Prompt fidelity | Adherence to the generation prompt |
| 5 | Aesthetic fidelity | Consistency with target aesthetic |
| 6 | Label fidelity | All text labels match topology manifest |
| 7 | Structural accuracy | Node count and connections match manifest |
| 8 | Color-category fidelity | Nodes under correct semantic categories |

**Scoring rubric (applies to dimensions 6-7):**
- 5 = Perfect match to ground truth
- 4 = Near-perfect, 1-2 minor issues
- 3 = Good, >80% correct
- 2 = Significant gaps, >20% missing
- 1 = Major failure, >40% missing

**Refinement threshold:** Any dimension scoring below 3 triggers a targeted
refinement pass (max 1 per panel per variant).

### Programmatic Verification (code-based, per diagram)

Independent of VLM self-assessment. Uses `diagram_beautifier/verify.py`:

| Check | Method | Output |
|-------|--------|--------|
| Label completeness | VLM extraction + fuzzy matching (difflib) | 0.0-1.0 score + missing list |
| Edge completeness | VLM extraction + fuzzy matching (difflib) | 0.0-1.0 score + missing list |
| OCR cross-check | pytesseract (optional, if installed) | Independent label extraction |

### Aggregate Reporting

The eval recipe produces `quality-report.json` with:
- Per-diagram quality scores (VLM ratings + verification scores)
- Aggregate averages across all diagrams
- Complexity band analysis (avg/min scores per band)
- Missing labels and edges lists for threshold detection

---

## Current Coverage Matrix

### By Input Format

| Format | Files | Mermaid Types |
|--------|:-----:|--------------|
| `.dot` | 12 | N/A |
| `.mmd` | 6 | flowchart TD, sequenceDiagram, classDiagram, erDiagram |
| `.png` | 6 | mixed AI workflow flowcharts |

### By Diagram Complexity

| Complexity | Node Range | Diagrams | Claymation Sub-mode |
|-----------|:----------:|----------|:------------------:|
| Small | <=10 nodes | comprehensive-review (5), multi-repo-activity-report (9), conditional-workflow (10) | Diorama |
| Medium | 11-25 | amplifier-module-types (11), code-review-recipe (11), amplifier-bundle-composition (12), dependency-upgrade-staged-recipe (12), amplifier-context-sink (13), component-map (13), multi-level-python-code-analysis (18), amplifier-session-loop (21), amplifier-hook-lifecycle (22), amplifier-agent-spawn (24) | Normal |
| Large | 26-40 | ecommerce-microservices (36, 5 subgraphs) | Normal |
| Very large | 41+ | data-platform-architecture (50, 8 subgraphs, feedback cycle) | Normal |

### By Edge Density

| Density Band | Diagram | Nodes | Edges | Density |
|-------------|---------|:-----:|:-----:|:-------:|
| Sparse | comprehensive-review | 5 | 4 | 0.08 |
| Medium | amplifier-module-types | 11 | 14 | 0.13 |
| Dense | dense-module-dependencies | 18 | 61 | 0.20 |

### Behavior Coverage

| Behavior | Status |
|---------|:------:|
| `.dot` render -> beautify | Done |
| `.mmd` render -> beautify | Done |
| PNG direct -> beautify | Done |
| Diorama sub-mode | Done |
| Normal Claymation | Done |
| Multi-panel decomposition (3 panels) | Done |
| Multi-panel decomposition (4 panels) | Done |
| Multi-panel decomposition (6 panels) | Done |
| All 4 aesthetic variants generated | Done |
| Topology manifest as quality ground truth | Done |
| Numerical quality scoring (1-5) | Done |
| Programmatic label verification | Done |
| Structured quality reporting (JSON) | Done |

---

## Running the Eval

```bash
# Run all diagrams -- always runs everything (no filtering)
amplifier run -B diagram-beautifier "execute recipes/evaluate-diagrams.yaml"

# Output per diagram (96 images total: 24 diagrams x 4 variants):
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_darkmode.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_minimal.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_sketchnote.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_claymation.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/quality.json
#
# Aggregate quality report:
#   eval-results/<timestamp>-diagrams/quality-report.json
```

---

## Adding New Eval Inputs

Before adding an input, answer:

1. **Which cell in the matrix does this fill?** If the format and complexity
   band are already well-covered, the input is redundant unless it exercises
   a meaningfully different topology (e.g., a very wide graph vs. a deep tree).

2. **Which format?** Prefer `.dot` or `.mmd` source files over `.png` inputs
   where possible -- they exercise the render step and give deterministic
   topology for quality review.

3. **What complexity?** Consider whether this input helps with threshold
   detection -- is it at a scale where we expect the pipeline to struggle?

4. **Does it exercise a distinct Mermaid type?** `stateDiagram` and `gantt`
   are not currently represented in `.mmd` inputs.

5. **What density?** If the input has an unusually high edge-to-node ratio,
   it may stress edge fidelity in ways existing inputs don't.

Input file naming convention:
```
eval/diagrams/<descriptive-slug>.<dot|mmd|png>
```

---

## Known Remaining Gaps

See `BACKLOG.md` at project root for deferred improvements.

| Gap | Priority | Notes |
|-----|:--------:|-------|
| `.png` input diversity (all flowcharts currently) | Medium | Add an ER diagram or network topology PNG |
| Mermaid `stateDiagram` type not covered | Low | Add one `.mmd` state diagram |
| Cross-variant topology comparison | Low | Verify all 4 variants contain same topology |
