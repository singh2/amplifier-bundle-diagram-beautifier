"""Tests for diagram_beautifier/review.py -- quality review prompt builders."""
from __future__ import annotations
from diagram_beautifier.review import build_label_fidelity_prompt, build_structural_accuracy_prompt


def test_label_fidelity_prompt_includes_all_node_labels() -> None:
    prompt = build_label_fidelity_prompt(
        node_labels=["Load Balancer", "Web Server", "Database"],
        edge_labels=["HTTP", "SQL"],
    )
    assert "Load Balancer" in prompt
    assert "Web Server" in prompt
    assert "Database" in prompt


def test_label_fidelity_prompt_includes_edge_labels() -> None:
    prompt = build_label_fidelity_prompt(node_labels=["A", "B"], edge_labels=["HTTP/443", "gRPC"])
    assert "HTTP/443" in prompt
    assert "gRPC" in prompt


def test_label_fidelity_prompt_mentions_ground_truth() -> None:
    prompt = build_label_fidelity_prompt(node_labels=["A"], edge_labels=[])
    assert "ground truth" in prompt.lower()


def test_label_fidelity_prompt_asks_for_pass_or_needs_refinement() -> None:
    prompt = build_label_fidelity_prompt(node_labels=["A"], edge_labels=[])
    assert "PASS" in prompt
    assert "NEEDS_REFINEMENT" in prompt


def test_structural_accuracy_prompt_includes_node_count() -> None:
    prompt = build_structural_accuracy_prompt(
        node_count=12, edge_count=15,
        node_labels=["A", "B", "C"], edge_pairs=[("A", "B"), ("B", "C")],
    )
    assert "12" in prompt


def test_structural_accuracy_prompt_includes_edge_count() -> None:
    prompt = build_structural_accuracy_prompt(
        node_count=12, edge_count=15,
        node_labels=["A", "B", "C"], edge_pairs=[("A", "B"), ("B", "C")],
    )
    assert "15" in prompt


def test_structural_accuracy_prompt_lists_major_nodes() -> None:
    prompt = build_structural_accuracy_prompt(
        node_count=5, edge_count=4,
        node_labels=["Load Balancer", "API Gateway", "Database"],
        edge_pairs=[("Load Balancer", "API Gateway")],
    )
    assert "Load Balancer" in prompt
    assert "API Gateway" in prompt
    assert "Database" in prompt


def test_structural_accuracy_prompt_lists_key_connections() -> None:
    prompt = build_structural_accuracy_prompt(
        node_count=3, edge_count=2,
        node_labels=["A", "B", "C"], edge_pairs=[("A", "B"), ("B", "C")],
    )
    assert "A" in prompt and "B" in prompt


def test_structural_accuracy_prompt_asks_for_rating() -> None:
    prompt = build_structural_accuracy_prompt(
        node_count=3, edge_count=2,
        node_labels=["A", "B"], edge_pairs=[("A", "B")],
    )
    assert "PASS" in prompt
    assert "NEEDS_REFINEMENT" in prompt
