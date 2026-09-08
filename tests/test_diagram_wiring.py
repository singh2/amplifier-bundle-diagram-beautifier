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


def test_behavior_wires_diagram_awareness_context() -> None:
    """The behavior must wire in the diagram-awareness context.

    The root bundle.md is intentionally frontmatter-only: a bodied root bundle
    replaces the host session's instruction when installed with --app, so the
    awareness context is wired through the behavior instead.
    """
    data = yaml.safe_load(BEHAVIOR_FILE.read_text(encoding="utf-8"))
    includes = data.get("context", {}).get("include", [])
    assert any("diagram-awareness" in ref for ref in includes), f"Not found in: {includes}"


def test_bundle_md_has_no_body() -> None:
    """Root bundle.md must be frontmatter-only so --app installs don't hijack the host."""
    content = BUNDLE_FILE.read_text(encoding="utf-8")
    body = "---".join(content.split("---")[2:]).strip()
    assert body == "", f"bundle.md must have no markdown body, found: {body[:200]!r}"


def test_awareness_file_has_no_unconditional_directives() -> None:
    """Awareness context must not order the session to delegate unconditionally."""
    lower = AWARENESS_FILE.read_text(encoding="utf-8").lower()
    for banned in ("any user message", "all user requests", "not conditional", "you are the router"):
        assert banned not in lower, f"Unconditional directive found: {banned!r}"


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
