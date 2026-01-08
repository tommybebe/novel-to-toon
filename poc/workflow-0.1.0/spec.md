# Proof of Concept Specification

## Overview

### Purpose

This document defines the Proof of Concept (PoC) phase for the novel-to-webtoon workflow. The PoC validates critical image generation capabilities before implementing the full production workflow.

### Objectives

1. Validate Google Gemini API image generation quality and consistency
2. Test Claude Agent SDK for art style orchestration and prompt engineering
3. Establish character design consistency across multiple generations
4. Define reusable background and material generation patterns
5. Prototype storyboard-to-panel generation workflow
6. Generate final panel images with quality control and batch processing

### Test Material

- **Source**: `source/001/` directory (10 chapter files)
- **Novel Title**: 악인의 제자 (Disciple of the Villain)
- **Genre**: Korean Wuxia/Martial Arts Fantasy
- **Key Visual Elements**:
  - Mysterious tower shrouded in fog (마선루)
  - Twin masters with contrasting aesthetics (black robes vs white robes)
  - Poison/medicine duality themes
  - Dark martial arts world atmosphere

---

## Phase 1: Character Design with Google Gemini API

### 1.1 Objectives

- Generate consistent character reference sheets using **reference image-based generation**
- Establish a two-step workflow: base image generation + reference-based variations
- Validate facial feature and clothing detail fidelity across variations
- Establish prompt patterns and style guidelines for character generation

### 1.1.1 Key Insight: Reference Image-Based Consistency

**Problem**: Prompt-only generation cannot guarantee style consistency. Each generation produces different:
- Line styles and weights
- Color palettes and shading techniques
- Character appearances (hair, facial features, clothing details)

**Solution**: Use Gemini API's reference image input capability:
- Generate a high-quality **base image** for each character first
- Use the base image as **reference input** for all subsequent variations
- Model preserves visual identity from reference image

| Model | Max Reference Images | Human Identity Preservation |
|-------|---------------------|----------------------------|
| gemini-3-pro-image-preview | 14 | Up to 5 subjects |

### 1.2 Target Characters from Test Novel

#### Primary Characters

| Character | Korean | Description | Visual Key Points |
|-----------|--------|-------------|-------------------|
| Jin Sohan | 진소한 | Main protagonist, 26 years old | Cloudy/murky eyes (from poison exposure), performance troupe background, wields twin crescent moon blades |
| Dokma | 독마 (毒魔) | Poison Master, twin brother | Black robes (흑의), dark complexion, sinister aura |
| Uiseon | 의선 (醫仙) | Medicine Sage, twin brother | White robes (백의), scholarly appearance, gentle aura |

#### Secondary Characters

| Character | Korean | Description |
|-----------|--------|-------------|
| Duhyang | 두향 | Beautiful senior sister from Sword Dance Troupe |
| Siwol | 시월 (嘶月) | Jin Sohan's childhood friend, female, one year younger |
| Chumyeon-gwi | 추면귀 (醜面鬼) | Man with disfigured face who helped the troupe |

### 1.3 Test Cases

#### Test 1.3.1: Base Character Generation (Step 1)

Generate a high-quality base reference image for each character. This will be used as reference for all variations.

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Step 1: Generate BASE reference image (no input image)
base_prompt = """
Korean webtoon style character portrait:
- Character: Jin Sohan (진소한), 26-year-old male martial artist
- Features: Cloudy, murky eye color (poison-affected), sharp handsome features
- Expression: Neutral, calm expression
- Pose: Front view, straight posture
- Attire: Dark traditional martial arts robes (dark gray/navy)
- Style: Korean webtoon (manhwa), clean detailed linework, cel-shaded with gradient accents
- Composition: Upper body portrait, centered
- Background: Simple neutral gradient
- Quality: High detail, publication ready, no text

IMPORTANT STYLE ELEMENTS TO ESTABLISH:
- Line weight: Medium with varied thickness for emphasis
- Shading: Cel-shaded with soft gradients
- Color palette: Dark muted tones (#2d2d44, #4a4a6a, #6b6b8a)
"""

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[base_prompt],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="2K"
        )
    )
)
# Save as base_reference.png
```

**Success Criteria for Base Image**:
- Clear facial features with consistent proportions
- Distinctive cloudy eye effect visible
- Appropriate martial arts aesthetic
- Clean art style that can be replicated
- High resolution (minimum 2048x2048)

#### Test 1.3.2: Reference-Based Variation Generation (Step 2)

Use the base image as reference input to generate consistent variations.

```python
from PIL import Image

# Step 2: Load base reference image
base_image = Image.open("poc/phase1_characters/jin_sohan/base_reference.png")

# Generate variation WITH reference image
variation_prompt = """
Generate the SAME character from the reference image with the following changes:
- Expression: Angry, intense expression with furrowed brows
- Pose: 3/4 view, tense posture
- Background: Dramatic dark gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette
"""

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        base_image,  # Reference image FIRST
        variation_prompt
    ],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="2K"
        )
    )
)
```

**Variations to Generate** (all using base reference):
1. Neutral expression, front view (base image itself)
2. Angry expression, 3/4 view
3. Subtle smile, side profile
4. Action pose, dynamic angle

**Success Criteria**:
- Facial features remain identical across all 4 images
- Eye color and style consistency maintained
- Clothing design and colors consistent
- Line weight and shading technique consistent
- Overall character immediately recognizable

#### Test 1.3.3: Twin Character Differentiation

For twins Dokma and Uiseon, use a special workflow:

1. Generate ONE base face reference first
2. Use that same face reference to generate both characters with different attire/atmosphere

```python
from PIL import Image

# Step 1: Generate base twin face (neutral, no clothing emphasis)
twin_base_prompt = """
Korean webtoon style character portrait:
- Character: Middle-aged male with scholarly features
- Features: Sharp intelligent eyes, defined jaw, dignified bearing
- Expression: Neutral, composed
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Face focus, minimal background
- Quality: High detail, emphasis on facial features
"""

# Generate and save as twin_base_face.png

