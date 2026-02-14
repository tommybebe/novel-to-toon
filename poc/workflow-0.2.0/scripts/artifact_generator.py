"""
Phase 3b: Artifact Reference Generator for PoC v0.2.0

Generates artifact reference sheets with consistent designs across variations.
Uses fal.ai FLUX Kontext: text-to-image for base, Kontext editing for variations.
Each artifact gets a base reference + 3-5 context variations.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional
from pathlib import Path

import fal_client
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
POC_DIR = BASE_DIR / "phase3_backgrounds_artifacts" / "artifacts"

# Import cost tracker
sys.path.insert(0, str(Path(__file__).parent))
from cost_tracker import FalCostTracker


@dataclass
class ArtifactSpec:
    """Artifact specification for reference generation."""
    artifact_id: str
    name: str
    korean_name: str
    owner: str
    significance: str
    base_prompt: str
    design_spec: dict
    color_palette: dict
    variations: list[dict]
    scenes_appearing: list[str]


# Artifact definitions
ARTIFACTS = {
    "twin_crescent_blades": ArtifactSpec(
        artifact_id="twin_crescent_blades",
        name="Twin Crescent Moon Blades",
        korean_name="쌍월 (雙月)",
        owner="Jin Sohan",
        significance="Signature weapons, gift from master Dokma",
        base_prompt="""Korean webtoon style weapon illustration:
- Object: Twin Crescent Moon Blades (paired weapons)
- Design: Curved crescent-shaped blades attached to handles
- Handle: Wrapped leather grip, dark color, decorative pommel
- Blade: Dark steel with subtle engravings, crescent moon curve
- Material appearance: Aged but well-maintained metal
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Both weapons displayed side by side, showing full design
- Background: Simple neutral, focus on weapons
- Lighting: Clear, even lighting to show all details
- Quality: High detail, publication ready

IMPORTANT DESIGN ELEMENTS TO ESTABLISH:
- Exact blade curvature and proportions
- Handle wrap pattern and color
- Pommel and guard design
- Relative size of blade to handle
- Surface finish and any engravings""",
        design_spec={
            "type": "paired_weapons",
            "blade": {"shape": "crescent_curve", "length_cm": 35, "material": "dark_steel", "finish": "matte_with_subtle_sheen", "engravings": "subtle_cloud_pattern"},
            "handle": {"length_cm": 20, "wrap_material": "dark_leather", "wrap_pattern": "crossed_diagonal", "pommel": "rounded_cap_with_ring"},
            "guard": {"style": "minimal_curved", "material": "matching_dark_steel"},
        },
        color_palette={"blade": "#3a3a4a", "handle_wrap": "#2d2520", "pommel": "#4a4a5a"},
        variations=[
            {"name": "held_combat", "prompt": """Show the EXACT SAME weapons from this image being held:
- Context: Being held by a martial artist (hands visible, face cropped)
- Pose: Combat ready stance, one blade raised, one lowered
- Lighting: Dramatic side lighting

MAINTAIN EXACTLY from reference:
- Blade shape, curvature, and proportions
- Handle design, wrap pattern, and pommel
- Metal finish and any engravings
- Overall weapon dimensions"""},
            {"name": "action_blur", "prompt": """Show the EXACT SAME weapons from this image in motion:
- Context: Mid-swing motion blur
- Effect: Motion lines, dynamic angle
- Lighting: High contrast action lighting

MAINTAIN EXACTLY from reference:
- Blade shape and design (even with motion blur)
- Handle design consistency
- Metal color and finish"""},
            {"name": "warm_display", "prompt": """Show the EXACT SAME weapons from this image in warm lighting:
- Context: Displayed on wooden table
- Lighting: Warm lamplight (indoor scene)
- Atmosphere: Intimate, reverent presentation

MAINTAIN EXACTLY from reference:
- All design elements, proportions and dimensions
- Blade and handle details"""},
        ],
        scenes_appearing=["scene_03"],
    ),
    "white_fan": ArtifactSpec(
        artifact_id="white_fan",
        name="White Fan (Baekseon)",
        korean_name="백선 (白扇)",
        owner="Jin Sohan (gift from Uiseon)",
        significance="Elegant weapon/accessory, gift from master Uiseon",
        base_prompt="""Korean webtoon style accessory illustration:
