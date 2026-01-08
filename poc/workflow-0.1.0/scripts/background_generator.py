"""
Phase 3: Background and Material Settings Generator for Novel-to-Toon PoC

This script generates location backgrounds and material textures using Google Gemini API
for the "Disciple of the Villain" novel.
"""

import os
import json
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
POC_DIR = BASE_DIR / "phase3_backgrounds"
STYLE_SPEC_PATH = BASE_DIR / "phase2_style" / "style_spec.json"


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


# Location definitions based on novel analysis
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

# Material specifications for texture generation
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

# Lighting presets for different scene types
LIGHTING_PRESETS = {
    "fog_day": {
        "name": "Daytime Fog",
        "description": "Diffused daylight through thick fog",
        "color_temperature": "5500K (neutral)",
        "shadow_intensity": "Low (soft, diffused)",
        "key_light_direction": "overhead, scattered",
        "ambient_level": "high",
        "mood": "mysterious, ethereal",
        "usage": "Magic Tower exterior, mysterious locations"
    },
    "fog_night": {
        "name": "Moonlit Fog",
        "description": "Cool moonlight filtering through fog",
        "color_temperature": "4000K (cool)",
        "shadow_intensity": "Medium",
        "key_light_direction": "overhead, lunar",
        "ambient_level": "low",
        "mood": "eerie, tense",
        "usage": "Night scenes at Magic Tower, outdoor night"
    },
    "indoor_lamp": {
        "name": "Traditional Lamp Light",
        "description": "Warm oil lamp or candle lighting",
        "color_temperature": "2700K (warm)",
        "shadow_intensity": "High (dramatic)",
        "key_light_direction": "multiple point sources",
        "ambient_level": "low",
        "mood": "intimate, tense, warm",
        "usage": "Inn interiors, taverns, indoor scenes"
    },
    "combat_intense": {
        "name": "Combat Lighting",
        "description": "High contrast action scene lighting",
        "color_temperature": "6500K (cool white)",
        "shadow_intensity": "Very high",
        "key_light_direction": "dramatic side lighting",
        "ambient_level": "very low",
        "mood": "explosive, dangerous",
        "usage": "Fight scenes, action sequences"
    },
    "emotional_soft": {
        "name": "Soft Emotional",
        "description": "Gentle lighting for intimate scenes",
        "color_temperature": "3500K (warm)",
        "shadow_intensity": "Low",
        "key_light_direction": "diffused, frontal",
        "ambient_level": "medium",
        "mood": "melancholic, tender",
        "usage": "Emotional moments, flashbacks, farewells"
    }
}

# Variation types for each location
LOCATION_VARIATIONS = {
    "magic_tower": [
        {"name": "exterior_day", "time": "day", "view": "exterior", "description": "Tower exterior shrouded in daytime fog"},
        {"name": "exterior_night", "time": "night", "view": "exterior", "description": "Tower under moonlight with fog"},
        {"name": "interior_hall", "time": "indoor", "view": "interior", "description": "Main hall interior where masters receive guests"},
        {"name": "interior_quarters", "time": "indoor", "view": "interior", "description": "Private quarters with subtle furnishings"}
    ],
    "black_path": [
        {"name": "alley_day", "time": "day", "view": "exterior", "description": "Dark alleyway during daytime, still shadowy"},
        {"name": "alley_night", "time": "night", "view": "exterior", "description": "Dangerous night scene in the alleys"},
        {"name": "tavern_interior", "time": "indoor", "view": "interior", "description": "Seedy tavern interior"},
        {"name": "market_street", "time": "day", "view": "exterior", "description": "Black market street scene"}
    ],
    "sword_dance_troupe": [
        {"name": "courtyard_day", "time": "day", "view": "exterior", "description": "Training courtyard with peach tree"},
        {"name": "training_ground", "time": "day", "view": "exterior", "description": "Practice area with weapons"},
        {"name": "living_quarters", "time": "indoor", "view": "interior", "description": "Shared living space"},
        {"name": "stage_area", "time": "indoor", "view": "interior", "description": "Performance stage"}
    ],
    "inn": [
        {"name": "exterior_day", "time": "day", "view": "exterior", "description": "Inn exterior with traditional signage"},
        {"name": "dining_area", "time": "indoor", "view": "interior", "description": "Main dining hall with patrons"},
        {"name": "private_room", "time": "indoor", "view": "interior", "description": "Private guest room"},
        {"name": "kitchen_view", "time": "indoor", "view": "interior", "description": "View from kitchen area"}
    ],
    "wolya_pavilion": [
        {"name": "exterior_night", "time": "night", "view": "exterior", "description": "Pavilion exterior with red lanterns"},
        {"name": "main_hall", "time": "indoor", "view": "interior", "description": "Main entertainment hall"},
        {"name": "private_room", "time": "indoor", "view": "interior", "description": "Luxurious private room"},
        {"name": "garden_courtyard", "time": "night", "view": "exterior", "description": "Inner garden at night"}
    ]
}