# Step 2: Generate Dokma using twin face reference
twin_base = Image.open("poc/phase1_characters/twins/twin_base_face.png")

dokma_prompt = """
Generate the SAME face from the reference image as a full character:
- Character: Dokma (독마), Poison Master
- Expression: Cynical smirk, sinister knowing eyes
- Attire: Black traditional robes (흑의), flowing dark fabric
- Atmosphere: Dark, poisonous, mysterious
- Complexion: Slightly darker, weathered

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN)
- Art style and line weight
"""

# Step 3: Generate Uiseon using SAME twin face reference
uiseon_prompt = """
Generate the SAME face from the reference image as a full character:
- Character: Uiseon (의선), Medicine Sage
- Expression: Warm, wise gentle smile
- Attire: White traditional robes (백의), pristine and elegant
- Atmosphere: Clean, healing, serene
- Complexion: Fair, scholarly

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN - must match Dokma)
- Art style and line weight
"""
```

**Success Criteria**:
- Faces are clearly identical (twin appearance verified)
- Atmosphere and aura clearly differentiated (dark vs light)
- Clothing colors accurately rendered (black vs white)
- Character personalities visually distinct despite same face
- Art style consistent between both characters

### 1.4 API Configuration

```python
from google import genai
from google.genai import types
from PIL import Image

# Available models for image generation:
# - gemini-3-pro-image-preview: Higher quality, more references (14 max, 5 humans)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Configuration for BASE image generation (no reference)
base_config = types.GenerateContentConfig(
    response_modalities=['TEXT', 'IMAGE'],
    image_config=types.ImageConfig(
        aspect_ratio="1:1",  # Square for character portraits
        image_size="2K"      # 2048x2048 for high quality base
    )
)

# Configuration for VARIATION generation (with reference)
variation_config = types.GenerateContentConfig(
    response_modalities=['TEXT', 'IMAGE'],
    thinking_level="high",  # Better reasoning for consistency
    image_config=types.ImageConfig(
        aspect_ratio="1:1",
        image_size="2K"
    )
)

# Example: Generate variation with reference
def generate_with_reference(reference_path: str, variation_prompt: str):
    reference_image = Image.open(reference_path)

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[
            reference_image,  # Reference image MUST come first
            variation_prompt
        ],
        config=variation_config
    )
    return response
```

### 1.5 Character Generation Workflow

```
Step 1: Generate Base Reference (per character)
├── Use detailed prompt with style specifications
├── No input reference image
├── Save as base_reference.png
└── This establishes: face, hair, clothing, art style

Step 2: Generate Variations (using base reference)
├── Load base_reference.png as input
├── Prompt specifies ONLY what changes
├── Explicitly state what to MAINTAIN
└── Generate: neutral, angry, smile, action

Step 3: Validate Consistency
├── Compare all variations against base
├── Check: face, hair, clothing, line style
└── Re-generate if consistency < 80%
```

### 1.6 Deliverables

- Base reference image for each of 3 primary characters
- 4 consistent variations per character (using reference input)
- Twin character set with identical faces
- Consistency validation results
- Optimal prompt templates for base and variation generation
- Reference image workflow documentation

---

## Phase 2: Art Style Definition with Claude Agent SDK

### 2.1 Objectives

- Use Claude Agent SDK to analyze and define art style specifications
- Create structured style guides from natural language descriptions
- Generate consistent style prompts for image generation
- Test multi-turn conversation for style refinement

### 2.2 Style Categories

#### 2.2.1 Base Art Style

| Style Aspect | Options to Test |
|--------------|-----------------|
| Line Weight | Thin/crisp, Medium, Bold/thick |
| Shading | Flat/cel-shaded, Soft gradient, Cross-hatching |
| Color Palette | Muted/dark, Vibrant, Monochromatic |
| Detail Level | Minimal, Moderate, Highly detailed |

#### 2.2.2 Genre-Specific Style (Wuxia)

- Traditional Korean/Chinese aesthetic elements
- Martial arts action dynamics
- Mystical/supernatural visual effects
- Period-appropriate clothing and architecture

### 2.3 Claude Agent Implementation

#### Test 2.3.1: Style Analysis Agent

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def style_analysis_agent():
    options = ClaudeAgentOptions(
        system_prompt="""You are a webtoon art director specializing in Korean martial arts (wuxia) genre.

        Your role is to:
        1. Analyze novel text for visual style cues
        2. Define comprehensive art style specifications
        3. Create structured prompts for image generation
        4. Ensure consistency across all visual elements

        Output structured JSON for style specifications.""",
        allowed_tools=["Read"],
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("""
        Analyze the following novel excerpt and define an art style specification:

        [Novel excerpt from source/001/001.txt]

        Create a style guide that includes:
        1. Overall visual mood
        2. Color palette (hex codes)
        3. Line style recommendations
        4. Shading approach
        5. Key visual motifs
        """)
```

#### Test 2.3.2: Style Prompt Generator

```python
async def style_prompt_generator():
    options = ClaudeAgentOptions(
        system_prompt="""You are an image prompt engineer.

        Given a style specification and scene description, generate optimized prompts
        for Google Gemini image generation API.

        Focus on:
        - Consistent style keywords
        - Appropriate technical terms for image generation
        - Balance between specificity and creative freedom""",
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("""
        Given this style specification:
        - Style: Korean webtoon, wuxia genre
        - Mood: Dark, mysterious, tense
        - Colors: Deep purples, blacks, muted golds
        - Lines: Clean, varied weight for emphasis

        Generate 5 image prompts for different scene types:
        1. Character close-up
        2. Action sequence
        3. Dialogue scene
        4. Environment establishing shot
        5. Emotional moment
        """)
```

### 2.4 Style Specification Output Format

```json
{
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
    "resolution": "2048x2048 for references, 1024x1440 for panels",
    "aspect_ratios": {
      "character_portrait": "1:1",
      "panel_vertical": "9:16",
      "panel_wide": "16:9",
      "full_page": "2:3"
    }
  }
}
```

### 2.5 Deliverables

- Complete style specification JSON for test novel
- Prompt template library (minimum 10 templates)
- Claude Agent code for style analysis
- Style consistency validation checklist