- Object: Elegant white folding fan (Korean/Chinese style)
- Design: Pristine white fan with subtle decorative pattern
- Material: High-quality fabric/paper with bamboo or ivory frame
- Open state: Fully opened, showing full design
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Fan displayed at slight angle to show depth
- Background: Simple neutral
- Lighting: Soft, even lighting
- Quality: High detail, publication ready

IMPORTANT DESIGN ELEMENTS:
- Fan ribbing pattern and material
- Edge details and any tassels
- Subtle pattern on fan surface
- Frame material and color""",
        design_spec={
            "type": "folding_fan",
            "material": "silk_on_bamboo",
            "color": "pristine_white_with_subtle_pattern",
            "pattern": "faint_cloud_motif",
            "tassel": "white_silk_cord",
        },
        color_palette={"fan_surface": "#f8f8f0", "frame": "#e8e0d0", "tassel": "#f0f0e8"},
        variations=[
            {"name": "open_held", "prompt": """Show the EXACT SAME fan from this image being held open:
- Context: Held elegantly in one hand
- Pose: Scholar's graceful hold
- Lighting: Warm, indoor

MAINTAIN EXACTLY from reference:
- Fan design, pattern, and color
- Frame material and details"""},
            {"name": "closed", "prompt": """Show the EXACT SAME fan from this image in closed position:
- Context: Folded closed, resting on surface
- Lighting: Clear, even lighting
- Show the edge profile and closed frame

MAINTAIN EXACTLY from reference:
- Frame design and material
- Overall proportions"""},
            {"name": "action_swing", "prompt": """Show the EXACT SAME fan from this image being used as weapon:
- Context: Mid-swing, being used offensively
- Effect: Slight motion blur, dynamic angle
- Lighting: Combat lighting

MAINTAIN EXACTLY from reference:
- Fan design and color
- Frame details"""},
        ],
        scenes_appearing=["scene_03"],
    ),
    "poison_pouch": ArtifactSpec(
        artifact_id="poison_pouch",
        name="Poison Pouch",
        korean_name="독낭 (毒囊)",
        owner="Dokma",
        significance="Contains poisons and medicines, symbol of Dokma's craft",
        base_prompt="""Korean webtoon style item illustration:
- Object: Dark leather medicine/poison pouch
- Design: Aged dark leather drawstring pouch with mysterious contents
- Details: Multiple small compartments, worn from use
- Material: Dark leather with subtle stitching
- Decoration: Small carved bone or metal clasp
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Pouch with some vials partially visible
- Background: Simple neutral
- Lighting: Moody, slight shadow
- Quality: High detail, publication ready

IMPORTANT DESIGN ELEMENTS:
- Leather texture and aging
- Clasp/closure design
- Size relative to a hand
- Contents hint (vials, dried herbs visible)""",
        design_spec={
            "type": "container",
            "material": "aged_dark_leather",
            "closure": "drawstring_with_bone_toggle",
            "compartments": "multiple_internal",
            "contents_hint": "glass_vials_dried_herbs",
        },
        color_palette={"leather": "#2a2018", "stitching": "#3a3028", "clasp": "#8a7a60"},
        variations=[
            {"name": "held", "prompt": """Show the EXACT SAME pouch from this image being held:
- Context: Held by weathered hand, opening to reveal contents
- Lighting: Warm lamplight
MAINTAIN EXACTLY from reference: All design elements"""},
            {"name": "on_belt", "prompt": """Show the EXACT SAME pouch from this image attached to a belt:
- Context: Hanging from dark robe belt
- Lighting: Indoor dim
MAINTAIN EXACTLY from reference: All design elements"""},
            {"name": "contents_spilled", "prompt": """Show the EXACT SAME pouch from this image with contents spilled:
