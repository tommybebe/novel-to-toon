"""
Phase 1: Character Design Generator for Novel-to-Toon PoC

This script generates character reference images using Google Gemini API
for the "Disciple of the Villain" novel characters.
"""

import os
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
POC_DIR = BASE_DIR / "phase1_characters"


@dataclass
class CharacterSpec:
    """Character specification for image generation."""
    name: str
    korean_name: str
    age: str
    role: str
    visual_features: list[str]
    clothing: str
    atmosphere: str
    color_palette: list[str]


# Character definitions based on novel analysis
CHARACTERS = {
    "jin_sohan": CharacterSpec(
        name="Jin Sohan",
        korean_name="진소한 (眞昭悍)",
        age="26 years old",
        role="Main protagonist, former member of Sword Dance Troupe",
        visual_features=[
            "Cloudy, murky eye color (from poison exposure)",
            "Sharp, handsome features",
            "Athletic martial artist build",
            "Calm but intense gaze",
            "Subtle signs of poison resistance in skin tone"
        ],
        clothing="Dark traditional martial arts robes (dark gray/navy), practical design for combat",
        atmosphere="Determined, mysterious, hidden strength",
        color_palette=["#2d2d44", "#4a4a6a", "#6b6b8a", "#8b8ba3"]
    ),
    "dokma": CharacterSpec(
        name="Dokma (Poison Demon)",
        korean_name="독마 (毒魔)",
        age="Middle-aged (appears 50s)",
        role="One of the twin masters, Poison Master",
        visual_features=[
            "Dark complexion",
            "Identical twin face with Uiseon",
            "Sinister, knowing eyes",
            "Cynical smirk",
            "Weathered appearance from poison work"
        ],
        clothing="Black traditional robes (흑의), flowing dark fabric",
        atmosphere="Dark, poisonous, mysterious, cynical",
        color_palette=["#0d0d0d", "#1a1a1a", "#333333", "#4a4a4a"]
    ),
    "uiseon": CharacterSpec(
        name="Uiseon (Medicine Sage)",
        korean_name="의선 (醫仙)",
        age="Middle-aged (appears 50s)",
        role="One of the twin masters, Medicine Sage",
        visual_features=[
            "Fair, scholarly complexion",
            "Identical twin face with Dokma",
            "Gentle, wise eyes",
            "Warm, knowing smile",
            "Clean, refined appearance"
        ],
        clothing="White traditional robes (백의), pristine and elegant",
        atmosphere="Clean, healing, serene, scholarly",
        color_palette=["#f5f5f5", "#e0e0e0", "#cccccc", "#b8b8b8"]
    )
}


# Prompt templates for different generation types
PROMPT_TEMPLATES = {
    "base_reference": """Korean webtoon style character portrait:
- Character: {name} ({korean_name}), {age}, {role}
- Key Features: {features}
- Expression: Neutral, calm expression
- Pose: Front view, straight posture
- Attire: {clothing}
- Atmosphere: {atmosphere}
- Style: Korean webtoon (manhwa), clean detailed linework, cel-shaded with gradient accents
- Composition: Upper body portrait, centered
- Background: Simple neutral gradient
- Quality: High detail, publication ready, no text

IMPORTANT STYLE ELEMENTS TO ESTABLISH:
- Line weight: Medium with varied thickness for emphasis
- Shading: Cel-shaded with soft gradients
- Color palette: {color_info}""",

    "variation_neutral": """Generate the SAME character from the reference image with the following changes:
- Expression: Neutral, calm expression
- Pose: Front view, straight posture
- Background: Simple neutral gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette""",

    "variation_angry": """Generate the SAME character from the reference image with the following changes:
- Expression: Angry, intense expression with furrowed brows
- Pose: 3/4 view, tense posture
- Background: Dramatic dark gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette""",

    "variation_smile": """Generate the SAME character from the reference image with the following changes:
- Expression: Subtle smile, relaxed expression
- Pose: Side profile view
- Background: Warm gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette""",

    "variation_action": """Generate the SAME character from the reference image with the following changes:
- Expression: Focused, battle-ready
- Pose: Dynamic action pose, martial arts stance
- Background: Action-oriented, motion effects

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette"""
}


