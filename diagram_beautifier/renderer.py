"""Render diagram source to a plain PNG using CLI tools."""

from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path


class RenderError(RuntimeError):
    """Raised when the CLI rendering tool fails."""


def render_plain_png(
    source_or_path: str,
    fmt: str,
    output_path: str,
    *,
    is_source_text: bool = False,
) -> str:
    """Render diagram source to a plain PNG.

    Args:
        source_or_path: File path or source text (when is_source_text=True).
        fmt: ``"dot"`` for Graphviz or ``"mermaid"`` for Mermaid.
        output_path: Where to write the output PNG.
        is_source_text: If True, source_or_path is treated as raw source text.

    Returns:
        The output_path on success.

    Raises:
        RenderError: If the CLI tool exits with a non-zero return code.
        ValueError: If fmt is not supported.
    """
    if is_source_text:
        suffix = ".dot" if fmt == "dot" else ".mmd"
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
        tmp.write(source_or_path)
        tmp.close()
        source_path = tmp.name
    else:
        source_path = source_or_path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "dot":
        cmd = ["dot", "-Tpng", "-Gdpi=150", source_path, "-o", output_path]
    elif fmt in ("mermaid", "mmd"):
        cmd = [
            "mmdc",
            "-i",
            source_path,
            "-o",
            output_path,
            "-w",
            "2048",
            "-H",
            "1536",
            "--scale",
            "2",
        ]
    else:
        raise ValueError(f"Unsupported format: {fmt!r}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenderError(
            f"{cmd[0]} exited with code {result.returncode}: {result.stderr}"
        )

    return output_path
