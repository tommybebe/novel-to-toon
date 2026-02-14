"""
Phase 3a: Background and Material Settings Generator for PoC v0.2.0

Generates location backgrounds and material textures using fal.ai FLUX Kontext.
Kontext text-to-image for base references, Kontext editing for variations.
Flux 2 Flash for cheaper lighting tests.
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
POC_DIR = BASE_DIR / "phase3_backgrounds_artifacts"
STYLE_SPEC_PATH = BASE_DIR / "phase2_style" / "style_spec.json"

# Import cost tracker
sys.path.insert(0, str(Path(__file__).parent))
from cost_tracker import FalCostTracker


@dataclass
class LocationSpec:
    """Location specification for background generation."""
    name: str
    korean_name: str
    description: str
    visual_elements: list[str]
    atmosphere: str
    lighting_default: str
    color_emphasis: list[str]


@dataclass
class MaterialSpec:
    """Material specification for texture generation."""
    name: str
    description: str
    color: str
    pattern: str
    usage: str


# Location definitions
LOCATIONS = {
    "magic_tower": LocationSpec(
        name="Magic Tower",
        korean_name="마선루 (魔仙樓)",
        description="Hidden mystical tower where the twin masters Dokma and Uiseon live in seclusion",
        visual_elements=[
            "Ancient multi-story tower structure",
            "Dense, perpetual fog surrounding the area",
            "Traditional East Asian architecture with weathered stone",
            "Isolated mountain setting",
            "Mysterious aura, otherworldly atmosphere",
            "Subtle signs of age and mysticism"
        ],
        atmosphere="Mysterious, isolated, otherworldly, hidden from the world",
        lighting_default="fog_day",
        color_emphasis=["#b8c5d6", "#8a9eb5", "#5a6f8a", "#1a1a2e"]
    ),
    "black_path": LocationSpec(
        name="Black Path Territory",
        korean_name="흑도 (黑道)",
        description="Criminal underworld region where martial artists of the dark path gather",
        visual_elements=[
            "Dark, narrow alleyways",
            "Seedy establishments and taverns",
            "Dangerous atmosphere with hidden threats",
            "Crowded streets with shadowy figures",
            "Traditional architecture in disrepair",
            "Dim lantern lighting"
        ],
        atmosphere="Dangerous, seedy, tense, lawless",
        lighting_default="indoor_lamp",
        color_emphasis=["#1a1a2e", "#4a4a6a", "#8b0000", "#333333"]
    ),
    "sword_dance_troupe": LocationSpec(
        name="Sword Dance Troupe Headquarters",
        korean_name="검무단 (劍舞團)",
        description="Performance troupe headquarters where Jin Sohan grew up",
        visual_elements=[
            "Training grounds with practice equipment",
            "Peach tree in the courtyard (significant to story)",
            "Living quarters for troupe members",
            "Performance stage area",
            "Traditional Korean architecture",
            "Warm, lived-in atmosphere"
        ],
        atmosphere="Homely, nostalgic, bittersweet, artistic",
        lighting_default="emotional_soft",
        color_emphasis=["#c9a227", "#8b8ba3", "#4a4a6a", "#f0e6dc"]
    ),
    "inn": LocationSpec(
        name="Guest House / Inn",
        korean_name="객잔",
        description="Traditional Korean inn serving as a common meeting place for travelers",
        visual_elements=[
            "Traditional Korean inn architecture",
            "Dining area with low tables",
            "Wooden interior with warm tones",
            "Paper screen doors (hanji)",
            "Lantern lighting",
            "Kitchen area visible in background"
        ],
        atmosphere="Busy, tense undercurrent, public space, transient",
        lighting_default="indoor_lamp",
        color_emphasis=["#c9a227", "#8b7355", "#5a4a3a", "#1a1a2e"]
    ),
    "wolya_pavilion": LocationSpec(
        name="Wolya Pavilion",
        korean_name="월야루 (月夜樓)",
        description="Pleasure house/entertainment district establishment",
        visual_elements=[
            "Ornate traditional architecture",
            "Red lanterns throughout",
            "Entertainment district atmosphere",
            "Elaborate decorations and silk hangings",
            "Multiple levels with private rooms",
            "Garden courtyard"
        ],
        atmosphere="Luxurious, sensual, mysterious, entertainment",
        lighting_default="indoor_lamp",
        color_emphasis=["#8b0000", "#c9a227", "#4a2d6a", "#1a1a2e"]
    )
}

# Materials
MATERIALS = {
    "black_silk_robe": MaterialSpec(
        name="Black Silk Robe Fabric",
        description="Traditional Korean silk hanbok fabric for Dokma's robes",
        color="Deep black with subtle purple undertones",
        pattern="Subtle cloud motif, barely visible",
        usage="Clothing texture for dark-robed characters"
    ),
    "white_silk_robe": MaterialSpec(
        name="White Silk Robe Fabric",
        description="Traditional Korean silk fabric for Uiseon's pristine robes",
        color="Pure white with subtle cream undertones",
        pattern="Faint floral pattern",
        usage="Clothing texture for light-robed characters"
    ),
    "weathered_stone": MaterialSpec(
        name="Ancient Weathered Stone",
        description="Stone texture for tower and traditional architecture",
        color="Gray with moss and age marks",
        pattern="Natural stone grain with weathering",
        usage="Architecture, walls, floors"
    ),
    "aged_wood": MaterialSpec(
        name="Aged Wood",
        description="Traditional wooden structures texture",
        color="Dark brown with warm undertones",
        pattern="Wood grain with age patina",
        usage="Inn interiors, traditional buildings"
    ),
    "fog_atmosphere": MaterialSpec(
        name="Atmospheric Fog",
        description="Dense fog effect for Magic Tower scenes",
        color="Blue-gray gradient",
        pattern="Wispy, layered fog particles",
        usage="Atmospheric overlay for mysterious scenes"
    )
}

# Lighting presets
LIGHTING_PRESETS = {
    "fog_day": {
        "name": "Daytime Fog",
        "description": "Diffused daylight through thick fog",
        "color_temperature": "5500K (neutral)",
        "shadow_intensity": "Low (soft, diffused)",
        "key_light_direction": "overhead, scattered",
        "ambient_level": "high",
        "mood": "mysterious, ethereal",
    },
    "fog_night": {
        "name": "Moonlit Fog",
        "description": "Cool moonlight filtering through fog",
        "color_temperature": "4000K (cool)",
        "shadow_intensity": "Medium",
        "key_light_direction": "overhead, lunar",
        "ambient_level": "low",
        "mood": "eerie, tense",
    },
    "indoor_lamp": {
        "name": "Traditional Lamp Light",
        "description": "Warm oil lamp or candle lighting",
        "color_temperature": "2700K (warm)",
        "shadow_intensity": "High (dramatic)",
        "key_light_direction": "multiple point sources",
        "ambient_level": "low",
        "mood": "intimate, tense, warm",
    },
    "combat_intense": {
        "name": "Combat Lighting",
        "description": "High contrast action scene lighting",
        "color_temperature": "6500K (cool white)",
        "shadow_intensity": "Very high",
        "key_light_direction": "dramatic side lighting",
        "ambient_level": "very low",
        "mood": "explosive, dangerous",
    },
    "emotional_soft": {
        "name": "Soft Emotional",
        "description": "Gentle lighting for intimate scenes",
        "color_temperature": "3500K (warm)",
        "shadow_intensity": "Low",
        "key_light_direction": "diffused, frontal",
        "ambient_level": "medium",
        "mood": "melancholic, tender",
    }
}

# Location variations
LOCATION_VARIATIONS = {
    "magic_tower": [
        {"name": "exterior_day", "time": "day", "view": "exterior", "description": "Tower exterior shrouded in daytime fog"},
        {"name": "exterior_night", "time": "night", "view": "exterior", "description": "Tower under moonlight with fog"},
        {"name": "interior_hall", "time": "indoor", "view": "interior", "description": "Main hall interior where masters receive guests"},
    ],
    "black_path": [
        {"name": "alley_night", "time": "night", "view": "exterior", "description": "Dangerous night scene in the alleys"},
        {"name": "tavern_interior", "time": "indoor", "view": "interior", "description": "Seedy tavern interior"},
        {"name": "market_street", "time": "day", "view": "exterior", "description": "Black market street scene"},
    ],
    "sword_dance_troupe": [
        {"name": "courtyard_day", "time": "day", "view": "exterior", "description": "Training courtyard with peach tree"},
        {"name": "training_ground", "time": "day", "view": "exterior", "description": "Practice area with weapons"},
        {"name": "living_quarters", "time": "indoor", "view": "interior", "description": "Shared living space"},
    ],
    "inn": [
        {"name": "exterior_day", "time": "day", "view": "exterior", "description": "Inn exterior with traditional signage"},
        {"name": "dining_area", "time": "indoor", "view": "interior", "description": "Main dining hall with patrons"},
        {"name": "private_room", "time": "indoor", "view": "interior", "description": "Private guest room"},
    ],
    "wolya_pavilion": [
        {"name": "exterior_night", "time": "night", "view": "exterior", "description": "Pavilion exterior with red lanterns"},
        {"name": "main_hall", "time": "indoor", "view": "interior", "description": "Main entertainment hall"},
        {"name": "garden_courtyard", "time": "night", "view": "exterior", "description": "Inner garden at night"},
    ]
}


def download_image(url: str, output_path: Path) -> int:
    """Download image from URL. Returns size in bytes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return len(response.content)