class BackgroundGenerator:
    """Generate background images and materials using Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-pro-image-preview"
        self.style_spec = self._load_style_spec()

    def _load_style_spec(self) -> dict:
        """Load the style specification from Phase 2."""
        if STYLE_SPEC_PATH.exists():
            with open(STYLE_SPEC_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_style_keywords(self) -> str:
        """Extract style keywords from style spec."""
        keywords = self.style_spec.get("prompt_keywords", {})
        style_words = keywords.get("style", [])
        atmosphere_words = keywords.get("atmosphere", [])
        quality_words = keywords.get("quality", [])
        return ", ".join(style_words + atmosphere_words + quality_words)

    def _build_location_prompt(self, location: LocationSpec, variation: dict) -> str:
        """Build a prompt for location background generation."""
        elements_str = ", ".join(location.visual_elements)
        colors_str = ", ".join(location.color_emphasis)
        lighting = LIGHTING_PRESETS.get(location.lighting_default, LIGHTING_PRESETS["fog_day"])

        # Adjust lighting based on variation
        if variation["time"] == "night":
            lighting = LIGHTING_PRESETS.get("fog_night", lighting)
        elif variation["time"] == "indoor":
            lighting = LIGHTING_PRESETS.get("indoor_lamp", lighting)

        prompt = f"""Korean webtoon background illustration:
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
- {"Fog effects visible" if "fog" in location.atmosphere.lower() or "magic_tower" in location.name.lower() else "Appropriate atmospheric effects"}

