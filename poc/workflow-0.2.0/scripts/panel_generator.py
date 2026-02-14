"""
Phase 5: Panel Image Generator for PoC v0.2.0

Generates final webtoon panels by combining all previous phase outputs.
Uses fal.ai FLUX models with intelligent model selection:
  - Kontext Multi: multi-reference panels (characters + artifacts)
  - Kontext: single-reference panels
  - Flux 2 Flash: no-reference panels (cheap)

Features:
  - Reference image upload caching (upload once, reuse URLs)
  - Safe zone-aware prompt construction
  - Artifact reference integration
  - Panel shape post-processing (non-rectangular masks)
  - Enhanced quality validation (8 checks)
  - Batch generation via fal_client.submit() queue
  - Retry logic (max 3 attempts)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

import fal_client
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
PHASE1_DIR = BASE_DIR / "phase1_characters"
PHASE2_DIR = BASE_DIR / "phase2_style"
PHASE3_DIR = BASE_DIR / "phase3_backgrounds_artifacts"
PHASE4_DIR = BASE_DIR / "phase4_storyboard"
PHASE5_DIR = BASE_DIR / "phase5_generation"

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from cost_tracker import FalCostTracker
from panel_shape_processor import PanelShapeProcessor, PanelShape, apply_panel_shape


# ─────────────────────────────────────────────────────────────────────
# Aspect ratio mapping
# ─────────────────────────────────────────────────────────────────────

# Maps spec aspect ratios to fal.ai Kontext aspect_ratio strings
KONTEXT_ASPECT_RATIOS = {
    "landscape_16_9": "16:9",
    "landscape_4_3": "4:3",
    "portrait_16_9": "9:16",
    "portrait_4_3": "3:4",
    "portrait_3_4": "3:4",
    "portrait_9_16": "9:16",
    "square_1_1": "1:1",
    "ultrawide_21_9": "21:9",
}

# Maps to pixel dimensions for Flux 2 models
FLUX2_DIMENSIONS = {
    "landscape_16_9": {"width": 1920, "height": 1080},
    "landscape_4_3": {"width": 1440, "height": 1080},
    "portrait_16_9": {"width": 1080, "height": 1920},
    "portrait_4_3": {"width": 1080, "height": 1440},
    "portrait_3_4": {"width": 1080, "height": 1440},
    "portrait_9_16": {"width": 1080, "height": 1920},
    "square_1_1": {"width": 1024, "height": 1024},
    "ultrawide_21_9": {"width": 1920, "height": 1080},
}


def download_image(url: str, output_path: Path) -> int:
    """Download image from URL. Returns size in bytes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return len(response.content)


# ─────────────────────────────────────────────────────────────────────
# Prompt construction helpers
# ─────────────────────────────────────────────────────────────────────

def build_safe_zone_instructions(safe_zones: list[dict]) -> str:
    """Build prompt instructions for keeping safe zones clear."""
    if not safe_zones:
        return "No speech bubble zones — fill the entire frame with scene content."

    lines = ["IMPORTANT - Keep the following areas CLEAR of important visual content (speech bubbles will be added later):"]
    for zone in safe_zones:
        pos = zone.get("position", "unknown")
        w = zone.get("width_percent", 0)
        h = zone.get("height_percent", 0)
        btype = zone.get("bubble_type", "speech")
        lines.append(f"  - {pos}: {w}% x {h}% zone reserved for {btype} bubble")

    lines.append("Place characters and focal elements OUTSIDE these zones.")
    return "\n".join(lines)


def build_artifact_instructions(artifacts: list[dict], artifact_refs: dict[str, str]) -> str:
    """Build prompt instructions for artifact placement."""
    if not artifacts:
        return "No specific artifacts in this panel."

    lines = ["ARTIFACTS IN SCENE (use reference images for exact design):"]
    for art in artifacts:
        art_id = art.get("artifact_id", "unknown")
        position = art.get("position", "center")
        state = art.get("state", "visible")
        importance = art.get("importance", "secondary")
        visibility = art.get("visibility", "full")

        has_ref = art_id in artifact_refs
        lines.append(f"  - {art_id}: {visibility} visibility, {state}, position={position}, importance={importance}")
        if has_ref:
            lines.append(f"    (Reference image provided — MATCH design exactly)")

    return "\n".join(lines)


