"""Quality review prompt builders for diagram-specific dimensions."""

from __future__ import annotations


def build_label_fidelity_prompt(node_labels: list[str], edge_labels: list[str]) -> str:
    """Build a nano-banana analyze prompt for label fidelity checking."""
    lines: list[str] = [
        "LABEL FIDELITY CHECK:",
        "",
        "The source diagram contains these exact labels (ground truth):",
        f"Nodes: {', '.join(node_labels)}",
    ]
    if edge_labels:
        lines.append(f"Edge labels: {', '.join(edge_labels)}")
    lines += [
        "",
        "Check EVERY label in the generated image against this ground truth.",
        "Are any labels misspelled, truncated, missing, or replaced with different text? List each discrepancy.",
        "",
        "Rating: PASS (all labels correct) or NEEDS_REFINEMENT (any label wrong).",
    ]
    return "\n".join(lines)


def build_structural_accuracy_prompt(
    node_count: int,
    edge_count: int,
    node_labels: list[str],
    edge_pairs: list[tuple[str, str]],
) -> str:
    """Build a nano-banana analyze prompt for structural accuracy checking."""
    connections = "\n".join(f"  {src} \u2192 {dst}" for src, dst in edge_pairs)
    lines: list[str] = [
        "STRUCTURAL ACCURACY CHECK:",
        "",
        f"The source diagram has {node_count} nodes and {edge_count} connections.",
        f"Major nodes: {', '.join(node_labels)}",
        "Key connections:",
        connections,
        "",
        "Verify: Are all major nodes visible in the output? Are the primary connection paths represented? Is the directional flow preserved?",
        "",
        "Rating: PASS (topology preserved) or NEEDS_REFINEMENT (nodes/edges missing).",
    ]
    return "\n".join(lines)