---

## Phase 3: Background and Material Settings with Google Gemini API

### 3.1 Objectives

- Generate consistent location backgrounds
- Create reusable material textures and patterns
- Test environment lighting variations
- Establish background-to-panel integration workflow

### 3.2 Key Locations from Test Novel

| Location | Korean | Description | Visual Elements |
|----------|--------|-------------|-----------------|
| Magic Tower | 마선루 (魔仙樓) | Hidden tower in dense fog | Dense fog, mysterious architecture, isolated |
| Black Path Territory | 흑도 (黑道) | Criminal underworld region | Dark alleys, seedy establishments, danger |
| Sword Dance Troupe | 검무단 (劍舞團) | Performance troupe headquarters | Training grounds, peach tree, living quarters |
| Guest House/Inn | 객잔 | Common meeting place | Traditional Korean inn, dining area |
| Wolya Pavilion | 월야루 | Pleasure house/brothel | Ornate, red lanterns, entertainment district |

### 3.3 Test Cases

#### Test 3.3.1: Location Generation - Magic Tower

```python
prompt = """
Korean webtoon background illustration:
- Location: Ancient mystical tower (마선루)
- Setting: Hidden in dense, perpetual fog
- Architecture: Traditional East Asian tower, weathered stone
- Atmosphere: Mysterious, isolated, otherworldly
- Time: Twilight, diffused light through fog
- Style: Detailed background art, Korean webtoon aesthetic
- No characters, environment only
"""
```

**Success Criteria**:
- Fog effect properly rendered
- Architecture style consistent with wuxia genre
- Mood conveys mystery and isolation
- Suitable as reusable background template

#### Test 3.3.2: Location Consistency Test

Generate the same location under different conditions:

1. Magic Tower - Day/fog
2. Magic Tower - Night/fog
3. Magic Tower - Interior main hall
4. Magic Tower - Interior private quarters

**Success Criteria**:
- Architectural elements consistent across variations
- Lighting changes appropriate to time of day
- Interior/exterior relationship logical
- Style consistency maintained

#### Test 3.3.3: Material and Texture Generation

```python
# Traditional fabric texture
prompt_fabric = """
Seamless texture pattern:
- Material: Traditional Korean silk hanbok fabric
- Color: Deep black with subtle purple undertones
- Pattern: Subtle cloud motif, barely visible
- Style: Suitable for clothing in Korean webtoon
- Format: Tileable texture
"""

# Stone texture for architecture
prompt_stone = """
Seamless texture pattern:
- Material: Ancient weathered stone
- Color: Gray with moss and age marks
- Style: Suitable for traditional tower architecture
- Format: Tileable texture
"""
```

### 3.4 Lighting Presets

| Preset Name | Description | Color Temperature | Shadow Intensity |
|-------------|-------------|-------------------|------------------|
| fog_day | Diffused daylight through fog | 5500K (neutral) | Low (soft) |
| fog_night | Moonlight through fog | 4000K (cool) | Medium |
| indoor_lamp | Traditional oil lamp lighting | 2700K (warm) | High (dramatic) |
| combat_intense | High contrast action lighting | 6500K (cool white) | Very high |
| emotional_soft | Intimate conversation scenes | 3500K (warm) | Low |

### 3.5 Deliverables

- 5 key location background images
- Location variation sets (4 variations each)
- Material texture library (minimum 5 textures)
- Lighting preset documentation with examples

---

## Phase 4: Storyboarding with Gemini API

### 4.1 Objectives

- Convert novel scenes to visual panel descriptions
- Test panel composition generation
- Validate character-in-scene consistency
- Prototype full page storyboard generation

### 4.2 Storyboard Workflow

```
Novel Text → Scene Extraction → Panel Breakdown → Visual Description → Image Generation
```

### 4.3 Test Scene Selection

From `source/001/001.txt` - Select 3 key scenes:

#### Scene 1: The Request to Leave (Dialogue Heavy)

**Novel Text Summary**:
- Jin Sohan asks his masters for permission to return home
- Located in the fog-shrouded Magic Tower
- Tension between wanting to leave and masters' reluctance

**Panel Breakdown**:
| Panel | Type | Description |
|-------|------|-------------|
| 1 | Establishing | Magic Tower exterior, fog, mysterious atmosphere |
| 2 | Medium shot | Jin Sohan kneeling, speaking to masters |
| 3 | Close-up | Dokma's cynical expression, dark background |
| 4 | Close-up | Uiseon's thoughtful expression, light background |
| 5 | Two-shot | Twin masters looking at each other |
| 6 | Reaction | Jin Sohan's determined expression |

#### Scene 2: The Storytelling (Performance)

**Novel Text Summary**:
- Jin Sohan performs "Heoeon Singong" (虛言神功) - the art of storytelling
- Telling the tale of the two-headed snake and the peach
- Masters listening with interest

**Panel Breakdown**:
| Panel | Type | Description |
|-------|------|-------------|
| 1 | Wide | Jin Sohan in storytelling pose, masters listening |
| 2 | Fantasy insert | Young Jin Sohan discovering the golden peach |
| 3 | Fantasy insert | Two-headed snake wrapped around the peach |
| 4 | Close-up | Dokma's eyes widening with interest |
| 5 | Fantasy insert | Young Jin Sohan swallowing the snake's cores |
| 6 | Return to present | Jin Sohan finishing the story, subtle smile |

#### Scene 3: The Departure (Emotional)

**Novel Text Summary**:
- Masters give Jin Sohan parting gifts (weapons, medicine, money)
- Final words of advice
- Bittersweet farewell

**Panel Breakdown**:
| Panel | Type | Description |
|-------|------|-------------|
| 1 | Object focus | Twin crescent moon blades (쌍월) on table |
| 2 | Medium shot | Dokma presenting the blades |
| 3 | Object focus | White fan (백선) offered by Uiseon |
| 4 | Wide | Jin Sohan bowing deeply to both masters |
| 5 | Close-up | Masters' stoic but emotional expressions |
| 6 | Silhouette | Jin Sohan walking into the fog, departing |

