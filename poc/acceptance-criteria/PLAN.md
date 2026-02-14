# Acceptance Criteria v2: Multimodal LLM Evaluation Plan

## Problem Statement

Current acceptance criteria are purely technical file checks. They answer "is it a valid PNG?" but never "is it a good webtoon panel?".

**v0.2.0 passed 100% of quality checks (8/8 on all 18 panels).** Yet:
- Jin Sohan turned blonde in his "angry" variation (completely different person)
- Twin base face was a modern businessman in a suit and tie
- Korean text in speech bubbles was garbled nonsense
- Panels don't tell a story - just disconnected illustrations
- Art style varies wildly between panels
- No reader could follow the narrative

**These are the actual failures** that matter for a webtoon, and none of them are caught by the current system.

---

## Current Criteria (v1 - Naive Technical)

```python
# EnhancedQualityChecker - 8 checks
1. file_valid       → Image file loads successfully
2. resolution       → min(width, height) >= 512px
3. aspect_ratio     → Matches target within 15% tolerance
4. min_file_size    → >= 10KB
5. color_depth      → RGB or RGBA
6. not_blank        → Not a single solid color
7. dimensions_match → 256 <= dim <= 8192
8. format_valid     → .png/.jpg/.jpeg/.webp
```

**These stay as Tier 1.** They're fast, free, and catch basic generation failures. But they're the floor, not the standard.

---

## Proposed 4-Tier Criteria System

### Tier 1: Technical Validity (Automated, Free)
Keep existing 8 checks. Run on every generated image instantly.

**Pass/Fail threshold**: ALL must pass. Any failure = regenerate.

### Tier 2: Per-Image Quality (Multimodal LLM, Per-Image)
Evaluate each individual image against its specification.

### Tier 3: Cross-Image Consistency (Multimodal LLM, Batch)
Compare images across the same phase or scene.

### Tier 4: Narrative & Storytelling (Multimodal LLM, Scene-Level)
Evaluate whether panels actually work as a webtoon story.

---

## Tier 2: Per-Image Quality Criteria

Run after each image generation. Feed the generated image + its spec to a multimodal LLM.

### 2.1 Character Identity Match
**What**: Does the character in the panel match their reference sheet?
**When**: Phase 1 variations, Phase 5 panels with characters
**Inputs**: [character_reference.png, generated_image.png]
**Evaluator**: Claude Sonnet (vision)

```
PROMPT:
I'm showing you two images.
Image 1 is a CHARACTER REFERENCE SHEET for a character named {character_name}.
Image 2 is a GENERATED PANEL that should contain this character.

Score the following on a 1-10 scale:
1. FACE MATCH: Does the face in Image 2 match Image 1? (bone structure, eyes, nose, mouth)
2. HAIR MATCH: Same hairstyle, color, and length?
3. CLOTHING MATCH: Same outfit style and colors?
4. BUILD MATCH: Same body type and proportions?
5. OVERALL IDENTITY: Would a reader recognize this as the same person?

Return JSON: {"face": N, "hair": N, "clothing": N, "build": N, "identity": N, "notes": "..."}

CRITICAL: Score 1-3 means clearly different person. 4-6 means recognizable but inconsistent.
7-8 means good match. 9-10 means excellent match.
```

**Threshold**: `identity >= 6` to pass. `identity >= 8` is target quality.
**Cost**: ~$0.005 per evaluation (Sonnet vision, ~500 tokens)

### 2.2 Prompt Adherence
**What**: Does the image match what was requested in the panel spec?
**When**: Every generated image
**Inputs**: [generated_image.png, panel_spec JSON]

```
PROMPT:
I'm showing you an image and the specification that was used to generate it.

SPECIFICATION:
- Shot type: {shot_type}
- Camera angle: {camera_angle}
- Characters present: {character_list}
- Location: {location_id}
- Time of day: {time_of_day}
- Mood: {mood}
- Lighting: {lighting_preset}

Score each on 1-10:
1. COMPOSITION: Does the shot type and camera angle match?
2. CHARACTERS: Are the right characters present in roughly the right positions?
3. SETTING: Does the location match?
4. MOOD: Does the atmosphere/lighting match the requested mood?
5. OVERALL ADHERENCE: How well does the image follow the spec?

Return JSON: {"composition": N, "characters": N, "setting": N, "mood": N, "adherence": N, "notes": "..."}
```

