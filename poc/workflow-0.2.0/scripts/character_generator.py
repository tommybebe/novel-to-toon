"""
Phase 1: Character Design Generator for Novel-to-Toon PoC v0.2.0

Generates character reference images using fal.ai FLUX Kontext models.
Two-step workflow: text-to-image base → Kontext editing for variations.
Special twin workflow for Dokma and Uiseon (shared face reference).
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

import fal_client
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
POC_DIR = BASE_DIR / "phase1_characters"

# Import cost tracker
sys.path.insert(0, str(Path(__file__).parent))
from cost_tracker import FalCostTracker


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


# Prompt templates
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

    "twin_base_face": """Korean webtoon style character portrait:
- Character: Middle-aged male with scholarly features
- Features: Sharp intelligent eyes, defined jaw, dignified bearing
- Expression: Neutral, composed
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Face focus, minimal background
- Quality: High detail, emphasis on facial features""",

    "variation_angry": """Change the expression and pose of this character:
- Expression: Angry, intense expression with furrowed brows
- Pose: 3/4 view, tense posture
- Background: Dramatic dark gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette""",

    "variation_smile": """Change the expression and pose of this character:
- Expression: Subtle smile, relaxed expression
- Pose: Side profile view
- Background: Warm gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette""",

    "variation_action": """Change the expression and pose of this character:
- Expression: Focused, battle-ready
- Pose: Dynamic action pose, martial arts stance
- Background: Action-oriented, motion effects

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette""",
}


def download_image(url: str, output_path: Path) -> int:
    """Download image from URL (fal.ai CDN URLs expire). Returns size in bytes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return len(response.content)