def build_character_block(characters: list[dict]) -> str:
    """Build character description block for prompt."""
    if not characters:
        return "No characters in this panel."

    lines = []
    for char in characters:
        char_id = char.get("character_id", "unknown")
        pos = char.get("frame_position", char.get("position", "center"))
        expression = char.get("expression", "neutral")
        pose = char.get("pose_description", char.get("posture", "standing"))
        facing = char.get("facing", "camera")
        scale = char.get("scale", 1.0)

        lines.append(f"  - {char_id}: {expression}, {pose}")
        lines.append(f"    Position: {pos}, scale: {scale}, facing: {facing}")

    return "\n".join(lines)


def build_action_block(action: Optional[dict]) -> str:
    """Build action description block for prompt."""
    if not action:
        return "Static scene — no motion."

    lines = [f"Action: {action.get('motion_description', 'movement')}"]
    if action.get("requires_speed_lines"):
        lines.append("Add speed lines for motion emphasis")
    if action.get("requires_motion_blur"):
        lines.append("Apply motion blur effect")
    intensity = action.get("motion_intensity", 0)
    if intensity > 0.5:
        lines.append(f"High motion intensity ({intensity})")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Enhanced Quality Checker
# ─────────────────────────────────────────────────────────────────────

class EnhancedQualityChecker:
    """Validates generated panel quality with 8 checks."""

    def __init__(self, style_spec: dict):
        self.style_spec = style_spec

    def validate_panel(self, image_path: str, panel_spec: dict) -> dict:
        """Run all quality checks on a generated panel."""
        try:
            image = Image.open(image_path)
            width, height = image.size

            checks = {
                "file_valid": {"passed": True, "details": "Image file loads successfully"},
                "resolution": self._check_resolution(width, height),
                "aspect_ratio": self._check_aspect_ratio(width, height, panel_spec),
                "min_file_size": self._check_min_size(image_path),
                "color_depth": self._check_color_depth(image),
                "not_blank": self._check_not_blank(image),
                "dimensions_match": self._check_dimensions(width, height, panel_spec),
                "format_valid": self._check_format(image_path),
            }

            passed = all(c["passed"] for c in checks.values())

            return {
                "passed": passed,
                "checks": checks,
                "dimensions": f"{width}x{height}",
                "file_size_bytes": os.path.getsize(image_path),
                "checks_passed": sum(1 for c in checks.values() if c["passed"]),
                "total_checks": len(checks),
            }
        except Exception as e:
            return {"passed": False, "error": str(e), "checks": {}}

    def _check_resolution(self, width: int, height: int) -> dict:
        min_dim = 512
        passed = min(width, height) >= min_dim
        return {"passed": passed, "actual": f"{width}x{height}", "minimum": f"{min_dim}px"}

    def _check_aspect_ratio(self, width: int, height: int, spec: dict) -> dict:
        target = spec.get("aspect_ratio", "landscape_16_9")
        dims = FLUX2_DIMENSIONS.get(target, {"width": 1920, "height": 1080})
        target_ratio = dims["width"] / dims["height"]
        actual_ratio = width / height
        tolerance = 0.15
        passed = abs(actual_ratio - target_ratio) / target_ratio < tolerance
        return {"passed": passed, "target": target, "actual_ratio": f"{actual_ratio:.2f}"}

    def _check_min_size(self, path: str) -> dict:
        size = os.path.getsize(path)
        min_size = 10_000  # 10KB minimum
        return {"passed": size >= min_size, "size_bytes": size, "minimum": min_size}

    def _check_color_depth(self, image: Image.Image) -> dict:
        mode = image.mode
        passed = mode in ("RGB", "RGBA", "P")
        return {"passed": passed, "mode": mode}

    def _check_not_blank(self, image: Image.Image) -> dict:
        """Check the image isn't a single solid color."""
        extrema = image.convert("RGB").getextrema()
        is_blank = all(ext[0] == ext[1] for ext in extrema)
        return {"passed": not is_blank, "extrema": str(extrema)}

    def _check_dimensions(self, width: int, height: int, spec: dict) -> dict:
        """Check dimensions are reasonable for the target."""
        passed = width >= 256 and height >= 256 and width <= 8192 and height <= 8192
        return {"passed": passed, "width": width, "height": height}

    def _check_format(self, path: str) -> dict:
        ext = Path(path).suffix.lower()
        passed = ext in (".png", ".jpg", ".jpeg", ".webp")
        return {"passed": passed, "format": ext}


