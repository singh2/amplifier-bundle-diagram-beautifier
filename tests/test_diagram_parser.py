"""Tests for diagram_beautifier/parser.py -- diagram source parser."""

from __future__ import annotations

import pytest

from diagram_beautifier.parser import parse_diagram_source


# ---------------------------------------------------------------------------
# Graphviz (.dot) parsing
# ---------------------------------------------------------------------------

SIMPLE_DIGRAPH = """\
digraph G {
    A [label="Load Balancer"]
    B [label="Web Server"]
    C [label="Database"]
    A -> B [label="HTTP"]
    B -> C [label="SQL"]
}
"""

DOT_WITH_SUBGRAPHS = """\
digraph architecture {
    subgraph cluster_frontend {
        label="Frontend"
        A [label="React App"]
        B [label="CDN"]
    }
    subgraph cluster_backend {
        label="Backend"
        C [label="API Server"]
        D [label="Worker"]
    }
    A -> C
    B -> A
    C -> D
}
"""

DOT_IMPLICIT_LABELS = """\
digraph G {
    server -> database
    database -> cache
}
"""

UNDIRECTED_GRAPH = """\
graph G {
    A [label="Node 1"]
    B [label="Node 2"]
    A -- B
}
"""


def test_parse_dot_simple_digraph_format() -> None:
    """Parser identifies .dot format and digraph type."""
    result = parse_diagram_source(SIMPLE_DIGRAPH, "dot")
    assert result["format"] == "dot"
    assert result["diagram_type"] == "digraph"


def test_parse_dot_simple_digraph_nodes() -> None:
    """Parser extracts all 3 nodes with their labels."""
    result = parse_diagram_source(SIMPLE_DIGRAPH, "dot")
    labels = {n["label"] for n in result["nodes"]}
    assert labels == {"Load Balancer", "Web Server", "Database"}
    assert result["node_count"] == 3


def test_parse_dot_simple_digraph_edges() -> None:
    """Parser extracts edges with labels."""
    result = parse_diagram_source(SIMPLE_DIGRAPH, "dot")
    assert result["edge_count"] == 2
    edge_labels = {e.get("label") for e in result["edges"] if e.get("label")}
    assert "HTTP" in edge_labels
    assert "SQL" in edge_labels


def test_parse_dot_subgraphs() -> None:
    """Parser extracts subgraph declarations with their node IDs."""
    result = parse_diagram_source(DOT_WITH_SUBGRAPHS, "dot")
    assert len(result["subgraphs"]) == 2
    names = {sg["name"] for sg in result["subgraphs"]}
    assert names == {"Frontend", "Backend"}


def test_parse_dot_implicit_labels() -> None:
    """When no label= attribute, node ID is used as label."""
    result = parse_diagram_source(DOT_IMPLICIT_LABELS, "dot")
    labels = {n["label"] for n in result["nodes"]}
    assert "server" in labels
    assert "database" in labels
    assert "cache" in labels


def test_parse_dot_undirected_graph() -> None:
    """Parser handles undirected 'graph' (not 'digraph')."""
    result = parse_diagram_source(UNDIRECTED_GRAPH, "dot")
    assert result["diagram_type"] == "graph"
    assert result["node_count"] == 2
    assert result["edge_count"] == 1


# ---------------------------------------------------------------------------
# Mermaid parsing
# ---------------------------------------------------------------------------

SIMPLE_FLOWCHART = """\
flowchart TD
    A[Load Balancer] --> B[Web Server]
    B --> C[Database]
    B --> D[Cache]
"""

MERMAID_WITH_SUBGRAPHS = """\
flowchart TD
    subgraph Frontend
        A[React App]
        B[CDN]
    end
    subgraph Backend
        C[API Server]
        D[Worker]
    end
    A --> C
    B --> A
"""

MERMAID_EDGE_LABELS = """\
flowchart LR
    A[Client] -->|HTTP| B[Server]
    B -->|SQL| C[DB]
"""


def test_parse_mermaid_flowchart_format() -> None:
    """Parser identifies mermaid format and flowchart type."""
    result = parse_diagram_source(SIMPLE_FLOWCHART, "mermaid")
    assert result["format"] == "mermaid"
    assert result["diagram_type"] == "flowchart"


def test_parse_mermaid_flowchart_nodes() -> None:
    """Parser extracts nodes with display labels from bracket syntax."""
    result = parse_diagram_source(SIMPLE_FLOWCHART, "mermaid")
    labels = {n["label"] for n in result["nodes"]}
    assert "Load Balancer" in labels
    assert "Web Server" in labels
    assert "Database" in labels
    assert "Cache" in labels
    assert result["node_count"] == 4


def test_parse_mermaid_flowchart_edges() -> None:
    """Parser extracts edges from --> syntax."""
    result = parse_diagram_source(SIMPLE_FLOWCHART, "mermaid")
    assert result["edge_count"] == 3


def test_parse_mermaid_subgraphs() -> None:
    """Parser extracts subgraph blocks."""
    result = parse_diagram_source(MERMAID_WITH_SUBGRAPHS, "mermaid")
    assert len(result["subgraphs"]) == 2
    names = {sg["name"] for sg in result["subgraphs"]}
    assert "Frontend" in names
    assert "Backend" in names