### 4.4 Panel Generation Prompts

#### Test 4.4.1: Dialogue Panel

```python
prompt = """
Korean webtoon panel illustration:
- Scene: Interior of foggy mystical tower
- Characters: Young man (Jin Sohan) kneeling before two identical older men
- The man on the left wears black robes (Dokma)
- The man on the right wears white robes (Uiseon)
- Expression: Jin Sohan - determined, Masters - skeptical
- Composition: Medium shot, centered framing
- Atmosphere: Tense, formal
- Style: Korean webtoon, clean lines, dramatic shading
- Leave space at top for dialogue bubbles
- Aspect ratio: 16:9 (wide panel)
"""
```

#### Test 4.4.2: Action Panel

```python
prompt = """
Korean webtoon action panel:
- Scene: Inn interior, sudden violence
- Character: Jin Sohan throwing chopsticks as weapons
- Motion: Chopsticks flying through air with motion blur
- Target: Enemy figure (can be partially shown)
- Composition: Dynamic diagonal, speed lines
- Atmosphere: Sudden, lethal, controlled violence
- Style: Korean webtoon action sequence
- High contrast, dramatic shadows
- Aspect ratio: 9:16 (vertical panel)
"""
```

#### Test 4.4.3: Emotional Panel

```python
prompt = """
Korean webtoon emotional panel:
- Scene: Foggy morning at tower entrance
- Character: Jin Sohan from behind, walking into fog
- Silhouette composition against misty background
- Two figures (masters) watching from tower entrance
- Mood: Bittersweet farewell, new beginning
- Colors: Muted, blue-gray fog, hints of warm light
- Style: Korean webtoon, atmospheric
- Aspect ratio: 2:3 (vertical full panel)
"""
```

### 4.5 Consistency Validation

For each scene, verify:

- [ ] Character appearances match reference designs
- [ ] Location matches established background
- [ ] Lighting consistent with scene time/mood
- [ ] Style elements match defined art style
- [ ] Panel compositions follow webtoon conventions

### 4.6 Deliverables

- 3 complete scene storyboards (18 panels total)
- Panel prompt templates for each composition type
- Character-in-scene consistency report
- Storyboard-to-generation workflow documentation

---

## Phase 5: Generate Images with Google Gemini API

### 5.1 Objectives

- Generate final panel images by combining all previous phase outputs
- Integrate character references, style specifications, and backgrounds
- Test full pipeline from storyboard to finished webtoon panels
- Implement quality control and consistency validation
- Establish batch generation workflow with error handling

### 5.2 Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INPUT ASSEMBLY                                │
├─────────────────────────────────────────────────────────────────────┤
│  Storyboard Panel Spec  +  Character Refs  +  Style Guide  +  BG   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROMPT CONSTRUCTION                             │
├─────────────────────────────────────────────────────────────────────┤
│  Claude Agent SDK: Compose optimized prompt from all inputs          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      IMAGE GENERATION                                │
├─────────────────────────────────────────────────────────────────────┤
│  Google Gemini API: Generate panel image                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      QUALITY VALIDATION                              │
├─────────────────────────────────────────────────────────────────────┤
│  Check: Character consistency, style adherence, composition          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌────────┴────────┐
                          ▼                 ▼
                       [PASS]            [FAIL]
                          │                 │
                          ▼                 ▼
                    Save to output    Regenerate with
                                      adjusted prompt
```

### 5.3 Prompt Assembly System

#### 5.3.1 Composite Prompt Structure

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def assemble_generation_prompt(
    panel_spec: dict,
    character_refs: dict,
    style_guide: dict,
    background_ref: str
) -> str:
    """
    Assemble a complete image generation prompt from all components.
    """
    options = ClaudeAgentOptions(
        system_prompt="""You are an expert image prompt engineer for Korean webtoon generation.

        Combine the provided components into a single, optimized prompt for Google Gemini API.

        Rules:
        1. Prioritize character consistency details
        2. Include style keywords from the style guide
        3. Reference background elements when relevant
        4. Maintain proper aspect ratio specifications
        5. Include technical quality parameters

        Output a single cohesive prompt string.""",
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"""
        Assemble an image generation prompt from these components:

        PANEL SPECIFICATION:
        {panel_spec}

        CHARACTER REFERENCES:
        {character_refs}

        STYLE GUIDE:
        {style_guide}

        BACKGROUND CONTEXT:
        {background_ref}

        Generate the final prompt.
        """)

        async for message in client.receive_response():
            return message
```

#### 5.3.2 Prompt Template with All Components

```python
# Complete panel generation prompt template
PANEL_PROMPT_TEMPLATE = """
Korean webtoon panel illustration:

[SCENE CONTEXT]
- Panel type: {panel_type}
- Scene: {scene_description}
- Moment: {narrative_moment}

[CHARACTERS]
{character_block}

[COMPOSITION]
- Shot type: {shot_type}
- Camera angle: {camera_angle}
- Focus point: {focus_point}
- Space for dialogue: {dialogue_space}

[STYLE REQUIREMENTS]
- Art style: Korean webtoon, wuxia genre
- Line work: {line_style}
- Shading: {shading_style}
- Color palette: {color_palette}
- Mood: {mood}
- Lighting: {lighting_preset}

[TECHNICAL SPECS]
- Aspect ratio: {aspect_ratio}
- Quality: High detail, publication ready
- No text, speech bubbles will be added separately

[ATMOSPHERE]
{atmosphere_description}
"""
```

### 5.4 Test Cases

#### Test 5.4.1: Single Panel Generation (Full Pipeline)

Generate a complete panel from Scene 1: The Request to Leave

