"""
Phase 2: Art Style Definition Agent

Uses Anthropic Claude API to analyze novel text and generate art style specifications.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

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
                # Take first 2000 characters as sample
                excerpts.append(f"=== Chapter {i} ===\n{content[:2000]}")
    return "\n\n".join(excerpts)


def create_style_analysis_agent(client: Anthropic) -> dict:
    """
    Create a style analysis agent that analyzes novel text
    and outputs structured style recommendations.
    """
    system_prompt = """You are a webtoon art director specializing in Korean martial arts (wuxia) genre.

Your role is to:
1. Analyze novel text for visual style cues
2. Define comprehensive art style specifications
3. Create structured JSON output for style specifications
4. Ensure consistency across all visual elements

Focus on extracting:
- Mood and atmosphere from narrative descriptions
- Character visual characteristics from text descriptions
- Environmental and setting details
- Action sequence visual requirements
- Color and lighting implications from scene descriptions

Output your analysis as structured JSON."""

    return {
        "system": system_prompt,
        "client": client
    }


async def analyze_novel_style(client: Anthropic, novel_text: str) -> dict:
    """Analyze novel text and extract visual style cues."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system="""You are a webtoon art director analyzing a Korean wuxia novel for visual adaptation.
Extract visual style cues and output as JSON.""",
        messages=[
            {
                "role": "user",
                "content": f"""Analyze the following novel excerpts and extract visual style specifications.

Novel Excerpts:
{novel_text}

Provide a JSON analysis with:
1. mood_analysis: Overall mood and atmosphere extracted from text
2. character_visuals: Visual descriptions found for characters
3. environment_details: Setting and location visual cues
4. action_style: How action sequences are described
5. color_implications: Colors mentioned or implied
6. recommended_style: Your recommendations for webtoon adaptation

Output as valid JSON only."""
            }
        ]
    )

    # Parse response
    response_text = response.content[0].text

    # Try to extract JSON from response
    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        return json.loads(response_text)
    except json.JSONDecodeError:
        return {"raw_analysis": response_text}


def generate_style_prompts(client: Anthropic, style_spec: dict) -> list:
    """Generate image generation prompts based on style specification."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system="""You are an image prompt engineer for Korean webtoon generation.
Generate optimized prompts for Google Gemini image generation API based on style specifications.""",
        messages=[
            {
                "role": "user",
                "content": f"""Based on this style specification:
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
- prompt_text: the full prompt for Gemini API
- aspect_ratio: recommended ratio

Output as JSON array."""
            }
        ]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        return json.loads(response_text)
    except json.JSONDecodeError:
        return [{"raw_prompts": response_text}]


def refine_style_with_feedback(client: Anthropic, style_spec: dict, feedback: str) -> dict:
    """Refine style specification based on feedback."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system="""You are a webtoon art director refining style specifications based on feedback.
Maintain the overall style while incorporating specific adjustments.""",
        messages=[
            {
                "role": "user",
                "content": f"""Current style specification:
{json.dumps(style_spec, indent=2, ensure_ascii=False)}

Feedback to incorporate:
{feedback}

Provide an updated style specification as JSON that:
1. Preserves the core style elements
2. Incorporates the feedback changes
3. Maintains internal consistency

Output as valid JSON only."""
            }
        ]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        return json.loads(response_text)
    except json.JSONDecodeError:
        return style_spec


def save_agent_output(output: dict, filename: str):
    """Save agent output to file."""
    output_path = OUTPUT_DIR / "agent_outputs" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    """Main execution for style analysis phase."""
    print("Phase 2: Art Style Definition with Claude Agent")
    print("=" * 50)

    # Initialize client
    client = Anthropic()

    # Load novel excerpts
    print("\n1. Loading novel excerpts...")
    novel_text = load_novel_excerpts(max_chapters=5)
    print(f"   Loaded {len(novel_text)} characters of text")

    # Analyze novel style
    print("\n2. Analyzing novel for visual style cues...")
    style_analysis = analyze_novel_style(client, novel_text)
    save_agent_output(style_analysis, "novel_style_analysis.json")
    print("   Style analysis saved to agent_outputs/novel_style_analysis.json")

    # Load base style spec
    print("\n3. Loading base style specification...")
    with open(STYLE_SPEC_PATH, "r", encoding="utf-8") as f:
        style_spec = json.load(f)

    # Generate prompts
    print("\n4. Generating image prompts...")
    prompts = generate_style_prompts(client, style_spec)
    save_agent_output(prompts, "generated_prompts.json")
    print("   Prompts saved to agent_outputs/generated_prompts.json")

    # Create prompt templates file
    print("\n5. Creating prompt templates...")
    templates_path = OUTPUT_DIR / "prompt_templates.json"
    with open(templates_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "style_name": style_spec["style_name"],
            "templates": prompts
        }, f, indent=2, ensure_ascii=False)
    print(f"   Saved to {templates_path}")

    # Summary
    print("\n" + "=" * 50)
    print("Phase 2 Complete!")
    print(f"- Style analysis: agent_outputs/novel_style_analysis.json")
    print(f"- Generated prompts: agent_outputs/generated_prompts.json")
    print(f"- Prompt templates: prompt_templates.json")

    return {
        "style_analysis": style_analysis,
        "prompts": prompts,
        "style_spec": style_spec
    }


if __name__ == "__main__":
    main()