- Context: Open on table, some vials and dried herbs scattered
- Lighting: Warm lamplight, mysterious atmosphere
MAINTAIN EXACTLY from reference: Pouch design and material"""},
        ],
        scenes_appearing=["scene_02", "scene_03"],
    ),
    "golden_peach": ArtifactSpec(
        artifact_id="golden_peach",
        name="Golden Peach",
        korean_name="황금 복숭아",
        owner="None (mystical fruit)",
        significance="Supernatural fruit that gave Jin Sohan his poison resistance",
        base_prompt="""Korean webtoon style mystical object illustration:
- Object: Golden glowing peach on a tree branch
- Design: Large luminous peach with supernatural golden glow
- Material: Organic fruit with ethereal golden sheen
- Effect: Emanating soft golden light, otherworldly presence
- Branch: Part of a peach tree, natural setting
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Peach centered, glowing against dark background
- Background: Dark nighttime, moonlit
- Lighting: Self-illuminating golden glow
- Quality: High detail, publication ready

IMPORTANT DESIGN ELEMENTS:
- Golden luminosity and glow effect
- Natural peach shape but clearly supernatural
- Soft particle effects around it
- Branch attachment detail""",
        design_spec={
            "type": "mystical_fruit",
            "shape": "oversized_peach",
            "glow": "golden_emanating",
            "size": "larger_than_normal_peach",
        },
        color_palette={"peach": "#ffd700", "glow": "#ffec8b", "branch": "#5a4a3a"},
        variations=[
            {"name": "close_up_glow", "prompt": """Show the EXACT SAME golden peach from this image in close-up:
- Context: Extreme close-up, showing glow detail
- Effect: Enhanced golden particles, dreamlike
- Lighting: Self-illuminating
MAINTAIN EXACTLY from reference: Peach design and glow quality"""},
            {"name": "held_by_child", "prompt": """Show the EXACT SAME golden peach from this image being held:
- Context: Small child hands reaching for or holding the peach
- Effect: Golden glow illuminating the hands
- Lighting: Dark background, peach provides light
MAINTAIN EXACTLY from reference: Peach design and golden glow"""},
            {"name": "on_tree", "prompt": """Show the EXACT SAME golden peach from this image on a tree:
- Context: Wide view of peach tree with this golden peach high up
- Effect: Standing out among normal peaches
- Lighting: Nighttime, moonlit, peach glowing
MAINTAIN EXACTLY from reference: Peach design, color, and glow"""},
        ],
        scenes_appearing=["scene_02"],
    ),
    "two_headed_snake": ArtifactSpec(
        artifact_id="two_headed_snake",
        name="Two-Headed Snake",
        korean_name="쌍두사 (雙頭蛇)",
        owner="None (mystical creature)",
        significance="Mythical creature whose inner cores gave Jin Sohan poison/medicine duality",
        base_prompt="""Korean webtoon style creature illustration:
- Creature: Two-headed snake (mystical, not realistic)
- Design: Serpentine body with two distinct heads
- Heads: One darker/venomous looking, one lighter/medicinal looking
- Body: Translucent with yin-yang duality visual
- Scale pattern: Iridescent, shifting between dark and light
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Full body coiled, both heads visible
- Background: Dark, mystical atmosphere
- Effect: Subtle ethereal glow, supernatural presence
- Quality: High detail, publication ready

IMPORTANT DESIGN ELEMENTS:
- Two distinct head designs (poison vs medicine duality)
- Body scale pattern with duality theme
- Translucent quality showing inner glow
- Overall serpentine proportions""",
        design_spec={
            "type": "mystical_creature",
            "body": "serpentine_dual_tone",
            "head_1": "darker_venomous",
            "head_2": "lighter_medicinal",
            "effect": "translucent_glow",
        },
        color_palette={"dark_head": "#2a1a2a", "light_head": "#c0d0c0", "body": "#4a5a4a", "glow": "#80c080"},
        variations=[
            {"name": "coiled_peach", "prompt": """Show the EXACT SAME two-headed snake from this image:
- Context: Coiled around a golden peach branch
- Pose: Relaxed, drunk on peach essence
- Effect: Both heads drooping contentedly
MAINTAIN EXACTLY from reference: Snake design, head details, scale pattern"""},
            {"name": "alert", "prompt": """Show the EXACT SAME two-headed snake from this image:
