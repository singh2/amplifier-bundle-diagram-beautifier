# Diagram Beautifier

Transform plain Graphviz, Mermaid, or PNG diagrams into publication-quality infographic visuals — preserving every node, edge, and label while upgrading the aesthetics.

One input produces four styled variants automatically. The topology never changes; only the presentation does.

## Getting Started

Diagram Beautifier is an [Amplifier](https://github.com/microsoft/amplifier) bundle.

### Prerequisites

| Requirement | Purpose | Install |
|-------------|---------|---------|
| **`GOOGLE_API_KEY`** | Gemini image generation (nano-banana) | Set in your environment |
| **Graphviz** | Renders `.dot` files to PNG before beautification | `brew install graphviz` |
| **Mermaid CLI** | Renders `.mmd` files to PNG before beautification | `npm i -g @mermaid-js/mermaid-cli` |

You only need the renderer for the format you're using. If you're beautifying an existing PNG, neither is required.

### Activate the bundle

In your project's `.amplifier/settings.yaml`:

```yaml
bundle:
  active: diagram-beautifier
```

### Beautify a diagram

Start an Amplifier session and ask in natural language:

```
Beautify eval/diagrams/comprehensive-review.dot
```

```
Beautify this Mermaid diagram: eval/diagrams/auth-sequence.mmd
```

```
Beautify this existing diagram screenshot: my-architecture.png
```

The agent handles everything from there — parsing, rendering, variant generation, quality review, and output.

## Supported Inputs

| Format | Extensions | Notes |
|--------|------------|-------|
| **Graphviz DOT** | `.dot` | Full pipeline — parsed, rendered, then beautified |
| **Mermaid** | `.mmd`, `.mermaid` | Supports `flowchart`, `sequenceDiagram`, `erDiagram`, `classDiagram` |
| **Existing PNG** | `.png` | Shortened pipeline — analyzed by vision model, then beautified |

## Output

You get four visually distinct renderings of the same diagram:

| Variant | Style | Description |
|---------|-------|-------------|
| **A — Dark Mode Tech** | Polished | Deep dark background, neon accents, glowing connectors, glassmorphism |
| **B — Clean Minimalist** | Polished | White/light-gray background, neutral palette, orthogonal connectors |
| **C — Hand-Drawn Sketchnote** | Cinematic | Kraft-paper texture, wobbly outlines, marker colors, hand-lettered labels |
| **D — Claymation Studio** | Cinematic | Sculpted clay figures, warm studio lighting, fingerprint textures |

For complex diagrams (25+ nodes), variants C and D automatically switch to **Blueprint/Schematic** and **Cyberpunk/Neon** styles that handle density better.

PNG files are saved to `./infographics/`, named by input:

```
infographics/
  my-diagram_dark-mode-tech.png
  my-diagram_clean-minimalist.png
  my-diagram_sketchnote.png
  my-diagram_claymation.png
```

Multi-panel diagrams (11+ nodes with subgraphs) are automatically decomposed into panels and stitched back together.

## How It Works

The pipeline runs in 8 steps:

```
Parse → Check Deps → Select Aesthetics → Decompose Panels →
  Beautify (×4) → Quality Review → Assemble → Present
```

1. **Parse** — Extracts a topology manifest from the input: nodes (classified as terminal, decision, process, or subprocess), edges, subgraphs, and counts. DOT and Mermaid are parsed structurally. PNGs are analyzed by a vision model.

2. **Dependency Check** — Verifies that `dot` (Graphviz) or `mmdc` (Mermaid CLI) is available for source-format inputs. Skipped for PNG.

3. **Aesthetic Selection** — All four variants are always generated. The agent decides between Claymation Normal vs. Diorama mode based on node semantics, and substitutes Blueprint/Cyberpunk styles for high-complexity diagrams.

4. **Panel Decomposition** — Determines how many panels the diagram needs based on node count and subgraph structure (1–6 panels). Small diagrams stay as a single panel.

5. **Beautify (×4)** — Each variant is generated via nano-banana (Gemini image generation) with a carefully constructed prompt covering quality bar, aesthetic properties, node shapes, color mapping, and structural preservation. The source diagram PNG is passed as a reference image.

6. **Quality Review** — Each variant is reviewed across 8 dimensions (content accuracy, layout quality, visual clarity, prompt fidelity, aesthetic fidelity, label fidelity, structural accuracy, color-category fidelity). Scores below 3/5 trigger a refinement pass. A separate programmatic verification step uses fuzzy string matching to independently check label and edge preservation.

7. **Assemble** — For multi-panel diagrams, panels are stitched vertically or horizontally based on the diagram's flow direction.

8. **Present** — All four variants are delivered with quality scores and rationale.

## Batch Evaluation

To run the full evaluation suite across all 24 test diagrams:

```
Run the recipe at recipes/evaluate-diagrams.yaml
```

View the results as an HTML report:

```bash
python -m diagram_beautifier.viewer eval-results/<timestamp>-diagrams/
```

## Project Structure

```
diagram-beautifier/
├── bundle.md                      # Bundle definition (entry point)
├── agents/
│   └── diagram-beautifier.md      # Main agent — full 8-step workflow
├── behaviors/
│   └── diagram.yaml               # Tool registration (nano-banana, stitch-panels)
├── context/
│   └── diagram-awareness.md       # Root session routing instructions
├── docs/
│   ├── style-guide.md             # Master aesthetic templates (6 styles)
│   └── diagram-style-guide.md     # Diagram-specific node shapes and connectors
├── diagram_beautifier/            # Python library
│   ├── parser.py                  # DOT + Mermaid parser
│   ├── decompose.py               # Panel decomposition logic
│   ├── prompt.py                  # Prompt builder
│   ├── renderer.py                # CLI rendering (dot/mmdc → PNG)
│   ├── deps.py                    # Dependency checker
│   ├── review.py                  # Quality review prompts
│   ├── verify.py                  # Programmatic label/edge verification
│   └── viewer.py                  # Eval report HTML generator
├── modules/
│   └── tool-stitch-panels/        # Panel stitching tool module
├── recipes/
│   └── evaluate-diagrams.yaml     # Batch evaluation recipe
├── eval/
│   └── diagrams/                  # 24 test inputs (10 .dot, 7 .mmd, 7 .png)
└── tests/                         # Test suite
```

## Tips

- **Start with DOT or Mermaid source** if you have it. The parser extracts exact topology, which produces more faithful results than vision-model analysis of a PNG.
- **Simpler diagrams produce better results.** 5–15 nodes is the sweet spot. Above 25, the system compensates with style substitution and multi-panel decomposition, but fidelity naturally decreases with complexity.
- **Labels matter.** The quality review checks label preservation with fuzzy matching. If your source diagram has clear, readable labels, the output will be more accurate.
- **You can iterate.** After seeing the four variants, ask for refinements in the same session — the agent retains context and can regenerate specific variants.

## Known Limitations

- Mermaid `stateDiagram` and `gantt` chart types are not yet supported.
- PNG inputs are analyzed by a vision model, which may miss subtle topology details that structural parsing would catch.
- Variants are reviewed independently — there's no cross-variant topology comparison to ensure all four preserved the same structure.
- Very dense diagrams (40+ nodes) may lose minor labels or edges despite the quality review pass.

## License

MIT
