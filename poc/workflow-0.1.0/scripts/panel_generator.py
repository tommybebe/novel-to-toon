"""
Phase 5: Panel Image Generator for Novel-to-Toon PoC

This script generates final webtoon panel images by combining:
- Character references from Phase 1
- Style specifications from Phase 2
- Background references from Phase 3
- Panel specifications from Phase 4

Uses Google Gemini API for image generation with reference-based consistency.
"""

import os
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
POC_DIR = BASE_DIR
PHASE1_DIR = POC_DIR / "phase1_characters"
PHASE2_DIR = POC_DIR / "phase2_style"
PHASE3_DIR = POC_DIR / "phase3_backgrounds"
PHASE4_DIR = POC_DIR / "phase4_storyboard"
PHASE5_DIR = POC_DIR / "phase5_generation"


@dataclass
class GenerationJob:
    """Tracks a single panel generation job."""
    panel_id: str
    panel_spec: dict
    status: str = "pending"  # pending, processing, completed, failed
    output_path: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    generation_time_ms: int = 0
    quality_validation: Optional[dict] = None


@dataclass
class CostTracker:
    """Tracks API usage and estimated costs."""
    api_calls: List[dict] = field(default_factory=list)

    def log_call(self, model: str, panel_id: str, success: bool):
        self.api_calls.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "panel_id": panel_id,
            "success": success
        })

    def get_summary(self) -> dict:
        # Estimated cost per image for gemini-3-pro-image-preview: ~$0.15 avg
        cost_per_image = 0.15
        successful_calls = sum(1 for c in self.api_calls if c["success"])

        return {
            "total_calls": len(self.api_calls),
            "successful_calls": successful_calls,
            "failed_calls": len(self.api_calls) - successful_calls,
            "estimated_cost_usd": successful_calls * cost_per_image,
            "calls": self.api_calls
        }


class QualityChecker:
    """Validates generated panel quality."""

    def __init__(self, style_spec: dict):
        self.style_spec = style_spec

    def validate_panel(self, image_path: str, panel_spec: dict) -> dict:
        """Run quality checks on a generated panel."""
        try:
            image = Image.open(image_path)
            width, height = image.size

            checks = {
                "resolution": self._check_resolution(width, height),
                "aspect_ratio": self._check_aspect_ratio(width, height, panel_spec),
                "file_valid": {"passed": True, "details": "Image file is valid"}
            }

            passed = all(c["passed"] for c in checks.values())

            return {
                "passed": passed,
                "checks": checks,
                "dimensions": f"{width}x{height}",
                "file_size_bytes": os.path.getsize(image_path)
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "checks": {}
            }

    def _check_resolution(self, width: int, height: int) -> dict:
        """Verify minimum resolution requirements."""
        min_dimension = 1024
        passed = min(width, height) >= min_dimension

        return {
            "passed": passed,
            "actual": f"{width}x{height}",
            "minimum": f"{min_dimension}px on shortest side"
        }

    def _check_aspect_ratio(self, width: int, height: int, panel_spec: dict) -> dict:
        """Verify aspect ratio matches specification."""
        actual_ratio = width / height
        target = panel_spec.get("aspect_ratio", "16:9")

        try:
            w, h = map(int, target.split(":"))
            target_ratio = w / h
        except ValueError:
            return {"passed": True, "note": "Could not parse target aspect ratio"}

        tolerance = 0.1
        passed = abs(actual_ratio - target_ratio) < tolerance

        return {
            "passed": passed,
            "target": target,
            "actual_ratio": f"{actual_ratio:.2f}",
            "target_ratio": f"{target_ratio:.2f}"
        }