- Context: Both heads raised alertly
- Pose: Defensive coiled position
- Effect: Eyes glowing, scales bristling
MAINTAIN EXACTLY from reference: Snake design, head details, dual nature"""},
            {"name": "inner_cores", "prompt": """Show the EXACT SAME two-headed snake from this image:
- Context: Two glowing inner cores visible inside translucent body
- One core dark purple (poison), one core bright green (medicine)
- Effect: Supernatural glow from within
MAINTAIN EXACTLY from reference: Overall snake design and dual nature"""},
        ],
        scenes_appearing=["scene_02"],
    ),
}


def download_image(url: str, output_path: Path) -> int:
    """Download image from URL. Returns size in bytes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return len(response.content)


class ArtifactGenerator:
    """Generate artifact reference sheets using fal.ai FLUX Kontext."""

    def __init__(self):
        self.cost_tracker = FalCostTracker(session_id="poc-v2-artifacts")

    def generate_base_reference(self, artifact_key: str) -> dict:
        """Generate base reference image for an artifact."""
        artifact = ARTIFACTS[artifact_key]
        output_dir = POC_DIR / artifact_key

        print(f"  Generating base: {artifact.name}...")
        output_path = output_dir / "base_reference.png"
        start_ms = time.time()

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/kontext/text-to-image",
                arguments={
                    "prompt": artifact.base_prompt,
                    "aspect_ratio": "16:9",
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
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id=f"art_{artifact_key}_base",
                generation_time_ms=gen_time_ms,
                width=1920, height=1080,
                phase="artifact_generation",
            )

            # Save design spec
            design_data = {
                "artifact_id": artifact.artifact_id,
                "name": artifact.name,
                "korean_name": artifact.korean_name,
                "owner": artifact.owner,
                "significance": artifact.significance,
                "design_spec": artifact.design_spec,
                "color_palette": artifact.color_palette,
                "reference_images": ["base_reference.png"],
                "scenes_appearing": artifact.scenes_appearing,
                "generation": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "fal-ai/flux-pro/kontext/text-to-image",
                    "generation_time_ms": gen_time_ms,
                }
            }
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "design_spec.json", "w", encoding="utf-8") as f:
                json.dump(design_data, f, indent=2, ensure_ascii=False)

            print(f"    OK - base_reference.png ({size_bytes} bytes, {gen_time_ms}ms)")
            return {"success": True, "path": str(output_path), "size_bytes": size_bytes}

        except Exception as e:
            gen_time_ms = int((time.time() - start_ms) * 1000)
            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id=f"art_{artifact_key}_base",
                generation_time_ms=gen_time_ms,
                width=1920, height=1080,
                phase="artifact_generation",
                status="failed",
                error_message=str(e),
            )
            print(f"    FAIL - {e}")
            return {"success": False, "error": str(e)}

    def generate_variations(self, artifact_key: str) -> list[dict]:
        """Generate variations of an artifact using Kontext editing."""
        artifact = ARTIFACTS[artifact_key]
        output_dir = POC_DIR / artifact_key
        base_ref_path = output_dir / "base_reference.png"

        if not base_ref_path.exists():
            print(f"  SKIP - No base reference for {artifact_key}")
            return []

        base_ref_url = fal_client.upload_file(str(base_ref_path))
        results = []

        for variation in artifact.variations:
            var_name = variation["name"]
            output_path = output_dir / f"variation_{var_name}.png"

            print(f"  Generating variation: {var_name}...")
            start_ms = time.time()

            try:
                result = fal_client.subscribe(
                    "fal-ai/flux-pro/kontext",
                    arguments={
                        "prompt": variation["prompt"],
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
                    panel_id=f"art_{artifact_key}_{var_name}",
                    generation_time_ms=gen_time_ms,
                    width=1920, height=1080,
                    phase="artifact_generation",
                )

                print(f"    OK - variation_{var_name}.png ({size_bytes} bytes, {gen_time_ms}ms)")
                results.append({"success": True, "variation": var_name, "path": str(output_path)})

            except Exception as e:
                gen_time_ms = int((time.time() - start_ms) * 1000)
                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"art_{artifact_key}_{var_name}",
                    generation_time_ms=gen_time_ms,
                    width=1920, height=1080,
                    phase="artifact_generation",
                    status="failed",
                    error_message=str(e),
                )
                print(f"    FAIL - {var_name}: {e}")
                results.append({"success": False, "variation": var_name, "error": str(e)})

        # Update design_spec with variation paths
        design_spec_path = output_dir / "design_spec.json"
        if design_spec_path.exists():
            with open(design_spec_path, "r") as f:
                design_data = json.load(f)
            design_data["reference_images"].extend(
                [f"variation_{v['name']}.png" for v in artifact.variations]
            )
            with open(design_spec_path, "w", encoding="utf-8") as f:
                json.dump(design_data, f, indent=2, ensure_ascii=False)

        return results