**Threshold**: `adherence >= 5` to pass. `adherence >= 7` is target.

### 2.3 Art Style Match
**What**: Does this image match the defined art style?
**When**: Every generated image (can batch)
**Inputs**: [generated_image.png, style_reference_description]

```
PROMPT:
Rate this image against the target art style:
- Target: Korean webtoon (manhwa), cel-shaded with gradient accents, clean detailed linework
- Color palette: Dark tones (#1a1a2e, #4a4a6a, #8b8ba3) with gold/red accents (#c9a227, #8b0000)
- Shading: Dramatic, high contrast
- Genre: Wuxia martial arts

Score 1-10:
1. STYLE MATCH: Does it look like a Korean webtoon?
2. LINE QUALITY: Clean linework appropriate for manhwa?
3. COLORING: Cel-shaded with gradients, not flat or photorealistic?
4. GENRE FIT: Does it fit wuxia/martial arts genre visually?

Return JSON: {"style": N, "lines": N, "coloring": N, "genre": N, "notes": "..."}
```

**Threshold**: `style >= 5` to pass. `style >= 7` is target.

### 2.4 Technical Defects
**What**: Anatomical errors, artifacts, distortions
**When**: Every image with characters

```
PROMPT:
Examine this image for technical defects common in AI-generated art:

Check for:
1. HANDS: Correct number of fingers? Natural hand poses?
2. FACE: Symmetrical? Natural features? No distortion?
3. ANATOMY: Correct proportions? Natural body structure?
4. ARTIFACTS: Any visual glitches, smearing, or unnatural elements?
5. TEXT: If any text is present, is it legible and correct? Or is it garbled?

Score each 1-10 (10 = no defects):
Return JSON: {"hands": N, "face": N, "anatomy": N, "artifacts": N, "text": N, "defects_found": ["list of specific issues"]}
```

**Threshold**: All scores >= 5. Text score < 3 = flag for text removal.

---

## Tier 3: Cross-Image Consistency

Run after completing each phase or scene. Compare multiple images together.

### 3.1 Character Consistency Across Panels
**What**: Does the same character look consistent across all their panels?
**When**: After Phase 1 (all variations), After Phase 5 (all panels per scene)
**Inputs**: [reference.png, variation1.png, variation2.png, ...] (up to 6 images)

```
PROMPT:
These images should all show the SAME character (or variations of them).
Image 1 is the base reference. Images 2-N are variations or panels.

For each image 2-N, score how well the character matches the reference:
- IDENTITY PRESERVED: Is it clearly the same person? (1-10)
- ART STYLE CONSISTENT: Same drawing style across all images? (1-10)

Return JSON: {
  "per_image": [{"image": 2, "identity": N, "style": N}, ...],
  "overall_consistency": N,
  "worst_offender": N,
  "notes": "..."
}
```

**Threshold**: `overall_consistency >= 6`, `worst_offender >= 4` (no image should be completely off).

### 3.2 Style Consistency Across Scene
**What**: Do all panels in a scene share the same art style?
**When**: After Phase 5 per scene
**Inputs**: [panel1.png, panel2.png, ..., panel6.png]

```
PROMPT:
These 6 images are sequential panels from the same webtoon scene.
They should share a consistent art style.

Score:
1. STYLE UNIFORMITY: Do they all look like they're from the same comic? (1-10)
2. COLOR CONSISTENCY: Similar color palette and grading? (1-10)
3. LINE CONSISTENCY: Similar line weight and technique? (1-10)
4. QUALITY CONSISTENCY: Similar level of detail and rendering? (1-10)

Return JSON: {"uniformity": N, "color": N, "lines": N, "quality": N, "outlier_panels": [indices], "notes": "..."}
```

**Threshold**: `uniformity >= 6`.

---

## Tier 4: Narrative & Storytelling

Run after all panels for a scene are complete. This is the **most important tier** - it answers "is this actually a webtoon?"