```python
from google import genai
from google.genai import types
import json

async def generate_panel(panel_spec: dict):
    """Generate a single panel with full component integration and reference images."""

    # Load pre-generated assets
    with open('poc/phase2_style/style_spec.json') as f:
        style_guide = json.load(f)

    # Load character reference images for consistency
    character_images = []
    for char in panel_spec.get('characters', []):
        char_key = char['name'].lower().replace(' ', '_')
        ref_path = f"poc/phase1_characters/{char_key}/base_reference.png"
        if os.path.exists(ref_path):
            character_images.append(Image.open(ref_path))

    # Assemble prompt using Claude Agent
    prompt = await assemble_generation_prompt(
        panel_spec=panel_spec,
        style_guide=style_guide,
        background_ref="Magic Tower interior, fog-shrouded"
    )

    # Generate image with Gemini using character references
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

    # Build contents with reference images FIRST, then prompt
    contents = character_images + [prompt]  # References before text prompt

    response = client.models.generate_content(
        model='gemini-3-pro-image-preview',  # Use pro for reference image support
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=panel_spec.get('aspect_ratio', '16:9'),
                image_size="2K"
            ),
        )
    )

    # Save result
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, 'image'):
                output_path = f"poc/phase5_generation/{panel_spec['id']}.png"
                with open(output_path, 'wb') as f:
                    f.write(part.image.data)
                return output_path

    return None

# Test panel specification
test_panel = {
    "id": "scene01_panel02",
    "panel_type": "dialogue",
    "scene_description": "Interior of Magic Tower main hall",
    "narrative_moment": "Jin Sohan kneeling, requesting permission to leave",
    "characters": [
        {"name": "Jin Sohan", "position": "center-bottom", "expression": "determined", "pose": "kneeling"},
        {"name": "Dokma", "position": "left-back", "expression": "skeptical", "pose": "seated"},
        {"name": "Uiseon", "position": "right-back", "expression": "thoughtful", "pose": "seated"}
    ],
    "shot_type": "medium shot",
    "camera_angle": "slightly low angle",
    "aspect_ratio": "16:9",
    "lighting_preset": "indoor_lamp",
    "mood": "tense, formal"
}
```

**Success Criteria**:
- All three characters present and recognizable
- Character appearances match Phase 1 references
- Style matches Phase 2 specifications
- Composition suitable for dialogue panel
- Quality sufficient for publication

#### Test 5.4.2: Sequential Panel Generation (Scene Continuity)

Generate all 6 panels from Scene 1 in sequence:

```python
async def generate_scene_panels(scene_id: str, panels: list):
    """Generate all panels for a scene with continuity checks."""

    results = []
    previous_panel = None

    for panel in panels:
        # Add continuity context from previous panel
        if previous_panel:
            panel['continuity_context'] = {
                'previous_panel_id': previous_panel['id'],
                'character_positions': previous_panel.get('character_positions'),
                'lighting_state': previous_panel.get('lighting_preset')
            }

        # Generate panel
        output_path = await generate_panel(panel)

        # Validate continuity
        if previous_panel:
            continuity_score = await validate_continuity(
                previous_panel['output_path'],
                output_path
            )
            panel['continuity_score'] = continuity_score

        panel['output_path'] = output_path
        results.append(panel)
        previous_panel = panel

    return results

# Scene 1 panels
scene1_panels = [
    {"id": "s1_p1", "panel_type": "establishing", "aspect_ratio": "16:9", ...},
    {"id": "s1_p2", "panel_type": "medium", "aspect_ratio": "16:9", ...},
    {"id": "s1_p3", "panel_type": "close-up", "aspect_ratio": "1:1", ...},
    {"id": "s1_p4", "panel_type": "close-up", "aspect_ratio": "1:1", ...},
    {"id": "s1_p5", "panel_type": "two-shot", "aspect_ratio": "16:9", ...},
    {"id": "s1_p6", "panel_type": "reaction", "aspect_ratio": "4:3", ...},
]
```

**Success Criteria**:
- All 6 panels generated successfully
- Character consistency maintained across panels
- Lighting consistency within scene
- Continuity score > 75% between adjacent panels
- No jarring visual discontinuities

#### Test 5.4.3: Action Sequence Generation

Generate the chopstick attack scene (from chapter 5):

```python
action_panels = [
    {
        "id": "action_01",
        "panel_type": "setup",
        "scene_description": "Inn interior, tense atmosphere",
        "narrative_moment": "Jin Sohan sitting calmly, enemies approaching",
        "aspect_ratio": "16:9",
        "motion_elements": None,
        "speed_lines": False
    },
    {
        "id": "action_02",
        "panel_type": "action_peak",
        "scene_description": "Chopsticks flying through air",
        "narrative_moment": "Lightning-fast throw, motion blur",
        "aspect_ratio": "9:16",
        "motion_elements": "chopsticks trajectory",
        "speed_lines": True,
        "special_effects": ["motion_blur", "impact_lines"]
    },
    {
        "id": "action_03",
        "panel_type": "impact",
        "scene_description": "Enemy struck, chopstick embedded",
        "narrative_moment": "Lethal precision revealed",
        "aspect_ratio": "1:1",
        "motion_elements": None,
        "special_effects": ["shock_effect"]
    },
    {
        "id": "action_04",
        "panel_type": "reaction",
        "scene_description": "Survivors frozen in fear",
        "narrative_moment": "Realization of Jin Sohan's power",
        "aspect_ratio": "16:9",
        "motion_elements": None,
        "atmosphere": "frozen_moment"
    }
]
```

**Success Criteria**:
- Dynamic motion conveyed in action panels
- Speed lines and motion blur properly integrated
- Character poses convey movement and power
- Impact moment has appropriate visual weight
- Sequence reads smoothly from panel to panel

#### Test 5.4.4: Emotional Scene Generation

Generate the departure scene with emotional depth:

```python
emotional_panels = [
    {
        "id": "emotion_01",
        "panel_type": "object_focus",
        "focus_object": "Twin crescent moon blades (쌍월)",
        "symbolism": "Gift representing trust and legacy",
        "lighting": "warm, reverent",
        "aspect_ratio": "16:9"
    },
    {
        "id": "emotion_02",
        "panel_type": "medium_shot",
        "characters": ["Dokma", "Jin Sohan"],
        "emotion": "gruff affection",
        "subtext": "Master hides care behind stern exterior",
        "aspect_ratio": "4:3"
    },
    {
        "id": "emotion_03",
        "panel_type": "silhouette",
        "scene_description": "Jin Sohan walking into fog, masters watching",
        "composition": "Jin Sohan small against vast fog",
        "mood": "bittersweet, hopeful",
        "color_emphasis": "blue-gray with warm hints",
        "aspect_ratio": "2:3"
    }
]
```