class BackgroundGenerator:
    """Generate backgrounds and materials using fal.ai FLUX Kontext."""

    def __init__(self):
        self.cost_tracker = FalCostTracker(session_id="poc-v2-backgrounds")
        self.style_spec = self._load_style_spec()

    def _load_style_spec(self) -> dict:
        if STYLE_SPEC_PATH.exists():
            with open(STYLE_SPEC_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_style_keywords(self) -> str:
        keywords = self.style_spec.get("prompt_keywords", {})
        parts = keywords.get("style", []) + keywords.get("atmosphere", []) + keywords.get("quality", [])
        return ", ".join(parts) if parts else "Korean webtoon, manhwa, wuxia genre, high detail"

    def _build_location_prompt(self, location: LocationSpec, variation: dict) -> str:
        elements_str = ", ".join(location.visual_elements)
        colors_str = ", ".join(location.color_emphasis)
        lighting = LIGHTING_PRESETS.get(location.lighting_default, LIGHTING_PRESETS["fog_day"])

        if variation["time"] == "night":
            lighting = LIGHTING_PRESETS.get("fog_night", lighting)
        elif variation["time"] == "indoor":
            lighting = LIGHTING_PRESETS.get("indoor_lamp", lighting)

        return f"""Korean webtoon background illustration:
- Location: {location.name} ({location.korean_name})
- Setting: {variation["description"]}
- View: {variation["view"]} view

VISUAL ELEMENTS:
{elements_str}

ATMOSPHERE:
- Mood: {location.atmosphere}
- Lighting: {lighting["description"]}
- Color Temperature: {lighting["color_temperature"]}
- Shadow Intensity: {lighting["shadow_intensity"]}

STYLE REQUIREMENTS:
- Art style: Korean webtoon (manhwa), wuxia genre
- Clean detailed linework, cel-shaded with gradient accents
- Color emphasis: {colors_str}
- High detail environment art, publication ready
- No characters, environment only
- No text or UI elements

COMPOSITION:
- {"Wide establishing shot" if variation["view"] == "exterior" else "Medium interior shot"}
- Depth and atmosphere emphasized

QUALITY: High detail, professional illustration"""

    def _build_material_prompt(self, material: MaterialSpec) -> str:
        return f"""Seamless texture pattern for Korean webtoon illustration:
- Material: {material.name}
- Description: {material.description}
- Color: {material.color}
- Pattern: {material.pattern}
- Usage: {material.usage}

REQUIREMENTS:
- Style: Suitable for Korean webtoon (manhwa) art
- Format: Tileable/seamless texture
- Detail level: Medium, not photorealistic
- Clean, stylized appearance matching cel-shaded art style
- No text, no watermarks
- Square format

QUALITY: High detail, professional texture asset"""

    def generate_location_base(self, location_key: str) -> dict:
        """Generate base reference image for a location using Kontext text-to-image."""
        location = LOCATIONS[location_key]
        output_dir = POC_DIR / "locations" / location_key

        variations = LOCATION_VARIATIONS.get(location_key, [])
        if not variations:
            return {"success": False, "error": "No variations defined"}

        base_variation = variations[0]
        prompt = self._build_location_prompt(location, base_variation)
        output_path = output_dir / "base_reference.png"

        print(f"  Generating base: {location.name} ({base_variation['name']})...")
        start_ms = time.time()

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/kontext/text-to-image",
                arguments={
                    "prompt": prompt,
                    "aspect_ratio": "16:9",
                    "num_images": 1,
                    "output_format": "png",
                    "safety_tolerance": 5,
                }
            )

            gen_time_ms = int((time.time() - start_ms) * 1000)
            image_url = result["images"][0]["url"]
            size_bytes = download_image(image_url, output_path)

            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id=f"bg_{location_key}_base",
                generation_time_ms=gen_time_ms,
                width=1920, height=1080,
                phase="background_generation",
            )

            # Save metadata
            metadata = {
                "location": asdict(location),
                "variation": base_variation,
                "generation": {
                    "timestamp": datetime.now().isoformat(),
                    "model": "fal-ai/flux-pro/kontext/text-to-image",
                    "prompt": prompt,
                    "generation_time_ms": gen_time_ms,
                    "size_bytes": size_bytes,
                }
            }
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "base_reference_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            print(f"    OK - base_reference.png ({size_bytes} bytes, {gen_time_ms}ms)")
            return {"success": True, "path": str(output_path), "size_bytes": size_bytes}

        except Exception as e:
            gen_time_ms = int((time.time() - start_ms) * 1000)
            self.cost_tracker.track(
                model="fal-ai/flux-pro/kontext/text-to-image",
                panel_id=f"bg_{location_key}_base",
                generation_time_ms=gen_time_ms,
                width=1920, height=1080,
                phase="background_generation",
                status="failed",
                error_message=str(e),
            )
            print(f"    FAIL - {e}")
            return {"success": False, "error": str(e)}

    def generate_location_variations(self, location_key: str) -> list[dict]:
        """Generate variations for a location using Kontext editing from base."""
        location = LOCATIONS[location_key]
        output_dir = POC_DIR / "locations" / location_key
        base_ref_path = output_dir / "base_reference.png"

        if not base_ref_path.exists():
            print(f"  SKIP - No base reference for {location_key}")
            return []

        variations = LOCATION_VARIATIONS.get(location_key, [])
        base_ref_url = fal_client.upload_file(str(base_ref_path))

        results = []
        for variation in variations[1:]:  # Skip first (already base)
            prompt = f"""Transform this location scene:
- New setting: {variation["description"]}
- View: {variation["view"]}
- Time: {variation["time"]}

MAINTAIN from reference:
- Overall architectural style and design
- Art style, line weight, and color approach
- Quality level and detail

CHANGE:
- Lighting appropriate for {variation["time"]}
- {"Interior perspective" if variation["view"] == "interior" else "Exterior perspective"}
- Atmosphere and mood matching {variation["time"]} setting"""

            output_path = output_dir / f"{variation['name']}.png"
            print(f"  Generating variation: {variation['name']}...")
            start_ms = time.time()

            try:
                result = fal_client.subscribe(
                    "fal-ai/flux-pro/kontext",
                    arguments={
                        "prompt": prompt,
                        "image_url": base_ref_url,
                        "num_images": 1,
                        "output_format": "png",
                        "safety_tolerance": 5,
                    }
                )

                gen_time_ms = int((time.time() - start_ms) * 1000)
                image_url = result["images"][0]["url"]
                size_bytes = download_image(image_url, output_path)

                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"bg_{location_key}_{variation['name']}",
                    generation_time_ms=gen_time_ms,
                    width=1920, height=1080,
                    phase="background_generation",
                )

                print(f"    OK - {variation['name']}.png ({size_bytes} bytes, {gen_time_ms}ms)")
                results.append({"success": True, "variation": variation["name"], "path": str(output_path)})

            except Exception as e:
                gen_time_ms = int((time.time() - start_ms) * 1000)
                self.cost_tracker.track(
                    model="fal-ai/flux-pro/kontext",
                    panel_id=f"bg_{location_key}_{variation['name']}",
                    generation_time_ms=gen_time_ms,
                    width=1920, height=1080,
                    phase="background_generation",
                    status="failed",
                    error_message=str(e),
                )
                print(f"    FAIL - {variation['name']}: {e}")
                results.append({"success": False, "variation": variation["name"], "error": str(e)})

        return results

    def generate_material(self, material_key: str) -> dict:
        """Generate a material texture using Flux 2 Flash (cheaper)."""
        material = MATERIALS[material_key]
        output_dir = POC_DIR / "materials"

        prompt = self._build_material_prompt(material)
        output_path = output_dir / f"{material_key}.png"

        print(f"  Generating material: {material.name}...")
        start_ms = time.time()

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-2/flash",
                arguments={
                    "prompt": prompt,
                    "image_size": {"width": 1024, "height": 1024},
                    "num_images": 1,
                    "output_format": "png",
                    "num_inference_steps": 4,
                }
            )

            gen_time_ms = int((time.time() - start_ms) * 1000)
            image_url = result["images"][0]["url"]
            size_bytes = download_image(image_url, output_path)

            self.cost_tracker.track(
                model="fal-ai/flux-2/flash",
                panel_id=f"mat_{material_key}",
                generation_time_ms=gen_time_ms,
                width=1024, height=1024,
                phase="material_generation",
            )

            print(f"    OK - {material_key}.png ({size_bytes} bytes, {gen_time_ms}ms)")
            return {"success": True, "path": str(output_path), "size_bytes": size_bytes}

        except Exception as e:
            gen_time_ms = int((time.time() - start_ms) * 1000)
            self.cost_tracker.track(
                model="fal-ai/flux-2/flash",
                panel_id=f"mat_{material_key}",
                generation_time_ms=gen_time_ms,
                width=1024, height=1024,
                phase="material_generation",
                status="failed",
                error_message=str(e),
            )
            print(f"    FAIL - {material_key}: {e}")
            return {"success": False, "error": str(e)}

    def generate_lighting_test(self, location_key: str, preset_key: str) -> dict:
        """Generate a lighting test using Flux 2 Flash (cheapest)."""
        location = LOCATIONS[location_key]
        preset = LIGHTING_PRESETS[preset_key]
        output_dir = POC_DIR / "lighting_tests"

        prompt = f"""Korean webtoon background illustration:
- Location: {location.name} interior scene
- Purpose: Lighting test demonstration

LIGHTING SETTINGS:
- Preset: {preset["name"]}
- {preset["description"]}
- Color Temperature: {preset["color_temperature"]}
- Shadow Intensity: {preset["shadow_intensity"]}
- Mood: {preset["mood"]}

STYLE: Korean webtoon (manhwa), cel-shaded, no characters, no text

QUALITY: High detail, professional lighting demonstration"""

        output_path = output_dir / f"{location_key}_{preset_key}.png"
        print(f"  Lighting test: {location.name} + {preset['name']}...")
        start_ms = time.time()

        try:
            result = fal_client.subscribe(
                "fal-ai/flux-2/flash",
                arguments={
                    "prompt": prompt,
                    "image_size": {"width": 1920, "height": 1080},
                    "num_images": 1,
                    "output_format": "png",
                    "num_inference_steps": 4,
                }
            )

            gen_time_ms = int((time.time() - start_ms) * 1000)
            image_url = result["images"][0]["url"]
            size_bytes = download_image(image_url, output_path)

            self.cost_tracker.track(
                model="fal-ai/flux-2/flash",
                panel_id=f"light_{location_key}_{preset_key}",
                generation_time_ms=gen_time_ms,
                width=1920, height=1080,
                phase="lighting_test",
            )

            print(f"    OK ({gen_time_ms}ms)")
            return {"success": True, "path": str(output_path)}

        except Exception as e:
            gen_time_ms = int((time.time() - start_ms) * 1000)
            self.cost_tracker.track(
                model="fal-ai/flux-2/flash",
                panel_id=f"light_{location_key}_{preset_key}",
                generation_time_ms=gen_time_ms,
                width=1920, height=1080,
                phase="lighting_test",
                status="failed",
                error_message=str(e),
            )
            print(f"    FAIL - {e}")
            return {"success": False, "error": str(e)}