class PanelGenerator:
    """Generate webtoon panel images using Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-pro-image-preview"

        # Load assets from previous phases
        self.style_spec = self._load_json(PHASE2_DIR / "style_spec.json")
        self.prompt_templates = self._load_json(PHASE2_DIR / "prompt_templates.json")
        self.lighting_presets = self._load_json(PHASE3_DIR / "lighting_presets.json")

        # Initialize helpers
        self.quality_checker = QualityChecker(self.style_spec)
        self.cost_tracker = CostTracker()

        # Track results
        self.results = []

    def _load_json(self, path: Path) -> dict:
        """Load JSON file."""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_json(self, data: dict, path: Path):
        """Save data to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_character_reference_path(self, char_name: str) -> Optional[Path]:
        """Get the base reference image path for a character."""
        # Normalize character name to directory format
        name_map = {
            "Jin Sohan": "jin_sohan",
            "jin_sohan": "jin_sohan",
            "Dokma": "dokma",
            "dokma": "dokma",
            "Uiseon": "uiseon",
            "uiseon": "uiseon",
        }

        char_key = name_map.get(char_name)
        if not char_key:
            return None

        ref_path = PHASE1_DIR / char_key / "base_reference.png"
        return ref_path if ref_path.exists() else None

    def _get_background_reference_path(self, location: str) -> Optional[Path]:
        """Get background reference image for a location."""
        location_lower = location.lower()

        # Map common location descriptions to file paths
        location_map = {
            "magic tower": PHASE3_DIR / "locations" / "magic_tower" / "base_reference.png",
            "magic tower exterior": PHASE3_DIR / "locations" / "magic_tower" / "base_reference.png",
            "magic tower interior": PHASE3_DIR / "locations" / "magic_tower" / "interior_hall.png",
            "magic tower interior hall": PHASE3_DIR / "locations" / "magic_tower" / "interior_hall.png",
            "magic tower quarters": PHASE3_DIR / "locations" / "magic_tower" / "interior_quarters.png",
            "inn": PHASE3_DIR / "locations" / "inn" / "base_reference.png",
            "black path": PHASE3_DIR / "locations" / "black_path" / "base_reference.png",
            "sword dance troupe": PHASE3_DIR / "locations" / "sword_dance_troupe" / "base_reference.png",
        }

        for key, path in location_map.items():
            if key in location_lower:
                if path.exists():
                    return path

        return None

    def _build_panel_prompt(self, panel_spec: dict) -> str:
        """Build a complete prompt for panel generation."""
        # Extract key info from panel spec
        panel_type = panel_spec.get("panel_type", "dialogue")
        scene_desc = panel_spec.get("scene_description", "")
        narrative = panel_spec.get("narrative_moment", "")
        characters = panel_spec.get("characters", [])
        mood = panel_spec.get("mood", "")
        lighting_preset = panel_spec.get("lighting_preset", "indoor_lamp")
        aspect_ratio = panel_spec.get("aspect_ratio", "16:9")
        shot_type = panel_spec.get("shot_type", "medium shot")
        camera_angle = panel_spec.get("camera_angle", "eye level")
        dialogue_space = panel_spec.get("dialogue_space", "none")
        special_effects = panel_spec.get("special_effects", [])
        location = panel_spec.get("location", "")

        # Get lighting details
        lighting = self.lighting_presets.get(lighting_preset, {})
        lighting_desc = lighting.get("description", "")
        color_temp = lighting.get("color_temperature", "")

        # Build character descriptions
        char_descriptions = []
        for char in characters:
            if isinstance(char, dict):
                name = char.get("name", "")
                position = char.get("position", "")
                expression = char.get("expression", "")
                pose = char.get("pose", "")
                char_descriptions.append(
                    f"- {name}: {expression}, {pose} (position: {position})"
                )

        char_block = "\n".join(char_descriptions) if char_descriptions else "No characters in this panel"

        # Get style keywords
        prompt_keywords = self.style_spec.get("prompt_keywords", {})
        style_keywords = ", ".join(prompt_keywords.get("style", ["Korean webtoon", "manhwa"]))
        quality_keywords = ", ".join(prompt_keywords.get("quality", ["high detail", "publication ready"]))

        # Build effects list
        effects_str = ", ".join(special_effects) if special_effects else "none"

        # Compose the prompt
        prompt = f"""Korean webtoon panel illustration:

[SCENE CONTEXT]
- Panel type: {panel_type}
- Scene: {scene_desc}
- Narrative moment: {narrative}
- Location: {location}

[CHARACTERS]
{char_block}

[COMPOSITION]
- Shot type: {shot_type}
- Camera angle: {camera_angle}
- Dialogue space: {dialogue_space}

[STYLE REQUIREMENTS]
- Art style: {style_keywords}
- Genre: Wuxia/martial arts, dark mature tone
- Line work: Clean with varied weight, cel-shaded with gradient accents
- Mood: {mood}

[LIGHTING]
- Preset: {lighting_preset}
- Description: {lighting_desc}
- Color temperature: {color_temp}

[SPECIAL EFFECTS]
{effects_str}

[TECHNICAL SPECS]
- Aspect ratio: {aspect_ratio}
- Quality: {quality_keywords}
- No text, no speech bubbles (will be added separately)
- No watermarks or signatures

IMPORTANT: Maintain Korean webtoon (manhwa) visual style throughout. Characters should match their reference images exactly."""

        return prompt

    def generate_panel(
        self,
        panel_spec: dict,
        output_path: Path,
        use_character_refs: bool = True,
        use_background_ref: bool = False
    ) -> dict:
        """Generate a single panel image."""
        panel_id = panel_spec.get("id", "unknown")
        print(f"  Generating panel: {panel_id}")

        start_time = datetime.now()

        try:
            # Build contents list: reference images first, then prompt
            contents = []

            # Add character reference images for consistency
            if use_character_refs:
                characters = panel_spec.get("characters", [])
                added_refs = set()

                for char in characters:
                    if isinstance(char, dict):
                        char_name = char.get("name", "")
                        # Skip if already added or partial character
                        if char_name in added_refs or "partial" in char.get("position", "").lower():
                            continue

                        ref_path = self._get_character_reference_path(char_name)
                        if ref_path and ref_path.exists():
                            try:
                                ref_image = Image.open(ref_path)
                                contents.append(ref_image)
                                added_refs.add(char_name)
                                print(f"    + Character ref: {char_name}")
                            except Exception as e:
                                print(f"    ! Failed to load ref for {char_name}: {e}")

            # Optionally add background reference
            if use_background_ref:
                location = panel_spec.get("location", "")
                bg_ref_path = self._get_background_reference_path(location)
                if bg_ref_path and bg_ref_path.exists():
                    try:
                        bg_image = Image.open(bg_ref_path)
                        contents.append(bg_image)
                        print(f"    + Background ref: {location}")
                    except Exception as e:
                        print(f"    ! Failed to load background ref: {e}")

            # Build and add the prompt
            prompt = self._build_panel_prompt(panel_spec)
            contents.append(prompt)

            # Determine aspect ratio
            aspect_ratio = panel_spec.get("aspect_ratio", "16:9")

            # Generate image with 2K resolution for quality
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size="2K",
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

                        end_time = datetime.now()
                        generation_time = int((end_time - start_time).total_seconds() * 1000)

                        # Log successful call
                        self.cost_tracker.log_call(self.model, panel_id, True)

                        return {
                            "success": True,
                            "panel_id": panel_id,
                            "path": str(output_path),
                            "size_bytes": len(part.inline_data.data),
                            "generation_time_ms": generation_time,
                            "character_refs_used": use_character_refs,
                            "background_ref_used": use_background_ref,
                            "aspect_ratio": aspect_ratio,
                        }

            # No image in response
            self.cost_tracker.log_call(self.model, panel_id, False)
            return {
                "success": False,
                "panel_id": panel_id,
                "error": "No image data in response"
            }

        except Exception as e:
            self.cost_tracker.log_call(self.model, panel_id, False)
            return {
                "success": False,
                "panel_id": panel_id,
                "error": str(e)
            }

    def generate_scene(self, scene_id: str, use_character_refs: bool = True) -> dict:
        """Generate all panels for a scene."""
        scene_dir = PHASE4_DIR / scene_id
        if not scene_dir.exists():
            return {"success": False, "error": f"Scene directory not found: {scene_dir}"}

        # Load scene manifest
        manifest_path = scene_dir / "scene_manifest.json"
        if not manifest_path.exists():
            return {"success": False, "error": f"Scene manifest not found: {manifest_path}"}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        panel_ids = manifest.get("panel_ids", [])
        print(f"\nGenerating scene: {scene_id} ({len(panel_ids)} panels)")

        # Create output directory
        output_dir = PHASE5_DIR / scene_id / "panels"
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata_dir = PHASE5_DIR / scene_id / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for panel_id in panel_ids:
            # Load panel spec
            spec_path = scene_dir / f"{panel_id}_spec.json"
            if not spec_path.exists():
                print(f"  ! Panel spec not found: {spec_path}")
                continue

            with open(spec_path, "r", encoding="utf-8") as f:
                panel_spec = json.load(f)

            # Generate panel
            output_path = output_dir / f"{panel_id}.png"
            result = self.generate_panel(
                panel_spec,
                output_path,
                use_character_refs=use_character_refs
            )

            # Validate quality if generation succeeded
            if result.get("success"):
                quality_result = self.quality_checker.validate_panel(
                    str(output_path),
                    panel_spec
                )
                result["quality_validation"] = quality_result

                if quality_result.get("passed"):
                    print(f"    PASS - Quality validation passed")
                else:
                    print(f"    WARN - Quality validation issues: {quality_result}")

            # Save panel metadata
            panel_metadata = {
                "panel_id": panel_id,
                "scene_id": scene_id,
                "generation": {
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model,
                    "result": result
                },
                "specifications": panel_spec,
                "quality_validation": result.get("quality_validation"),
                "file_info": {
                    "path": str(output_path),
                    "size_bytes": result.get("size_bytes"),
                    "dimensions": result.get("quality_validation", {}).get("dimensions")
                }
            }

            metadata_path = metadata_dir / f"{panel_id}_metadata.json"
            self._save_json(panel_metadata, metadata_path)

            results.append(result)

        # Calculate success rate
        successful = sum(1 for r in results if r.get("success"))
        quality_passed = sum(
            1 for r in results
            if r.get("success") and r.get("quality_validation", {}).get("passed")
        )

        scene_result = {
            "scene_id": scene_id,
            "total_panels": len(panel_ids),
            "generated": successful,
            "quality_passed": quality_passed,
            "success_rate": (successful / len(panel_ids) * 100) if panel_ids else 0,
            "quality_rate": (quality_passed / len(panel_ids) * 100) if panel_ids else 0,
            "panels": results
        }

        # Save scene manifest
        scene_manifest = {
            "scene_id": scene_id,
            "generated_at": datetime.now().isoformat(),
            "results": scene_result
        }
        manifest_output = PHASE5_DIR / scene_id / "scene_manifest.json"
        self._save_json(scene_manifest, manifest_output)

        return scene_result

    def generate_all_scenes(self) -> dict:
        """Generate panels for all scenes in Phase 4."""
        print("=" * 70)
        print("Phase 5: Panel Image Generation")
        print("=" * 70)

        all_results = {
            "phase": "Phase 5: Panel Image Generation",
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "scenes": {}
        }

        # Find all scene directories
        scene_dirs = [
            "scene_01_request",
            "scene_02_storytelling",
            "scene_03_departure"
        ]

        for scene_id in scene_dirs:
            scene_path = PHASE4_DIR / scene_id
            if scene_path.exists():
                result = self.generate_scene(scene_id)
                all_results["scenes"][scene_id] = result
            else:
                print(f"  ! Scene not found: {scene_id}")

        # Calculate overall statistics
        total_panels = sum(s.get("total_panels", 0) for s in all_results["scenes"].values())
        total_generated = sum(s.get("generated", 0) for s in all_results["scenes"].values())
        total_quality_passed = sum(s.get("quality_passed", 0) for s in all_results["scenes"].values())

        all_results["summary"] = {
            "total_panels": total_panels,
            "total_generated": total_generated,
            "total_quality_passed": total_quality_passed,
            "generation_success_rate": (total_generated / total_panels * 100) if total_panels else 0,
            "quality_pass_rate": (total_quality_passed / total_panels * 100) if total_panels else 0
        }

        # Add cost tracking
        all_results["cost_summary"] = self.cost_tracker.get_summary()

        # Save results
        reports_dir = PHASE5_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        results_path = reports_dir / "batch_results.json"
        self._save_json(all_results, results_path)

        cost_path = reports_dir / "cost_summary.json"
        self._save_json(self.cost_tracker.get_summary(), cost_path)

        # Print summary
        print("\n" + "=" * 70)
        print("Phase 5 Complete - Summary")
        print("=" * 70)
        print(f"\nScenes processed: {len(all_results['scenes'])}")
        print(f"Total panels: {total_panels}")
        print(f"Successfully generated: {total_generated}")
        print(f"Quality validation passed: {total_quality_passed}")
        print(f"\nGeneration success rate: {all_results['summary']['generation_success_rate']:.1f}%")
        print(f"Quality pass rate: {all_results['summary']['quality_pass_rate']:.1f}%")
        print(f"\nEstimated cost: ${all_results['cost_summary']['estimated_cost_usd']:.2f}")
        print(f"\nResults saved to: {results_path}")

        return all_results


