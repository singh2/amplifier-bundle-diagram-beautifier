"""Parse Graphviz (.dot) and Mermaid diagram sources into a normalized structure.

The parser extracts nodes, edges, labels, and subgraphs from diagram source text.
The output is used downstream for panel decomposition and quality review.

Supported Mermaid diagram types:
  - flowchart / graph  (TD, LR, BT, RL)
  - sequenceDiagram
  - erDiagram
  - classDiagram
"""

from __future__ import annotations

import re
from typing import Any


def parse_diagram_source(source: str, fmt: str) -> dict[str, Any]:
    """Parse diagram source into a normalized structure.

    Args:
        source: The diagram source text.
        fmt: Format identifier -- ``"dot"`` for Graphviz or ``"mermaid"`` /
             ``"mmd"`` for Mermaid.

    Returns:
        A dict with keys: ``format``, ``diagram_type``, ``nodes``, ``edges``,
        ``subgraphs``, ``node_count``, ``edge_count``, ``raw_source``.
    """
    if fmt == "dot":
        return _parse_dot(source)
    if fmt in ("mermaid", "mmd"):
        return _parse_mermaid(source)
    raise ValueError(f"Unsupported format: {fmt!r}")


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _mermaid_result(
    source: str,
    diagram_type: str,
    nodes: list[dict[str, str]],
    edges: list[dict[str, str | None]],
    subgraphs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a normalised Mermaid parse result dict."""
    return {
        "format": "mermaid",
        "diagram_type": diagram_type,
        "nodes": nodes,
        "edges": edges,
        "subgraphs": subgraphs if subgraphs is not None else [],
        "node_count": len(nodes),
        "edge_count": len(edges),
        "raw_source": source,
    }


# ---------------------------------------------------------------------------
# Graphviz (.dot) parser
# ---------------------------------------------------------------------------


def _parse_dot(source: str) -> dict[str, Any]:
    """Parse a Graphviz .dot source."""
    # Determine graph type
    if re.search(r"\bdigraph\b", source):
        diagram_type = "digraph"
    else:
        diagram_type = "graph"

    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str | None]] = []
    subgraphs: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()

    # Keywords that should not be treated as node IDs
    _dot_keywords = frozenset(
        {
            "label",
            "style",
            "color",
            "fontcolor",
            "bgcolor",
            "rank",
            "rankdir",
            "fontname",
            "fontsize",
            "node",
            "edge",
            "graph",
            "digraph",
            "subgraph",
            "compound",
            "newrank",
        }
    )

    # Extract subgraphs
    subgraph_pattern = re.compile(r"subgraph\s+(\w+)\s*\{([^}]*)\}", re.DOTALL)
    for match in subgraph_pattern.finditer(source):
        sg_id = match.group(1)
        sg_body = match.group(2)

        # Extract subgraph label
        label_match = re.search(r'label\s*=\s*"([^"]*)"', sg_body)
        sg_name = label_match.group(1) if label_match else sg_id

        # Extract node IDs declared in this subgraph
        sg_node_ids: list[str] = []
        for node_match in re.finditer(r"^\s*(\w+)\s*[\[;]", sg_body, re.MULTILINE):
            node_id = node_match.group(1)
            if node_id not in _dot_keywords:
                sg_node_ids.append(node_id)

        subgraphs.append({"name": sg_name, "node_ids": sg_node_ids})

    # Extract nodes with explicit labels
    node_pattern = re.compile(
        r"^\s*(\w+)\s*\[([^\]]*label\s*=\s*\"([^\"]*)\"[^\]]*)\]",
        re.MULTILINE,
    )
    for match in node_pattern.finditer(source):
        node_id = match.group(1)
        label = match.group(3)
        if node_id not in _dot_keywords:
            nodes.append({"id": node_id, "label": label})
            seen_node_ids.add(node_id)

    # Extract edges: A -> B or A -- B, with optional labels
    edge_pattern = re.compile(
        r"(\w+)\s*(-[->])\s*(\w+)(?:\s*\[([^\]]*)\])?", re.MULTILINE
    )
    for match in edge_pattern.finditer(source):
        from_id = match.group(1)
        to_id = match.group(3)
        attrs = match.group(4) or ""

        edge_label = None
        label_match = re.search(r'label\s*=\s*"([^"]*)"', attrs)
        if label_match:
            edge_label = label_match.group(1)

        edges.append({"from": from_id, "to": to_id, "label": edge_label})

        # Add nodes discovered only in edges (implicit labels = node ID)
        for nid in (from_id, to_id):
            if nid not in seen_node_ids:
                nodes.append({"id": nid, "label": nid})
                seen_node_ids.add(nid)

    return {
        "format": "dot",
        "diagram_type": diagram_type,
        "nodes": nodes,
        "edges": edges,
        "subgraphs": subgraphs,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "raw_source": source,
    }


# ---------------------------------------------------------------------------
# Mermaid dispatcher
# ---------------------------------------------------------------------------


def _parse_mermaid(source: str) -> dict[str, Any]:
    """Parse a Mermaid diagram source, dispatching by diagram type."""
    lines = source.strip().splitlines()
    first_line = lines[0].strip() if lines else ""
    diagram_type = first_line.split()[0] if first_line else "flowchart"
    body = lines[1:]

    if diagram_type == "sequenceDiagram":
        return _parse_mermaid_sequence(source, diagram_type, body)
    if diagram_type == "erDiagram":
        return _parse_mermaid_er(source, diagram_type, body)
    if diagram_type == "classDiagram":
        return _parse_mermaid_class(source, diagram_type, body)
    return _parse_mermaid_flowchart(source, diagram_type, body)


# ---------------------------------------------------------------------------
# Mermaid: flowchart / graph
# ---------------------------------------------------------------------------


def _parse_mermaid_flowchart(
    source: str, diagram_type: str, body: list[str]
) -> dict[str, Any]:
    """Parse a flowchart or graph Mermaid diagram."""
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str | None]] = []
    subgraphs: list[dict[str, Any]] = []
    seen_node_ids: set[str] = set()
    current_subgraph: dict[str, Any] | None = None

    for line in body:
        stripped = line.strip()

        # Subgraph start
        sg_match = re.match(r"subgraph\s+(.+)", stripped)
        if sg_match:
            current_subgraph = {
                "name": sg_match.group(1).strip(),
                "node_ids": [],
            }
            continue

        # Subgraph end
        if stripped == "end" and current_subgraph is not None:
            subgraphs.append(current_subgraph)
            current_subgraph = None
            continue

        # Edge with optional label: A -->|label| B or A --> B
        edge_match = re.match(
            r"(\w+)(?:\[[^\]]*\])?\s*--+>(?:\|([^|]*)?\|)?\s*(\w+)(?:\[([^\]]*)\])?",
            stripped,
        )
        if edge_match:
            from_id = edge_match.group(1)
            edge_label = edge_match.group(2)
            to_id = edge_match.group(3)

            edges.append(
                {
                    "from": from_id,
                    "to": to_id,
                    "label": edge_label,
                }
            )

            # Extract node labels from bracket syntax in the edge line
            for node_def in re.finditer(r"(\w+)\[([^\]]*)\]", stripped):
                nid = node_def.group(1)
                nlabel = node_def.group(2)
                if nid not in seen_node_ids:
                    nodes.append({"id": nid, "label": nlabel})
                    seen_node_ids.add(nid)
                    if current_subgraph is not None:
                        current_subgraph["node_ids"].append(nid)

            # Add nodes without bracket labels (implicit)
            for nid in (from_id, to_id):
                if nid not in seen_node_ids:
                    nodes.append({"id": nid, "label": nid})
                    seen_node_ids.add(nid)
                    if current_subgraph is not None:
                        current_subgraph["node_ids"].append(nid)

            continue

        # Standalone node definition: A[Label]
        node_match = re.match(r"(\w+)\[([^\]]*)\]", stripped)
        if node_match:
            nid = node_match.group(1)
            nlabel = node_match.group(2)
            if nid not in seen_node_ids:
                nodes.append({"id": nid, "label": nlabel})
                seen_node_ids.add(nid)
                if current_subgraph is not None:
                    current_subgraph["node_ids"].append(nid)

    return _mermaid_result(source, diagram_type, nodes, edges, subgraphs)


# ---------------------------------------------------------------------------
# Mermaid: sequenceDiagram
# ---------------------------------------------------------------------------

# Arrow tokens tried in order (longest first to avoid partial matches)
_SEQUENCE_ARROWS = [
    "-->>+",
    "-->>-",
    "->>+",
    "->>-",
    "-->>",
    "->>",
    "-->",
    "->",
    "--x",
    "-x",
    "--)",
    "-)",
]


def _parse_mermaid_sequence(
    source: str, diagram_type: str, body: list[str]
) -> dict[str, Any]:
    """Parse a Mermaid sequenceDiagram.

    Extracts participants as nodes and messages as directed edges.
    Handles multi-word participant names (e.g. ``API Gateway``).
    """
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str | None]] = []
    seen: set[str] = set()

    def ensure_node(name: str) -> None:
        if name and name not in seen:
            nodes.append({"id": name, "label": name})
            seen.add(name)

    # participant / actor Name  or  participant Name as Alias
    decl_re = re.compile(
        r"^\s*(?:participant|actor)\s+(.+?)(?:\s+as\s+(.+))?$", re.IGNORECASE
    )

    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue

        # Participant / actor declaration
        m = decl_re.match(stripped)
        if m:
            raw_name = m.group(1).strip()
            alias = m.group(2).strip() if m.group(2) else raw_name
            ensure_node(alias)
            continue

        # Message line: FromName ARROW ToName: message text
        for arrow in _SEQUENCE_ARROWS:
            idx = stripped.find(arrow)
            if idx > 0:
                from_name = stripped[:idx].strip()
                after_arrow = stripped[idx + len(arrow) :].lstrip("+- ")
                if ":" in after_arrow:
                    colon_idx = after_arrow.index(":")
                    to_name = after_arrow[:colon_idx].strip().rstrip("+-")
                    msg = after_arrow[colon_idx + 1 :].strip()
                else:
                    to_name = after_arrow.strip().rstrip("+-")
                    msg = ""

                if from_name and to_name:
                    ensure_node(from_name)
                    ensure_node(to_name)
                    edges.append(
                        {"from": from_name, "to": to_name, "label": msg or None}
                    )
                break

    return _mermaid_result(source, diagram_type, nodes, edges)


# ---------------------------------------------------------------------------
# Mermaid: erDiagram
# ---------------------------------------------------------------------------

# Relationship: ENTITY1 ||--o{ ENTITY2 : "label"
# The middle part is any combination of |, o, }, {, ., ~, -, –
_ER_REL_RE = re.compile(
    r"^\s*(\w+)\s+[|o}{.~-]+[-–.~]+[|o}{.~-]+\s+(\w+)\s*:\s*\"?([^\"]+)\"?"
)
_ER_ENTITY_RE = re.compile(r"^\s*(\w+)\s*\{")


def _parse_mermaid_er(
    source: str, diagram_type: str, body: list[str]
) -> dict[str, Any]:
    """Parse a Mermaid erDiagram.

    Extracts entities as nodes and relationships as edges with verb labels.
    """
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str | None]] = []
    seen: set[str] = set()

    def ensure_node(name: str) -> None:
        if name and name not in seen:
            nodes.append({"id": name, "label": name})
            seen.add(name)

    in_entity_block = False
    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue

        if in_entity_block:
            if stripped == "}":
                in_entity_block = False
            continue

        # Entity block declaration: ENTITY {
        e_match = _ER_ENTITY_RE.match(line)
        if e_match:
            ensure_node(e_match.group(1))
            in_entity_block = True
            continue

        # Relationship line: ENTITY1 REL ENTITY2 : "label"
        r_match = _ER_REL_RE.match(line)
        if r_match:
            from_entity = r_match.group(1)
            to_entity = r_match.group(2)
            label = r_match.group(3).strip()
            ensure_node(from_entity)
            ensure_node(to_entity)
            edges.append({"from": from_entity, "to": to_entity, "label": label or None})

    return _mermaid_result(source, diagram_type, nodes, edges)


# ---------------------------------------------------------------------------
# Mermaid: classDiagram
# ---------------------------------------------------------------------------

_CLASS_DECL_RE = re.compile(r"^\s*class\s+(\w+)")
# Relationship: ClassA ARROW ClassB  or  ClassA ARROW ClassB : label
# Arrow is any sequence of <, |, >, *, o, ., ~, -, –  between the two names
_CLASS_REL_RE = re.compile(r"^\s*(\w+)\s+([<|>*o.~-]{2,})\s+(\w+)(?:\s*:\s*(.*))?")
# Annotation: ClassName : member  (registers the class as a known node)
_CLASS_ANNOTATION_RE = re.compile(r"^\s*(\w+)\s*:\s*\S")


def _parse_mermaid_class(
    source: str, diagram_type: str, body: list[str]
) -> dict[str, Any]:
    """Parse a Mermaid classDiagram.

    Extracts classes as nodes and typed relationships as edges.
    Handles: -->, ..|>, --|>, ..>, <|--, o--, *--, and plain --.
    """
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str | None]] = []
    seen: set[str] = set()

    def ensure_node(name: str) -> None:
        if name and name not in seen:
            nodes.append({"id": name, "label": name})
            seen.add(name)

    in_class_block = False
    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue

        if in_class_block:
            if stripped == "}":
                in_class_block = False
            continue

        # Class declaration: class ClassName { or class ClassName
        c_match = _CLASS_DECL_RE.match(line)
        if c_match:
            ensure_node(c_match.group(1))
            if stripped.endswith("{"):
                in_class_block = True
            continue

        # Relationship: ClassA ARROW ClassB : optional label
        r_match = _CLASS_REL_RE.match(line)
        if r_match:
            from_cls = r_match.group(1)
            to_cls = r_match.group(3)
            label = (r_match.group(4) or "").strip() or None
            ensure_node(from_cls)
            ensure_node(to_cls)
            edges.append({"from": from_cls, "to": to_cls, "label": label})
            continue

        # Annotation: ClassName : something (registers class if not seen)
        a_match = _CLASS_ANNOTATION_RE.match(line)
        if a_match:
            ensure_node(a_match.group(1))

    return _mermaid_result(source, diagram_type, nodes, edges)
