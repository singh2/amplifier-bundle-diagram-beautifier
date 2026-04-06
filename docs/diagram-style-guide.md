# Diagram Style Guide

> **Scope:** This guide applies ONLY to diagram beautification via the
> `diagram-beautifier` agent. Infographic generation does not reference
> this file.

For general aesthetic templates (background, typography, color palette,
lighting, texture, mood), see `docs/style-guide.md` — the curated
aesthetic definitions there are the source of truth for both infographics
and diagrams. This file extends those templates with diagram-specific
node shape and connector guidance.

---

## Four Variants

Every beautification produces four variants simultaneously, using two generation
approaches across four fixed aesthetics.

**Dark Mode Tech** and **Clean Minimalist** use the **Polished** approach:
document-ready, faithful aesthetic application, clean connectors, fresh but
coherent spatial composition. For PNG input, the source is passed as a
reference image (completeness guard only). The result should feel like
"yes, that's what I meant, but beautiful."

**Hand-Drawn Sketchnote** and **Claymation Studio** use the **Cinematic**
approach: presentation-ready, topology as script, editorial emphasis. The
hero candidate gets visual prominence as the compositional focal point. No
reference image ever. Spatial composition serves the visual. The viewer
should stop and look.

**Claymation** has two sub-modes chosen automatically by the model in Step 3:
- **Normal**: sculpted clay nodes in a neutral clay environment, size encodes
  importance, rope/ribbon connectors
- **Diorama**: clay figures acting out the workflow in a physical scene, nodes
  staged left-to-right in sequence, domain-appropriate props and environment

**Shared across all four variants:**
- Same topology manifest
- Same panel decomposition
- Same 8 quality review dimensions

**Key differences by generation approach:**

| Dimension | Dark Mode Tech + Clean Minimalist | Sketchnote + Claymation |
|---|---|---|
| Reference image (PNG input) | Completeness guard | Never |
| Connector style | Clean / orthogonal | Expressive / gestural |
| Spatial freedom | Fresh but coherent | Fully compositional |
| Hero node emphasis | Maintained via color/scale | Dominant visual anchor |

---

## Node Shapes

Apply the per-aesthetic shape spec when constructing generation prompts.

| Aesthetic | Script Step | AI Agent Step | Condition | Start / End |
|---|---|---|---|---|
| **Clean Minimalist** | Rounded rect, 12px radius | Rounded rect, 12px radius | Diamond | Stadium / pill |
| **Dark Mode Tech** | Rounded rect, 6px radius | Hexagon | Diamond | Stadium / pill |
| **Bold Editorial** | Bold rect with thick color border | Bold rect with thick color border | Diamond with bold border | Bold stadium |
| **Hand-Drawn Sketchnote** | Wobbly outlined rounded rect | Wobbly outlined rounded rect | Wobbly diamond | Wobbly oval |
| **Claymation Studio** | Sculpted clay blob | Sculpted clay blob | Rounded clay blob | Clay oval |
| **Lego Brick Builder** | Brick-built rectangular construction | Brick-built rectangular construction | Brick diamond | Brick oval |

---

## Connector Styling

| Aesthetic | Connector style | Special constraints |
|---|---|---|
| **Clean Minimalist** | Orthogonal only (H/V segments, 4px rounded joins). **Diagonal edges strictly forbidden.** | Canvas must contain EXACTLY N diagram nodes. Legend must use text + colored squares only — no floating sample nodes. |
| **Dark Mode Tech** | Curved bezier paths; gradient glow from source-node color to destination-node color; arrowheads with matching neon glow tips. | Render exactly **ONE** legend box (bottom-right). Do not duplicate. |
| **Bold Editorial** | Heavy straight lines with bold arrowheads matching source-node border color. | — |
| **Hand-Drawn Sketchnote** | Hand-drawn arrows, slightly wobbly curves, informal arrowheads. | — |
| **Claymation Studio** | Rope or ribbon connectors, soft curves. | — |
| **Lego Brick Builder** | Rigid brick-peg connector rods. | — |

---

## Cinematic Guidance Per Aesthetic

Variants C (Sketchnote) and D (Claymation) use the Cinematic generation approach.
Apply these directives on top of the shared Cinematic rules above.

| Aesthetic | Cinematic guidance |
|---|---|
| **Hand-Drawn Sketchnote** | Gestural organic spacing between nodes; wobbly arrows with varying weight; hero node gets hand-drawn callout or emphasis circle. |
| **Claymation Studio — Normal** | Full scene with sculpted characters/objects in clay environment; rope or ribbon connectors; hero node is physically larger or more prominent than surrounding nodes. |
| **Claymation Studio — Diorama** | Physical scene with clay figures enacting the workflow steps in sequence; nodes staged as characters or props in a shallow-depth environment; hero node is the most elaborately sculpted figure; warm studio lighting; domain-appropriate miniature props. |

---

## Prompt Construction Rules

These rules govern how generation prompts are assembled for diagrams.
See Step 5 of the diagram-beautifier workflow for the full ordering spec.

### Quality bar directive (always first)

Always open the generation prompt with:

> "This should be dramatically more visually impressive than the source
> diagram — publication quality, not a recolored version of the input."

### Aesthetic before structural

VLMs respond better when the aesthetic directive appears before structural
preservation constraints. State the full aesthetic (background, nodes,
connectors, typography, lighting) first; state topology preservation last.

### Color-category mapping

When the source diagram has a semantic color legend, explicitly list every
category and the node names that belong to it. Do not rely on the reference
image — state the mapping in plain text.

Example:
```
Script Steps (cyan border): Check Environment, Discover Recipes,
  Validate Structure, Check Best Practices, Validate Semantics,
  Quick Approval, Compile Report
AI Agent Steps (purple border): Classify Quality, Check Diagram Freshness
Condition diamonds (green border): All clean?, Issues found?
Start/End terminals (gray border): Start, Done
```