### 4.1 Sequential Readability
**What**: Can someone follow the story from panel to panel?
**When**: After Phase 5 per scene
**Inputs**: All panels in order + scene manifest with source text

```
PROMPT:
These images are sequential webtoon panels telling a story. I'll provide the intended narrative.

INTENDED NARRATIVE:
Scene: {scene_title}
Source text (Korean): {source_text_summary}
Panel descriptions:
1. {p1_narrative_purpose}
2. {p2_narrative_purpose}
3. {p3_narrative_purpose}
4. {p4_narrative_purpose}
5. {p5_narrative_purpose}
6. {p6_narrative_purpose}

Looking at ONLY the images (pretend you can't read the descriptions above), answer:

1. NARRATIVE CLARITY: Can you tell what's happening in each panel? (1-10)
2. SEQUENTIAL FLOW: Do the panels feel like a sequence? Does one lead to the next? (1-10)
3. CAMERA WORK: Does the "camera" move naturally between shots? (1-10)
4. CHARACTER ACTING: Do characters express emotions and reactions? (1-10)
5. PACING: Is the rhythm of panels appropriate (establishing shots vs close-ups vs action)? (1-10)
6. WEBTOON QUALITY: Could this pass as a real webtoon episode? (1-10)

Also describe what you think is happening in each panel (without referencing the descriptions).

Return JSON: {
  "narrative_clarity": N,
  "sequential_flow": N,
  "camera_work": N,
  "character_acting": N,
  "pacing": N,
  "webtoon_quality": N,
  "panel_interpretations": ["Panel 1: ...", "Panel 2: ...", ...],
  "overall_storytelling": N,
  "notes": "..."
}
```

**Threshold**: `overall_storytelling >= 5`. Below 5 means the panels fail as a webtoon.
**Cost**: ~$0.03 per scene evaluation (6 images + long prompt)

### 4.2 Emotional Arc
**What**: Does the scene convey the intended emotional progression?
**When**: After Phase 5 per scene

```
PROMPT:
These panels should convey this emotional arc: {emotional_arc_description}

Starting emotion: {start_emotion}
Climax emotion: {climax_emotion}
Ending emotion: {end_emotion}

Score:
1. EMOTIONAL RANGE: Do the panels show emotional variation? (1-10)
2. ARC PROGRESSION: Does emotion build/shift across panels? (1-10)
3. FACIAL EXPRESSION: Do character faces convey emotion? (1-10)
4. ATMOSPHERIC SUPPORT: Does lighting/color support the mood? (1-10)

Return JSON: {"range": N, "progression": N, "expression": N, "atmosphere": N, "notes": "..."}
```

**Threshold**: `range >= 4` (panels should not all feel the same).

---

## Per-Phase Gate Checks

Catch problems **early** before they propagate. Don't wait until Phase 5 to discover Phase 1 failed.

| Phase | Gate Check | Criteria | Action on Fail |
|-------|-----------|----------|---------------|
| Phase 1 | Character generation | Tier 2.1 (identity) on all variations vs base | Regenerate failed variations |
| Phase 1 | Twin differentiation | Tier 3.1 on twins: high identity similarity + clothing difference | Regenerate twins |
| Phase 3a | Background quality | Tier 2.3 (style match) on base references | Regenerate with adjusted prompt |
| Phase 3b | Artifact consistency | Tier 3.1 on artifact variations vs base | Regenerate variations |
| Phase 5 | Per-panel quality | Tier 2.1 + 2.2 + 2.4 per panel | Regenerate failed panels |
| Phase 5 | Scene consistency | Tier 3.1 + 3.2 per scene | Flag for review |
| Phase 5 | Storytelling | Tier 4.1 + 4.2 per scene | **Block release** |

---

## Evaluation Cost Budget

