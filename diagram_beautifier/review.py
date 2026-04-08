"""Quality review prompt builders for diagram-specific dimensions.

All review prompts use a 1-5 numerical scoring rubric and request explicit
enumeration of visible elements for programmatic extraction downstream.
"""

from __future__ import annotations


def build_label_fidelity_prompt(node_labels: list[str], edge_labels: list[str]) -> str:
    """Build a prompt for label fidelity checking with 1-5 scoring."""
    all_labels = list(node_labels) + list(edge_labels)
    lines: list[str] = [
        "LABEL FIDELITY CHECK:",
        "",
        f"Ground truth labels from the source diagram ({len(all_labels)} total):",
        f"  Node labels ({len(node_labels)}): {', '.join(node_labels)}",
    ]
    if edge_labels:
        lines.append(f"  Edge labels ({len(edge_labels)}): {', '.join(edge_labels)}")
    lines += [
        "",
        "Instructions:",
        "1. List EVERY text label visible in this image.",
        "2. For each ground truth label, state: FOUND (exact match), CLOSE (minor difference), or MISSING.",
        "3. List any labels in the image NOT in ground truth (hallucinated).",
        "4. Counts: found_exact=N, found_close=N, missing=N, hallucinated=N",
        "",
        "Rating (1-5):",
        "  5 = All labels exact match, zero hallucinations",
        "  4 = All labels present, minor spelling or truncation on 1-2",
        "  3 = Most labels present (>80%), a few missing or wrong",
        "  2 = Significant gaps: many labels missing or wrong",
        "  1 = Majority of labels missing, wrong, or hallucinated",
    ]
    return "\n".join(lines)


def build_structural_accuracy_prompt(
    node_count: int,
    edge_count: int,
    node_labels: list[str],
    edge_pairs: list[tuple[str, str]],
) -> str:
    """Build a prompt for structural accuracy checking with 1-5 scoring."""
    connections = "\n".join(f"  {src} -> {dst}" for src, dst in edge_pairs)
    lines: list[str] = [
        "STRUCTURAL ACCURACY CHECK:",
        "",
        f"Ground truth: {node_count} nodes, {edge_count} connections.",
        "",
        f"Expected nodes ({node_count}):",
        f"  {', '.join(node_labels)}",
        "",
        f"Expected connections ({edge_count}):",
        connections,
        "",
        "Instructions:",
        "1. List EVERY node visible in the image.",
        "2. List EVERY connection visible: source -> destination.",
        "3. For each expected node: PRESENT or MISSING.",
        "4. For each expected connection: PRESENT or MISSING.",
        "5. Counts: nodes_present=N, nodes_missing=N, edges_present=N, edges_missing=N",
        "",
        "Rating (1-5):",
        "  5 = All nodes and connections present, correct directional flow",
        "  4 = All nodes present, 1-2 connections missing or unclear",
        "  3 = Most nodes present (>80%), some connections missing",
        "  2 = Significant gaps: >20% nodes or >30% connections missing",
        "  1 = Major structural failure: >40% nodes or >50% connections missing",
    ]
    return "\n".join(lines)
