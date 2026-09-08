# Diagram Beautifier

You have access to diagram beautification via the
`diagram-beautifier:diagram-beautifier` agent — it takes Graphviz (`.dot`),
Mermaid (`.mmd`), or existing diagram PNGs and re-renders them as
infographic-quality visuals, preserving the original topology and labels.

## When to Use

- User asks to beautify, restyle, or improve the look of a diagram they already have
- User supplies a `.dot`, `.mmd`, `.mermaid`, or diagram `.png` file and wants it
  rendered attractively
- User pastes Graphviz or Mermaid source (`digraph`, `graph`, `flowchart`) and asks
  for a visual version of it
- User asks for a particular aesthetic on an existing diagram — "make this flowchart
  claymation", "dark mode version of this architecture diagram"

## How to Use

Delegate the request as-is. The agent parses the source, extracts a topology
manifest, checks renderer dependencies, generates styled variants, runs its own
quality review, and assembles the output. It is fully self-contained — no file
reading, research, or preparation is needed before delegating.

    delegate(agent="diagram-beautifier:diagram-beautifier",
             instruction="<the user's request, verbatim>")

## Prerequisites

- `GOOGLE_API_KEY` must be set (Gemini image analysis via nano-banana)
- `dot` CLI for `.dot` sources (Graphviz: `brew install graphviz`)
- `mmdc` CLI for `.mmd` sources (`npm i -g @mermaid-js/mermaid-cli`)