**Success Criteria**:
- Emotional weight conveyed through composition
- Symbolic objects rendered with appropriate reverence
- Character expressions subtle but readable
- Atmosphere matches emotional tone
- Color grading enhances mood

### 5.5 Batch Generation System

#### 5.5.1 Batch Processing Implementation

```python
import asyncio
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import json

@dataclass
class GenerationJob:
    panel_id: str
    panel_spec: dict
    status: str = "pending"  # pending, processing, completed, failed
    output_path: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3

class BatchGenerator:
    def __init__(self, gemini_client, claude_client, config):
        self.gemini = gemini_client
        self.claude = claude_client
        self.config = config
        self.results = []

    async def process_batch(self, panels: List[dict], concurrency: int = 2):
        """Process a batch of panels with rate limiting."""

        jobs = [GenerationJob(panel_id=p['id'], panel_spec=p) for p in panels]
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_limit(job: GenerationJob):
            async with semaphore:
                return await self.generate_single(job)

        tasks = [process_with_limit(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return self.compile_results(jobs, results)

    async def generate_single(self, job: GenerationJob) -> GenerationJob:
        """Generate a single panel with retry logic."""

        while job.attempts < job.max_attempts:
            job.attempts += 1
            job.status = "processing"

            try:
                # Assemble prompt
                prompt = await self.assemble_prompt(job.panel_spec)

                # Generate image
                response = await self.gemini.generate_image(prompt, job.panel_spec)

                # Save and validate
                output_path = await self.save_and_validate(response, job.panel_id)

                job.status = "completed"
                job.output_path = output_path
                return job

            except Exception as e:
                job.error = str(e)
                if job.attempts >= job.max_attempts:
                    job.status = "failed"
                else:
                    await asyncio.sleep(2 ** job.attempts)  # Exponential backoff

        return job

    def compile_results(self, jobs, results) -> dict:
        """Compile batch results into summary report."""

        completed = sum(1 for j in jobs if j.status == "completed")
        failed = sum(1 for j in jobs if j.status == "failed")

        return {
            "timestamp": datetime.now().isoformat(),
            "total_panels": len(jobs),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / len(jobs) * 100,
            "jobs": [
                {
                    "panel_id": j.panel_id,
                    "status": j.status,
                    "output_path": j.output_path,
                    "attempts": j.attempts,
                    "error": j.error
                }
                for j in jobs
            ]
        }
```

#### 5.5.2 Rate Limiting and Cost Control

```python
class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.rpm = requests_per_minute
        self.request_times = []

    async def acquire(self):
        """Wait if necessary to respect rate limits."""
        now = datetime.now()

        # Remove requests older than 1 minute
        self.request_times = [
            t for t in self.request_times
            if (now - t).seconds < 60
        ]

        if len(self.request_times) >= self.rpm:
            # Wait until oldest request expires
            wait_time = 60 - (now - self.request_times[0]).seconds
            await asyncio.sleep(wait_time)

        self.request_times.append(now)

class CostTracker:
    def __init__(self):
        self.api_calls = []

    def log_call(self, model: str, input_tokens: int, output_type: str):
        self.api_calls.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_type": output_type
        })

    def get_summary(self) -> dict:
        # Estimated costs per image (based on output tokens)
        # gemini-3-pro-image-preview: ~$0.10-0.24/image depending on resolution
        cost_per_image = {
            "gemini-3-pro-image-preview": 0.15  # Average for 2K
        }

        total_cost = sum(
            cost_per_image.get(call['model'], 0.05)
            for call in self.api_calls
        )

        return {
            "total_calls": len(self.api_calls),
            "estimated_cost_usd": total_cost,
            "calls_by_model": self._group_by_model()
        }
```

### 5.6 Quality Control System

#### 5.6.1 Automated Quality Checks

```python
from PIL import Image
import numpy as np

class QualityChecker:
    def __init__(self, style_guide: dict, character_refs: dict):
        self.style_guide = style_guide
        self.character_refs = character_refs

    async def validate_panel(self, image_path: str, panel_spec: dict) -> dict:
        """Run all quality checks on generated panel."""

        image = Image.open(image_path)

        checks = {
            "resolution": self.check_resolution(image, panel_spec),
            "aspect_ratio": self.check_aspect_ratio(image, panel_spec),
            "color_palette": self.check_color_palette(image),
            "composition": self.check_composition(image, panel_spec),
            "overall_quality": self.check_overall_quality(image)
        }

        passed = all(c['passed'] for c in checks.values())

        return {
            "passed": passed,
            "checks": checks,
            "recommendations": self.get_recommendations(checks)
        }

    def check_resolution(self, image: Image, panel_spec: dict) -> dict:
        """Verify image meets minimum resolution requirements."""
        width, height = image.size
        min_dimension = 1024

        passed = min(width, height) >= min_dimension

        return {
            "passed": passed,
            "actual": f"{width}x{height}",
            "minimum": f"{min_dimension}x{min_dimension}"
        }

    def check_aspect_ratio(self, image: Image, panel_spec: dict) -> dict:
        """Verify aspect ratio matches specification."""
        width, height = image.size
        actual_ratio = width / height

        target = panel_spec.get('aspect_ratio', '16:9')
        w, h = map(int, target.split(':'))
        target_ratio = w / h

        tolerance = 0.05
        passed = abs(actual_ratio - target_ratio) < tolerance

        return {
            "passed": passed,
            "target": target,
            "actual": f"{width}:{height}"
        }

    def check_color_palette(self, image: Image) -> dict:
        """Check if colors align with style guide palette."""
        # Extract dominant colors
        img_array = np.array(image)
        # Simplified color analysis
        avg_color = img_array.mean(axis=(0, 1))

        # Check against style guide palette
        palette = self.style_guide.get('visual_elements', {}).get('color_palette', {})

        return {
            "passed": True,  # Detailed implementation would compare against palette
            "dominant_colors": avg_color.tolist(),
            "target_palette": palette
        }

    def check_composition(self, image: Image, panel_spec: dict) -> dict:
        """Basic composition analysis."""
        # Rule of thirds check, character placement, etc.
        return {
            "passed": True,
            "notes": "Composition analysis placeholder"
        }

    def check_overall_quality(self, image: Image) -> dict:
        """Check for artifacts, blur, or other quality issues."""
        # Simplified quality check
        return {
            "passed": True,
            "notes": "Quality check placeholder"
        }

    def get_recommendations(self, checks: dict) -> list:
        """Generate recommendations based on failed checks."""
        recommendations = []

        for check_name, result in checks.items():
            if not result['passed']:
                recommendations.append({
                    "issue": check_name,
                    "suggestion": self.get_fix_suggestion(check_name, result)
                })

        return recommendations
```

