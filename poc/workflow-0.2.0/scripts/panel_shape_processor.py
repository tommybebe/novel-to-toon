"""
Phase 5 Helper: Panel Shape Processor for PoC v0.2.0

Generates and applies panel shape masks for non-rectangular panels.
Supports 10 shape types: rectangles, diagonal, jagged, circular, borderless, inset.
Uses PIL for mask generation and numpy for jagged polygon points.
"""

import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class PanelShape:
    """Panel shape constants matching the storyboard enum."""
    RECTANGLE_WIDE = "rectangle_wide"
    RECTANGLE_STANDARD = "rectangle_standard"
    RECTANGLE_TALL = "rectangle_tall"
    SQUARE = "square"
    DIAGONAL_LEFT = "diagonal_left"
    DIAGONAL_RIGHT = "diagonal_right"
    IRREGULAR_JAGGED = "irregular_jagged"
    BORDERLESS = "borderless"
    CIRCULAR = "circular"
    INSET = "inset"

    RECTANGULAR_SHAPES = {RECTANGLE_WIDE, RECTANGLE_STANDARD, RECTANGLE_TALL, SQUARE}


class PanelShapeProcessor:
    """Generate and apply panel shape masks."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def create_mask(self, shape: str, params: Optional[dict] = None) -> Image.Image:
        """
        Create a mask for the specified panel shape.

        Args:
            shape: One of the PanelShape constants
            params: Optional shape-specific parameters

        Returns:
            PIL Image in mode 'L' (grayscale), white=visible, black=transparent
        """
        params = params or {}
        mask = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(mask)

        if shape in PanelShape.RECTANGULAR_SHAPES:
            draw.rectangle([0, 0, self.width - 1, self.height - 1], fill=255)

        elif shape == PanelShape.DIAGONAL_LEFT:
            offset = int(params.get('offset', self.width * 0.15))
            points = [
                (offset, 0),
                (self.width, 0),
                (self.width, self.height),
                (0, self.height),
                (0, offset),
            ]
            draw.polygon(points, fill=255)

        elif shape == PanelShape.DIAGONAL_RIGHT:
            offset = int(params.get('offset', self.width * 0.15))
            points = [
                (0, 0),
                (self.width - offset, 0),
                (self.width, offset),
                (self.width, self.height),
                (0, self.height),
            ]
            draw.polygon(points, fill=255)

        elif shape == PanelShape.IRREGULAR_JAGGED:
            points = self._generate_jagged_polygon(params)
            draw.polygon(points, fill=255)

        elif shape == PanelShape.CIRCULAR:
            margin = params.get('margin', 0.05)
            cx, cy = self.width // 2, self.height // 2
            radius = int(min(cx, cy) * (1 - margin))
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=255
            )

        elif shape == PanelShape.BORDERLESS:
            # Full image — borderless means no mask clipping
            draw.rectangle([0, 0, self.width - 1, self.height - 1], fill=255)

        elif shape == PanelShape.INSET:
            # Inset: smaller centered rectangle with rounded corners
            inset_pct = params.get('inset_percent', 0.15)
            ix = int(self.width * inset_pct)
            iy = int(self.height * inset_pct)
            corner_radius = params.get('corner_radius', 20)
            draw.rounded_rectangle(
                [ix, iy, self.width - ix, self.height - iy],
                radius=corner_radius,
                fill=255
            )

        else:
            # Fallback: full rectangle
            draw.rectangle([0, 0, self.width - 1, self.height - 1], fill=255)

        # Optionally apply feathering for smoother edges
        feather = params.get('feather', 0)
        if feather > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))

        return mask

    def apply_mask(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """
        Apply mask to image, making masked-out areas transparent.

        Args:
            image: Source image (RGB or RGBA)
            mask: Grayscale mask (white=visible)

        Returns:
            RGBA image with transparency applied
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Resize mask to match image if needed
        if mask.size != image.size:
            mask = mask.resize(image.size, Image.Resampling.LANCZOS)

        result = image.copy()
        result.putalpha(mask)
        return result

    def _generate_jagged_polygon(self, params: dict) -> list[tuple[int, int]]:
        """Generate jagged polygon points for impact/chaos panels."""
        jaggedness = params.get('jaggedness', 0.1)
        num_points = params.get('num_points', 16)
        seed = params.get('seed', 42)

        rng = np.random.RandomState(seed)
        points = []

        for i in range(num_points):
            angle = (2 * np.pi * i) / num_points
            # Base radius varies between 0.4 and 0.5 of dimension
            radius = 0.45 + rng.uniform(-jaggedness, jaggedness)
            x = self.width / 2 + radius * self.width * np.cos(angle)
            y = self.height / 2 + radius * self.height * np.sin(angle)
            # Clamp to image bounds
            x = max(0, min(self.width - 1, int(x)))
            y = max(0, min(self.height - 1, int(y)))
            points.append((x, y))

        return points

    def needs_mask(self, shape: str) -> bool:
        """Check if a shape requires post-processing mask (non-rectangular)."""
        return shape not in PanelShape.RECTANGULAR_SHAPES and shape != PanelShape.BORDERLESS


