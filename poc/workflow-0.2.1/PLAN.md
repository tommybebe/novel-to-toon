# Workflow v0.2.1 Plan: Gemini + v0.2.0 Pipeline (A/B Test)

## Purpose

Isolate the variable that caused quality regression between v0.1.0 and v0.2.0.

We changed **two things at once**:
1. Model: Gemini → fal.ai FLUX Kontext
2. Pipeline: simple 5-phase → sophisticated 6-phase

v0.2.1 uses **Gemini + sophisticated pipeline** to determine which change caused the quality drop.

| Version | Model | Pipeline | Purpose |
|---------|-------|----------|---------|
| v0.1.0 | Gemini | Simple | Baseline |
| v0.2.0 | FLUX Kontext | Sophisticated | Full change |
| **v0.2.1** | **Gemini** | **Sophisticated** | **Isolate model variable** |

If v0.2.1 quality ≈ v0.1.0 → the model was the problem, pipeline is fine.
If v0.2.1 quality ≈ v0.2.0 → the pipeline is the problem, model doesn't matter.
If v0.2.1 quality > both → best of both worlds.

---

## API Mapping: fal.ai → Gemini

### Core Pattern Change

**v0.2.0 (fal.ai):**
```python
# Upload reference → get URL → pass URL to API → download result from CDN
ref_url = fal_client.upload_file(local_path)
result = fal_client.subscribe("fal-ai/flux-pro/kontext", arguments={
    "prompt": prompt, "image_url": ref_url, ...
})
download_image(result["images"][0]["url"], output_path)
```

**v0.2.1 (Gemini):**
```python
# Load PIL Image → pass directly to API → extract binary from response
from PIL import Image
ref_image = Image.open(local_path)
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-05-20",
    contents=[ref_image, prompt],  # Images FIRST, then text
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K"),
    )
)
# Extract image data
for part in response.candidates[0].content.parts:
    if hasattr(part, "inline_data"):
        with open(output_path, "wb") as f:
            f.write(part.inline_data.data)
```

### Model Mapping

| v0.2.0 fal.ai Model | Usage | v0.2.1 Gemini Equivalent |
|---------------------|-------|--------------------------|
| `fal-ai/flux-pro/kontext/text-to-image` | Base generation (no reference) | `gemini-2.5-flash-preview-05-20` with text-only contents |
| `fal-ai/flux-pro/kontext` | Single-reference editing | `gemini-2.5-flash-preview-05-20` with `[PIL_Image, prompt]` |
| `fal-ai/flux-pro/kontext/multi` | Multi-reference (2-4 images) | `gemini-2.5-flash-preview-05-20` with `[PIL_Image1, PIL_Image2, ..., prompt]` |
| `fal-ai/flux-2/flash` | Budget panels (no reference) | `gemini-2.5-flash-preview-05-20` with text-only (Gemini Flash is already cheap) |

### Key Differences

1. **No upload/download dance**: Gemini takes PIL Image objects directly, returns binary data
2. **Reference caching unnecessary**: No `ReferenceCache` class needed - just `Image.open()`
3. **Aspect ratios already compatible**: v0.2.0 maps internal names to `"16:9"` format which Gemini uses natively
4. **Resolution control**: Gemini supports `image_size="2K"` for high-res output (vs FLUX ~1MP)
5. **Multi-reference**: Gemini accepts multiple PIL Images in contents list (tested in v0.1.0)

---

## Script Modification Plan

### Scripts to Copy & Modify (from `poc/workflow-0.2.0/scripts/`)

#### 1. `cost_tracker.py` → Minimal changes
- Replace fal.ai pricing model with Gemini pricing
- Gemini Flash: ~$0.04/image (flat, resolution-independent for ≤2K)
- Remove megapixel-based pricing logic
- Keep same interface: `track()`, `summary()`, `export()`

#### 2. `character_generator.py` → Medium changes
- Replace `import fal_client` with `from google import genai`
- Replace `fal_client.subscribe("fal-ai/flux-pro/kontext/text-to-image", ...)` with Gemini text-to-image
- Replace `fal_client.subscribe("fal-ai/flux-pro/kontext", arguments={"image_url": ...})` with Gemini reference-based generation
- Remove `fal_client.upload_file()` calls → use `Image.open()` directly
- Remove `download_image()` → extract `inline_data.data` from response
- Keep: all character specs, prompt templates, twin workflow logic, directory structure
- Aspect ratio: use `"1:1"` directly (no mapping needed)

#### 3. `style_agent.py` → No changes
- Uses Claude Agent SDK, not image generation
- Keep as-is

#### 4. `background_generator.py` → Medium changes
- Same fal.ai → Gemini swap as character_generator
- Replace text-to-image calls for base locations
- Replace Kontext editing calls for variations
- Replace Flux 2 Flash calls for materials/lighting tests with Gemini Flash
- Keep: all location specs, material specs, lighting presets, variation definitions

#### 5. `artifact_generator.py` → Medium changes
- Same fal.ai → Gemini swap
- Replace base reference generation
- Replace Kontext editing for variations
- Keep: all artifact specs, design specs, registry generation