#### 5.6.2 Character Consistency Validation

```python
class CharacterConsistencyChecker:
    """
    Validate character appearance consistency across panels.
    Uses reference images from Phase 1.
    """

    def __init__(self, character_refs_dir: str):
        self.refs_dir = character_refs_dir
        self.reference_features = self.load_reference_features()

    def load_reference_features(self) -> dict:
        """Load pre-computed feature vectors for each character."""
        features = {}
        for char_dir in os.listdir(self.refs_dir):
            ref_path = os.path.join(self.refs_dir, char_dir, 'reference_01.png')
            if os.path.exists(ref_path):
                features[char_dir] = self.extract_features(ref_path)
        return features

    async def validate_character_in_panel(
        self,
        panel_path: str,
        expected_characters: List[str]
    ) -> dict:
        """
        Check if characters in panel match their references.
        """
        # This would use image analysis/ML in production
        # Placeholder for PoC

        return {
            "characters_detected": expected_characters,
            "consistency_scores": {
                char: 0.85  # Placeholder score
                for char in expected_characters
            },
            "overall_consistency": 0.85,
            "passed": True
        }
```

### 5.7 Output Organization

#### 5.7.1 Generated Assets Structure

```
poc/phase5_generation/
├── scene_01_request/
│   ├── panels/
│   │   ├── s1_p01_establishing.png
│   │   ├── s1_p02_medium.png
│   │   ├── s1_p03_closeup_dokma.png
│   │   ├── s1_p04_closeup_uiseon.png
│   │   ├── s1_p05_twoshot.png
│   │   └── s1_p06_reaction.png
│   ├── metadata/
│   │   ├── s1_p01_metadata.json
│   │   └── ...
│   └── scene_manifest.json
├── scene_02_storytelling/
│   └── ...
├── scene_03_departure/
│   └── ...
├── action_sequence/
│   └── ...
├── reports/
│   ├── batch_results.json
│   ├── quality_report.json
│   ├── consistency_report.json
│   └── cost_summary.json
└── failed/
    ├── retry_queue.json
    └── failed_panels/
```

#### 5.7.2 Panel Metadata Format

```json
{
  "panel_id": "s1_p02_medium",
  "scene_id": "scene_01_request",
  "sequence_number": 2,
  "generation": {
    "timestamp": "2025-12-30T14:32:00Z",
    "model": "gemini-3-pro-image-preview",
    "prompt_hash": "abc123...",
    "attempts": 1,
    "generation_time_ms": 3420
  },
  "specifications": {
    "panel_type": "medium_shot",
    "aspect_ratio": "16:9",
    "characters": ["Jin Sohan", "Dokma", "Uiseon"],
    "location": "Magic Tower interior"
  },
  "quality_validation": {
    "passed": true,
    "resolution_check": true,
    "color_palette_match": 0.92,
    "character_consistency": 0.88
  },
  "file_info": {
    "path": "scene_01_request/panels/s1_p02_medium.png",
    "size_bytes": 1245678,
    "dimensions": "2048x1152"
  }
}
```

### 5.8 Deliverables

- Complete panel images for all 3 test scenes (18+ panels)
- 4-panel action sequence with motion effects
- 3-panel emotional sequence with atmosphere
- Batch generation system code
- Quality validation reports
- Character consistency analysis
- API usage and cost report
- Failure analysis and retry logs
- Complete generation pipeline documentation

---

## Implementation Plan

### Phase Timeline

| Phase | Focus Area | Key Deliverable |
|-------|------------|-----------------|
| Phase 1 | Character Design | Character reference sheets |
| Phase 2 | Art Style | Style specification JSON |
| Phase 3 | Backgrounds | Location and material library |
| Phase 4 | Storyboarding | Panel specifications and layouts |
| Phase 5 | Image Generation | Final panel images with quality validation |

### Technical Requirements

#### Environment Setup

```bash
# Required packages
pip install google-genai
pip install claude-agent-sdk
pip install python-dotenv
pip install pillow
```

#### Environment Variables

```bash
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### File Structure for PoC

```
novel-to-toon/
├── poc/
│   ├── phase1_characters/
│   │   ├── jin_sohan/
│   │   │   ├── reference_01.png
│   │   │   ├── reference_02.png
│   │   │   ├── consistency_test/
│   │   │   └── metadata.json
│   │   ├── dokma/
│   │   ├── uiseon/
│   │   └── prompts.md
│   ├── phase2_style/
│   │   ├── style_spec.json
│   │   ├── prompt_templates.json
│   │   └── agent_outputs/
│   ├── phase3_backgrounds/
│   │   ├── locations/
│   │   │   ├── magic_tower/
│   │   │   ├── inn/
│   │   │   └── black_path/
│   │   ├── materials/
│   │   └── lighting_tests/
│   ├── phase4_storyboard/
│   │   ├── scene_01_request/
│   │   ├── scene_02_storytelling/
│   │   ├── scene_03_departure/
│   │   └── panel_templates.json
│   ├── phase5_generation/
│   │   ├── scene_01_request/
│   │   │   ├── panels/
│   │   │   └── metadata/
│   │   ├── scene_02_storytelling/
│   │   ├── scene_03_departure/
│   │   ├── action_sequence/
│   │   ├── reports/
│   │   │   ├── batch_results.json
│   │   │   ├── quality_report.json
│   │   │   ├── consistency_report.json
│   │   │   └── cost_summary.json
│   │   └── failed/
│   └── results/
│       ├── consistency_report.md
│       ├── api_usage_log.json
│       └── recommendations.md
├── scripts/
│   ├── character_generator.py
│   ├── style_agent.py
│   ├── background_generator.py
│   ├── storyboard_generator.py
│   └── panel_generator.py
└── docs/
    └── poc-specification.md (this file)
