"""
Phase 2: Art Style Definition Agent for PoC v0.2.0

Uses Claude Agent SDK to analyze novel text and generate art style specifications.
Updated for fal.ai FLUX model prompts (was Gemini in v0.1.0).
"""

import os
import sys
import json
import anyio
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Agent SDK uses Claude CLI's own OAuth auth; an OAuth token in ANTHROPIC_API_KEY
# causes auth failures (sent as x-api-key instead of Bearer).
if os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-oat"):
    del os.environ["ANTHROPIC_API_KEY"]

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent
SOURCE_DIR = REPO_ROOT / "source" / "001"
OUTPUT_DIR = PROJECT_ROOT / "phase2_style"
STYLE_SPEC_PATH = OUTPUT_DIR / "style_spec.json"


def load_novel_excerpts(max_chapters: int = 3) -> str:
    """Load novel excerpts for style analysis."""
    excerpts = []
    for i in range(1, max_chapters + 1):
        file_path = SOURCE_DIR / f"{i:03d}.txt"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                excerpts.append(f"=== Chapter {i} ===\n{content[:2000]}")
    return "\n\n".join(excerpts)


def extract_json_from_response(response_text: str):
    """Extract JSON from a response that may contain markdown fences."""
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    return json.loads(response_text)


async def collect_agent_response(prompt: str, system_prompt: str) -> str:
    """Run a Claude Agent SDK query and collect the full text response."""
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        max_turns=1,
    )

    result_parts = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_parts.append(block.text)

    return "".join(result_parts)


async def analyze_novel_style(novel_text: str) -> dict:
    """Analyze novel text and extract visual style cues."""

    system_prompt = """You are a webtoon art director analyzing a Korean wuxia novel for visual adaptation.
Extract visual style cues and output as JSON.
The images will be generated using fal.ai FLUX Kontext models (high-quality image generation with reference-based editing)."""

    prompt = f"""Analyze the following novel excerpts and extract visual style specifications.

Novel Excerpts:
{novel_text}

Provide a JSON analysis with:
1. mood_analysis: Overall mood and atmosphere extracted from text
2. character_visuals: Visual descriptions found for characters
3. environment_details: Setting and location visual cues
4. action_style: How action sequences are described
5. color_implications: Colors mentioned or implied
6. recommended_style: Your recommendations for webtoon adaptation using FLUX Kontext models

Output as valid JSON only."""

    response_text = await collect_agent_response(prompt, system_prompt)

    try:
        return extract_json_from_response(response_text)
    except json.JSONDecodeError:
        return {"raw_analysis": response_text}


async def generate_style_prompts(style_spec: dict) -> list:
    """Generate fal.ai FLUX-optimized image prompts based on style spec."""

    system_prompt = """You are an image prompt engineer for Korean webtoon generation.
Generate optimized prompts for fal.ai FLUX Kontext image generation models.

Key differences from other models:
- FLUX Kontext supports reference-based editing (maintains character consistency from input image)
- Prompts should be descriptive but not overly long
- Style keywords like "Korean webtoon", "manhwa", "cel-shaded" work well
- Aspect ratios use string format: "landscape_16_9", "portrait_4_3", "square_1_1"
- safety_tolerance parameter (1-6) controls content filtering"""

    prompt = f"""Based on this style specification:
{json.dumps(style_spec, indent=2, ensure_ascii=False)}

Generate 10 image prompts for different scene types:
1. Character close-up (emotional)
2. Character close-up (action)
3. Action sequence - attack
4. Action sequence - impact
5. Dialogue scene - two characters
6. Dialogue scene - group
7. Environment - fog/mysterious
8. Environment - interior/tavern
9. Emotional moment - farewell
10. Establishing shot - tower

For each prompt, output:
- prompt_name: identifier
- scene_type: category
- prompt_text: the full prompt for fal.ai FLUX generation
- aspect_ratio: recommended fal.ai aspect ratio string
- recommended_model: which FLUX model to use (kontext_text_to_image, kontext_edit, kontext_multi, flux_2_flash)

Output as JSON array."""

    response_text = await collect_agent_response(prompt, system_prompt)

    try:
        return extract_json_from_response(response_text)
    except json.JSONDecodeError:
        return [{"raw_prompts": response_text}]


async def refine_style_with_feedback(style_spec: dict, feedback: str) -> dict:
    """Refine style specification based on feedback."""

    system_prompt = """You are a webtoon art director refining style specifications based on feedback.
Maintain the overall style while incorporating specific adjustments.
Output should be optimized for fal.ai FLUX Kontext generation."""

    prompt = f"""Current style specification:
{json.dumps(style_spec, indent=2, ensure_ascii=False)}

Feedback to incorporate:
{feedback}

Provide an updated style specification as JSON that:
1. Preserves the core style elements
2. Incorporates the feedback changes
3. Maintains internal consistency
4. Is optimized for fal.ai FLUX Kontext model prompts

Output as valid JSON only."""

    response_text = await collect_agent_response(prompt, system_prompt)

    try:
        return extract_json_from_response(response_text)
    except json.JSONDecodeError:
        return style_spec