QUALITY: High detail, 2K resolution quality, professional illustration"""

        return prompt

    def _build_material_prompt(self, material: MaterialSpec) -> str:
        """Build a prompt for material texture generation."""
        prompt = f"""Seamless texture pattern for Korean webtoon illustration:
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

        return prompt

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str = "16:9",
        reference_image_path: Optional[Path] = None
    ) -> dict:
        """Generate a single image using Gemini API."""
        print(f"  Generating: {output_path.name}")

        try:
            contents = []

            if reference_image_path and reference_image_path.exists():
                ref_image = Image.open(reference_image_path)
                contents.append(ref_image)
                print(f"    Using reference: {reference_image_path.name}")

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
                            "prompt": prompt[:300] + "..." if len(prompt) > 300 else prompt,
                            "used_reference": reference_image_path is not None,
                        }

            return {
                "success": False,
                "error": "No image data in response",
                "prompt": prompt[:200] + "...",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt[:200] + "...",
            }

    def generate_location_base(self, location_key: str) -> dict:
        """Generate the base reference image for a location."""
        if location_key not in LOCATIONS:
            raise ValueError(f"Unknown location: {location_key}")

        location = LOCATIONS[location_key]
        output_dir = POC_DIR / "locations" / location_key

        print(f"\nGenerating base reference for {location.name}...")

        # Use first variation as base
        variations = LOCATION_VARIATIONS.get(location_key, [])
        if not variations:
            return {"success": False, "error": "No variations defined"}

        base_variation = variations[0]
        prompt = self._build_location_prompt(location, base_variation)

        output_path = output_dir / "base_reference.png"
        result = self.generate_image(prompt, output_path, aspect_ratio="16:9")

        # Save metadata
        metadata = {
            "location": asdict(location),
            "variation": base_variation,
            "generation": {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "prompt": prompt,
                "result": result,
            }
        }

        metadata_path = output_dir / "base_reference_metadata.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return result

    def generate_location_variations(self, location_key: str) -> list[dict]:
        """Generate all variations for a location using base reference."""
        if location_key not in LOCATIONS:
            raise ValueError(f"Unknown location: {location_key}")

        location = LOCATIONS[location_key]
        output_dir = POC_DIR / "locations" / location_key
        base_ref_path = output_dir / "base_reference.png"

        print(f"\nGenerating variations for {location.name}...")

        variations = LOCATION_VARIATIONS.get(location_key, [])
        results = []

        for i, variation in enumerate(variations):
            if i == 0:
                # Skip first variation (already generated as base)
                continue

            prompt = self._build_location_prompt(location, variation)

            # Use base reference for consistency (optional, may not work as well for backgrounds)
            output_path = output_dir / f"{variation['name']}.png"

            # For backgrounds, we might not need reference images
            # but we can still use them for style consistency
            ref_path = base_ref_path if base_ref_path.exists() else None

            result = self.generate_image(
                prompt,
                output_path,
                aspect_ratio="16:9",
                reference_image_path=ref_path
            )
            result["variation"] = variation["name"]
            results.append(result)

        return results

    def generate_material(self, material_key: str) -> dict:
        """Generate a material texture."""
        if material_key not in MATERIALS:
            raise ValueError(f"Unknown material: {material_key}")

        material = MATERIALS[material_key]
        output_dir = POC_DIR / "materials"

        print(f"\nGenerating material: {material.name}...")

        prompt = self._build_material_prompt(material)
        output_path = output_dir / f"{material_key}.png"

        result = self.generate_image(prompt, output_path, aspect_ratio="1:1")

        # Save metadata
        metadata = {
            "material": asdict(material),
            "generation": {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "prompt": prompt,
                "result": result,
            }
        }

        metadata_path = output_dir / f"{material_key}_metadata.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return result

    def generate_lighting_test(self, location_key: str, preset_key: str) -> dict:
        """Generate a lighting test for a specific preset."""
        if location_key not in LOCATIONS:
            raise ValueError(f"Unknown location: {location_key}")
        if preset_key not in LIGHTING_PRESETS:
            raise ValueError(f"Unknown lighting preset: {preset_key}")

        location = LOCATIONS[location_key]
        preset = LIGHTING_PRESETS[preset_key]
        output_dir = POC_DIR / "lighting_tests"

        print(f"\nGenerating lighting test: {location.name} with {preset['name']}...")

        # Create a simple test scene
        prompt = f"""Korean webtoon background illustration:
- Location: {location.name} interior scene
- Purpose: Lighting test demonstration

LIGHTING SETTINGS:
- Preset: {preset["name"]}
- {preset["description"]}
- Color Temperature: {preset["color_temperature"]}
- Shadow Intensity: {preset["shadow_intensity"]}
- Light Direction: {preset["key_light_direction"]}
- Ambient Level: {preset["ambient_level"]}
- Mood: {preset["mood"]}

STYLE:
- Korean webtoon (manhwa), wuxia genre
- Cel-shaded with gradient accents
- Clean detailed linework
- No characters, environment only
- No text

QUALITY: High detail, professional lighting demonstration"""

        output_path = output_dir / f"{location_key}_{preset_key}.png"
        result = self.generate_image(prompt, output_path, aspect_ratio="16:9")

        return result


def save_lighting_presets_doc():
    """Save lighting presets documentation."""
    doc_path = POC_DIR / "lighting_presets.json"
    POC_DIR.mkdir(parents=True, exist_ok=True)

    with open(doc_path, "w", encoding="utf-8") as f:
        json.dump(LIGHTING_PRESETS, f, indent=2, ensure_ascii=False)

    print(f"Saved lighting presets to: {doc_path}")
    return doc_path