```

---

## Success Criteria

### Phase 1: Character Design

- [ ] 3 primary characters have reference sheets
- [ ] Character consistency score > 80% across variations
- [ ] Distinct visual identity for each character
- [ ] Prompt templates documented and reproducible

### Phase 2: Art Style

- [ ] Complete style specification JSON created
- [ ] Claude Agent successfully analyzes novel text
- [ ] Prompt templates generate consistent style
- [ ] Style guide usable for all subsequent phases

### Phase 3: Backgrounds

- [ ] 5 key locations generated
- [ ] Location consistency maintained across variations
- [ ] Material textures suitable for integration
- [ ] Lighting presets documented with examples

### Phase 4: Storyboarding

- [ ] 18 panel specifications created across 3 scenes
- [ ] Panel layouts follow webtoon conventions
- [ ] Scene-to-panel conversion workflow documented
- [ ] Panel templates ready for generation

### Phase 5: Image Generation

- [ ] 18+ panels generated from storyboards
- [ ] Character consistency score > 80% across panels
- [ ] Quality validation pass rate > 90%
- [ ] Action sequence (4 panels) with motion effects
- [ ] Emotional sequence (3 panels) with atmosphere
- [ ] Batch generation system functional
- [ ] API cost tracking implemented
- [ ] Failed generation retry system tested

### Overall PoC Success

- [ ] All 5 phases completed with deliverables
- [ ] End-to-end pipeline validated (novel → panels)
- [ ] Technical recommendations documented
- [ ] API cost estimates calculated
- [ ] Production workflow design finalized
- [ ] Quality benchmarks established

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Character inconsistency | High | **Use base reference images as input for all variations** |
| API rate limiting | Medium | Implement retry logic, batch processing |
| Style drift across panels | High | Use reference images + strict prompt templates |
| Korean text rendering | Medium | Test early, use romanization fallback |

### Content Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Violence depiction limits | Medium | Review safety settings, adjust prompts |
| Cultural accuracy | Low | Research traditional elements, validate |

---

## Appendix

### A. Sample Novel Excerpts for Testing

#### Excerpt 1: Character Introduction

```
흑의(黑衣)를 걸친 사내는 독마(毒魔)라 불렸는데 낯빛이 어두웠고,
백의(白依)를 입은 사내는 의선(醫仙)이라 불렸는데 학사 같은 분위기가 풍겼다.
```

**Translation**: The man in black robes was called Dokma (Poison Demon), with a dark complexion, while the man in white robes was called Uiseon (Medicine Sage), with a scholarly atmosphere.

#### Excerpt 2: Setting Description

```
안개가 자욱한 마선루(魔仙樓).
외부에서 보면 사람이 있다는 것조차 보이지 않을 정도로 짙은 안개 속에
마선(魔仙)이라는 별호로 불리는 기인이사 형제가 은거하고 있었다.
```

**Translation**: The fog-shrouded Magic Tower. Hidden in fog so thick that one couldn't even tell people lived there, the eccentric twin brothers known as the Magic Sages lived in seclusion.

#### Excerpt 3: Action Scene

```
진소한의 잔잔한 목소리가 흘러나왔다.
"두향……."
...
무언가가 오제철의 눈앞을 스치고 지나갔다.
이어서 푹 하는 소리가 들렸다.
깜짝 놀란 오제철이 멱살을 쥐고 있던 오제광을 다시 바라보자,
그의 이마에 젓가락이 박혀 있었다.
```

**Translation**: Jin Sohan's calm voice flowed out. "Duhyang..." Something flashed past Oh Je-cheol's eyes. Then came a 'thud' sound. When the startled Oh Je-cheol looked back at Oh Je-gwang, whom he had been grabbing by the collar, a chopstick was embedded in his forehead.

### B. Gemini API Model Recommendations

| Use Case | Recommended Model | Rationale |
|----------|-------------------|-----------|
| Character base reference | gemini-3-pro-image-preview | Highest quality, supports reference images |
| Character variations | gemini-3-pro-image-preview | Up to 14 reference images, 5 human subjects |
| Quick iterations | gemini-3-pro-image-preview | Supports image generation with references |
| Background art | gemini-3-pro-image-preview | High quality environments |
| Panel generation | gemini-3-pro-image-preview | Context-aware, flexible aspect ratios |

**Reference Image Capabilities**:

| Model | Max References | Human Identity | Resolution |
|-------|---------------|----------------|------------|
| gemini-3-pro-image-preview | 14 | Up to 5 | 1K, 2K, 4K |

### C. Claude Agent SDK Model Recommendations

| Use Case | Approach | Notes |
|----------|----------|-------|
| Style analysis | ClaudeSDKClient with Read tool | Access to novel files |
| Prompt generation | query() function | Simple, stateless prompts |
| Iterative refinement | Multi-turn session | Maintains context for adjustments |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-30 | Initial | Created PoC specification document |
| 1.1 | 2025-12-30 | Update | Added Phase 5: Generate Images with full pipeline |
| 1.2 | 2025-12-30 | Update | **Major revision**: Added reference image-based generation workflow for character consistency. Replaced prompt-only approach with two-step workflow (base image + reference-based variations). Updated model recommendations to use gemini-3-pro-image-preview. Removed imagen models. |
| 1.3 | 2025-12-30 | Update | Standardized on gemini-3-pro-image-preview for all image generation tasks. Removed gemini-2.5-flash-image references. |
