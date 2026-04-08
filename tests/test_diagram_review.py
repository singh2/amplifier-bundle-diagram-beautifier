"""Tests for diagram_beautifier/review.py -- quality review prompt builders."""

from __future__ import annotations

from diagram_beautifier.review import (
    build_label_fidelity_prompt,
    build_structural_accuracy_prompt,
)


class TestLabelFidelityPrompt:
    def test_includes_all_node_labels(self) -> None:
        prompt = build_label_fidelity_prompt(
            node_labels=["Load Balancer", "Web Server", "Database"],
            edge_labels=["HTTP", "SQL"],
        )
        assert "Load Balancer" in prompt
        assert "Web Server" in prompt
        assert "Database" in prompt

    def test_includes_edge_labels(self) -> None:
        prompt = build_label_fidelity_prompt(
            node_labels=["A", "B"], edge_labels=["HTTP/443", "gRPC"]
        )
        assert "HTTP/443" in prompt
        assert "gRPC" in prompt

    def test_mentions_ground_truth(self) -> None:
        prompt = build_label_fidelity_prompt(node_labels=["A"], edge_labels=[])
        assert "ground truth" in prompt.lower()

    def test_uses_numerical_rating(self) -> None:
        prompt = build_label_fidelity_prompt(node_labels=["A"], edge_labels=[])
        assert "1-5" in prompt or ("1 =" in prompt and "5 =" in prompt)

    def test_no_binary_pass_fail(self) -> None:
        prompt = build_label_fidelity_prompt(node_labels=["A"], edge_labels=[])
        assert "NEEDS_REFINEMENT" not in prompt

    def test_asks_for_explicit_listing(self) -> None:
        prompt = build_label_fidelity_prompt(node_labels=["A", "B"], edge_labels=[])
        lower = prompt.lower()
        assert "list" in lower
        assert "found" in lower.lower() or "missing" in lower.lower()

    def test_asks_for_counts(self) -> None:
        prompt = build_label_fidelity_prompt(node_labels=["A"], edge_labels=[])
        assert "found_exact" in prompt or "count" in prompt.lower()

    def test_includes_label_counts(self) -> None:
        prompt = build_label_fidelity_prompt(
            node_labels=["A", "B", "C"],
            edge_labels=["X"],
        )
        assert "3" in prompt  # node count
        assert "1" in prompt  # edge count


class TestStructuralAccuracyPrompt:
    def test_includes_node_count(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=12,
            edge_count=15,
            node_labels=["A", "B", "C"],
            edge_pairs=[("A", "B"), ("B", "C")],
        )
        assert "12" in prompt

    def test_includes_edge_count(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=12,
            edge_count=15,
            node_labels=["A", "B", "C"],
            edge_pairs=[("A", "B"), ("B", "C")],
        )
        assert "15" in prompt

    def test_lists_all_node_labels(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=5,
            edge_count=4,
            node_labels=["Load Balancer", "API Gateway", "Database"],
            edge_pairs=[("Load Balancer", "API Gateway")],
        )
        assert "Load Balancer" in prompt
        assert "API Gateway" in prompt
        assert "Database" in prompt

    def test_lists_all_connections(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=3,
            edge_count=2,
            node_labels=["A", "B", "C"],
            edge_pairs=[("A", "B"), ("B", "C")],
        )
        assert "A" in prompt and "B" in prompt and "C" in prompt

    def test_uses_numerical_rating(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=3,
            edge_count=2,
            node_labels=["A", "B"],
            edge_pairs=[("A", "B")],
        )
        assert "1-5" in prompt or ("1 =" in prompt and "5 =" in prompt)

    def test_no_binary_pass_fail(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=3,
            edge_count=2,
            node_labels=["A", "B"],
            edge_pairs=[("A", "B")],
        )
        assert "NEEDS_REFINEMENT" not in prompt

    def test_asks_for_explicit_node_listing(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=2,
            edge_count=1,
            node_labels=["A", "B"],
            edge_pairs=[("A", "B")],
        )
        lower = prompt.lower()
        assert "list every node" in lower or "list every" in lower

    def test_asks_for_explicit_connection_listing(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=2,
            edge_count=1,
            node_labels=["A", "B"],
            edge_pairs=[("A", "B")],
        )
        lower = prompt.lower()
        assert "list every connection" in lower or "list every" in lower

    def test_asks_for_counts(self) -> None:
        prompt = build_structural_accuracy_prompt(
            node_count=2,
            edge_count=1,
            node_labels=["A", "B"],
            edge_pairs=[("A", "B")],
        )
        assert "nodes_present" in prompt or "count" in prompt.lower()