class CharacterGenerator:
    """Generate character reference images using fal.ai FLUX Kontext."""

    def __init__(self):
        self.cost_tracker = FalCostTracker(session_id="poc-v2-characters")
        self.results = []

    def _build_prompt(self, character: CharacterSpec, template_name: str) -> str:
        """Build a prompt from template and character spec."""
        template = PROMPT_TEMPLATES[template_name]
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
        )

    def generate_base_reference(self, char_key: str) -> dict:
        """Step 1: Generate base reference image (text-to-image, no input reference)."""
        character = CHARACTERS[char_key]
        output_dir = POC_DIR / char_key
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  Step 1: Generating base reference for {character.name}...")

        prompt = self._build_prompt(character, "base_reference")
        start_ms = time.time()

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/kontext/text-to-image",
                arguments={
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "num_images": 1,
                    "output_format": "png",
                    "guidance_scale": 3.5,
                    "num_inference_steps": 28,
                    "safety_tolerance": 5,
                }
            )

            gen_time_ms = int((time.time() - start_ms) * 1000)
            image_url = result["images"][0]["url"]
            output_path = output_dir / "base_reference.png"
            size_bytes = download_image(image_url, output_path)

            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id=f"{char_key}_base",
                generation_time_ms=gen_time_ms,
                width=1024, height=1024,
                phase="character_generation",
            )

            # Save metadata
            metadata = {
                "character": asdict(character),
                "step": "1_base_reference",
                "generation": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "fal-ai/flux-pro/kontext/text-to-image",
                    "prompt": prompt,
                    "generation_time_ms": gen_time_ms,
                    "size_bytes": size_bytes,
                }
            }
            with open(output_dir / "base_reference_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            print(f"    OK - {output_path.name} ({size_bytes} bytes, {gen_time_ms}ms)")
            return {"success": True, "path": str(output_path), "size_bytes": size_bytes}

        except Exception as e:
            gen_time_ms = int((time.time() - start_ms) * 1000)
            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id=f"{char_key}_base",
                generation_time_ms=gen_time_ms,
                width=1024, height=1024,
                phase="character_generation",
                status="failed",
                error_message=str(e),
            )
            print(f"    FAIL - {e}")
            return {"success": False, "error": str(e)}

    def generate_reference_variations(self, char_key: str) -> list[dict]:
        """Step 2: Generate variations using base reference via Kontext editing."""
        character = CHARACTERS[char_key]
        output_dir = POC_DIR / char_key

        base_ref_path = output_dir / "base_reference.png"
        if not base_ref_path.exists():
            print(f"  ERROR: Base reference not found at {base_ref_path}")
            return []

        print(f"\n  Step 2: Generating variations for {character.name}...")

        # Upload base reference once
        base_ref_url = fal_client.upload_file(str(base_ref_path))

        variations = [
            ("angry", "variation_angry"),
            ("smile", "variation_smile"),
            ("action", "variation_action"),
        ]

        results = []
        for var_name, template in variations:
            prompt = self._build_prompt(character, template)
            output_path = output_dir / f"variation_{var_name}.png"
            start_ms = time.time()

            try:
                result = fal_client.subscribe(
                    "fal-ai/flux-pro/kontext",
                    arguments={
                        "prompt": prompt,
                        "image_url": base_ref_url,
                        "num_images": 1,
                        "output_format": "png",
                        "guidance_scale": 3.5,
                        "num_inference_steps": 28,
                        "safety_tolerance": 5,
                    }
                )

                gen_time_ms = int((time.time() - start_ms) * 1000)
                image_url = result["images"][0]["url"]
                size_bytes = download_image(image_url, output_path)

                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"{char_key}_{var_name}",
                    generation_time_ms=gen_time_ms,
                    width=1024, height=1024,
                    phase="character_generation",
                )

                print(f"    OK - variation_{var_name}.png ({size_bytes} bytes, {gen_time_ms}ms)")
                results.append({"success": True, "variation": var_name, "path": str(output_path)})

            except Exception as e:
                gen_time_ms = int((time.time() - start_ms) * 1000)
                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"{char_key}_{var_name}",
                    generation_time_ms=gen_time_ms,
                    width=1024, height=1024,
                    phase="character_generation",
                    status="failed",
                    error_message=str(e),
                )
                print(f"    FAIL - variation_{var_name}: {e}")
                results.append({"success": False, "variation": var_name, "error": str(e)})

        # Save variations metadata
        metadata = {
            "character": char_key,
            "step": "2_reference_variations",
            "base_reference_used": str(base_ref_path),
            "timestamp": datetime.now().isoformat(),
            "variations": results,
            "success_rate": sum(1 for r in results if r["success"]) / len(results) * 100 if results else 0,
        }
        with open(output_dir / "variations_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return results

    def generate_twin_characters(self) -> dict:
        """
        Twin workflow: Generate shared face base → Kontext edit for Dokma and Uiseon.
        Both twins share the same face but differ in attire and atmosphere.
        """
        print("\n  Twin Character Workflow: Dokma and Uiseon")
        twins_dir = POC_DIR / "twins"
        twins_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate shared base face
        print("    Step 1: Generating shared twin base face...")
        start_ms = time.time()

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/kontext/text-to-image",
                arguments={
                    "prompt": PROMPT_TEMPLATES["twin_base_face"],
                    "aspect_ratio": "1:1",
                    "num_images": 1,
                    "output_format": "png",
                    "safety_tolerance": 5,
                }
            )

            gen_time_ms = int((time.time() - start_ms) * 1000)
            image_url = result["images"][0]["url"]
            base_path = twins_dir / "twin_base_face.png"
            download_image(image_url, base_path)

            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id="twin_base_face",
                generation_time_ms=gen_time_ms,
                width=1024, height=1024,
                phase="character_generation",
            )
            print(f"      OK - twin_base_face.png ({gen_time_ms}ms)")

        except Exception as e:
            gen_time_ms = int((time.time() - start_ms) * 1000)
            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id="twin_base_face",
                generation_time_ms=gen_time_ms,
                width=1024, height=1024,
                phase="character_generation",
                status="failed",
                error_message=str(e),
            )
            print(f"      FAIL - {e}")
            return {"success": False, "error": str(e)}

        # Upload shared face
        twin_base_url = fal_client.upload_file(str(base_path))

        # Step 2: Generate Dokma from shared face
        twin_results = {}
        for twin_key, twin_prompt in [
            ("dokma", """Transform this character into a full portrait:
- Character: Dokma, Poison Master
- Expression: Cynical smirk, sinister knowing eyes
- Attire: Black traditional robes, flowing dark fabric
- Atmosphere: Dark, poisonous, mysterious
- Complexion: Slightly darker, weathered

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN)
- Art style and line weight"""),
            ("uiseon", """Transform this character into a full portrait:
- Character: Uiseon, Medicine Sage
- Expression: Warm, wise gentle smile
- Attire: White traditional robes, pristine and elegant
- Atmosphere: Clean, healing, serene
- Complexion: Fair, scholarly

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN - must match Dokma)
- Art style and line weight"""),
        ]:
            print(f"    Step 2: Generating {twin_key} from shared face...")
            start_ms = time.time()

            try:
                result = fal_client.subscribe(
                    "fal-ai/flux-pro/kontext",
                    arguments={
                        "prompt": twin_prompt,
                        "image_url": twin_base_url,
                        "output_format": "png",
                        "safety_tolerance": 5,
                    }
                )

                gen_time_ms = int((time.time() - start_ms) * 1000)
                image_url = result["images"][0]["url"]
                output_path = twins_dir / f"{twin_key}_from_twin_face.png"
                download_image(image_url, output_path)

                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"twin_{twin_key}",
                    generation_time_ms=gen_time_ms,
                    width=1024, height=1024,
                    phase="character_generation",
                )
                print(f"      OK - {output_path.name} ({gen_time_ms}ms)")
                twin_results[twin_key] = {"success": True, "path": str(output_path)}

            except Exception as e:
                gen_time_ms = int((time.time() - start_ms) * 1000)
                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"twin_{twin_key}",
                    generation_time_ms=gen_time_ms,
                    width=1024, height=1024,
                    phase="character_generation",
                    status="failed",
                    error_message=str(e),
                )
                print(f"      FAIL - {twin_key}: {e}")
                twin_results[twin_key] = {"success": False, "error": str(e)}

        # Save twin metadata
        metadata = {
            "test": "twin_character_differentiation",
            "timestamp": datetime.now().isoformat(),
            "method": "shared_face_reference_kontext_editing",
            "base_face": str(base_path),
            "results": twin_results,
        }
        with open(twins_dir / "twin_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return twin_results


def main():
    """Main execution function for Phase 1."""
    # Support --test flag for single character test
    test_mode = "--test" in sys.argv

    print("=" * 70)
    print("Phase 1: Character Design with fal.ai FLUX Kontext")
    if test_mode:
        print("*** TEST MODE - Jin Sohan base reference only ***")
    print("=" * 70)

    generator = CharacterGenerator()

    all_results = {
        "phase": "Phase 1: Character Design",
        "workflow": "fal_ai_kontext_reference_based",
        "timestamp": datetime.now().isoformat(),
        "characters": {},
    }

    if test_mode:
        # Test mode: only generate Jin Sohan base
        char_key = "jin_sohan"
        print(f"\n{'='*70}")
        print(f"Processing (test): {CHARACTERS[char_key].name}")
        print("=" * 70)
        base_result = generator.generate_base_reference(char_key)
        all_results["characters"][char_key] = {"base_reference": base_result}
    else:
        # Full mode: all characters + variations + twins
        for char_key in ["jin_sohan", "dokma", "uiseon"]:
            print(f"\n{'='*70}")
            print(f"Processing: {CHARACTERS[char_key].name}")
            print("=" * 70)

            base_result = generator.generate_base_reference(char_key)
            if not base_result.get("success"):
                all_results["characters"][char_key] = {
                    "base_reference": base_result,
                    "variations": [],
                    "success": False,
                }
                continue

            variations = generator.generate_reference_variations(char_key)
            all_results["characters"][char_key] = {
                "base_reference": base_result,
                "variations": variations,
                "base_success": True,
                "variations_success_count": sum(1 for r in variations if r["success"]),
                "total_variations": len(variations),
            }

        # Twin workflow
        print(f"\n{'='*70}")
        print("Twin Character Workflow")
        print("=" * 70)
        twin_results = generator.generate_twin_characters()
        all_results["twin_differentiation"] = twin_results

    # Save results
    POC_DIR.mkdir(parents=True, exist_ok=True)
    results_path = POC_DIR / "phase1_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Cost summary
    generator.cost_tracker.print_summary()
    report_dir = BASE_DIR / "reports"
    generator.cost_tracker.export(str(report_dir / "phase1_cost_report.json"))

    # Print summary
    print("\n" + "=" * 70)
    print("Phase 1 Complete - Summary")
    print("=" * 70)

    total_images = 0
    successful = 0

    for char_key, char_data in all_results.get("characters", {}).items():
        char_name = CHARACTERS[char_key].name
        base_ok = char_data.get("base_reference", {}).get("success", False)
        var_ok = char_data.get("variations_success_count", 0)
        total_var = char_data.get("total_variations", 0)

        print(f"\n  {char_name}:")
        print(f"    Base Reference: {'PASS' if base_ok else 'FAIL'}")
        if total_var > 0:
            print(f"    Variations: {var_ok}/{total_var}")

        total_images += 1 + total_var
        successful += (1 if base_ok else 0) + var_ok

    if "twin_differentiation" in all_results:
        twin_data = all_results["twin_differentiation"]
        for twin_key, twin_res in twin_data.items():
            if isinstance(twin_res, dict) and "success" in twin_res:
                ok = twin_res["success"]
                print(f"\n  Twin {twin_key}: {'PASS' if ok else 'FAIL'}")
                total_images += 1
                successful += 1 if ok else 0

    if total_images > 0:
        print(f"\n  Total: {successful}/{total_images} images generated successfully")
        print(f"  Success Rate: {successful/total_images*100:.1f}%")

    print(f"\n  Results: {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
