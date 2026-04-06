"""Tests for diagram_beautifier/renderer.py -- plain PNG rendering via CLI tools."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from diagram_beautifier.renderer import render_plain_png, RenderError

DOT_SOURCE = """\
digraph G {
    A [label="Hello"]
    B [label="World"]
    A -> B
}
"""

def test_render_dot_calls_subprocess_correctly(tmp_path: Path) -> None:
    source_file = tmp_path / "test.dot"
    source_file.write_text(DOT_SOURCE)
    output_path = tmp_path / "output.png"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        render_plain_png(str(source_file), "dot", str(output_path))
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "dot"
    assert "-Tpng" in call_args
    assert "-Gdpi=150" in call_args
    assert str(source_file) in call_args


def test_render_dot_failure_raises(tmp_path: Path) -> None:
    source_file = tmp_path / "bad.dot"
    source_file.write_text("not valid dot")
    output_path = tmp_path / "output.png"
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error: syntax error"
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RenderError, match="syntax error"):
            render_plain_png(str(source_file), "dot", str(output_path))


MERMAID_SOURCE = """\
flowchart TD
    A[Hello] --> B[World]
"""

def test_render_mermaid_calls_subprocess_correctly(tmp_path: Path) -> None:
    source_file = tmp_path / "test.mmd"
    source_file.write_text(MERMAID_SOURCE)
    output_path = tmp_path / "output.png"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        render_plain_png(str(source_file), "mermaid", str(output_path))
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "mmdc"
    assert "-i" in call_args


def test_render_from_source_string_creates_temp_file(tmp_path: Path) -> None:
    output_path = tmp_path / "output.png"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result):
        render_plain_png(DOT_SOURCE, "dot", str(output_path), is_source_text=True)
