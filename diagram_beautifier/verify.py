"""Programmatic label and topology verification against ground truth.

Separates extraction (VLM or OCR) from comparison (programmatic fuzzy matching).
Provides an independent ground-truth check that does not rely on VLM self-assessment.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field


@dataclass
class LabelMatch:
    """Result of matching a single expected label against extracted labels."""

    expected: str
    found: str | None
    similarity: float
    status: str  # "exact", "close", "missing"


@dataclass
class VerificationResult:
    """Structured result of a programmatic verification pass."""

    total_expected: int
    exact_matches: int
    close_matches: int
    missing: int
    extra: int
    completeness_score: float
    details: list[LabelMatch] = field(default_factory=list)
    extra_labels: list[str] = field(default_factory=list)
    duplicates: list[str] = field(
        default_factory=list
    )  # labels appearing more than once


def build_label_extraction_prompt() -> str:
    """Build a VLM prompt for structured label extraction (not judgment).

    The VLM reports what it sees. Comparison is done programmatically.
    """
    return "\n".join(
        [
            "TEXT EXTRACTION (not quality judgment):",
            "",
            "List every piece of text visible in this image.",
            "Include: node labels, edge labels, legend text, title text,",
            "annotation text, and any text inside containers or grouping boxes.",
            "",
            "IMPORTANT: Do not skip any text, no matter how small, abbreviated,",
            "or technical. Include labels with special characters, parentheses,",
            "arrows, dots, and underscores exactly as shown.",
            "",
            "Format your response as:",
            "LABELS: label1 | label2 | label3 | ...",
            "",
            "List every label on a single line separated by ' | '.",
            "Preserve exact spelling and capitalization as shown in the image.",
            "Do not interpret, summarize, or rephrase -- copy exactly what you see.",
        ]
    )


def compare_labels(
    expected: list[str],
    found: list[str],
    threshold: float = 0.8,
) -> VerificationResult:
    """Compare extracted labels against ground-truth manifest labels.

    Uses difflib.SequenceMatcher for fuzzy matching. Greedy best-match,
    no reuse of found labels.
    """
    if not expected:
        return VerificationResult(
            total_expected=0,
            exact_matches=0,
            close_matches=0,
            missing=0,
            extra=len(found),
            completeness_score=1.0,
            extra_labels=list(found),
        )

    expected_norm = [_normalize(label) for label in expected]
    found_norm = [_normalize(label) for label in found]
    used_found: set[int] = set()
    details: list[LabelMatch] = []

    for exp_raw, exp_n in zip(expected, expected_norm):
        best_idx = -1
        best_sim = 0.0
        best_raw = None

        for j, (fnd_raw, fnd_n) in enumerate(zip(found, found_norm)):
            if j in used_found:
                continue
            sim = difflib.SequenceMatcher(None, exp_n, fnd_n).ratio()
            if sim > best_sim:
                best_sim = sim
                best_idx = j
                best_raw = fnd_raw

        if best_sim == 1.0:
            details.append(LabelMatch(exp_raw, best_raw, 1.0, "exact"))
            used_found.add(best_idx)
        elif best_sim >= threshold:
            details.append(LabelMatch(exp_raw, best_raw, best_sim, "close"))
            used_found.add(best_idx)
        else:
            details.append(LabelMatch(exp_raw, None, best_sim, "missing"))

    exact = sum(1 for d in details if d.status == "exact")
    close = sum(1 for d in details if d.status == "close")
    miss = sum(1 for d in details if d.status == "missing")
    extra_labels = [found[j] for j in range(len(found)) if j not in used_found]
    completeness = (exact + close) / len(expected)

    # Detect duplicate labels in found list
    from collections import Counter

    found_counts = Counter(_normalize(f) for f in found)
    duplicates = [label for label, count in found_counts.items() if count > 1]

    # Penalize completeness score for duplicates
    if duplicates:
        completeness *= max(0.5, 1 - 0.1 * len(duplicates))

    return VerificationResult(
        total_expected=len(expected),
        exact_matches=exact,
        close_matches=close,
        missing=miss,
        extra=len(extra_labels),
        completeness_score=completeness,
        details=details,
        extra_labels=extra_labels,
        duplicates=duplicates,
    )


def compare_edges(
    expected: list[tuple[str, str]],
    found: list[tuple[str, str]],
    threshold: float = 0.8,
) -> VerificationResult:
    """Compare extracted edge pairs against ground-truth manifest edges.

    An edge matches if both endpoints match above the threshold.
    """
    if not expected:
        return VerificationResult(
            total_expected=0,
            exact_matches=0,
            close_matches=0,
            missing=0,
            extra=len(found),
            completeness_score=1.0,
        )

    used_found: set[int] = set()
    details: list[LabelMatch] = []

    for exp_src, exp_dst in expected:
        exp_key = f"{exp_src} -> {exp_dst}"
        best_idx = -1
        best_sim = 0.0
        best_key = None

        for j, (fnd_src, fnd_dst) in enumerate(found):
            if j in used_found:
                continue
            src_sim = difflib.SequenceMatcher(
                None,
                _normalize(exp_src),
                _normalize(fnd_src),
            ).ratio()
            dst_sim = difflib.SequenceMatcher(
                None,
                _normalize(exp_dst),
                _normalize(fnd_dst),
            ).ratio()
            edge_sim = min(src_sim, dst_sim)
            if edge_sim > best_sim:
                best_sim = edge_sim
                best_idx = j
                best_key = f"{fnd_src} -> {fnd_dst}"

        if best_sim == 1.0:
            details.append(LabelMatch(exp_key, best_key, 1.0, "exact"))
            used_found.add(best_idx)
        elif best_sim >= threshold:
            details.append(LabelMatch(exp_key, best_key, best_sim, "close"))
            used_found.add(best_idx)
        else:
            details.append(LabelMatch(exp_key, None, best_sim, "missing"))

    exact = sum(1 for d in details if d.status == "exact")
    close = sum(1 for d in details if d.status == "close")
    miss = sum(1 for d in details if d.status == "missing")
    extra_count = len(found) - len(used_found)
    completeness = (exact + close) / len(expected)

    return VerificationResult(
        total_expected=len(expected),
        exact_matches=exact,
        close_matches=close,
        missing=miss,
        extra=extra_count,
        completeness_score=completeness,
        details=details,
    )


def ocr_extract_labels(image_path: str) -> list[str] | None:
    """Extract text labels via pytesseract OCR (optional dependency).

    Returns None if pytesseract is not installed.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return None

    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image)

    labels: list[str] = []
    for line in raw_text.strip().split("\n"):
        cleaned = line.strip()
        if cleaned and len(cleaned) > 1:
            labels.append(cleaned)
    return labels


def _normalize(text: str) -> str:
    """Normalize label text for fuzzy comparison."""
    return text.strip().lower().replace("_", " ").replace("-", " ")
