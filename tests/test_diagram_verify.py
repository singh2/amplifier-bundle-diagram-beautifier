"""Tests for diagram_beautifier/verify.py -- programmatic verification."""

from __future__ import annotations

from diagram_beautifier.verify import (
    build_label_extraction_prompt,
    compare_edges,
    compare_labels,
    ocr_extract_labels,
)


class TestBuildLabelExtractionPrompt:
    def test_returns_nonempty_string(self) -> None:
        prompt = build_label_extraction_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_requests_structured_format(self) -> None:
        prompt = build_label_extraction_prompt()
        assert "LABELS:" in prompt

    def test_asks_for_exact_spelling(self) -> None:
        prompt = build_label_extraction_prompt()
        lower = prompt.lower()
        assert "exact" in lower or "preserve" in lower

    def test_is_extraction_not_judgment(self) -> None:
        prompt = build_label_extraction_prompt()
        assert (
            "not quality judgment" in prompt.lower() or "not judgment" in prompt.lower()
        )


class TestCompareLabels:
    def test_perfect_match(self) -> None:
        result = compare_labels(
            expected=["Load Balancer", "API Gateway", "Database"],
            found=["Load Balancer", "API Gateway", "Database"],
        )
        assert result.exact_matches == 3
        assert result.missing == 0
        assert result.completeness_score == 1.0

    def test_all_missing(self) -> None:
        result = compare_labels(
            expected=["Load Balancer", "API Gateway"],
            found=[],
        )
        assert result.missing == 2
        assert result.exact_matches == 0
        assert result.completeness_score == 0.0

    def test_close_match_above_threshold(self) -> None:
        result = compare_labels(
            expected=["Load Balancer"],
            found=["Load Balancr"],  # typo
            threshold=0.8,
        )
        assert result.close_matches == 1
        assert result.missing == 0
        assert result.completeness_score == 1.0

    def test_close_match_below_threshold(self) -> None:
        result = compare_labels(
            expected=["Load Balancer"],
            found=["XYZ"],
            threshold=0.8,
        )
        assert result.missing == 1
        assert result.completeness_score == 0.0

    def test_extra_labels_detected(self) -> None:
        result = compare_labels(
            expected=["A", "B"],
            found=["A", "B", "C", "D"],
        )
        assert result.extra == 2
        assert result.extra_labels == ["C", "D"]

    def test_empty_expected(self) -> None:
        result = compare_labels(expected=[], found=["A", "B"])
        assert result.total_expected == 0
        assert result.completeness_score == 1.0
        assert result.extra == 2

    def test_case_insensitive_matching(self) -> None:
        result = compare_labels(
            expected=["Load Balancer"],
            found=["load balancer"],
        )
        assert result.exact_matches == 1 or result.close_matches == 1
        assert result.completeness_score == 1.0

    def test_underscore_normalization(self) -> None:
        result = compare_labels(
            expected=["api_gateway"],
            found=["api gateway"],
        )
        assert result.completeness_score == 1.0

    def test_no_reuse_of_found_labels(self) -> None:
        result = compare_labels(
            expected=["A", "B"],
            found=["A"],
        )
        assert result.exact_matches == 1
        assert result.missing == 1

    def test_details_populated(self) -> None:
        result = compare_labels(
            expected=["A", "B", "C"],
            found=["A", "C"],
        )
        assert len(result.details) == 3
        statuses = {d.expected: d.status for d in result.details}
        assert statuses["A"] == "exact"
        assert statuses["C"] == "exact"
        assert statuses["B"] == "missing"

    def test_mixed_results(self) -> None:
        result = compare_labels(
            expected=["Load Balancer", "API Gateway", "Database", "Cache"],
            found=["Load Balancer", "API Gatway", "Extra Node"],
        )
        assert result.exact_matches == 1  # Load Balancer
        assert result.close_matches == 1  # API Gatway ~ API Gateway
        assert result.missing == 2  # Database, Cache
        assert result.extra == 1  # Extra Node

    def test_duplicate_detection(self) -> None:
        result = compare_labels(
            expected=["A", "B", "C"],
            found=["A", "B", "C", "A", "A"],  # A appears 3 times
        )
        assert len(result.duplicates) > 0
        assert "a" in result.duplicates  # normalized

    def test_duplicates_penalize_completeness(self) -> None:
        result = compare_labels(
            expected=["A", "B"],
            found=["A", "B", "A", "A"],  # A appears 3 times
        )
        assert result.completeness_score < 1.0  # penalized

    def test_no_duplicates_when_clean(self) -> None:
        result = compare_labels(
            expected=["A", "B", "C"],
            found=["A", "B", "C"],
        )
        assert result.duplicates == []


class TestCompareEdges:
    def test_perfect_match(self) -> None:
        result = compare_edges(
            expected=[("A", "B"), ("B", "C")],
            found=[("A", "B"), ("B", "C")],
        )
        assert result.exact_matches == 2
        assert result.missing == 0

    def test_all_missing(self) -> None:
        result = compare_edges(
            expected=[("A", "B"), ("B", "C")],
            found=[],
        )
        assert result.missing == 2
        assert result.completeness_score == 0.0

    def test_fuzzy_endpoint_matching(self) -> None:
        result = compare_edges(
            expected=[("Load Balancer", "API Gateway")],
            found=[("Load Balancr", "API Gatway")],
            threshold=0.8,
        )
        assert result.close_matches == 1
        assert result.completeness_score == 1.0

    def test_empty_expected(self) -> None:
        result = compare_edges(expected=[], found=[("A", "B")])
        assert result.total_expected == 0
        assert result.completeness_score == 1.0

    def test_extra_edges(self) -> None:
        result = compare_edges(
            expected=[("A", "B")],
            found=[("A", "B"), ("X", "Y")],
        )
        assert result.exact_matches == 1
        assert result.extra == 1


class TestOcrExtractLabels:
    def test_returns_none_without_pytesseract(self) -> None:
        # pytesseract is not in project dependencies, so should return None
        result = ocr_extract_labels("/nonexistent/path.png")
        assert result is None
