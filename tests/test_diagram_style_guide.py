from pathlib import Path

DIAGRAM_STYLE_GUIDE = Path(__file__).parent.parent / "docs" / "diagram-style-guide.md"


def _read_style_guide() -> str:
    return DIAGRAM_STYLE_GUIDE.read_text(encoding="utf-8")


def test_file_exists() -> None:
    """docs/diagram-style-guide.md must exist."""
    assert DIAGRAM_STYLE_GUIDE.exists(), "docs/diagram-style-guide.md not found"


def test_scoping_disclaimer_present() -> None:
    """File must state its scope — 'ONLY' and 'diagram-beautifier' must both appear."""
    content = _read_style_guide()
    assert "ONLY" in content, "Scope disclaimer missing 'ONLY'"
    assert "diagram-beautifier" in content, (
        "Scope disclaimer missing 'diagram-beautifier'"
    )


def test_node_shape_table_present() -> None:
    """File must contain a 'Node Shapes' section heading."""
    content = _read_style_guide()
    assert "Node Shapes" in content, "'Node Shapes' section heading not found"


def test_dark_mode_tech_has_hexagon_for_ai_agent_steps() -> None:
    """Dark Mode Tech row in Node Shapes table must specify Hexagon for AI Agent steps."""
    content = _read_style_guide()
    lines = content.splitlines()
    dark_mode_row = next(
        (line for line in lines if "Dark Mode Tech" in line and "Hexagon" in line), None
    )
    assert dark_mode_row is not None, (
        "Dark Mode Tech row must specify 'Hexagon' for AI Agent steps — "
        "no single line contained both 'Dark Mode Tech' and 'Hexagon'."
    )


def test_clean_minimalist_has_orthogonal_connector_constraint() -> None:
    """Clean Minimalist must require orthogonal connectors and forbid diagonals."""
    content = _read_style_guide()
    assert "Orthogonal only" in content, "'Orthogonal only' connector rule not found"
    assert "Diagonal edges strictly forbidden" in content, (
        "Diagonal edges constraint not found"
    )


def test_dark_mode_tech_has_single_legend_constraint() -> None:
    """Dark Mode Tech connector row must specify exactly ONE legend constraint."""
    content = _read_style_guide()
    lines = content.splitlines()
    dark_mode_connector_row = next(
        (
            line
            for line in lines
            if "Dark Mode Tech" in line and "ONE" in line and "legend" in line.lower()
        ),
        None,
    )
    assert dark_mode_connector_row is not None, (
        "Dark Mode Tech connector row must specify exactly ONE legend constraint — "
        "no single line contained 'Dark Mode Tech', 'ONE', and 'legend'."
    )


def test_connector_styling_table_present() -> None:
    """File must contain a 'Connector Styling' section heading."""
    content = _read_style_guide()
    assert "Connector Styling" in content, (
        "'Connector Styling' section heading not found"
    )


def test_quality_bar_directive_present() -> None:
    """File must contain the quality bar opening directive."""
    content = _read_style_guide()
    assert "dramatically more visually impressive" in content, (
        "Quality bar directive ('dramatically more visually impressive') not found"
    )


def test_color_category_mapping_guidance_present() -> None:
    """File must contain color-category mapping guidance (any casing)."""
    content = _read_style_guide()
    assert "color-category mapping" in content.lower(), (
        "'Color-category mapping' guidance not found"
    )


def test_four_variants_section_present() -> None:
    """File must contain a '## Four Variants' section heading."""
    content = _read_style_guide()
    assert "## Four Variants" in content, (
        "'## Four Variants' section heading not found"
    )


def test_polished_described_as_document_ready() -> None:
    """Polished variant must be described as 'document-ready'."""
    content = _read_style_guide()
    assert "document-ready" in content, (
        "'document-ready' description for Polished variant not found"
    )


def test_cinematic_described_as_presentation_ready() -> None:
    """Cinematic variant must be described as 'presentation-ready'."""
    content = _read_style_guide()
    assert "presentation-ready" in content, (
        "'presentation-ready' description for Cinematic variant not found"
    )


def test_hero_candidate_mentioned_in_cinematic_description() -> None:
    """Cinematic variant description must mention 'hero candidate'."""
    content = _read_style_guide()
    assert "hero candidate" in content, (
        "'hero candidate' not found in style guide — expected in Cinematic description"
    )


def test_cinematic_guidance_section_present() -> None:
    """File must contain a '## Cinematic Guidance Per Aesthetic' section heading."""
    content = _read_style_guide()
    assert "## Cinematic Guidance Per Aesthetic" in content, (
        "'## Cinematic Guidance Per Aesthetic' section heading not found"
    )


def test_dark_mode_tech_is_described_as_polished_variant() -> None:
    """Dark Mode Tech must be described as a Polished variant in the Four Variants section."""
    content = _read_style_guide()
    four_variants_start = content.find("## Four Variants")
    assert four_variants_start != -1, "'## Four Variants' section not found"
    four_variants_block = content[four_variants_start : four_variants_start + 600]
    assert "Dark Mode Tech" in four_variants_block and "Polished" in four_variants_block, (
        "Four Variants section must associate Dark Mode Tech with the Polished approach"
    )


def test_clean_minimalist_is_described_as_polished_variant() -> None:
    """Clean Minimalist must be described as a Polished variant in the Four Variants section."""
    content = _read_style_guide()
    four_variants_start = content.find("## Four Variants")
    assert four_variants_start != -1, "'## Four Variants' section not found"
    four_variants_block = content[four_variants_start : four_variants_start + 600]
    assert (
        "Clean Minimalist" in four_variants_block and "Polished" in four_variants_block
    ), "Four Variants section must associate Clean Minimalist with the Polished approach"


def test_cinematic_claymation_has_scene_description() -> None:
    """Claymation Studio row in Cinematic Guidance table must mention 'full scene'."""
    content = _read_style_guide()
    lines = content.splitlines()
    claymation_cinematic_row = next(
        (
            line
            for line in lines
            if "Claymation" in line and "full scene" in line.lower()
        ),
        None,
    )
    assert claymation_cinematic_row is not None, (
        "Claymation Studio cinematic row must mention 'full scene' — "
        "no single line contained 'Claymation' and 'full scene'."
    )