def generate_single_panel_test():
    """Test single panel generation."""
    print("=" * 70)
    print("Phase 5: Single Panel Test")
    print("=" * 70)

    generator = PanelGenerator()

    # Load a test panel spec
    test_spec_path = PHASE4_DIR / "scene_01_request" / "s1_p01_spec.json"
    if not test_spec_path.exists():
        print(f"Test spec not found: {test_spec_path}")
        return

    with open(test_spec_path, "r", encoding="utf-8") as f:
        panel_spec = json.load(f)

    # Generate test panel
    output_dir = PHASE5_DIR / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_panel.png"

    result = generator.generate_panel(
        panel_spec,
        output_path,
        use_character_refs=True
    )

    if result.get("success"):
        print(f"\nTest panel generated successfully!")
        print(f"  Path: {result['path']}")
        print(f"  Size: {result['size_bytes']} bytes")
        print(f"  Generation time: {result['generation_time_ms']}ms")

        # Validate
        quality = generator.quality_checker.validate_panel(str(output_path), panel_spec)
        print(f"  Quality check: {'PASSED' if quality['passed'] else 'FAILED'}")
        print(f"  Dimensions: {quality.get('dimensions', 'unknown')}")
    else:
        print(f"\nTest panel generation failed: {result.get('error')}")

    return result


def main():
    """Main execution function for Phase 5."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run single panel test
        generate_single_panel_test()
    else:
        # Generate all scenes
        generator = PanelGenerator()
        results = generator.generate_all_scenes()

        return results


if __name__ == "__main__":
    main()
