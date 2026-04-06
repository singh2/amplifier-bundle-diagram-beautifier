"""Tests for agents/diagram-beautifier.md structure and correctness."""

from pathlib import Path

AGENT_FILE = Path(__file__).parent.parent / "agents" / "diagram-beautifier.md"


def _read_agent() -> str:
    return AGENT_FILE.read_text(encoding="utf-8")


def test_agent_file_exists() -> None:
    assert AGENT_FILE.exists(), f"Agent file not found: {AGENT_FILE}"


def test_agent_has_yaml_frontmatter() -> None:
    content = _read_agent()
    assert content.startswith("---"), "Agent file must start with '---' frontmatter"
    second_delimiter = content.index("---", 3)
    assert second_delimiter > 3


def test_agent_frontmatter_has_meta_name() -> None:
    content = _read_agent()
    frontmatter_end = content.index("---", 3)
    frontmatter = content[:frontmatter_end]
    assert "name: diagram-beautifier" in frontmatter


def test_agent_frontmatter_has_model_role() -> None:
    content = _read_agent()
    frontmatter_end = content.index("---", 3)
    frontmatter = content[:frontmatter_end]
    assert "image-gen" in frontmatter


def test_workflow_has_8_steps() -> None:
    content = _read_agent()
    for n in range(1, 9):
        assert f"{n}. **" in content or f"{n}." in content, f"Step {n} not found"


def test_workflow_step_order() -> None:
    content = _read_agent()
    keywords_in_order = [
        "parse",
        "dependency",
        "aesthetic",
        "decompos",
        "beautif",
        "review",
        "assembl",
        "present",
    ]
    lower = content.lower()
    last_pos = -1
    for keyword in keywords_in_order:
        pos = lower.find(keyword)
        assert pos != -1, f"Keyword '{keyword}' not found"
        assert pos > last_pos, f"Keyword '{keyword}' out of order"
        last_pos = pos


def test_agent_mentions_structural_preservation() -> None:
    content = _read_agent()
    lower = content.lower()
    assert "structural preservation" in lower or "preserve" in lower


def test_agent_mentions_label_fidelity() -> None:
    content = _read_agent()
    assert "label fidelity" in content.lower()


def test_agent_mentions_nano_banana() -> None:
    content = _read_agent()
    assert "nano-banana" in content


def test_agent_mentions_stitch_panels() -> None:
    content = _read_agent()
    assert "stitch_panels" in content


def test_agent_references_style_guide() -> None:
    content = _read_agent()
    assert "style-guide" in content or "style guide" in content.lower()


def test_agent_mentions_png_input() -> None:
    """Agent must describe PNG input path in the Input Types section."""
    content = _read_agent()
    lower = content.lower()
    assert "input types" in lower and "png" in lower


def test_agent_uses_analyze_for_png_ground_truth() -> None:
    """Agent must mention using nano-banana analyze for PNG label ground truth."""
    content = _read_agent()
    lower = content.lower()
    assert "analyze" in lower and "ground truth" in lower


def test_agent_accepts_precomputed_analysis() -> None:
    """Agent Step 1 must accept pre-computed analysis from root session."""
    content = _read_agent()
    lower = content.lower()
    assert "pre" in lower and (
        "analys" in lower or "classif" in lower or "passed" in lower
    )


def test_agent_skips_step1_analyze_when_precomputed() -> None:
    """Agent must skip its own analyze call when root session already provided analysis."""
    content = _read_agent()
    lower = content.lower()
    assert "skip" in lower and ("step 1" in lower or "analyze" in lower)


def test_agent_accepts_pre_analysis_from_root_session() -> None:
    """Agent must describe using PRE-ANALYSIS block when passed from root session."""
    content = _read_agent()
    assert "PRE-ANALYSIS" in content


def test_agent_skips_steps_when_pre_analysis_provided() -> None:
    """Agent must skip Step 2 when pre-analysis is available."""
    content = _read_agent()
    lower = content.lower()
    # Must mention skipping when pre-analysis exists
    assert "pre-analysis" in lower and "skip" in lower


def _get_step_5_block(content: str) -> str:
    start = content.find("5. **Beautify**")
    assert start != -1, "Step 5 header '5. **Beautify**' not found in agent file"
    end = content.find("6. **Quality review**", start)
    return content[start:end] if end != -1 else content[start:]


