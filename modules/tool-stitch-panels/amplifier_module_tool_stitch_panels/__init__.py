"""Amplifier tool module — stitch PNG panels into a combined infographic."""

import logging
from pathlib import Path
from typing import Any

from amplifier_core import ToolResult

logger = logging.getLogger(__name__)


class StitchPanelsTool:
    """Stack multiple PNG panel images into a single combined image."""

    @property
    def name(self) -> str:
        return "stitch_panels"

    @property
    def description(self) -> str:
        return (
            "Stitch multiple PNG panel images into a single combined image. "
            "Panels are composited in order, either top-to-bottom (vertical, default) "
            "or left-to-right (horizontal). Use after generating multi-panel "
            "infographics to produce a single combined file."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "panel_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered list of PNG file paths to combine",
                },
                "output_path": {
                    "type": "string",
                    "description": "File path for the stitched output PNG",
                },
                "direction": {
                    "type": "string",
                    "enum": ["vertical", "horizontal"],
                    "description": (
                        "Stack direction. 'vertical' (default) stacks top-to-bottom. "
                        "'horizontal' stacks left-to-right."
                    ),
                },
            },
            "required": ["panel_paths", "output_path"],
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Stack panel images and save the combined result."""
        try:
            from PIL import Image
        except ImportError:
            return ToolResult(
                success=False,
                output="Pillow is not installed. Run: pip install pillow",
            )

        panel_paths = input_data["panel_paths"]
        output_path = Path(input_data["output_path"])
        direction = input_data.get("direction", "vertical")

        if len(panel_paths) < 2:
            return ToolResult(
                success=False,
                output="Need at least 2 panel paths to stitch.",
            )

        try:
            images = [Image.open(p).convert("RGBA") for p in panel_paths]
        except FileNotFoundError as e:
            return ToolResult(success=False, output=f"Panel file not found: {e}")

        if direction == "horizontal":
            total_width = sum(img.width for img in images)
            total_height = max(img.height for img in images)
            combined = Image.new(
                "RGBA", (total_width, total_height), (255, 255, 255, 255)
            )
            x_offset = 0
            for img in images:
                combined.paste(img, (x_offset, 0))
                x_offset += img.width
        else:
            total_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)
            combined = Image.new(
                "RGBA", (total_width, total_height), (255, 255, 255, 255)
            )
            y_offset = 0
            for img in images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height

        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.save(str(output_path), "PNG")

        label = "vertically" if direction == "vertical" else "horizontally"
        return ToolResult(
            success=True,
            output=(
                f"Stitched {len(images)} panels {label} -> "
                f"{output_path} ({total_width}x{total_height}px)"
            ),
        )


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Mount the stitch-panels tool into the coordinator."""
    tool = StitchPanelsTool()
    await coordinator.mount("tools", tool, name=tool.name)
    logger.info("tool-stitch-panels mounted: registered 'stitch_panels'")
    return {
        "name": "tool-stitch-panels",
        "version": "0.1.0",
        "provides": ["stitch_panels"],
    }
