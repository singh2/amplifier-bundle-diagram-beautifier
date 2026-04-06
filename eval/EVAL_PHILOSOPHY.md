# Evaluation Philosophy

## Purpose

This document defines how we think about evaluation coverage for the
diagram-beautifier system, why the eval set is structured the way it is,
and how to extend it without losing signal or creating redundancy.

The eval has two jobs:
1. **Regression detection** — did a change to the agent, style guide, or
   pipeline break something that was working?
2. **Capability coverage** — does the system handle all input formats and
   complexity levels we claim to support?

An eval input that does neither is dead weight.

Unlike infographic-builder's scenario-based eval, diagram-beautifier's eval
is input-based: every file in `eval/diagrams/` is run through the full
pipeline (all four variants). There is no tier system — all inputs run every
time.

---

## Dimension Space

### Dimension 1 — Input Format

| Value | How it enters the pipeline |
|-------|--------------------------| 
| `.dot` | Graphviz source → `dot -Tpng` render → topology manifest extract → 4 variants |
| `.mmd` | Mermaid source → `mmdc` render → topology manifest extract → 4 variants |
| `.png` | Existing diagram image → topology manifest extract (skip render) → 4 variants |

**Coverage target:** At least 3 files per format. For `.mmd`, diversity of
diagram types: `flowchart`, `sequenceDiagram`, `classDiagram`, `erDiagram`.

---

### Dimension 2 — Diagram Complexity

Controls panel decomposition behavior in `diagram_beautifier/decompose.py`.

| Range | Behavior |
|-------|---------|
| ≤10 nodes | 1 panel |
| 11–25 nodes, multi-subgraph | Up to 3 panels |
| 26–40 nodes | Up to 4 panels |
| 41+ nodes | Up to 6 panels |

Also controls Claymation sub-mode:
- ≤12 nodes, sequential workflow → **Diorama mode** (characters in scene)
- 13+ nodes, or architectural/hierarchical → **Normal Claymation**

**Coverage target:** At least one diagram in each complexity band. Both
Diorama and Normal Claymation must be triggered.

---

## Current Coverage Matrix

### By Input Format

| Format | Files | Mermaid Types |
|--------|:-----:|--------------|
| `.dot` | 9 | N/A |
| `.mmd` | 6 | flowchart TD, sequenceDiagram, classDiagram, erDiagram |
| `.png` | 6 | mixed AI workflow flowcharts |

### By Diagram Complexity

| Complexity | Node Range | Example | Claymation Sub-mode |
|-----------|:----------:|---------|:------------------:|
| Small | ≤10 nodes | conditional-workflow-v1 (9) | Diorama ✓ |
| Medium | 11–25 | amplifier-module-types (11), recipe-validation (13) | Normal ✓ |
| Large | 21+ | amplifier-session-loop (21, 2 subgraphs) | Normal ✓ |
| Very large | 41+ | ✗ (no test for 4+ panel decomposition) | — |

### Behavior Coverage

| Behavior | Status |
|---------|:------:|
| `.dot` render → beautify | ✓ |
| `.mmd` render → beautify | ✓ |
| PNG direct → beautify | ✓ |
| Diorama sub-mode | ✓ |
| Normal Claymation | ✓ |
| Multi-panel decomposition (3 panels) | ✓ |
| Multi-panel decomposition (4+ panels) | ✗ |
| All 4 aesthetic variants generated | ✓ |
| Topology manifest as quality ground truth | ✓ |

---

## Running the Eval

```bash
# Run all diagrams — always runs everything (no filtering)
amplifier run -B diagram-beautifier "execute recipes/evaluate-diagrams.yaml"

# Output per diagram (84 images total: 21 diagrams × 4 variants):
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_darkmode.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_minimal.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_sketchnote.png
#   eval-results/<timestamp>-diagrams/<diagram-name>/<diagram-name>_claymation.png
```

---

## Adding New Eval Inputs

Before adding an input, answer:

1. **Which cell in the matrix does this fill?** If the format and complexity
   band are already well-covered, the input is redundant unless it exercises
   a meaningfully different topology (e.g., a very wide graph vs. a deep tree).

2. **Which format?** Prefer `.dot` or `.mmd` source files over `.png` inputs
   where possible — they exercise the render step and give deterministic
   topology for quality review.

3. **What complexity?** The 41+ node band (4+ panel decomposition) is the
   current gap. Adding one large `.dot` file there would complete coverage.

4. **Does it exercise a distinct Mermaid type?** `stateDiagram` and `gantt`
   are not currently represented in `.mmd` inputs.

Input file naming convention:
```
eval/diagrams/<descriptive-slug>.<dot|mmd|png>
```

---

## Known Remaining Gaps

| Gap | Priority | Notes |
|-----|:--------:|-------|
| Very large diagram (41+ nodes) for 4+ panel decomposition | Low | Add one `.dot` with 45+ nodes |
| `.png` input diversity (all flowcharts currently) | Low | Add an ER diagram or network topology PNG |
| Mermaid `stateDiagram` type not covered | Low | Add one `.mmd` state diagram |