def test_parse_mermaid_edge_labels() -> None:
    """Parser extracts edge labels from |label| syntax."""
    result = parse_diagram_source(MERMAID_EDGE_LABELS, "mermaid")
    edge_labels = {e.get("label") for e in result["edges"] if e.get("label")}
    assert "HTTP" in edge_labels
    assert "SQL" in edge_labels


# ---------------------------------------------------------------------------
# Raw source preservation
# ---------------------------------------------------------------------------


def test_parse_preserves_raw_source() -> None:
    """Parser includes the original source text in the result."""
    result = parse_diagram_source(SIMPLE_DIGRAPH, "dot")
    assert result["raw_source"] == SIMPLE_DIGRAPH


def test_parse_unsupported_format_raises() -> None:
    """Parser raises ValueError for unknown format identifiers."""
    with pytest.raises(ValueError, match="Unsupported format"):
        parse_diagram_source("some source", "svg")


# ---------------------------------------------------------------------------
# Mermaid: sequenceDiagram
# ---------------------------------------------------------------------------

SEQUENCE_DIAGRAM = """\
sequenceDiagram
    participant Browser
    participant API Gateway
    Browser->>API Gateway: POST /login
    API Gateway-->>Browser: 200 OK
    Browser->>API Gateway: GET /profile
"""


def test_parse_mermaid_sequence_format() -> None:
    """Parser identifies sequenceDiagram type."""
    result = parse_diagram_source(SEQUENCE_DIAGRAM, "mermaid")
    assert result["format"] == "mermaid"
    assert result["diagram_type"] == "sequenceDiagram"


def test_parse_mermaid_sequence_nodes() -> None:
    """Parser extracts participants as nodes, including multi-word names."""
    result = parse_diagram_source(SEQUENCE_DIAGRAM, "mermaid")
    labels = {n["label"] for n in result["nodes"]}
    assert "Browser" in labels
    assert "API Gateway" in labels
    assert result["node_count"] >= 2


def test_parse_mermaid_sequence_edges() -> None:
    """Parser extracts messages as directed edges with message text as label."""
    result = parse_diagram_source(SEQUENCE_DIAGRAM, "mermaid")
    assert result["edge_count"] == 3
    edge_labels = {e["label"] for e in result["edges"] if e.get("label")}
    assert "POST /login" in edge_labels
    assert "200 OK" in edge_labels


# ---------------------------------------------------------------------------
# Mermaid: erDiagram
# ---------------------------------------------------------------------------

ER_DIAGRAM = """\
erDiagram
    USER {
        int id PK
        string email
    }
    ORDER {
        int id PK
        int user_id FK
    }
    PRODUCT {
        int id PK
        string name
    }
    USER ||--o{ ORDER : places
    ORDER ||--|{ PRODUCT : contains
"""


def test_parse_mermaid_er_format() -> None:
    """Parser identifies erDiagram type."""
    result = parse_diagram_source(ER_DIAGRAM, "mermaid")
    assert result["format"] == "mermaid"
    assert result["diagram_type"] == "erDiagram"


def test_parse_mermaid_er_nodes() -> None:
    """Parser extracts entity names as nodes."""
    result = parse_diagram_source(ER_DIAGRAM, "mermaid")
    labels = {n["label"] for n in result["nodes"]}
    assert "USER" in labels
    assert "ORDER" in labels
    assert "PRODUCT" in labels
    assert result["node_count"] >= 3


def test_parse_mermaid_er_edges() -> None:
    """Parser extracts relationships as edges with verb label."""
    result = parse_diagram_source(ER_DIAGRAM, "mermaid")
    assert result["edge_count"] >= 2
    edge_labels = {e["label"] for e in result["edges"] if e.get("label")}
    assert "places" in edge_labels
    assert "contains" in edge_labels


# ---------------------------------------------------------------------------
# Mermaid: classDiagram
# ---------------------------------------------------------------------------

CLASS_DIAGRAM = """\
classDiagram
    class Session {
        +String id
        +execute(prompt)
    }
    class Coordinator {
        +mount(point, instance)
        +get(point)
    }
    class Tool {
        <<interface>>
        +execute(input)
    }
    Session --> Coordinator : uses
    Coordinator --> Tool : mounts
    ConcreteTools ..|> Tool : implements
"""


def test_parse_mermaid_class_format() -> None:
    """Parser identifies classDiagram type."""
    result = parse_diagram_source(CLASS_DIAGRAM, "mermaid")
    assert result["format"] == "mermaid"
    assert result["diagram_type"] == "classDiagram"


def test_parse_mermaid_class_nodes() -> None:
    """Parser extracts class names as nodes from class declarations."""
    result = parse_diagram_source(CLASS_DIAGRAM, "mermaid")
    labels = {n["label"] for n in result["nodes"]}
    assert "Session" in labels
    assert "Coordinator" in labels
    assert "Tool" in labels
    assert result["node_count"] >= 3


def test_parse_mermaid_class_edges() -> None:
    """Parser extracts relationships as edges including --> and ..|> arrows."""
    result = parse_diagram_source(CLASS_DIAGRAM, "mermaid")
    assert result["edge_count"] >= 3
    edge_labels = {e["label"] for e in result["edges"] if e.get("label")}
    assert "uses" in edge_labels
    assert "mounts" in edge_labels
    assert "implements" in edge_labels