def main():
    """Main execution function for Phase 3a."""
    test_mode = "--test" in sys.argv

    print("=" * 70)
    print("Phase 3a: Background and Material Settings (fal.ai)")
    if test_mode:
        print("*** TEST MODE - Magic Tower base only ***")
    print("=" * 70)

    generator = BackgroundGenerator()

    all_results = {
        "phase": "Phase 3a: Background and Material Settings",
        "platform": "fal.ai",
        "timestamp": datetime.now().isoformat(),
        "locations": {},
        "materials": {},
        "lighting_tests": {},
    }

    if test_mode:
        # Test: only Magic Tower base
        base_result = generator.generate_location_base("magic_tower")
        all_results["locations"]["magic_tower"] = {"base_reference": base_result}
    else:
        # Full: all locations
        print("\n" + "=" * 70)
        print("SECTION 1: Location Backgrounds")
        print("=" * 70)

        for location_key in LOCATIONS:
            print(f"\n{'='*50}")
            print(f"Processing: {LOCATIONS[location_key].name}")
            print("=" * 50)

            base_result = generator.generate_location_base(location_key)
            if not base_result.get("success"):
                all_results["locations"][location_key] = {
                    "base_reference": base_result, "variations": [], "success": False
                }
                continue

            variations = generator.generate_location_variations(location_key)
            all_results["locations"][location_key] = {
                "base_reference": base_result,
                "variations": variations,
                "base_success": True,
                "variations_success_count": sum(1 for r in variations if r["success"]),
                "total_variations": len(variations),
            }

        # Materials
        print("\n" + "=" * 70)
        print("SECTION 2: Material Textures")
        print("=" * 70)

        for material_key in MATERIALS:
            result = generator.generate_material(material_key)
            all_results["materials"][material_key] = result

        # Lighting tests
        print("\n" + "=" * 70)
        print("SECTION 3: Lighting Preset Tests")
        print("=" * 70)

        lighting_tests = [
            ("magic_tower", "fog_day"),
            ("magic_tower", "fog_night"),
            ("inn", "indoor_lamp"),
            ("black_path", "combat_intense"),
            ("sword_dance_troupe", "emotional_soft"),
        ]

        for location_key, preset_key in lighting_tests:
            result = generator.generate_lighting_test(location_key, preset_key)
            all_results["lighting_tests"][f"{location_key}_{preset_key}"] = result

    # Save lighting presets doc
    POC_DIR.mkdir(parents=True, exist_ok=True)
    with open(POC_DIR / "lighting_presets.json", "w", encoding="utf-8") as f:
        json.dump(LIGHTING_PRESETS, f, indent=2, ensure_ascii=False)

    # Save results
    results_path = POC_DIR / "phase3a_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Cost summary
    generator.cost_tracker.print_summary()
    report_dir = BASE_DIR / "reports"
    generator.cost_tracker.export(str(report_dir / "phase3a_cost_report.json"))

    # Print summary
    print("\n" + "=" * 70)
    print("Phase 3a Complete - Summary")
    print("=" * 70)

    total = 0
    success = 0
    for loc_key, loc_data in all_results["locations"].items():
        base_ok = loc_data.get("base_reference", {}).get("success", False)
        var_ok = loc_data.get("variations_success_count", 0)
        total_var = loc_data.get("total_variations", 0)
        print(f"  {LOCATIONS[loc_key].name}: Base {'PASS' if base_ok else 'FAIL'}, Variations {var_ok}/{total_var}")
        total += 1 + total_var
        success += (1 if base_ok else 0) + var_ok

    for mat_key, mat_data in all_results["materials"].items():
        ok = mat_data.get("success", False)
        print(f"  Material {mat_key}: {'PASS' if ok else 'FAIL'}")
        total += 1
        success += 1 if ok else 0

    for test_name, test_data in all_results["lighting_tests"].items():
        ok = test_data.get("success", False)
        total += 1
        success += 1 if ok else 0

    if total > 0:
        print(f"\n  Total: {success}/{total} ({success/total*100:.1f}%)")
    print(f"  Results: {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