def main():
    """Main execution function for Phase 3."""
    print("=" * 70)
    print("Phase 3: Background and Material Settings")
    print("Google Gemini API Generation")
    print("=" * 70)

    generator = BackgroundGenerator()

    all_results = {
        "phase": "Phase 3: Background and Material Settings",
        "timestamp": datetime.now().isoformat(),
        "locations": {},
        "materials": {},
        "lighting_tests": {},
    }

    # Generate location backgrounds
    print("\n" + "=" * 70)
    print("SECTION 1: Location Backgrounds")
    print("=" * 70)

    for location_key in LOCATIONS.keys():
        print(f"\n{'='*50}")
        print(f"Processing: {LOCATIONS[location_key].name}")
        print("=" * 50)

        # Generate base reference
        base_result = generator.generate_location_base(location_key)

        if not base_result.get("success", False):
            print(f"  ERROR: Base generation failed for {location_key}")
            all_results["locations"][location_key] = {
                "base_reference": base_result,
                "variations": [],
                "success": False,
            }
            continue

        # Generate variations
        variations = generator.generate_location_variations(location_key)

        all_results["locations"][location_key] = {
            "base_reference": base_result,
            "variations": variations,
            "base_success": base_result.get("success", False),
            "variations_success_count": sum(1 for r in variations if r.get("success", False)),
            "total_variations": len(variations),
        }

    # Generate materials
    print("\n" + "=" * 70)
    print("SECTION 2: Material Textures")
    print("=" * 70)

    for material_key in MATERIALS.keys():
        result = generator.generate_material(material_key)
        all_results["materials"][material_key] = result

    # Generate lighting tests (sample)
    print("\n" + "=" * 70)
    print("SECTION 3: Lighting Preset Tests")
    print("=" * 70)

    # Test a few combinations
    lighting_tests = [
        ("magic_tower", "fog_day"),
        ("magic_tower", "fog_night"),
        ("inn", "indoor_lamp"),
        ("black_path", "combat_intense"),
        ("sword_dance_troupe", "emotional_soft"),
    ]

    for location_key, preset_key in lighting_tests:
        result = generator.generate_lighting_test(location_key, preset_key)
        test_name = f"{location_key}_{preset_key}"
        all_results["lighting_tests"][test_name] = result

    # Save lighting presets documentation
    save_lighting_presets_doc()

    # Save overall results
    results_path = POC_DIR / "phase3_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 70)
    print("Phase 3 Complete - Summary")
    print("=" * 70)

    total_images = 0
    successful = 0

    print("\nLocations:")
    for loc_key, loc_results in all_results["locations"].items():
        loc_name = LOCATIONS[loc_key].name
        base_success = loc_results.get("base_success", False)
        var_success = loc_results.get("variations_success_count", 0)
        total_var = loc_results.get("total_variations", 0)

        print(f"  {loc_name}: Base {'PASS' if base_success else 'FAIL'}, Variations {var_success}/{total_var}")

        total_images += 1 + total_var
        successful += (1 if base_success else 0) + var_success

    print("\nMaterials:")
    for mat_key, mat_result in all_results["materials"].items():
        mat_name = MATERIALS[mat_key].name
        success = mat_result.get("success", False)
        print(f"  {mat_name}: {'PASS' if success else 'FAIL'}")
        total_images += 1
        successful += 1 if success else 0

    print("\nLighting Tests:")
    for test_name, test_result in all_results["lighting_tests"].items():
        success = test_result.get("success", False)
        print(f"  {test_name}: {'PASS' if success else 'FAIL'}")
        total_images += 1
        successful += 1 if success else 0

    print(f"\n{'='*70}")
    print(f"Total: {successful}/{total_images} images generated successfully")
    print(f"Success Rate: {successful/total_images*100:.1f}%" if total_images > 0 else "N/A")
    print(f"Results saved to: {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
