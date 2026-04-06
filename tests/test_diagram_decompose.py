"""Tests for diagram_beautifier/decompose.py -- panel decomposition logic."""
from __future__ import annotations
from diagram_beautifier.decompose import decide_panels


def test_small_diagram_single_panel() -> None:
    result = decide_panels(node_count=8, subgraphs=[
        {"name": "A", "node_ids": ["1", "2", "3", "4"]},
        {"name": "B", "node_ids": ["5", "6", "7", "8"]},
    ])
    assert result["panel_count"] == 1
    assert result["strategy"] == "single"


def test_medium_diagram_no_subgraphs_single_panel() -> None:
    result = decide_panels(node_count=20, subgraphs=[])
    assert result["panel_count"] == 1
    assert result["strategy"] == "single"


def test_medium_diagram_one_subgraph_single_panel() -> None:
    result = decide_panels(node_count=15, subgraphs=[
        {"name": "Main", "node_ids": [str(i) for i in range(15)]},
    ])
    assert result["panel_count"] == 1
    assert result["strategy"] == "single"


def test_medium_diagram_multiple_subgraphs_splits() -> None:
    result = decide_panels(node_count=20, subgraphs=[
        {"name": "Frontend", "node_ids": [str(i) for i in range(10)]},
        {"name": "Backend", "node_ids": [str(i) for i in range(10, 20)]},
    ])
    assert result["panel_count"] >= 2
    assert result["strategy"] == "subgraph_split"


def test_large_diagram_splits() -> None:
    result = decide_panels(node_count=30, subgraphs=[
        {"name": "A", "node_ids": [str(i) for i in range(15)]},
        {"name": "B", "node_ids": [str(i) for i in range(15, 30)]},
    ])
    assert result["panel_count"] >= 2
    assert result["strategy"] == "subgraph_split"


def test_very_large_diagram_splits_max_6() -> None:
    result = decide_panels(node_count=80, subgraphs=[
        {"name": f"Group{i}", "node_ids": [str(j) for j in range(i * 10, (i + 1) * 10)]}
        for i in range(8)
    ])
    assert result["panel_count"] >= 3
    assert result["panel_count"] <= 6


def test_large_diagram_no_subgraphs_suggests_single() -> None:
    result = decide_panels(node_count=35, subgraphs=[])
    assert result["panel_count"] == 1
    assert result["strategy"] == "single"
    assert result.get("warning") is not None


def test_panel_assignments_cover_all_subgraphs() -> None:
    result = decide_panels(node_count=30, subgraphs=[
        {"name": "Frontend", "node_ids": ["A", "B", "C"]},
        {"name": "Backend", "node_ids": ["D", "E", "F"]},
        {"name": "Database", "node_ids": ["G", "H", "I"]},
    ])
    assigned_subgraphs = set()
    for panel in result["panels"]:
        for sg_name in panel["subgraph_names"]:
            assigned_subgraphs.add(sg_name)
    assert assigned_subgraphs == {"Frontend", "Backend", "Database"}
