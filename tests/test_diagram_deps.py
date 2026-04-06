"""Tests for diagram_beautifier/deps.py -- CLI dependency checker."""
from __future__ import annotations
from unittest.mock import patch
import pytest
from diagram_beautifier.deps import check_dependency, DependencyError


def test_check_dependency_dot_found() -> None:
    with patch("shutil.which", return_value="/usr/local/bin/dot"):
        result = check_dependency("dot")
    assert result == "/usr/local/bin/dot"


def test_check_dependency_mmdc_found() -> None:
    with patch("shutil.which", return_value="/usr/local/bin/mmdc"):
        result = check_dependency("mermaid")
    assert result == "/usr/local/bin/mmdc"


def test_check_dependency_dot_missing_raises() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyError, match="brew install graphviz"):
            check_dependency("dot")


def test_check_dependency_mmdc_missing_raises() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyError, match="mermaid-cli"):
            check_dependency("mermaid")


def test_check_dependency_dot_error_includes_platform_instructions() -> None:
    with patch("shutil.which", return_value=None):
        with pytest.raises(DependencyError) as exc_info:
            check_dependency("dot")
    message = str(exc_info.value)
    assert "brew install graphviz" in message
    assert "apt-get install graphviz" in message
    assert "dnf install graphviz" in message


def test_check_dependency_unknown_format_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported format"):
        check_dependency("svg")