class CharacterGenerator:
    """Generate character reference images using Google Gemini API."""

    # Available models for image generation:
    # - gemini-2.5-flash-image: Fast, efficient image generation
    # - gemini-3-pro-image-preview: Higher quality, preview model (used for PoC)

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-pro-image-preview"  # Using Gemini 3 Pro for PoC
        self.results = []

    def _build_prompt(self, character: CharacterSpec, template_name: str, **kwargs) -> str:
        """Build a prompt from template and character spec."""
        template = PROMPT_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")

        features_str = ", ".join(character.visual_features)
        color_palette_str = ", ".join(character.color_palette)

        return template.format(
            name=character.name,
            korean_name=character.korean_name,
            age=character.age,
            role=character.role,
            features=features_str,
            clothing=character.clothing,
            atmosphere=character.atmosphere,
            color_info=color_palette_str,
            **kwargs
        )

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "1:1",
        reference_image_path: Optional[Path] = None
    ) -> dict:
        """Generate a single image using Gemini API with optional reference image."""
        print(f"  Generating image: {output_path.name}")

        try:
            # Build contents list: reference image (if provided) first, then text prompt
            contents = []

            if reference_image_path and reference_image_path.exists():
                ref_image = Image.open(reference_image_path)
                contents.append(ref_image)
                print(f"    Using reference image: {reference_image_path.name}")

            contents.append(prompt)

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                )
            )

            # Extract and save image
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data"):
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(part.inline_data.data)

                        return {
                            "success": True,
                            "path": str(output_path),
                            "size_bytes": len(part.inline_data.data),
                            "prompt": prompt[:200] + "...",
                            "used_reference": reference_image_path is not None,
                        }

            return {
                "success": False,
                "error": "No image data in response",
                "prompt": prompt[:200] + "...",
                "used_reference": reference_image_path is not None,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt[:200] + "...",
                "used_reference": reference_image_path is not None,
            }

    def generate_base_reference(self, char_key: str) -> dict:
        """
        Step 1: Generate base reference image for a character (no input reference).
        This establishes the character's visual identity.
        """
        if char_key not in CHARACTERS:
            raise ValueError(f"Unknown character: {char_key}")

        character = CHARACTERS[char_key]
        output_dir = POC_DIR / char_key
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nStep 1: Generating base reference for {character.name}...")

        # Build prompt for base generation
        prompt = self._build_prompt(character, "base_reference")

        # Generate image WITHOUT reference (Step 1)
        output_path = output_dir / "base_reference.png"
        result = self.generate_image(prompt, output_path)

        # Save metadata
        metadata = {
            "character": asdict(character),
            "step": "1_base_reference",
            "generation": {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "prompt": prompt,
                "result": result,
            }
        }

        metadata_path = output_dir / "base_reference_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return result

    def generate_reference_variations(self, char_key: str) -> list[dict]:
        """
        Step 2: Generate variations of a character using base reference image.
        Uses reference image as input to maintain consistency.
        """
        if char_key not in CHARACTERS:
            raise ValueError(f"Unknown character: {char_key}")

        character = CHARACTERS[char_key]
        output_dir = POC_DIR / char_key
        output_dir.mkdir(parents=True, exist_ok=True)

        # Check if base reference exists
        base_ref_path = output_dir / "base_reference.png"
        if not base_ref_path.exists():
            print(f"  ERROR: Base reference not found at {base_ref_path}")
            return []

        print(f"\nStep 2: Generating variations for {character.name} using reference image...")

        variations = [
            ("neutral", "variation_neutral", "1:1"),
            ("angry", "variation_angry", "1:1"),
            ("smile", "variation_smile", "1:1"),
            ("action", "variation_action", "9:16"),
        ]

        results = []
        for var_name, template, ratio in variations:
            prompt = self._build_prompt(character, template)
            output_path = output_dir / f"variation_{var_name}.png"

            # Generate WITH reference image (Step 2)
            result = self.generate_image(
                prompt,
                output_path,
                aspect_ratio=ratio,
                reference_image_path=base_ref_path
            )
            result["variation"] = var_name
            results.append(result)

        # Save variations metadata
        variations_metadata = {
            "character": char_key,
            "step": "2_reference_variations",
            "base_reference_used": str(base_ref_path),
            "timestamp": datetime.now().isoformat(),
            "variations": results,
            "success_rate": sum(1 for r in results if r["success"]) / len(results) * 100 if results else 0,
        }

        variations_file = output_dir / "variations_metadata.json"
        with open(variations_file, "w", encoding="utf-8") as f:
            json.dump(variations_metadata, f, indent=2, ensure_ascii=False)

        return results

    def generate_twin_comparison(self) -> dict:
        """
        Test 1.3.3: Generate twin comparison using shared face reference.
        Both Dokma and Uiseon should have identical faces but different atmospheres.
        """
        print("\nTest 1.3.3: Generating twin comparison using shared face reference...")

        dokma = CHARACTERS["dokma"]
        uiseon = CHARACTERS["uiseon"]

        # For twins, we use ONE shared base face reference
        dokma_dir = POC_DIR / "dokma"
        base_ref_path = dokma_dir / "base_reference.png"

        if not base_ref_path.exists():
            print("  ERROR: Dokma base reference not found for twin comparison")
            return {"success": False, "error": "Missing base reference"}

        # Generate Dokma as the base (already done in Step 2)
        # Now generate Uiseon using Dokma's face as reference

        prompt = f"""Generate the SAME face from the reference image as a full character:
- Character: {uiseon.name} ({uiseon.korean_name})
- Expression: Warm, wise gentle smile
- Attire: {uiseon.clothing}
- Atmosphere: Clean, healing, serene, scholarly
- Complexion: Fair, scholarly

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN - must match exactly)
- Art style and line weight

Important: This is Dokma's identical twin brother, so the face must be EXACTLY the same."""

        output_path = POC_DIR / "twin_comparison" / "uiseon_from_dokma_face.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = self.generate_image(
            prompt,
            output_path,
            aspect_ratio="1:1",
            reference_image_path=base_ref_path
        )

        # Also create a side-by-side comparison description
        comparison_metadata = {
            "test": "1.3.3_twin_character_differentiation",
            "timestamp": datetime.now().isoformat(),
            "method": "single_face_reference_two_characters",
            "base_reference": "dokma/base_reference.png",
            "dokma_already_generated": True,
            "uiseon_from_reference": result,
            "success": result.get("success", False),
            "notes": "Both twins should have identical faces but different clothing and atmosphere"
        }

        comparison_file = POC_DIR / "twin_comparison" / "comparison_metadata.json"
        with open(comparison_file, "w", encoding="utf-8") as f:
            json.dump(comparison_metadata, f, indent=2, ensure_ascii=False)

        return result


