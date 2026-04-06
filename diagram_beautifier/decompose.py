"""Panel decomposition for diagrams based on graph structure."""

from __future__ import annotations
from typing import Any


def decide_panels(node_count: int, subgraphs: list[dict[str, Any]]) -> dict[str, Any]:
    """Decide panel decomposition based on node count and subgraph structure."""
    num_subgraphs = len(subgraphs)

    if node_count <= 10:
        return _single_panel_result(subgraphs)

    if node_count <= 25:
        if num_subgraphs <= 1:
            return _single_panel_result(subgraphs)
        return _split_by_subgraphs(subgraphs, max_panels=3)

    if num_subgraphs == 0:
        return {
            "panel_count": 1,
            "strategy": "single",
            "panels": [{"panel_number": 1, "subgraph_names": []}],
            "warning": (
                f"Diagram has {node_count} nodes but no subgraph declarations. "
                "Consider adding explicit subgraph groupings to your source "
                "for better multi-panel decomposition."
            ),
        }

    if node_count <= 40:
        return _split_by_subgraphs(subgraphs, max_panels=4)

    return _split_by_subgraphs(subgraphs, max_panels=6)


def _single_panel_result(subgraphs: list[dict[str, Any]]) -> dict[str, Any]:
    sg_names = [sg["name"] for sg in subgraphs]
    return {
        "panel_count": 1,
        "strategy": "single",
        "panels": [{"panel_number": 1, "subgraph_names": sg_names}],
    }


def _split_by_subgraphs(
    subgraphs: list[dict[str, Any]], max_panels: int
) -> dict[str, Any]:
    if len(subgraphs) <= max_panels:
        panels = [
            {"panel_number": i + 1, "subgraph_names": [sg["name"]]}
            for i, sg in enumerate(subgraphs)
        ]
    else:
        panels = []
        per_panel = len(subgraphs) / max_panels
        current: list[str] = []
        for i, sg in enumerate(subgraphs):
            current.append(sg["name"])
            if len(current) >= per_panel and len(panels) < max_panels - 1:
                panels.append(
                    {"panel_number": len(panels) + 1, "subgraph_names": current}
                )
                current = []
        if current:
            panels.append({"panel_number": len(panels) + 1, "subgraph_names": current})

    return {"panel_count": len(panels), "strategy": "subgraph_split", "panels": panels}