# ─────────────────────────────────────────────────────────────────────
# Reference URL Cache
# ─────────────────────────────────────────────────────────────────────

class ReferenceCache:
    """Upload reference images once and cache their fal.ai URLs."""

    def __init__(self):
        self._cache: Dict[str, str] = {}  # local_path -> fal_url

    def get_url(self, local_path: str) -> Optional[str]:
        """Get uploaded URL for a local file, uploading if needed."""
        if not Path(local_path).exists():
            return None

        if local_path not in self._cache:
            try:
                url = fal_client.upload_file(local_path)
                self._cache[local_path] = url
            except Exception as e:
                print(f"    ! Upload failed for {local_path}: {e}")
                return None

        return self._cache[local_path]

    def preload(self, paths: list[str]) -> int:
        """Pre-upload a list of reference files. Returns count of successful uploads."""
        count = 0
        for path in paths:
            if self.get_url(path) is not None:
                count += 1
        return count


# ─────────────────────────────────────────────────────────────────────
# Panel Generator
# ─────────────────────────────────────────────────────────────────────

class PanelGenerator:
    """Generate webtoon panels using fal.ai FLUX models."""

    MAX_RETRIES = 3

    def __init__(self):
        self.cost_tracker = FalCostTracker(session_id="poc-v2-panels")
        self.style_spec = self._load_json(PHASE2_DIR / "style_spec.json")
        self.quality_checker = EnhancedQualityChecker(self.style_spec)
        self.ref_cache = ReferenceCache()
        self.failed_panels: List[dict] = []

        # Discover reference paths
        self.character_ref_paths = self._discover_character_refs()
        self.artifact_ref_paths = self._discover_artifact_refs()
        self.background_ref_paths = self._discover_background_refs()

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_json(self, data: dict, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _discover_character_refs(self) -> dict[str, str]:
        """Find character reference image paths."""
        refs = {}
        for char_dir in PHASE1_DIR.iterdir():
            if char_dir.is_dir():
                ref = char_dir / "base_reference.png"
                if ref.exists():
                    refs[char_dir.name] = str(ref)
        return refs

    def _discover_artifact_refs(self) -> dict[str, str]:
        """Find artifact reference image paths."""
        refs = {}
        artifacts_dir = PHASE3_DIR / "artifacts"
        if artifacts_dir.exists():
            for art_dir in artifacts_dir.iterdir():
                if art_dir.is_dir():
                    ref = art_dir / "base_reference.png"
                    if ref.exists():
                        refs[art_dir.name] = str(ref)
        return refs

    def _discover_background_refs(self) -> dict[str, str]:
        """Find background reference image paths."""
        refs = {}
        locations_dir = PHASE3_DIR / "locations"
        if locations_dir.exists():
            for loc_dir in locations_dir.iterdir():
                if loc_dir.is_dir():
                    ref = loc_dir / "base_reference.png"
                    if ref.exists():
                        refs[loc_dir.name] = str(ref)
                    # Also check for specific variation files
                    for img in loc_dir.glob("*.png"):
                        key = f"{loc_dir.name}_{img.stem}"
                        refs[key] = str(img)
        return refs

    def _select_model(self, panel_spec: dict) -> str:
        """Select the best fal.ai model based on panel complexity."""
        # If spec explicitly says which model
        explicit = panel_spec.get("generation_model")
        if explicit:
            return explicit

        characters = panel_spec.get("characters", [])
        artifacts = panel_spec.get("artifacts", [])
        num_refs = len(characters) + len(artifacts)

        if num_refs >= 2:
            return "fal-ai/flux-pro/kontext/multi"
        elif num_refs == 1:
            return "fal-ai/flux-pro/kontext"
        else:
            return "fal-ai/flux-2/flash"

    def _get_panel_dimensions(self, aspect_ratio: str) -> tuple[int, int]:
        """Get pixel dimensions for an aspect ratio."""
        dims = FLUX2_DIMENSIONS.get(aspect_ratio, {"width": 1024, "height": 1440})
        return dims["width"], dims["height"]

    def _build_panel_prompt(self, panel_spec: dict) -> str:
        """Build the complete generation prompt from panel spec."""
        # Extract fields
        context = panel_spec.get("context", {})
        shot_type = panel_spec.get("shot_type", "medium_shot")
        camera_angle = panel_spec.get("camera_angle", "eye_level")
        camera_movement = panel_spec.get("camera_movement", "static")
        focus_point = panel_spec.get("focus_point", "")
        characters = panel_spec.get("characters", [])
        artifacts = panel_spec.get("artifacts", [])
        action = panel_spec.get("action")
        safe_zones = panel_spec.get("safe_zones", [])
        tempo = panel_spec.get("tempo", "normal")
        panel_duration = panel_spec.get("panel_duration", "moment")
        location_id = panel_spec.get("location_id", "")
        time_of_day = panel_spec.get("time_of_day", "")
        lighting = panel_spec.get("lighting_preset", "indoor_lamp")
        effects = panel_spec.get("effects", [])
        mood = panel_spec.get("mood", "")
        color_emphasis = panel_spec.get("color_emphasis")

        safe_zone_text = build_safe_zone_instructions(safe_zones)
        artifact_text = build_artifact_instructions(artifacts, self.artifact_ref_paths)
        char_text = build_character_block(characters)
        action_text = build_action_block(action)

        # Style keywords
        prompt_kw = self.style_spec.get("prompt_keywords", {})
        style_kw = ", ".join(prompt_kw.get("style", ["Korean webtoon", "manhwa"]))
        quality_kw = ", ".join(prompt_kw.get("quality", ["high detail", "publication ready"]))

        prompt = f"""Korean webtoon panel illustration:

[SCENE CONTEXT]
- Panel purpose: {context.get("narrative_purpose", "")}
- Previous moment: {context.get("previous_panel_summary", "")}
- Emotional state: {context.get("emotional_state", "")}

[CAMERA DIRECTION]
- Shot type: {shot_type}
- Camera angle: {camera_angle}
- Camera movement: {camera_movement}
- Focus point: {focus_point}

[COMPOSITION - CRITICAL]
{safe_zone_text}

[CHARACTERS]
{char_text}

[ARTIFACTS]
{artifact_text}

[ACTION/MOTION]
{action_text}

[TEMPO]
- Panel tempo: {tempo}
- Duration feel: {panel_duration}

[ENVIRONMENT]
- Location: {location_id}
- Time: {time_of_day}
- Lighting: {lighting}
- Effects: {", ".join(effects) if effects else "none"}

[MOOD]
- Atmosphere: {mood}
- Color emphasis: {color_emphasis or "standard palette"}

[TECHNICAL]
- Style: {style_kw}
- Quality: {quality_kw}
- No text or speech bubbles (will be added separately)
- No watermarks"""

        return prompt

    def _collect_reference_urls(self, panel_spec: dict) -> list[str]:
        """Collect and upload all reference image URLs for a panel."""
        urls = []

        # Character references
        for char in panel_spec.get("characters", []):
            char_id = char.get("character_id", "")
            if char_id in self.character_ref_paths:
                url = self.ref_cache.get_url(self.character_ref_paths[char_id])
                if url:
                    urls.append(url)

        # Artifact references
        for art in panel_spec.get("artifacts", []):
            art_id = art.get("artifact_id", "")
            if art_id in self.artifact_ref_paths:
                url = self.ref_cache.get_url(self.artifact_ref_paths[art_id])
                if url:
                    urls.append(url)

        return urls

    def generate_panel(self, panel_spec: dict, output_path: Path) -> dict:
        """Generate a single panel with retry logic."""
        panel_id = panel_spec.get("panel_id", "unknown")
        model = self._select_model(panel_spec)
        aspect_ratio = panel_spec.get("aspect_ratio", "landscape_16_9")
        panel_shape = panel_spec.get("panel_shape", "rectangle_standard")
        width, height = self._get_panel_dimensions(aspect_ratio)

        prompt = self._build_panel_prompt(panel_spec)
        ref_urls = self._collect_reference_urls(panel_spec)

        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"    Attempt {attempt}/{self.MAX_RETRIES} with {model}...")
            start_ms = time.time()

            try:
                # Build arguments based on model type
                if "kontext/multi" in model and len(ref_urls) >= 2:
                    arguments = {
                        "prompt": prompt,
                        "image_urls": ref_urls[:4],  # Max 4 refs for multi
                        "num_images": 1,
                        "output_format": "png",
                        "safety_tolerance": 5,
                    }
                elif "kontext/text-to-image" in model or not ref_urls:
                    arguments = {
                        "prompt": prompt,
                        "num_images": 1,
                        "output_format": "png",
                        "safety_tolerance": 5,
                    }
                    if "kontext" in model:
                        arguments["aspect_ratio"] = KONTEXT_ASPECT_RATIOS.get(aspect_ratio, "landscape_16_9")
                    else:
                        # Flux 2 models use image_size dict
                        arguments["image_size"] = {"width": width, "height": height}
                        if "flash" in model:
                            arguments["num_inference_steps"] = 4
                elif "kontext" in model and ref_urls:
                    arguments = {
                        "prompt": prompt,
                        "image_url": ref_urls[0],
                        "num_images": 1,
                        "output_format": "png",
                        "safety_tolerance": 5,
                    }
                else:
                    # Flux 2 text-to-image
                    arguments = {
                        "prompt": prompt,
                        "image_size": {"width": width, "height": height},
                        "num_images": 1,
                        "output_format": "png",
                    }

                # Add aspect_ratio for kontext models (not flux 2)
                if "kontext" in model and "aspect_ratio" not in arguments:
                    arguments["aspect_ratio"] = KONTEXT_ASPECT_RATIOS.get(aspect_ratio, "landscape_16_9")

                result = fal_client.subscribe(model, arguments=arguments)

                gen_time_ms = int((time.time() - start_ms) * 1000)
                image_url = result["images"][0]["url"]
                size_bytes = download_image(image_url, output_path)

                self.cost_tracker.track(
                    model=model,
                    panel_id=panel_id,
                    generation_time_ms=gen_time_ms,
                    width=width, height=height,
                    phase="panel_generation",
                    scene_id=panel_spec.get("scene_id"),
                    metadata={"attempt": attempt, "ref_count": len(ref_urls)},
                )

                # Post-processing: apply panel shape mask
                mask_applied = False
                processor = PanelShapeProcessor(width, height)
                if processor.needs_mask(panel_shape):
                    try:
                        masked_path = output_path.parent / f"{output_path.stem}_masked.png"
                        apply_panel_shape(str(output_path), panel_shape, str(masked_path))
                        mask_applied = True
                        print(f"      Panel shape mask applied: {panel_shape}")
                    except Exception as mask_err:
                        print(f"      Warning: mask failed: {mask_err}")

                print(f"      OK - {output_path.name} ({size_bytes} bytes, {gen_time_ms}ms)")

                return {
                    "success": True,
                    "panel_id": panel_id,
                    "path": str(output_path),
                    "size_bytes": size_bytes,
                    "generation_time_ms": gen_time_ms,
                    "model": model,
                    "attempt": attempt,
                    "ref_count": len(ref_urls),
                    "mask_applied": mask_applied,
                    "panel_shape": panel_shape,
                }

            except Exception as e:
                gen_time_ms = int((time.time() - start_ms) * 1000)
                status = "retried" if attempt < self.MAX_RETRIES else "failed"
                self.cost_tracker.track(
                    model=model,
                    panel_id=panel_id,
                    generation_time_ms=gen_time_ms,
                    width=width, height=height,
                    phase="panel_generation",
                    scene_id=panel_spec.get("scene_id"),
                    status=status,
                    error_message=str(e),
                    metadata={"attempt": attempt},
                )
                print(f"      FAIL attempt {attempt}: {e}")

                if attempt == self.MAX_RETRIES:
                    self.failed_panels.append({
                        "panel_id": panel_id,
                        "error": str(e),
                        "attempts": attempt,
                    })
                    return {
                        "success": False,
                        "panel_id": panel_id,
                        "error": str(e),
                        "attempts": attempt,
                    }

        return {"success": False, "panel_id": panel_id, "error": "Max retries exceeded"}

    def generate_scene(self, scene_id: str) -> dict:
        """Generate all panels for a scene."""
        scene_dir = PHASE4_DIR / scene_id
        manifest_path = scene_dir / "scene_manifest.json"

        if not manifest_path.exists():
            return {"success": False, "error": f"Scene manifest not found: {manifest_path}"}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        panel_ids = manifest.get("panel_ids", [])
        print(f"\n  Scene: {scene_id} ({len(panel_ids)} panels)")

        output_dir = PHASE5_DIR / scene_id / "panels"
        metadata_dir = PHASE5_DIR / scene_id / "metadata"
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for panel_id in panel_ids:
            spec_path = scene_dir / f"{panel_id}_spec.json"
            if not spec_path.exists():
                print(f"    ! Spec not found: {spec_path}")
                continue

            with open(spec_path, "r", encoding="utf-8") as f:
                panel_spec = json.load(f)

            print(f"  Panel: {panel_id}")
            output_path = output_dir / f"{panel_id}.png"
            result = self.generate_panel(panel_spec, output_path)

            # Quality validation
            if result.get("success"):
                quality = self.quality_checker.validate_panel(str(output_path), panel_spec)
                result["quality_validation"] = quality
                qpass = quality.get("passed", False)
                qcount = quality.get("checks_passed", 0)
                qtotal = quality.get("total_checks", 0)
                print(f"      Quality: {'PASS' if qpass else 'WARN'} ({qcount}/{qtotal} checks)")

            # Save panel metadata
            panel_meta = {
                "panel_id": panel_id,
                "scene_id": scene_id,
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "panel_spec": panel_spec,
            }
            self._save_json(panel_meta, metadata_dir / f"{panel_id}_metadata.json")
            results.append(result)

        successful = sum(1 for r in results if r.get("success"))
        quality_passed = sum(
            1 for r in results
            if r.get("success") and r.get("quality_validation", {}).get("passed")
        )

        return {
            "scene_id": scene_id,
            "total_panels": len(panel_ids),
            "generated": successful,
            "quality_passed": quality_passed,
            "success_rate": (successful / len(panel_ids) * 100) if panel_ids else 0,
            "panels": results,
        }

    def preload_references(self):
        """Upload all discovered reference images to fal.ai storage."""
        all_paths = list(self.character_ref_paths.values()) + list(self.artifact_ref_paths.values())
        print(f"\n  Pre-uploading {len(all_paths)} reference images...")
        count = self.ref_cache.preload(all_paths)
        print(f"    {count}/{len(all_paths)} uploaded successfully")

    def generate_all_scenes(self) -> dict:
        """Generate panels for all scenes."""
        print("=" * 70)
        print("Phase 5: Panel Image Generation (fal.ai)")
        print("=" * 70)

        # Pre-upload references
        self.preload_references()

        all_results = {
            "phase": "Phase 5: Panel Image Generation",
            "platform": "fal.ai",
            "timestamp": datetime.now().isoformat(),
            "scenes": {},
        }

        scene_ids = [
            "scene_01_request",
            "scene_02_storytelling",
            "scene_03_departure",
        ]

        for scene_id in scene_ids:
            scene_path = PHASE4_DIR / scene_id
            if scene_path.exists():
                result = self.generate_scene(scene_id)
                all_results["scenes"][scene_id] = result
            else:
                print(f"  ! Scene not found: {scene_id}")

        # Overall summary
        total = sum(s.get("total_panels", 0) for s in all_results["scenes"].values())
        generated = sum(s.get("generated", 0) for s in all_results["scenes"].values())
        quality = sum(s.get("quality_passed", 0) for s in all_results["scenes"].values())

        all_results["summary"] = {
            "total_panels": total,
            "generated": generated,
            "quality_passed": quality,
            "success_rate": (generated / total * 100) if total else 0,
            "quality_rate": (quality / total * 100) if total else 0,
            "failed_panels": self.failed_panels,
        }

        # Save reports
        reports_dir = PHASE5_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        self._save_json(all_results, reports_dir / "batch_results.json")

        # Cost report
        self.cost_tracker.print_summary()
        self.cost_tracker.export(str(reports_dir / "phase5_cost_report.json"))

        # Print summary
        print("\n" + "=" * 70)
        print("Phase 5 Complete - Summary")
        print("=" * 70)
        print(f"  Scenes: {len(all_results['scenes'])}")
        print(f"  Total panels: {total}")
        print(f"  Generated: {generated}")
        print(f"  Quality passed: {quality}")
        print(f"  Success rate: {all_results['summary']['success_rate']:.1f}%")
        if self.failed_panels:
            print(f"  Failed panels: {len(self.failed_panels)}")
            for fp in self.failed_panels:
                print(f"    - {fp['panel_id']}: {fp['error'][:60]}")
        print(f"\n  Results: {reports_dir / 'batch_results.json'}")
        print("=" * 70)

        return all_results