def main():
    """Main execution function for Phase 1 with reference-based workflow."""
    print("=" * 70)
    print("Phase 1: Character Design with Google Gemini API")
    print("Reference Image-Based Consistency Workflow")
    print("=" * 70)

    generator = CharacterGenerator()

    # Track all results
    all_results = {
        "phase": "Phase 1: Character Design",
        "workflow": "reference_image_based_consistency",
        "timestamp": datetime.now().isoformat(),
        "characters": {},
        "test_cases": {
            "test_1_3_1": "Base Character Generation (Step 1)",
            "test_1_3_2": "Reference-Based Variation Generation (Step 2)",
            "test_1_3_3": "Twin Character Differentiation"
        }
    }

    # STEP 1 & 2: Generate base references and variations for all primary characters
    for char_key in ["jin_sohan", "dokma", "uiseon"]:
        print(f"\n{'='*70}")
        print(f"Processing: {CHARACTERS[char_key].name}")
        print("=" * 70)

        # Step 1: Generate base reference image
        base_result = generator.generate_base_reference(char_key)

        if not base_result.get("success", False):
            print(f"  ERROR: Base reference generation failed for {char_key}")
            all_results["characters"][char_key] = {
                "base_reference": base_result,
                "variations": [],
                "success": False,
            }
            continue

        # Step 2: Generate variations using base reference as input
        variations_results = generator.generate_reference_variations(char_key)

        char_results = {
            "base_reference": base_result,
            "variations": variations_results,
            "base_success": base_result.get("success", False),
            "variations_success_count": sum(1 for r in variations_results if r.get("success", False)),
            "total_variations": len(variations_results),
        }

        all_results["characters"][char_key] = char_results

    # STEP 3: Twin character differentiation (Test 1.3.3)
    print(f"\n{'='*70}")
    print("Twin Character Test: Dokma and Uiseon")
    print("=" * 70)
    twin_result = generator.generate_twin_comparison()
    all_results["test_1_3_3_twin_differentiation"] = twin_result

    # Save overall results
    results_path = POC_DIR / "phase1_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 70)
    print("Phase 1 Complete - Summary")
    print("=" * 70)

    total_images = 0
    successful = 0

    for char_key, char_results in all_results["characters"].items():
        char_name = CHARACTERS[char_key].name
        base_success = char_results.get("base_success", False)
        var_success = char_results.get("variations_success_count", 0)
        total_var = char_results.get("total_variations", 0)

        print(f"\n{char_name}:")
        print(f"  Test 1.3.1 - Base Reference: {'✓ PASS' if base_success else '✗ FAIL'}")
        print(f"  Test 1.3.2 - Reference Variations: {var_success}/{total_var} passed")

        total_images += 1 + total_var  # 1 base + N variations
        successful += (1 if base_success else 0) + var_success

    twin_success = twin_result.get("success", False)
    print(f"\nTest 1.3.3 - Twin Differentiation: {'✓ PASS' if twin_success else '✗ FAIL'}")
    total_images += 1
    successful += 1 if twin_success else 0

    print(f"\n{'='*70}")
    print(f"Total: {successful}/{total_images} images generated successfully")
    print(f"Success Rate: {successful/total_images*100:.1f}%")
    print(f"Results saved to: {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
