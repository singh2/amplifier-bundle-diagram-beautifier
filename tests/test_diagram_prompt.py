"""Tests for diagram_beautifier/prompt.py -- beautification prompt builder."""
from __future__ import annotations
from diagram_beautifier.prompt import build_beautify_prompt, STRUCTURAL_PRESERVATION_MODIFIER


def test_structural_modifier_mentions_topology() -> None:
    lower = STRUCTURAL_PRESERVATION_MODIFIER.lower()
    assert "topology" in lower or "node positions" in lower


def test_structural_modifier_mentions_labels() -> None:
    assert "label" in STRUCTURAL_PRESERVATION_MODIFIER.lower()


def test_structural_modifier_mentions_connections() -> None:
    lower = STRUCTURAL_PRESERVATION_MODIFIER.lower()
    assert "connection" in lower or "edge" in lower


def test_build_beautify_prompt_includes_aesthetic_template() -> None:
    prompt = build_beautify_prompt(
        aesthetic_template="Claymation Studio style with soft lighting",
        diagram_type="digraph",
        node_labels=["Load Balancer", "Web Server"],
        edge_labels=["HTTP"],
    )
    assert "Claymation Studio" in prompt


def test_build_beautify_prompt_includes_structural_modifier() -> None:
    prompt = build_beautify_prompt(
        aesthetic_template="Clean Minimalist style",
        diagram_type="flowchart",
        node_labels=["A", "B"],
        edge_labels=[],
    )
    assert "STRUCTURAL PRESERVATION" in prompt


def test_build_beautify_prompt_lists_node_labels() -> None:
    prompt = build_beautify_prompt(
        aesthetic_template="Dark Mode Tech",
        diagram_type="digraph",
        node_labels=["Load Balancer", "API Gateway", "Database"],
        edge_labels=["gRPC"],
    )
    assert "Load Balancer" in prompt
    assert "API Gateway" in prompt
    assert "Database" in prompt


def test_build_beautify_prompt_lists_edge_labels() -> None:
    prompt = build_beautify_prompt(
        aesthetic_template="Clean Minimalist",
        diagram_type="digraph",
        node_labels=["A", "B"],
        edge_labels=["HTTP/443", "gRPC"],
    )
    assert "HTTP/443" in prompt
    assert "gRPC" in prompt


def test_build_beautify_prompt_mentions_diagram_type() -> None:
    prompt = build_beautify_prompt(
        aesthetic_template="Bold Editorial",
        diagram_type="flowchart",
        node_labels=["Start", "End"],
        edge_labels=[],
    )
    assert "flowchart" in prompt.lower()