#### 6. `storyboard_generator.py` → Minimal changes
- Update `generation_model` field in specs from `"fal-ai/..."` to `"gemini-2.5-flash-preview-05-20"`
- Keep: all panel spec structure, safe zones, shapes, scene definitions

#### 7. `panel_shape_processor.py` → No changes
- Pure PIL/numpy processing, no API calls
- Keep as-is

#### 8. `panel_generator.py` → Major changes
- Replace entire model selection logic:
  - Remove `_select_model()` (only one model now)
  - Remove `KONTEXT_ASPECT_RATIOS` mapping (Gemini uses same format)
  - Remove `FLUX2_DIMENSIONS` mapping (Gemini uses aspect_ratio + image_size)
- Replace `_collect_reference_urls()` with `_collect_reference_images()` returning PIL Image list
- Replace `ReferenceCache` with simple `ImageCache` (cache PIL Image objects, no upload)
- Replace `fal_client.subscribe()` call with `client.models.generate_content()`
- Replace `download_image()` with inline_data extraction
- Keep: prompt construction, safe zone logic, artifact instructions, quality checker, retry logic, batch flow

### Scripts That Stay Identical
- `storyboard_generator.py` (Phase 4) - generates JSON specs, no image API
- `style_agent.py` (Phase 2) - uses Claude SDK, not image API
- `panel_shape_processor.py` - pure image processing

---

## What Must Stay Identical (for valid A/B comparison)

These must be **exactly the same** as v0.2.0 to isolate the model variable:

1. **Character specs** - same CharacterSpec definitions, same visual features, same color palettes
2. **Prompt text** - same prompt templates (the exact same words sent to the model)
3. **Location/artifact/material definitions** - identical specs
4. **Storyboard structure** - same scenes, same panel specs, same safe zones
5. **Panel spec schema** - same fields (context, safe_zones, characters with x/y %, etc.)
6. **Directory structure** - identical output paths for direct comparison
7. **Quality validation** - same 8-point checker (EnhancedQualityChecker)
8. **Phase execution order** - Phase 4 → 2 → 1 → 3a → 3b → 5

### What Will Differ (by necessity)

1. **API client** - `google.genai.Client` instead of `fal_client`
2. **Reference passing** - PIL Images instead of uploaded URLs
3. **Response extraction** - inline_data instead of CDN download
4. **Cost tracking** - Gemini pricing instead of fal.ai pricing
5. **Resolution** - Gemini outputs higher-res (up to 2K) vs Kontext (~1MP)
6. **Model selection** - single model instead of 4-model selection

---

## Cost Estimate

| Phase | Images | Model | Cost/Image | Total |
|-------|--------|-------|-----------|-------|
| Phase 1: Characters | 14 | Gemini Flash | ~$0.04 | $0.56 |
| Phase 2: Style | 0 | Claude SDK | ~$0.02 | $0.02 |
| Phase 3a: Backgrounds | 25 | Gemini Flash | ~$0.04 | $1.00 |
| Phase 3b: Artifacts | 20 | Gemini Flash | ~$0.04 | $0.80 |
| Phase 5: Panels | 18 | Gemini Flash | ~$0.04 | $0.72 |
| **Total** | **77** | | | **~$3.10** |

Comparable to v0.2.0 ($2.80) and v0.1.0 ($2.70). Well within $5 budget.

---

## Implementation Steps

1. Copy `poc/workflow-0.2.0/scripts/` → `poc/workflow-0.2.1/scripts/`
2. Create `GeminiImageClient` wrapper class with same interface:
   - `generate_text_to_image(prompt, aspect_ratio) → Path`
   - `generate_with_reference(prompt, ref_path, aspect_ratio) → Path`
   - `generate_with_multi_reference(prompt, ref_paths, aspect_ratio) → Path`
3. Modify each script to use the wrapper instead of `fal_client`
4. Update cost_tracker for Gemini pricing
5. Run Phase 4 (storyboard) first - same JSON output, just update model field
6. Run Phase 2 (style) - unchanged
7. Run Phase 1 (characters) - Gemini-powered
8. Run Phase 3a/3b (backgrounds/artifacts) - Gemini-powered
9. Run Phase 5 (panels) - Gemini-powered
10. Compare results side-by-side with v0.2.0

---

## Expected Outcomes

### If Gemini + Sophisticated Pipeline works well:
- Higher resolution panels (2K vs 1MP) with rich pipeline metadata
- Character consistency maintained (Gemini was good at this in v0.1.0)
- Safe zones, panel shapes, artifact references all preserved
- **Conclusion**: FLUX Kontext was the weak link, not the pipeline

### If it still has problems:
- The sophisticated prompt structure may be too complex for any model
- Safe zone instructions may confuse the model
- Over-specified prompts may reduce quality
- **Conclusion**: Pipeline needs simplification, test with simpler prompts next

### Key metrics to compare:
- Character identity preservation (most critical)
- Resolution and detail level
- Art style consistency across panels
- Background/environment quality
- Multi-character scene composition
- Cost per panel
- Generation speed
