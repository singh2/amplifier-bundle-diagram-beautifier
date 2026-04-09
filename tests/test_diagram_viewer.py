"""Tests for diagram_beautifier/viewer.py -- eval report viewer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from diagram_beautifier.viewer import (
    ALL_DIMENSIONS,
    VARIANT_NAMES,
    DiagramData,  # noqa: F401
    RunData,  # noqa: F401
    generate_dashboard_html,
    generate_detail_html,
    generate_grid_html,
    load_diagram_data,
    load_run_data,
    score_color,
)

QUALITY_2DIM = {
    "diagram": "test-diagram",
    "format": "dot",
    "node_count": 5,
    "edge_count": 4,
    "variants": {
        "darkmode": {"label_fidelity": 4, "structural_accuracy": 5},
        "minimal": {"label_fidelity": 3, "structural_accuracy": 4},
        "sketchnote": {"label_fidelity": 5, "structural_accuracy": 3},
        "claymation": {"label_fidelity": 4, "structural_accuracy": 4},
    },
    "verification": {
        "label_completeness": 0.9,
        "edge_completeness": 0.75,
        "missing_labels": ["NodeX"],
        "missing_edges": ["A -> B"],
    },
}

QUALITY_8DIM = {
    "diagram": "test-diagram-8",
    "format": "mermaid",
    "node_count": 10,
    "edge_count": 12,
    "variants": {
        "darkmode": {
            "content_accuracy": 4,
            "layout_quality": 3,
            "visual_clarity": 4,
            "prompt_fidelity": 5,
            "aesthetic_fidelity": 4,
            "label_fidelity": 3,
            "structural_accuracy": 5,
            "color_category_fidelity": 4,
        },
        "minimal": {
            "content_accuracy": 3,
            "layout_quality": 4,
            "visual_clarity": 5,
            "prompt_fidelity": 4,
            "aesthetic_fidelity": 3,
            "label_fidelity": 4,
            "structural_accuracy": 4,
            "color_category_fidelity": 3,
        },
        "sketchnote": {
            "content_accuracy": 5,
            "layout_quality": 2,
            "visual_clarity": 3,
            "prompt_fidelity": 4,
            "aesthetic_fidelity": 5,
            "label_fidelity": 2,
            "structural_accuracy": 3,
            "color_category_fidelity": 4,
        },
        "claymation": {
            "content_accuracy": 4,
            "layout_quality": 4,
            "visual_clarity": 4,
            "prompt_fidelity": 3,
            "aesthetic_fidelity": 4,
            "label_fidelity": 5,
            "structural_accuracy": 5,
            "color_category_fidelity": 5,
        },
    },
    "verification": {
        "label_completeness": 1.0,
        "edge_completeness": 1.0,
        "missing_labels": [],
        "missing_edges": [],
    },
}


@pytest.fixture()
def tmp_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run-test"
    run_dir.mkdir()
    d1 = run_dir / "test-diagram"
    d1.mkdir()
    (d1 / "quality.json").write_text(json.dumps(QUALITY_2DIM))
    for variant in VARIANT_NAMES:
        (d1 / f"test-diagram_{variant}.png").write_bytes(b"PNG_FAKE")
    d2 = run_dir / "test-diagram-8"
    d2.mkdir()
    (d2 / "quality.json").write_text(json.dumps(QUALITY_8DIM))
    for variant in VARIANT_NAMES:
        (d2 / f"test-diagram-8_{variant}.png").write_bytes(b"PNG_FAKE")
    (d2 / "test-diagram-8_source.png").write_bytes(b"PNG_SOURCE")
    return run_dir


class TestConstants:
    def test_variant_names_has_four(self) -> None:
        assert len(VARIANT_NAMES) == 4
        assert VARIANT_NAMES == ("darkmode", "minimal", "sketchnote", "claymation")

    def test_all_dimensions_has_eight(self) -> None:
        assert len(ALL_DIMENSIONS) == 8
        assert "label_fidelity" in ALL_DIMENSIONS
        assert "structural_accuracy" in ALL_DIMENSIONS
        assert "content_accuracy" in ALL_DIMENSIONS


class TestLoadDiagramData:
    def test_loads_2dim_quality_json(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        assert data.name == "test-diagram"
        assert data.fmt == "dot"
        assert data.node_count == 5
        assert data.edge_count == 4

    def test_2dim_has_label_fidelity_and_structural_accuracy(
        self, tmp_run_dir: Path
    ) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        assert data.variants["darkmode"]["label_fidelity"] == 4
        assert data.variants["darkmode"]["structural_accuracy"] == 5

    def test_2dim_missing_dimensions_are_none(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        assert data.variants["darkmode"].get("content_accuracy") is None
        assert data.variants["darkmode"].get("layout_quality") is None

    def test_loads_8dim_quality_json(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram-8")
        assert data is not None
        assert data.name == "test-diagram-8"
        assert data.fmt == "mermaid"
        assert data.variants["darkmode"]["content_accuracy"] == 4
        assert data.variants["sketchnote"]["aesthetic_fidelity"] == 5

    def test_discovers_variant_pngs(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        assert len(data.variant_images) == 4
        assert "darkmode" in data.variant_images
        assert data.variant_images["darkmode"].name == "test-diagram_darkmode.png"

    def test_discovers_source_image(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram-8")
        assert data is not None
        assert data.source_image is not None
        assert data.source_image.name == "test-diagram-8_source.png"

    def test_no_source_image_when_absent(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        assert data.source_image is None

    def test_verification_data_loaded(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        assert data.verification["label_completeness"] == 0.9
        assert data.verification["edge_completeness"] == 0.75
        assert data.verification["missing_labels"] == ["NodeX"]

    def test_average_score_2dim(self, tmp_run_dir: Path) -> None:
        data = load_diagram_data(tmp_run_dir / "test-diagram")
        assert data is not None
        # darkmode: (4+5)/2=4.5, minimal: (3+4)/2=3.5,
        # sketchnote: (5+3)/2=4, clay: (4+4)/2=4
        assert data.average_score == 4.0

    def test_returns_none_for_missing_quality_json(self, tmp_path: Path) -> None:
        d = tmp_path / "no-quality"
        d.mkdir()
        (d / "some-file.png").write_bytes(b"PNG")
        data = load_diagram_data(d)
        assert data is None


class TestLoadRunData:
    def test_loads_all_diagrams(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        assert len(run.diagrams) == 2

    def test_diagrams_sorted_by_name(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        names = [d.name for d in run.diagrams]
        assert names == sorted(names)

    def test_run_dir_path_stored(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        assert run.run_dir == tmp_run_dir

    def test_skips_non_directories(self, tmp_run_dir: Path) -> None:
        (tmp_run_dir / "stray-file.txt").write_text("not a diagram")
        run = load_run_data(tmp_run_dir)
        assert len(run.diagrams) == 2

    def test_skips_dirs_without_quality_json(self, tmp_run_dir: Path) -> None:
        d = tmp_run_dir / "empty-diagram"
        d.mkdir()
        run = load_run_data(tmp_run_dir)
        assert len(run.diagrams) == 2


class TestScoreColor:
    def test_green_for_4_and_above(self) -> None:
        assert score_color(4.0) == "green"
        assert score_color(5.0) == "green"

    def test_yellow_for_3_to_3_9(self) -> None:
        assert score_color(3.0) == "yellow"
        assert score_color(3.9) == "yellow"

    def test_red_for_below_3(self) -> None:
        assert score_color(2.9) == "red"
        assert score_color(1.0) == "red"


class TestGenerateGridHtml:
    def test_contains_diagram_cards(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "test-diagram" in html
        assert "test-diagram-8" in html

    def test_contains_format_badges(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "dot" in html
        assert "mermaid" in html

    def test_contains_score_values(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "4.0" in html

    def test_contains_complexity_indicators(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "5n" in html
        assert "4e" in html

    def test_contains_verification_data(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "90" in html  # label_completeness 0.9 -> 90%
        assert "75" in html  # edge_completeness 0.75 -> 75%

    def test_contains_card_css_class(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "card" in html

    def test_contains_image_references(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_grid_html(run)
        assert "test-diagram_darkmode.png" in html


class TestGenerateDetailHtml:
    def test_contains_image_strip(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d = run.diagrams[0]
        html = generate_detail_html(d)
        assert "image-strip" in html
        for variant in VARIANT_NAMES:
            assert f"{d.name}_{variant}.png" in html

    def test_contains_source_image_when_present(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d8 = [d for d in run.diagrams if d.name == "test-diagram-8"][0]
        html = generate_detail_html(d8)
        assert "test-diagram-8_source.png" in html

    def test_source_placeholder_when_absent(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d = [d for d in run.diagrams if d.name == "test-diagram"][0]
        html = generate_detail_html(d)
        assert "source not available" in html.lower() or "no-source" in html

    def test_contains_score_heatmap(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d = run.diagrams[0]
        html = generate_detail_html(d)
        assert "heatmap" in html
        assert "label_fidelity" in html or "Label Fidelity" in html
        assert "structural_accuracy" in html or "Structural Accuracy" in html

    def test_heatmap_shows_na_for_missing_dimensions(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d = [d for d in run.diagrams if d.name == "test-diagram"][0]
        html = generate_detail_html(d)
        assert "N/A" in html

    def test_heatmap_shows_all_scores_for_8dim(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d8 = [d for d in run.diagrams if d.name == "test-diagram-8"][0]
        html = generate_detail_html(d8)
        assert "content_accuracy" in html.lower() or "Content Accuracy" in html

    def test_contains_topology_diff(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d = [d for d in run.diagrams if d.name == "test-diagram"][0]
        html = generate_detail_html(d)
        assert "NodeX" in html
        assert "A -&gt; B" in html or "A -> B" in html

    def test_contains_completeness_percentages(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        d = run.diagrams[0]
        html = generate_detail_html(d)
        assert "90" in html
        assert "75" in html


class TestGenerateDashboardHtml:
    def test_contains_total_diagrams(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_dashboard_html(run)
        assert ">2<" in html or ">2 " in html

    def test_contains_dimension_averages(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_dashboard_html(run)
        assert "dimension-chart" in html or "bar-chart" in html
        assert "Label Fidelity" in html or "label_fidelity" in html

    def test_contains_complexity_bands(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_dashboard_html(run)
        assert "small" in html.lower() or "medium" in html.lower()

    def test_contains_worst_performers(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_dashboard_html(run)
        assert "worst" in html.lower() or "bottom" in html.lower()
        assert "test-diagram" in html

    def test_contains_key_metrics(self, tmp_run_dir: Path) -> None:
        run = load_run_data(tmp_run_dir)
        html = generate_dashboard_html(run)
        assert "metrics" in html.lower() or "key-metric" in html

    def test_handles_run_with_single_diagram(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "single-run"
        run_dir.mkdir()
        d = run_dir / "only-diagram"
        d.mkdir()
        quality = {
            "diagram": "only-diagram",
            "format": "dot",
            "node_count": 3,
            "edge_count": 2,
            "variants": {
                "darkmode": {"label_fidelity": 4, "structural_accuracy": 5},
                "minimal": {"label_fidelity": 3, "structural_accuracy": 4},
                "sketchnote": {"label_fidelity": 5, "structural_accuracy": 3},
                "claymation": {"label_fidelity": 4, "structural_accuracy": 4},
            },
            "verification": {
                "label_completeness": 0.9,
                "edge_completeness": 0.75,
                "missing_labels": ["NodeX"],
                "missing_edges": ["A -> B"],
            },
        }
        (d / "quality.json").write_text(json.dumps(quality))
        run = load_run_data(run_dir)
        html = generate_dashboard_html(run)
        assert "only-diagram" in html or "test-diagram" in html
