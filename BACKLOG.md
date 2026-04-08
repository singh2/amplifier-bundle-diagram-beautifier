# Diagram Beautifier — Backlog

Deferred improvements tracked for future work. Items are prioritized but
not scheduled.

---

## High Value — Next Up

### Cross-Variant Topology Comparison

**Problem:** The 4 aesthetic variants are reviewed independently. Dark Mode
Tech could preserve all nodes while Sketchnote drops a subgraph — and nothing
catches this because there is no cross-variant comparison step.

**Proposed solution:** After all 4 variants pass individual review (Step 6),
add a comparison step that verifies all 4 variants contain the same node set
and connection topology using the topology manifest as the shared reference.
Flag any variant that diverges.

**Effort:** Medium. Requires a new review prompt or programmatic check that
extracts labels from each variant and compares them.

---

### PNG Input Diversity

**Problem:** All 6 PNG eval inputs are AI workflow flowcharts. The PNG-direct
pipeline's topology extraction from non-flowchart visuals (ER diagrams, class
diagrams, network topologies) is completely untested.

**Proposed solution:** Add 2-3 PNG inputs of different diagram types:
- One ER diagram PNG
- One network topology or architecture diagram PNG
- One class diagram PNG

**Effort:** Low. Create or screenshot suitable diagrams and add to
`eval/diagrams/`.

---

## Medium Value

### Mermaid `stateDiagram` and `gantt` Support

**Problem:** Parser handles 4 Mermaid types but not `stateDiagram` or `gantt`.
These have distinct visual structures (state machines with transitions, Gantt
bar charts) that would test different topology extraction paths.

**Proposed solution:**
1. Add `stateDiagram` parsing to `parser.py`
2. Add one `.mmd` state diagram to eval inputs
3. Consider `gantt` support (lower priority — bar charts are structurally
   very different from node-edge graphs)

**Effort:** Low-Medium for stateDiagram, Medium for gantt.

---

### Reconcile `prompt.py` with Agent Instructions

**Problem:** `build_beautify_prompt()` produces a generic prompt with aesthetic
template + structural modifier. The agent's Steps 5a-5d describe elaborate
per-variant prompt construction (hexagonal nodes, neon accents, etc.) that the
Python function doesn't implement — the agent constructs these inline.

**Proposed solution:** Either enrich the Python module to produce per-variant
prompts, or document that the library handles structural preservation while the
agent handles aesthetic creativity. The current implicit split works but is
undocumented.

**Effort:** Medium if enriching library, Low if documenting the split.