def test_step5_has_quality_bar_directive() -> None:
    """Step 5 must include a quality bar directive about being dramatically more
    visually impressive or publication quality."""
    content = _read_agent()
    block = _get_step_5_block(content)
    assert (
        "dramatically more visually impressive" in block
        or "publication quality" in block
    ), (
        "Step 5 must include a quality bar directive "
        "('dramatically more visually impressive' or 'publication quality').\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step5_prompt_construction_order_aesthetic_before_structural() -> None:
    """Step 5 must describe aesthetic properties before structural preservation,
    and both must be present."""
    content = _read_agent()
    block = _get_step_5_block(content)
    assert "aesthetic properties" in block.lower(), (
        f"Step 5 must mention 'aesthetic properties'.\nActual step 5 block:\n{block}"
    )
    assert "structural preservation" in block.lower(), (
        f"Step 5 must mention 'structural preservation'.\nActual step 5 block:\n{block}"
    )
    aesthetic_pos = block.lower().find("aesthetic properties")
    structural_pos = block.lower().find("structural preservation")
    assert aesthetic_pos < structural_pos, (
        "Step 5 must list 'aesthetic properties' before 'structural preservation'.\n"
        f"aesthetic_pos={aesthetic_pos}, structural_pos={structural_pos}\n"
        f"Actual step 5 block:\n{block}"
    )


def _get_step_6_block(content: str) -> str:
    start = content.find("6. **Quality review**")
    assert start != -1, "Step 6 header '6. **Quality review**' not found in agent file"
    end = content.find("7. **Assemble**", start)
    return content[start:end] if end != -1 else content[start:]


def test_step6_has_color_category_fidelity_dimension() -> None:
    """Step 6 must include 'color-category fidelity' as an 8th quality dimension."""
    content = _read_agent()
    block = _get_step_6_block(content)
    assert "color-category fidelity" in block.lower(), (
        "Step 6 must include 'color-category fidelity' dimension.\n"
        f"Actual step 6 block:\n{block}"
    )


def test_step6_color_category_fidelity_scoped_to_legend_diagrams() -> None:
    """Color-category fidelity must be scoped to diagrams with a semantic legend."""
    content = _read_agent()
    block = _get_step_6_block(content)
    assert "semantic legend" in block.lower(), (
        "Step 6 color-category fidelity must be scoped with 'semantic legend' qualifier.\n"
        f"Actual step 6 block:\n{block}"
    )


def test_agent_references_diagram_style_guide() -> None:
    """The agent file must reference 'diagram-style-guide.md' in the Design Knowledge section."""
    content = _read_agent()
    assert "diagram-style-guide.md" in content, (
        "Agent file must reference 'diagram-style-guide.md' in Design Knowledge section."
    )


def _get_step_1_block(content: str) -> str:
    start = content.find("1. **Parse")
    assert start != -1, "Step 1 header '1. **Parse' not found in agent file"
    end = content.find("2. **Dependency", start)
    return content[start:end] if end != -1 else content[start:]


def test_step1_mentions_topology_manifest() -> None:
    """Step 1 must produce a topology manifest from the parsed source."""
    content = _read_agent()
    block = _get_step_1_block(content)
    assert "topology manifest" in block.lower(), (
        f"Step 1 must mention 'topology manifest'.\nActual step 1 block:\n{block}"
    )


def test_step1_mentions_hero_candidate() -> None:
    """Step 1 must identify a hero candidate (highest-connectivity node)."""
    content = _read_agent()
    block = _get_step_1_block(content)
    assert "hero candidate" in block.lower(), (
        f"Step 1 must mention 'hero candidate'.\nActual step 1 block:\n{block}"
    )


def test_step1_lists_semantic_node_types() -> None:
    """Step 1 must list semantic node types including terminal, decision, and process."""
    content = _read_agent()
    block = _get_step_1_block(content)
    assert "terminal" in block.lower(), (
        "Step 1 must mention semantic node type 'terminal'.\n"
        f"Actual step 1 block:\n{block}"
    )
    assert "decision" in block.lower(), (
        "Step 1 must mention semantic node type 'decision'.\n"
        f"Actual step 1 block:\n{block}"
    )
    assert "process" in block.lower(), (
        "Step 1 must mention semantic node type 'process'.\n"
        f"Actual step 1 block:\n{block}"
    )


def test_step4_is_panel_decomposition() -> None:
    """Step 4 must be Panel decomposition (render step removed)."""
    content = _read_agent()
    assert "4. **Panel decomposition**" in content, (
        "Step 4 must be 'Panel decomposition'. "
        "The render step should have been removed and steps renumbered."
    )


def test_no_render_step() -> None:
    """'Render to plain PNG' must not appear anywhere in the agent file."""
    content = _read_agent()
    assert "Render to plain PNG" not in content, (
        "Agent file must not contain 'Render to plain PNG' — "
        "the render step has been removed from the workflow."
    )


def test_step5_has_polished_subsection() -> None:
    """Step 5 must contain a '5a' Polished generation subsection."""
    content = _read_agent()
    block = _get_step_5_block(content)
    assert "5a" in block, (
        "Step 5 must contain a '5a' Polished subsection.\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step5_has_cinematic_subsection() -> None:
    """Step 5 must contain a '5b' Cinematic generation subsection."""
    content = _read_agent()
    block = _get_step_5_block(content)
    assert "5b" in block, (
        "Step 5 must contain a '5b' Cinematic subsection.\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step5_cinematic_has_no_reference_image() -> None:
    """Step 5b Cinematic must explicitly state no reference_image_path is used."""
    content = _read_agent()
    block = _get_step_5_block(content)
    lower = block.lower()
    assert "never" in lower or "no reference" in lower, (
        "Step 5b Cinematic must explicitly state no reference image is used "
        "('never' or 'no reference').\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step5_cinematic_has_hero_element_instruction() -> None:
    """Step 5b Cinematic must mention hero element as focal point."""
    content = _read_agent()
    block = _get_step_5_block(content)
    lower = block.lower()
    assert "hero" in lower and "focal point" in lower, (
        "Step 5b Cinematic must mention hero element as focal point.\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step5_cinematic_has_spatial_freedom_statement() -> None:
    """Step 5b Cinematic must mention spatial freedom or 'not bound by original layout'."""
    content = _read_agent()
    block = _get_step_5_block(content)
    lower = block.lower()
    assert "spatial freedom" in lower or "not bound" in lower, (
        "Step 5b Cinematic must mention spatial freedom or 'not bound by original layout'.\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step5_polished_has_reference_image_guard() -> None:
    """Step 5a Polished must include a completeness guard for PNG reference image."""
    content = _read_agent()
    block = _get_step_5_block(content)
    lower = block.lower()
    assert "completeness" in lower or "no nodes or connections were missed" in lower, (
        "Step 5a Polished must include a completeness guard for the PNG reference image.\n"
        f"Actual step 5 block:\n{block}"
    )


def test_step6_has_polished_review_subsection() -> None:
    """Step 6 must contain a '6a' Polished quality review subsection."""
    content = _read_agent()
    block = _get_step_6_block(content)
    assert "6a" in block, (
        "Step 6 must contain a '6a' Polished quality review subsection.\n"
        f"Actual step 6 block:\n{block}"
    )


def test_step6_has_cinematic_review_subsection() -> None:
    """Step 6 must contain a '6b' Cinematic quality review subsection."""
    content = _read_agent()
    block = _get_step_6_block(content)
    assert "6b" in block, (
        "Step 6 must contain a '6b' Cinematic quality review subsection.\n"
        f"Actual step 6 block:\n{block}"
    )


def test_step6_cinematic_names_manifest_as_ground_truth() -> None:
    """Step 6b Cinematic review must name topology manifest as 'sole ground truth'."""
    content = _read_agent()
    block = _get_step_6_block(content)
    assert "sole ground truth" in block.lower(), (
        "Step 6b Cinematic review must name topology manifest as 'sole ground truth'.\n"
        f"Actual step 6 block:\n{block}"
    )


def test_step6_cinematic_has_missing_node_refinement_instruction() -> None:
    """Step 6b Cinematic review must describe a missing node refinement process."""
    content = _read_agent()
    block = _get_step_6_block(content)
    lower = block.lower()
    assert "absent" in lower or ("missing" in lower and "manifest" in lower), (
        "Step 6b Cinematic review must describe a missing node refinement process "
        "(e.g. 'absent from the output' with re-prompt instruction).\n"
        f"Actual step 6 block:\n{block}"
    )


def _get_step_8_block(content: str) -> str:
    start = content.find("8. **Present all four variants**")
    assert start != -1, (
        "Step 8 header '8. **Present all four variants**' not found in agent file"
    )
    # Find the next section after step 8 (e.g., "## Using nano-banana")
    end = content.find("\n## ", start)
    return content[start:end] if end != -1 else content[start:]


def test_step8_is_present_all_four_variants() -> None:
    """Step 8 header must be 'Present all four variants'."""
    content = _read_agent()
    assert "8. **Present all four variants**" in content, (
        "Step 8 header must be '8. **Present all four variants**'. "
        "The system now produces four aesthetic outputs, not a Polished/Cinematic pair."
    )


def test_step8_mentions_all_four_variants() -> None:
    """Step 8 must mention all four variant aesthetics."""
    content = _read_agent()
    block = _get_step_8_block(content)
    assert "Dark Mode Tech" in block, (
        f"Step 8 must mention 'Dark Mode Tech' variant.\nActual step 8 block:\n{block}"
    )
    assert "Clean Minimalist" in block, (
        f"Step 8 must mention 'Clean Minimalist' variant.\nActual step 8 block:\n{block}"
    )
    assert "Sketchnote" in block, (
        f"Step 8 must mention 'Sketchnote' variant.\nActual step 8 block:\n{block}"
    )
    assert "Claymation" in block, (
        f"Step 8 must mention 'Claymation' variant.\nActual step 8 block:\n{block}"
    )


def test_step8_offers_refinement_options() -> None:
    """Step 8 must offer refinement options to the user."""
    content = _read_agent()
    block = _get_step_8_block(content)
    lower = block.lower()
    assert "refin" in lower, (
        "Step 8 must offer refinement options (e.g. 'pick one for refinement').\n"
        f"Actual step 8 block:\n{block}"
    )