def main():
    test_mode = "--test" in sys.argv

    print("=" * 70)
    print("Phase 3b: Artifact Reference Generation (fal.ai)")
    if test_mode:
        print("*** TEST MODE - Twin Crescent Blades base only ***")
    print("=" * 70)

    generator = ArtifactGenerator()

    all_results = {
        "phase": "Phase 3b: Artifact Reference Generation",
        "platform": "fal.ai",
        "timestamp": datetime.now().isoformat(),
        "artifacts": {},
    }

    artifact_keys = ["twin_crescent_blades"] if test_mode else list(ARTIFACTS.keys())

    for artifact_key in artifact_keys:
        artifact = ARTIFACTS[artifact_key]
        print(f"\n{'='*50}")
        print(f"Processing: {artifact.name}")
        print("=" * 50)

        base_result = generator.generate_base_reference(artifact_key)

        if not base_result.get("success"):
            all_results["artifacts"][artifact_key] = {
                "base_reference": base_result, "variations": [], "success": False
            }
            continue

        if test_mode:
            all_results["artifacts"][artifact_key] = {"base_reference": base_result}
            continue

        variations = generator.generate_variations(artifact_key)
        all_results["artifacts"][artifact_key] = {
            "base_reference": base_result,
            "variations": variations,
            "base_success": True,
            "variations_success_count": sum(1 for r in variations if r["success"]),
            "total_variations": len(variations),
        }

    # Save artifact registry
    registry = {}
    for key, artifact in ARTIFACTS.items():
        registry[key] = {
            "artifact_id": artifact.artifact_id,
            "name": artifact.name,
            "korean_name": artifact.korean_name,
            "owner": artifact.owner,
            "significance": artifact.significance,
            "base_reference": f"{key}/base_reference.png",
            "variations": [f"{key}/variation_{v['name']}.png" for v in artifact.variations],
            "scenes_appearing": artifact.scenes_appearing,
        }

    POC_DIR.mkdir(parents=True, exist_ok=True)
    with open(POC_DIR / "artifact_registry.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    # Save results
    results_path = POC_DIR / "phase3b_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Cost summary
    generator.cost_tracker.print_summary()
    report_dir = BASE_DIR / "reports"
    generator.cost_tracker.export(str(report_dir / "phase3b_cost_report.json"))

    # Print summary
    print("\n" + "=" * 70)
    print("Phase 3b Complete - Summary")
    print("=" * 70)

    total = 0
    success = 0
    for art_key, art_data in all_results["artifacts"].items():
        base_ok = art_data.get("base_reference", {}).get("success", False)
        var_ok = art_data.get("variations_success_count", 0)
        total_var = art_data.get("total_variations", 0)
        name = ARTIFACTS[art_key].name
        print(f"  {name}: Base {'PASS' if base_ok else 'FAIL'}", end="")
        if total_var > 0:
            print(f", Variations {var_ok}/{total_var}")
        else:
            print()
        total += 1 + total_var
        success += (1 if base_ok else 0) + var_ok

    if total > 0:
        print(f"\n  Total: {success}/{total} ({success/total*100:.1f}%)")
    print(f"  Results: {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
