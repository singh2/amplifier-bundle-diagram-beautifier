"""Build nano-banana generate prompts for diagram beautification."""

from __future__ import annotations

STRUCTURAL_PRESERVATION_MODIFIER = """\
STRUCTURAL PRESERVATION REQUIREMENTS:
- This is a diagram beautification. The reference image shows the exact topology to preserve.
- Maintain all node positions, connections, and directional flow from the reference image.
- Reproduce every text label EXACTLY as shown -- spelling, capitalization, and content must match.
- Preserve the directed/undirected nature of all edges.
- Enhance the visual presentation (colors, shapes, textures, lighting) without altering the structure.
- Node shapes may be stylized to match the aesthetic but must remain visually distinct and readable."""


def build_beautify_prompt(
    aesthetic_template: str,
    diagram_type: str,
    node_labels: list[str],
    edge_labels: list[str],
) -> str:
    """Build a nano-banana generate prompt for diagram beautification."""
    lines: list[str] = [
        f"Beautify this {diagram_type} diagram as a polished, publication-ready visual.",
        "",
        "AESTHETIC STYLE:",
        aesthetic_template,
        "",
        STRUCTURAL_PRESERVATION_MODIFIER,
        "",
        "EXACT TEXT LABELS TO REPRODUCE:",
        f"Node labels: {', '.join(node_labels)}",
    ]
    if edge_labels:
        lines.append(f"Edge labels: {', '.join(edge_labels)}")
    lines += [
        "",
        "Render every label listed above with precise spelling. Do not omit, truncate, or paraphrase any label.",
    ]
    return "\n".join(lines)
