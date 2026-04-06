"""Check for required CLI tools (dot for Graphviz, mmdc for Mermaid)."""

from __future__ import annotations
import shutil


class DependencyError(RuntimeError):
    """Raised when a required CLI tool is not installed."""


_GRAPHVIZ_INSTALL = """\
Graphviz is required to render .dot diagrams but was not found.

Install with:
  macOS:  brew install graphviz
  Ubuntu: sudo apt-get install graphviz
  Fedora: sudo dnf install graphviz"""

_MERMAID_INSTALL = """\
Mermaid CLI is required to render Mermaid diagrams but was not found.

Install with:
  npm install -g @mermaid-js/mermaid-cli"""


def check_dependency(fmt: str) -> str:
    """Verify the required CLI tool is available for the given format.

    Args:
        fmt: ``"dot"`` for Graphviz or ``"mermaid"`` for Mermaid.

    Returns:
        The absolute path to the CLI tool.

    Raises:
        DependencyError: If the tool is not found on PATH.
        ValueError: If *fmt* is not a supported format.
    """
    if fmt == "dot":
        path = shutil.which("dot")
        if path is None:
            raise DependencyError(_GRAPHVIZ_INSTALL)
        return path
    if fmt in ("mermaid", "mmd"):
        path = shutil.which("mmdc")
        if path is None:
            raise DependencyError(_MERMAID_INSTALL)
        return path
    raise ValueError(f"Unsupported format: {fmt!r}")
