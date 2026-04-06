"""Tests for diagram-beautifier wiring into behavior YAML and bundle context."""
from pathlib import Path
import yaml

BUNDLE_FILE = Path(__file__).parent.parent / "bundle.md"
BEHAVIOR_FILE = Path(__file__).parent.parent / "behaviors" / "diagram.yaml"
AWARENESS_FILE = Path(__file__).parent.parent / "context" / "diagram-awareness.md"


def test_behavior_yaml_includes_diagram_beautifier_agent() -> None:
    content = BEHAVIOR_FILE.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    agent_includes = data.get("agents", {}).get("include", [])
    agent_refs = [ref if isinstance(ref, str) else str(ref) for ref in agent_includes]
    assert any("diagram-beautifier" in ref for ref in agent_refs), f"Not found in: {agent_refs}"


def test_bundle_references_diagram_awareness_context() -> None:
    """bundle.md must wire in the diagram-awareness context."""
    content = BUNDLE_FILE.read_text(encoding="utf-8")
    assert "diagram-awareness" in content


def test_diagram_awareness_file_exists() -> None:
    assert AWARENESS_FILE.exists(), f"File not found: {AWARENESS_FILE}"


def test_diagram_awareness_mentions_dot_extension() -> None:
    content = AWARENESS_FILE.read_text(encoding="utf-8")
    assert ".dot" in content


def test_diagram_awareness_mentions_mermaid_keywords() -> None:
    content = AWARENESS_FILE.read_text(encoding="utf-8")
    lower = content.lower()
    assert "flowchart" in lower or "mermaid" in lower


def test_diagram_awareness_mentions_delegation() -> None:
    content = AWARENESS_FILE.read_text(encoding="utf-8")
    assert "diagram-beautifier" in content