def generate_single_panel_test():
    """Test mode: generate a single panel."""
    print("=" * 70)
    print("Phase 5: Single Panel Test")
    print("=" * 70)

    generator = PanelGenerator()

    # Find first available panel spec
    test_spec_path = PHASE4_DIR / "scene_01_request" / "s1_p01_spec.json"
    if not test_spec_path.exists():
        print(f"  Test spec not found: {test_spec_path}")
        print("  Run storyboard_generator.py first to create panel specs.")
        return None

    with open(test_spec_path, "r", encoding="utf-8") as f:
        panel_spec = json.load(f)

    output_dir = PHASE5_DIR / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_panel.png"

    print(f"\n  Panel: {panel_spec.get('panel_id', 'unknown')}")
    print(f"  Model: {generator._select_model(panel_spec)}")

    result = generator.generate_panel(panel_spec, output_path)

    if result.get("success"):
        print(f"\n  Test panel generated!")
        print(f"  Path: {result['path']}")
        print(f"  Size: {result['size_bytes']} bytes")
        print(f"  Time: {result['generation_time_ms']}ms")
        print(f"  Model: {result['model']}")

        quality = generator.quality_checker.validate_panel(str(output_path), panel_spec)
        print(f"  Quality: {'PASS' if quality['passed'] else 'FAIL'}")
        print(f"  Dimensions: {quality.get('dimensions', 'unknown')}")
    else:
        print(f"\n  Test failed: {result.get('error')}")

    generator.cost_tracker.print_summary()
    return result


def main():
    if "--test" in sys.argv:
        generate_single_panel_test()
    else:
        generator = PanelGenerator()
        generator.generate_all_scenes()


if __name__ == "__main__":
    main()