def apply_panel_shape(
    image_path: str,
    shape: str,
    output_path: Optional[str] = None,
    params: Optional[dict] = None,
) -> str:
    """
    Convenience function to apply a panel shape mask to an image file.

    Args:
        image_path: Path to source image
        shape: Panel shape string
        output_path: Path for output (defaults to adding _masked suffix)
        params: Optional shape parameters

    Returns:
        Path to the masked output image
    """
    image = Image.open(image_path)
    processor = PanelShapeProcessor(image.width, image.height)

    if not processor.needs_mask(shape):
        # No masking needed for rectangular/borderless shapes
        return image_path

    mask = processor.create_mask(shape, params)
    result = processor.apply_mask(image, mask)

    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / f"{p.stem}_masked{p.suffix}")

    # Save mask separately for reference
    mask_path = Path(output_path).parent / f"{Path(output_path).stem}_mask.png"
    mask.save(str(mask_path))

    result.save(output_path)
    return output_path


def main():
    """Standalone test mode: generate sample masks for all shapes."""
    print("=" * 60)
    print("Panel Shape Processor - Test Mode")
    print("=" * 60)

    test_dir = Path(__file__).parent.parent / "phase5_generation" / "shape_tests"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create a test image (gradient)
    test_width, test_height = 1024, 1440
    test_image = Image.new('RGB', (test_width, test_height))
    for y in range(test_height):
        for x in range(test_width):
            r = int(255 * x / test_width)
            g = int(255 * y / test_height)
            b = 128
            test_image.putpixel((x, y), (r, g, b))

    test_image_path = test_dir / "test_gradient.png"
    test_image.save(str(test_image_path))
    print(f"\n  Test image: {test_image_path}")

    processor = PanelShapeProcessor(test_width, test_height)

    shapes_to_test = [
        (PanelShape.RECTANGLE_WIDE, {}),
        (PanelShape.DIAGONAL_LEFT, {"offset": test_width * 0.15}),
        (PanelShape.DIAGONAL_RIGHT, {"offset": test_width * 0.15}),
        (PanelShape.IRREGULAR_JAGGED, {"jaggedness": 0.1, "num_points": 16, "seed": 42}),
        (PanelShape.CIRCULAR, {"margin": 0.05}),
        (PanelShape.BORDERLESS, {}),
        (PanelShape.INSET, {"inset_percent": 0.1, "corner_radius": 30}),
    ]

    for shape, params in shapes_to_test:
        mask = processor.create_mask(shape, params)
        needs = processor.needs_mask(shape)

        # Save mask
        mask_path = test_dir / f"mask_{shape}.png"
        mask.save(str(mask_path))

        # Apply to test image if non-rectangular
        if needs:
            result = processor.apply_mask(test_image, mask)
            result_path = test_dir / f"result_{shape}.png"
            result.save(str(result_path))
            print(f"  {shape}: mask + result saved (needs_mask=True)")
        else:
            print(f"  {shape}: mask saved (needs_mask=False, no clipping needed)")

    print(f"\n  All test outputs in: {test_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