def save_agent_output(output, filename: str):
    """Save agent output to file."""
    output_path = OUTPUT_DIR / "agent_outputs" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output_path


def create_default_style_spec() -> dict:
    """Create the default style specification for the novel."""
    return {
        "style_name": "Disciple of the Villain - Wuxia Dark",
        "base_style": {
            "genre": "Korean webtoon",
            "sub_genre": "wuxia/martial arts",
            "influence": ["manhwa", "traditional ink painting"]
        },
        "visual_elements": {
            "line_work": {
                "weight": "varied",
                "quality": "clean with intentional roughness for action",
                "emphasis_technique": "thicker lines for foreground elements"
            },
            "shading": {
                "style": "cel-shaded with gradient accents",
                "shadow_color": "#1a1a2e",
                "highlight_approach": "selective, dramatic"
            },
            "color_palette": {
                "primary": ["#1a1a2e", "#4a4a6a", "#8b8ba3"],
                "accent": ["#c9a227", "#8b0000"],
                "character_specific": {
                    "jin_sohan": ["#2d2d44", "#6b6b8a"],
                    "dokma": ["#0d0d0d", "#1a1a1a", "#333333"],
                    "uiseon": ["#f5f5f5", "#e0e0e0", "#cccccc"]
                }
            }
        },
        "atmosphere": {
            "lighting": "dramatic, high contrast",
            "mood": "mysterious, tense, dark",
            "effects": ["fog/mist", "subtle glow for mystical elements"]
        },
        "technical_specs": {
            "resolution": "1024x1024 for references, 1024x1440 for panels",
            "aspect_ratios": {
                "character_portrait": "square_1_1",
                "panel_vertical": "portrait_16_9",
                "panel_wide": "landscape_16_9",
                "full_page": "portrait_4_3"
            }
        },
        "prompt_keywords": {
            "style": ["Korean webtoon", "manhwa", "wuxia genre"],
            "atmosphere": ["dark mature tone", "mysterious", "dramatic lighting"],
            "quality": ["high detail", "publication ready", "cel-shaded with gradient accents"]
        },
        "generation_platform": "fal.ai",
        "generation_models": {
            "character_base": "fal-ai/flux-pro/kontext/text-to-image",
            "character_edit": "fal-ai/flux-pro/kontext",
            "multi_character": "fal-ai/flux-pro/kontext/multi",
            "bulk_panels": "fal-ai/flux-2/flash",
            "quality_panels": "fal-ai/flux-2-pro"
        }
    }


async def async_main():
    """Async main execution for style analysis phase."""
    test_mode = "--test" in sys.argv

    print("=" * 60)
    print("Phase 2: Art Style Definition with Claude Agent SDK")
    if test_mode:
        print("*** TEST MODE - Style spec creation only ***")
    print("=" * 60)

    # Create default style spec if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not STYLE_SPEC_PATH.exists():
        print("\n1. Creating default style specification...")
        style_spec = create_default_style_spec()
        with open(STYLE_SPEC_PATH, "w", encoding="utf-8") as f:
            json.dump(style_spec, f, indent=2, ensure_ascii=False)
        print(f"   Saved to {STYLE_SPEC_PATH}")
    else:
        print("\n1. Loading existing style specification...")
        with open(STYLE_SPEC_PATH, "r", encoding="utf-8") as f:
            style_spec = json.load(f)

    if test_mode:
        print("\n  Test mode complete - style spec created/loaded.")
        print(f"  Path: {STYLE_SPEC_PATH}")
        return {"style_spec": style_spec}

    # Load novel excerpts
    print("\n2. Loading novel excerpts...")
    novel_text = load_novel_excerpts(max_chapters=5)
    print(f"   Loaded {len(novel_text)} characters of text")

    # Analyze novel style
    print("\n3. Analyzing novel for visual style cues...")
    style_analysis = await analyze_novel_style(novel_text)
    save_agent_output(style_analysis, "novel_style_analysis.json")
    print("   Style analysis saved to agent_outputs/novel_style_analysis.json")

    # Generate prompts
    print("\n4. Generating fal.ai FLUX image prompts...")
    prompts = await generate_style_prompts(style_spec)
    save_agent_output(prompts, "generated_prompts.json")
    print("   Prompts saved to agent_outputs/generated_prompts.json")

    # Create prompt templates file
    print("\n5. Creating prompt templates...")
    templates_path = OUTPUT_DIR / "prompt_templates.json"
    with open(templates_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "style_name": style_spec["style_name"],
            "platform": "fal.ai",
            "templates": prompts
        }, f, indent=2, ensure_ascii=False)
    print(f"   Saved to {templates_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Phase 2 Complete!")
    print(f"  Style analysis: agent_outputs/novel_style_analysis.json")
    print(f"  Generated prompts: agent_outputs/generated_prompts.json")
    print(f"  Prompt templates: prompt_templates.json")

    return {
        "style_analysis": style_analysis,
        "prompts": prompts,
        "style_spec": style_spec
    }


def main():
    anyio.run(async_main)


if __name__ == "__main__":
    main()