| Tier | Evaluations per run | Cost per eval | Total |
|------|-------------------|---------------|-------|
| Tier 1 | 77 images | $0 (automated) | $0 |
| Tier 2.1 | ~50 (chars in panels) | ~$0.005 | $0.25 |
| Tier 2.2 | 77 images | ~$0.005 | $0.39 |
| Tier 2.3 | 77 images | ~$0.003 | $0.23 |
| Tier 2.4 | ~50 (with characters) | ~$0.005 | $0.25 |
| Tier 3.1 | ~10 batch checks | ~$0.01 | $0.10 |
| Tier 3.2 | 3 scenes | ~$0.01 | $0.03 |
| Tier 4.1 | 3 scenes | ~$0.03 | $0.09 |
| Tier 4.2 | 3 scenes | ~$0.02 | $0.06 |
| **Total** | | | **~$1.40** |

Roughly 50% of image generation cost. Worthwhile given it replaces hours of manual review.

---

## Evaluator Model Choice

**Use a DIFFERENT model from the generator for evaluation.** This avoids the model "grading its own homework."

| Generator | Evaluator | Why |
|-----------|-----------|-----|
| Gemini | Claude Sonnet (vision) | Cross-model evaluation |
| FLUX (fal.ai) | Claude Sonnet (vision) | FLUX can't evaluate anyway |
| Any | Claude Sonnet 4.5 | Best vision capabilities, reasonable cost |

Claude Sonnet 4.5 is the recommended evaluator:
- Excellent vision understanding
- Structured JSON output
- Cost-effective for evaluation workload
- Independent from generation model

---

## Output Structure

### Per-Image Evaluation Report
```json
{
  "image_id": "s1_p02",
  "tier1": {"passed": true, "checks": 8, "total": 8},
  "tier2": {
    "identity_match": {"score": 7, "threshold": 6, "passed": true},
    "prompt_adherence": {"score": 6, "threshold": 5, "passed": true},
    "style_match": {"score": 8, "threshold": 5, "passed": true},
    "technical_defects": {"score": 7, "threshold": 5, "passed": true}
  },
  "overall_pass": true,
  "overall_score": 7.0
}
```

### Per-Scene Evaluation Report
```json
{
  "scene_id": "scene_01_request",
  "tier3": {
    "character_consistency": {"score": 7, "worst": 5, "passed": true},
    "style_consistency": {"score": 8, "passed": true}
  },
  "tier4": {
    "storytelling": {"score": 6, "passed": true},
    "emotional_arc": {"score": 5, "passed": true}
  },
  "scene_pass": true,
  "scene_score": 6.5
}
```

### Cross-Version Comparison Report
```json
{
  "versions_compared": ["v0.1.0", "v0.2.0", "v0.2.1"],
  "metrics": {
    "avg_identity_score": {"v0.1.0": 8.2, "v0.2.0": 4.1, "v0.2.1": "?"},
    "avg_style_consistency": {"v0.1.0": 7.5, "v0.2.0": 5.0, "v0.2.1": "?"},
    "avg_storytelling": {"v0.1.0": 5.5, "v0.2.0": 3.0, "v0.2.1": "?"},
    "cost_per_panel": {"v0.1.0": 0.15, "v0.2.0": 0.037, "v0.2.1": "?"}
  }
}
```

---

## Implementation Priority

### Phase A: Retroactive Evaluation (run on existing v0.1.0 and v0.2.0 outputs)
1. Build evaluation framework (prompts + scoring + JSON output)
2. Run Tier 2 + 3 on both existing POCs
3. Generate baseline comparison numbers
4. Validate that the criteria actually catch the known problems

### Phase B: Integrated Evaluation (build into v0.2.1 pipeline)
1. Add evaluation hooks to each phase script
2. Gate checks between phases
3. Automatic regeneration on Tier 2 failures
4. Scene-level review on Tier 4 failures

### Phase C: Dashboard/Reporting
1. Aggregate scores across versions
2. Trend tracking over iterations
3. Identify which criteria best predict "actual quality"

---

## Success Criteria for the Criteria Themselves

The evaluation system itself needs validation. It succeeds if:

1. **Known-bad images score low**: v0.2.0's blonde Jin Sohan should score < 3 on identity match
2. **Known-good images score high**: v0.1.0's consistent Dokma close-up should score > 7
3. **Tier 4 distinguishes storytelling**: v0.1.0 panels should score higher on narrative than v0.2.0
4. **Scores correlate with human judgment**: Run a small human eval to calibrate
5. **Actionable**: Low scores point to specific fixable problems, not just "bad"
