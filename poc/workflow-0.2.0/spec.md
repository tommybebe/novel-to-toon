# Proof of Concept Specification v2

## Overview

### Purpose

This document defines the revised Proof of Concept (PoC) phase for the novel-to-webtoon workflow. Version 2 incorporates critical feedback from the initial PoC run, addressing artifact consistency, enhanced storyboard specifications, and panel composition requirements.

### Key Changes from v1

| Area | v1 Issue | v2 Solution |
|------|----------|-------------|
| Artifact Consistency | Same artifacts (e.g., twin crescent moon blades) looked different across panels | Dedicated artifact reference workflow similar to characters |
| Storyboard Detail | Insufficient panel specifications | Enhanced specs with position, posture, action, tempo, context |
| Camera Direction | Basic shot types only | Full camera angle specifications for directing effect |
| Panel Shapes | All plain rectangles | Variable panel shapes based on scene direction |
| Speech Bubbles | Areas getting cut off or empty | Safe zone specifications for dialogue placement |
| Cost | ~$12 for POC, not sustainable | Hybrid model strategy (80% Flash + 20% Pro), 1K resolution, batch processing |
| Spending Tracking | No visibility into API costs | Integrated cost tracking with per-call logging and session summaries |

### Objectives

1. Validate Google Gemini API image generation quality and consistency
2. Test Claude Agent SDK for art style orchestration and prompt engineering
3. Establish character design consistency across multiple generations
4. **NEW: Establish artifact design consistency with reference sheets**
5. Define reusable background and material generation patterns
6. Prototype detailed storyboard-to-panel generation workflow
7. **NEW: Implement variable panel shapes and speech bubble safe zones**
8. Generate final panel images with quality control and batch processing
9. Reduce API costs by 70-80% through model selection and optimization
10. Implement spending tracking and cost visibility

### Test Material

- **Source**: `source/001/` directory (10 chapter files)
- **Novel Title**: Disciple of the Villain
- **Genre**: Korean Wuxia/Martial Arts Fantasy
- **Key Visual Elements**:
  - Mysterious tower shrouded in fog
  - Twin masters with contrasting aesthetics (black robes vs white robes)
  - Poison/medicine duality themes
  - Dark martial arts world atmosphere
  - **Important Artifacts**: Twin crescent moon blades, white fan, medicine pouches

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
| Jin Sohan | - | Main protagonist, 26 years old | Cloudy/murky eyes (from poison exposure), performance troupe background, wields twin crescent moon blades |
| Dokma | - | Poison Master, twin brother | Black robes, dark complexion, sinister aura |
| Uiseon | - | Medicine Sage, twin brother | White robes, scholarly appearance, gentle aura |

#### Secondary Characters

| Character | Korean | Description |
|-----------|--------|-------------|
| Duhyang | - | Beautiful senior sister from Sword Dance Troupe |
| Siwol | - | Jin Sohan's childhood friend, female, one year younger |
| Chumyeon-gwi | - | Man with disfigured face who helped the troupe |

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
- Character: Jin Sohan, 26-year-old male martial artist
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
- Character: Dokma, Poison Master
- Expression: Cynical smirk, sinister knowing eyes
- Attire: Black traditional robes, flowing dark fabric
- Atmosphere: Dark, poisonous, mysterious
- Complexion: Slightly darker, weathered

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN)
- Art style and line weight
"""

# Step 3: Generate Uiseon using SAME twin face reference
uiseon_prompt = """
Generate the SAME face from the reference image as a full character:
- Character: Uiseon, Medicine Sage
- Expression: Warm, wise gentle smile
- Attire: White traditional robes, pristine and elegant
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

### 1.4 Deliverables

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

## Phase 3: Backgrounds and Artifact Settings with Google Gemini API

### 3.1 Objectives

- Generate consistent location backgrounds
- Create reusable material textures and patterns
- Test environment lighting variations
- Establish background-to-panel integration workflow
- **NEW: Generate artifact reference sheets with multiple angles/lighting**
- **NEW: Establish artifact consistency workflow similar to characters**

### 3.2 Key Locations from Test Novel

| Location | Korean | Description | Visual Elements |
|----------|--------|-------------|-----------------|
| Magic Tower | - | Hidden tower in dense fog | Dense fog, mysterious architecture, isolated |
| Black Path Territory | - | Criminal underworld region | Dark alleys, seedy establishments, danger |
| Sword Dance Troupe | - | Performance troupe headquarters | Training grounds, peach tree, living quarters |
| Guest House/Inn | - | Common meeting place | Traditional Korean inn, dining area |
| Wolya Pavilion | - | Pleasure house/brothel | Ornate, red lanterns, entertainment district |

### 3.3 Important Artifacts Registry

**NEW SECTION**: Artifacts that appear multiple times and require consistent visual representation.

| Artifact | Korean | Description | Visual Key Points | Appears In |
|----------|--------|-------------|-------------------|------------|
| Twin Crescent Moon Blades | - | Jin Sohan's signature weapons | Curved crescent shape, matching pair, wrapped handles, dark metal | Scenes 3, 5, 7, 10 |
| White Fan | - | Gift from Uiseon | Elegant white folding fan, possibly with subtle pattern | Scenes 3, 8 |
| Poison Pouch | - | Dokma's medicine/poison container | Dark leather, aged appearance, mysterious contents | Scenes 2, 3 |
| Golden Peach | - | Mystical fruit from backstory | Luminous golden color, supernatural glow | Scene 2 (flashback) |
| Two-Headed Snake | - | Mythical creature from backstory | Distinct dual heads, serpentine body | Scene 2 (flashback) |

### 3.4 Artifact Reference Sheet Workflow

**NEW WORKFLOW**: Following the same two-step process as character generation.

#### 3.4.1 Artifact Base Reference Generation

```python
from google import genai
from google.genai import types

# Step 1: Generate BASE artifact reference
artifact_base_prompt = """
Korean webtoon style weapon illustration:
- Object: Twin Crescent Moon Blades (paired weapons)
- Design: Curved crescent-shaped blades attached to handles
- Handle: Wrapped leather grip, dark color, decorative pommel
- Blade: Dark steel with subtle engravings, crescent moon curve
- Material appearance: Aged but well-maintained metal
- Style: Korean webtoon (manhwa), clean detailed linework
- Composition: Both weapons displayed, showing full design
- Background: Simple neutral, focus on weapons
- Lighting: Clear, even lighting to show all details
- Quality: High detail, publication ready

IMPORTANT DESIGN ELEMENTS TO ESTABLISH:
- Exact blade curvature and proportions
- Handle wrap pattern and color
- Pommel and guard design
- Relative size of blade to handle
- Surface finish and any engravings
"""

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[artifact_base_prompt],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        )
    )
)
# Save as twin_blades_base_reference.png
```

#### 3.4.2 Artifact Variation Generation

Generate the same artifact in different contexts (to be used as reference when the artifact appears in panels).

```python
from PIL import Image

# Load artifact base reference
artifact_ref = Image.open("poc/phase3_artifacts/twin_blades/base_reference.png")

# Variation 1: Held in hand
held_prompt = """
Generate the EXACT SAME weapons from the reference image:
- Context: Being held by a martial artist (hands visible, face cropped)
- Pose: Combat ready stance, one blade raised, one lowered
- Lighting: Dramatic side lighting

MAINTAIN EXACTLY from reference:
- Blade shape, curvature, and proportions
- Handle design, wrap pattern, and pommel
- Metal finish and any engravings
- Overall weapon dimensions
"""

# Variation 2: Action blur
action_prompt = """
Generate the EXACT SAME weapons from the reference image:
- Context: Mid-swing motion blur
- Effect: Motion lines, dynamic angle
- Lighting: High contrast action lighting

MAINTAIN EXACTLY from reference:
- Blade shape and design (even with motion blur)
- Handle design consistency
- Metal color and finish
"""

# Variation 3: Different lighting
lighting_prompt = """
Generate the EXACT SAME weapons from the reference image:
- Context: Displayed on wooden table
- Lighting: Warm lamplight (indoor scene)
- Atmosphere: Intimate, reverent presentation

MAINTAIN EXACTLY from reference:
- All design elements
- Proportions and dimensions
- Blade and handle details
"""
```

#### 3.4.3 Artifact Reference Sheet Structure

```
poc/phase3_artifacts/
├── twin_crescent_blades/
│   ├── base_reference.png          # Primary reference, clear view
│   ├── variation_held.png          # In-hand context
│   ├── variation_action.png        # Motion/action context
│   ├── variation_warm_light.png    # Different lighting
│   ├── variation_cool_light.png    # Different lighting
│   ├── design_spec.json            # Detailed design specifications
│   └── metadata.json
├── white_fan/
│   ├── base_reference.png
│   ├── variation_open.png
│   ├── variation_closed.png
│   ├── variation_held.png
│   └── metadata.json
├── poison_pouch/
│   └── ...
└── artifact_registry.json          # Master list of all artifacts
```

#### 3.4.4 Artifact Design Specification Format

```json
{
  "artifact_id": "twin_crescent_blades",
  "name": "Twin Crescent Moon Blades",
  "korean_name": "-",
  "owner": "Jin Sohan",
  "significance": "Signature weapons, gift from masters",
  "design_spec": {
    "type": "paired_weapons",
    "blade": {
      "shape": "crescent_curve",
      "length_cm": 35,
      "curvature_degrees": 120,
      "material": "dark_steel",
      "finish": "matte_with_subtle_sheen",
      "engravings": "subtle_cloud_pattern"
    },
    "handle": {
      "length_cm": 20,
      "wrap_material": "dark_leather",
      "wrap_pattern": "crossed_diagonal",
      "pommel": "rounded_cap_with_ring"
    },
    "guard": {
      "style": "minimal_curved",
      "material": "matching_dark_steel"
    }
  },
  "color_palette": {
    "blade": "#3a3a4a",
    "handle_wrap": "#2d2520",
    "pommel": "#4a4a5a"
  },
  "reference_images": [
    "base_reference.png",
    "variation_held.png",
    "variation_action.png"
  ],
  "scenes_appearing": ["scene_03", "scene_05", "scene_07", "scene_10"]
}
```

### 3.5 Background Test Cases

#### Test 3.5.1: Location Generation - Magic Tower

```python
prompt = """
Korean webtoon background illustration:
- Location: Ancient mystical tower
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

#### Test 3.5.2: Location Consistency Test

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

### 3.6 Lighting Presets

| Preset Name | Description | Color Temperature | Shadow Intensity |
|-------------|-------------|-------------------|------------------|
| fog_day | Diffused daylight through fog | 5500K (neutral) | Low (soft) |
| fog_night | Moonlight through fog | 4000K (cool) | Medium |
| indoor_lamp | Traditional oil lamp lighting | 2700K (warm) | High (dramatic) |
| combat_intense | High contrast action lighting | 6500K (cool white) | Very high |
| emotional_soft | Intimate conversation scenes | 3500K (warm) | Low |

### 3.7 Deliverables

- 5 key location background images
- Location variation sets (4 variations each)
- Material texture library (minimum 5 textures)
- Lighting preset documentation with examples
- **NEW: Artifact reference sheets for 5 key artifacts**
- **NEW: Artifact design specifications (JSON)**
- **NEW: Artifact consistency validation results**

---

## Phase 4: Enhanced Storyboarding with Detailed Panel Specifications

### 4.1 Objectives

- Convert novel scenes to visual panel descriptions
- **NEW: Create comprehensive panel specifications with positioning and directing details**
- **NEW: Include camera angle specifications for maximum directing effect**
- **NEW: Specify panel shapes based on scene direction**
- **NEW: Define speech bubble safe zones**
- Validate character-in-scene consistency
- Prototype full page storyboard generation

### 4.2 Enhanced Storyboard Workflow

```
Novel Text
    -> Scene Extraction
    -> Context Analysis (what happened before)
    -> Panel Breakdown with Directing Intent
    -> Detailed Panel Specification
    -> Panel Shape Selection
    -> Safe Zone Definition
    -> Image Generation Ready
```

### 4.3 Enhanced Panel Specification Data Structure

**NEW DATA STRUCTURE**: Comprehensive panel specification format.

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

class ShotType(Enum):
    EXTREME_CLOSE_UP = "extreme_close_up"  # Eyes, mouth, small detail
    CLOSE_UP = "close_up"                  # Face only
    MEDIUM_CLOSE_UP = "medium_close_up"    # Head and shoulders
    MEDIUM_SHOT = "medium_shot"            # Waist up
    MEDIUM_WIDE = "medium_wide"            # Knees up
    WIDE_SHOT = "wide_shot"                # Full body with environment
    ESTABLISHING = "establishing"           # Environment focus, characters small

class CameraAngle(Enum):
    EYE_LEVEL = "eye_level"          # Neutral, conversational
    LOW_ANGLE = "low_angle"          # Power, dominance, heroic
    HIGH_ANGLE = "high_angle"        # Vulnerability, insignificance
    DUTCH_ANGLE = "dutch_angle"      # Tension, disorientation
    BIRDS_EYE = "birds_eye"          # Overview, god's view
    WORMS_EYE = "worms_eye"          # Extreme power, towering

class CameraMovement(Enum):
    STATIC = "static"                # No implied movement
    ZOOM_IN = "zoom_in"              # Drawing attention, revelation
    ZOOM_OUT = "zoom_out"            # Context reveal, isolation
    PAN_LEFT = "pan_left"            # Following action
    PAN_RIGHT = "pan_right"          # Following action
    TILT_UP = "tilt_up"              # Revealing height, awe
    TILT_DOWN = "tilt_down"          # Revealing depth, dread

class PanelShape(Enum):
    RECTANGLE_WIDE = "rectangle_wide"        # 16:9, landscape, calm
    RECTANGLE_STANDARD = "rectangle_standard" # 4:3, dialogue
    RECTANGLE_TALL = "rectangle_tall"        # 9:16, vertical, power
    SQUARE = "square"                        # 1:1, balanced
    DIAGONAL_LEFT = "diagonal_left"          # Action, tension
    DIAGONAL_RIGHT = "diagonal_right"        # Action, tension
    IRREGULAR_JAGGED = "irregular_jagged"    # Chaos, impact
    BORDERLESS = "borderless"                # Emotional overflow
    CIRCULAR = "circular"                    # Memory, focus
    INSET = "inset"                         # Detail, reaction

class Tempo(Enum):
    SLOW = "slow"           # Emotional, contemplative (fewer panels, larger)
    NORMAL = "normal"       # Standard pacing
    FAST = "fast"           # Action, tension (more panels, smaller)
    FREEZE = "freeze"       # Dramatic pause (single large panel)

@dataclass
class CharacterPosition:
    character_id: str
    frame_position: str          # "left", "center", "right", "background", "foreground"
    x_percent: float             # 0-100, horizontal position
    y_percent: float             # 0-100, vertical position
    scale: float                 # 1.0 = normal, 0.5 = half size (distant)
    posture: str                 # "standing", "sitting", "kneeling", "lying", "crouching"
    pose_description: str        # Detailed pose
    expression: str              # Emotional expression
    facing: str                  # "camera", "left", "right", "away"

@dataclass
class ActionDescription:
    action_type: str             # "static", "moving", "attacking", "reacting"
    motion_description: str      # What movement is happening
    motion_direction: str        # Direction of movement
    motion_intensity: float      # 0-1, affects motion blur/speed lines
    requires_speed_lines: bool
    requires_motion_blur: bool
    impact_point: Optional[str]  # Where impact occurs if applicable

@dataclass
class ArtifactPlacement:
    artifact_id: str             # References artifact registry
    position: str                # Where in frame
    visibility: str              # "full", "partial", "silhouette"
    state: str                   # "resting", "held", "in_motion", "displayed"
    lighting_context: str        # How lighting affects it
    importance: str              # "focus", "secondary", "background"

@dataclass
class SpeechBubbleSafeZone:
    zone_id: str
    position: str                # "top_left", "top_center", "top_right", etc.
    x_percent: float             # Starting X position (0-100)
    y_percent: float             # Starting Y position (0-100)
    width_percent: float         # Width of safe zone (0-100)
    height_percent: float        # Height of safe zone (0-100)
    speaker_id: Optional[str]    # Who is speaking
    bubble_type: str             # "speech", "thought", "narration", "sfx"
    text_preview: Optional[str]  # Preview of dialogue for sizing

@dataclass
class PanelContext:
    previous_panel_summary: str  # What happened in previous panel
    scene_context: str           # Where we are in the story
    emotional_state: str         # Current emotional tone
    narrative_purpose: str       # What this panel accomplishes

@dataclass
class EnhancedPanelSpec:
    # Basic identification
    panel_id: str
    scene_id: str
    sequence_number: int

    # Context (NEW)
    context: PanelContext

    # Visual Composition
    shot_type: ShotType
    camera_angle: CameraAngle
    camera_movement: CameraMovement
    focus_point: str             # What the eye should be drawn to
    depth_of_field: str          # "shallow", "medium", "deep"

    # Panel Shape and Layout (NEW)
    panel_shape: PanelShape
    aspect_ratio: str            # Specific ratio for generation
    page_position: Optional[str] # Where on page if known
    bleed: bool                  # Extends to page edge

    # Characters
    characters: List[CharacterPosition]

    # Actions (NEW)
    action: Optional[ActionDescription]

    # Artifacts (NEW)
    artifacts: List[ArtifactPlacement]

    # Tempo and Pacing (NEW)
    tempo: Tempo
    panel_duration: str          # "instant", "moment", "extended"

    # Speech Bubbles (NEW)
    safe_zones: List[SpeechBubbleSafeZone]

    # Environment
    location_id: str
    time_of_day: str
    lighting_preset: str
    weather: Optional[str]

    # Special Effects
    effects: List[str]           # ["fog", "glow", "speed_lines", etc.]

    # Mood and Atmosphere
    mood: str
    color_emphasis: Optional[str]
```

### 4.4 Test Scene Selection with Enhanced Specifications

From `source/001/001.txt` - 3 key scenes with full specifications:

#### Scene 1: The Request to Leave (Dialogue Heavy)

**Scene Context**: Jin Sohan has spent 10 years with his masters at the Magic Tower. He now wishes to return home to check on his sister. This is a formal request scene with tension.

**Enhanced Panel Breakdown**:

```json
{
  "scene_id": "scene_01_request",
  "scene_title": "The Request to Leave",
  "scene_type": "dialogue",
  "overall_tempo": "slow",
  "page_count": 2,
  "panels": [
    {
      "panel_id": "s1_p01",
      "sequence_number": 1,
      "context": {
        "previous_panel_summary": "Chapter opening - no previous panel",
        "scene_context": "Jin Sohan approaches his masters to make a formal request",
        "emotional_state": "Tense formality, respectful determination",
        "narrative_purpose": "Establish setting and atmosphere"
      },
      "shot_type": "establishing",
      "camera_angle": "low_angle",
      "camera_movement": "static",
      "focus_point": "Tower silhouette through fog",
      "depth_of_field": "deep",
      "panel_shape": "rectangle_wide",
      "aspect_ratio": "21:9",
      "page_position": "top_full_width",
      "bleed": true,
      "characters": [],
      "artifacts": [],
      "action": null,
      "tempo": "slow",
      "panel_duration": "extended",
      "safe_zones": [
        {
          "zone_id": "narration_top",
          "position": "top_center",
          "x_percent": 30,
          "y_percent": 5,
          "width_percent": 40,
          "height_percent": 15,
          "speaker_id": null,
          "bubble_type": "narration",
          "text_preview": "The fog-shrouded Magic Tower..."
        }
      ],
      "location_id": "magic_tower_exterior",
      "time_of_day": "twilight",
      "lighting_preset": "fog_day",
      "weather": "heavy_fog",
      "effects": ["atmospheric_fog", "subtle_glow"],
      "mood": "mysterious, isolated",
      "color_emphasis": "cool_blues_grays"
    },
    {
      "panel_id": "s1_p02",
      "sequence_number": 2,
      "context": {
        "previous_panel_summary": "Establishing shot of Magic Tower exterior",
        "scene_context": "Moving inside to the main hall where conversation happens",
        "emotional_state": "Formal, respectful tension",
        "narrative_purpose": "Show Jin Sohan's humble request posture"
      },
      "shot_type": "medium_wide",
      "camera_angle": "eye_level",
      "camera_movement": "static",
      "focus_point": "Jin Sohan kneeling",
      "depth_of_field": "medium",
      "panel_shape": "rectangle_standard",
      "aspect_ratio": "4:3",
      "page_position": "middle_left",
      "bleed": false,
      "characters": [
        {
          "character_id": "jin_sohan",
          "frame_position": "center",
          "x_percent": 50,
          "y_percent": 70,
          "scale": 1.0,
          "posture": "kneeling",
          "pose_description": "Formal kneeling position, hands on thighs, head slightly bowed",
          "expression": "determined_but_respectful",
          "facing": "away"
        },
        {
          "character_id": "dokma",
          "frame_position": "background_left",
          "x_percent": 25,
          "y_percent": 30,
          "scale": 0.7,
          "posture": "sitting",
          "pose_description": "Seated on elevated platform, leaning back casually",
          "expression": "skeptical_smirk",
          "facing": "camera"
        },
        {
          "character_id": "uiseon",
          "frame_position": "background_right",
          "x_percent": 75,
          "y_percent": 30,
          "scale": 0.7,
          "posture": "sitting",
          "pose_description": "Seated on elevated platform, leaning forward with interest",
          "expression": "thoughtful_concern",
          "facing": "camera"
        }
      ],
      "artifacts": [],
      "action": null,
      "tempo": "normal",
      "panel_duration": "moment",
      "safe_zones": [
        {
          "zone_id": "jin_speech",
          "position": "bottom_center",
          "x_percent": 25,
          "y_percent": 80,
          "width_percent": 50,
          "height_percent": 18,
          "speaker_id": "jin_sohan",
          "bubble_type": "speech",
          "text_preview": "Masters, I wish to request leave to return home..."
        }
      ],
      "location_id": "magic_tower_interior",
      "time_of_day": "twilight",
      "lighting_preset": "indoor_lamp",
      "weather": null,
      "effects": ["subtle_fog_interior"],
      "mood": "formal, tense",
      "color_emphasis": null
    },
    {
      "panel_id": "s1_p03",
      "sequence_number": 3,
      "context": {
        "previous_panel_summary": "Wide shot showing Jin Sohan kneeling before both masters",
        "scene_context": "Dokma responds with characteristic cynicism",
        "emotional_state": "Skeptical, testing",
        "narrative_purpose": "Show Dokma's reaction and personality"
      },
      "shot_type": "close_up",
      "camera_angle": "low_angle",
      "camera_movement": "static",
      "focus_point": "Dokma's face",
      "depth_of_field": "shallow",
      "panel_shape": "rectangle_tall",
      "aspect_ratio": "3:4",
      "page_position": "middle_right",
      "bleed": false,
      "characters": [
        {
          "character_id": "dokma",
          "frame_position": "center",
          "x_percent": 50,
          "y_percent": 50,
          "scale": 1.2,
          "posture": "sitting",
          "pose_description": "Upper body and face, chin slightly raised",
          "expression": "cynical_smirk, raised_eyebrow",
          "facing": "camera_slight_left"
        }
      ],
      "artifacts": [],
      "action": null,
      "tempo": "normal",
      "panel_duration": "moment",
      "safe_zones": [
        {
          "zone_id": "dokma_speech",
          "position": "top_right",
          "x_percent": 50,
          "y_percent": 5,
          "width_percent": 45,
          "height_percent": 25,
          "speaker_id": "dokma",
          "bubble_type": "speech",
          "text_preview": "After all these years, you finally want to leave?"
        }
      ],
      "location_id": "magic_tower_interior",
      "time_of_day": "twilight",
      "lighting_preset": "indoor_lamp",
      "weather": null,
      "effects": ["dramatic_shadow"],
      "mood": "skeptical, testing",
      "color_emphasis": "dark_shadows"
    }
  ]
}
```

#### Scene 3: The Departure (Emotional + Artifact Focus)

**Scene Context**: After granting permission, the masters give Jin Sohan parting gifts. This scene features important artifacts that must remain consistent.

**Enhanced Panel Breakdown with Artifact References**:

```json
{
  "scene_id": "scene_03_departure",
  "scene_title": "The Departure",
  "scene_type": "emotional",
  "overall_tempo": "slow",
  "page_count": 2,
  "artifact_references_required": ["twin_crescent_blades", "white_fan"],
  "panels": [
    {
      "panel_id": "s3_p01",
      "sequence_number": 1,
      "context": {
        "previous_panel_summary": "Masters have agreed to let Jin Sohan leave",
        "scene_context": "Dokma presents the twin crescent moon blades as a parting gift",
        "emotional_state": "Reverent, significant moment",
        "narrative_purpose": "Introduce the signature weapons with proper weight"
      },
      "shot_type": "close_up",
      "camera_angle": "eye_level",
      "camera_movement": "zoom_in",
      "focus_point": "Twin crescent moon blades on table",
      "depth_of_field": "shallow",
      "panel_shape": "rectangle_wide",
      "aspect_ratio": "16:9",
      "page_position": "top_full_width",
      "bleed": true,
      "characters": [],
      "artifacts": [
        {
          "artifact_id": "twin_crescent_blades",
          "position": "center",
          "visibility": "full",
          "state": "displayed",
          "lighting_context": "warm_lamp_reverent",
          "importance": "focus"
        }
      ],
      "action": null,
      "tempo": "slow",
      "panel_duration": "extended",
      "safe_zones": [],
      "location_id": "magic_tower_interior",
      "time_of_day": "evening",
      "lighting_preset": "indoor_lamp",
      "weather": null,
      "effects": ["subtle_glow_on_blades"],
      "mood": "reverent, significant",
      "color_emphasis": "warm_gold_highlights",
      "generation_notes": "CRITICAL: Use twin_crescent_blades reference images. Blade design must match exactly."
    },
    {
      "panel_id": "s3_p02",
      "sequence_number": 2,
      "context": {
        "previous_panel_summary": "Close-up of twin blades on table",
        "scene_context": "Dokma hands the blades to Jin Sohan",
        "emotional_state": "Gruff affection, hidden care",
        "narrative_purpose": "Show master-student bond through gift-giving"
      },
      "shot_type": "medium_shot",
      "camera_angle": "eye_level",
      "camera_movement": "static",
      "focus_point": "Exchange of weapons between hands",
      "depth_of_field": "medium",
      "panel_shape": "rectangle_standard",
      "aspect_ratio": "4:3",
      "page_position": "middle_left",
      "bleed": false,
      "characters": [
        {
          "character_id": "dokma",
          "frame_position": "left",
          "x_percent": 30,
          "y_percent": 50,
          "scale": 1.0,
          "posture": "standing",
          "pose_description": "Holding out the blades with both hands, formal presentation",
          "expression": "stern_but_fond",
          "facing": "right"
        },
        {
          "character_id": "jin_sohan",
          "frame_position": "right",
          "x_percent": 70,
          "y_percent": 50,
          "scale": 1.0,
          "posture": "standing",
          "pose_description": "Receiving with both hands, slight bow",
          "expression": "grateful_moved",
          "facing": "left"
        }
      ],
      "artifacts": [
        {
          "artifact_id": "twin_crescent_blades",
          "position": "center_between_characters",
          "visibility": "full",
          "state": "held",
          "lighting_context": "warm_lamp",
          "importance": "focus"
        }
      ],
      "action": {
        "action_type": "static",
        "motion_description": "Formal handover moment, frozen in time",
        "motion_direction": null,
        "motion_intensity": 0,
        "requires_speed_lines": false,
        "requires_motion_blur": false,
        "impact_point": null
      },
      "tempo": "slow",
      "panel_duration": "extended",
      "safe_zones": [
        {
          "zone_id": "dokma_speech",
          "position": "top_left",
          "x_percent": 5,
          "y_percent": 5,
          "width_percent": 40,
          "height_percent": 20,
          "speaker_id": "dokma",
          "bubble_type": "speech",
          "text_preview": "Take these. They've served me well."
        }
      ],
      "location_id": "magic_tower_interior",
      "time_of_day": "evening",
      "lighting_preset": "indoor_lamp",
      "weather": null,
      "effects": [],
      "mood": "gruff_affection, significant_moment",
      "color_emphasis": null,
      "generation_notes": "CRITICAL: Use twin_crescent_blades reference. Same blade design as s3_p01."
    }
  ]
}
```

### 4.5 Panel Shape Selection Guide

**NEW SECTION**: Guidelines for selecting appropriate panel shapes.

| Panel Shape | Use When | Effect | Example |
|-------------|----------|--------|---------|
| Rectangle Wide (16:9, 21:9) | Establishing shots, landscapes, calm dialogue | Stability, breadth, calm | Tower in fog, wide conversation |
| Rectangle Standard (4:3) | Normal dialogue, medium shots | Neutral, conversational | Two characters talking |
| Rectangle Tall (9:16, 3:4) | Power shots, revealing height, single character focus | Dominance, importance | Master looking down at student |
| Square (1:1) | Balanced moments, portraits, reactions | Equality, focus | Character close-up reaction |
| Diagonal Left/Right | Action, tension, movement | Dynamism, instability | Sword strike, character lunging |
| Irregular/Jagged | Chaos, impact, surprise | Disorientation, shock | Explosion, sudden attack |
| Borderless | Emotional overflow, dreamlike | Freedom, intensity | Flashback, overwhelming emotion |
| Circular | Memories, focus on detail | Isolation, nostalgia | Remembered moment, small detail |
| Inset | Quick reaction, detail callout | Emphasis, simultaneity | Eye reaction, hand grabbing |

### 4.6 Camera Angle Selection Guide

**NEW SECTION**: When to use each camera angle for maximum effect.

| Camera Angle | Effect | Use For |
|--------------|--------|---------|
| Eye Level | Neutral, equal | Normal conversation, objective scenes |
| Low Angle | Power, dominance, heroic | Masters, villain reveals, triumphant moments |
| High Angle | Vulnerability, smallness | Character in distress, overwhelmed |
| Dutch Angle | Tension, unease, wrongness | Something is off, psychological tension |
| Bird's Eye | Overview, fate, insignificance | Showing scope, god's perspective |
| Worm's Eye | Extreme power, towering | Giant enemy, dramatic architecture |

### 4.7 Speech Bubble Safe Zone Guidelines

**NEW SECTION**: Rules for defining safe zones.

**Safe Zone Placement Rules**:
1. Never place safe zones over character faces
2. Never place safe zones over focal points (artifacts, action)
3. Prefer top 20% of panel for narration
4. Prefer corners for dialogue bubbles
5. Minimum safe zone size: 15% width, 10% height
6. Maximum safe zone coverage: 30% of total panel area
7. Consider reading flow (left-to-right, top-to-bottom for Korean webtoon)

**Safe Zone Types**:
| Type | Typical Position | Size | Visual Style |
|------|-----------------|------|--------------|
| Speech | Near speaker, corners | 20-30% width | Rounded rectangle |
| Thought | Above character | 15-25% width | Cloud shape |
| Narration | Top or bottom strip | Full width, 10-15% height | Rectangle box |
| SFX | Near action | Variable | Stylized text |

### 4.8 Deliverables

- 3 complete scene storyboards with enhanced specifications
- **NEW: Comprehensive panel specification JSON for each scene**
- **NEW: Camera angle and shot type documentation with examples**
- **NEW: Panel shape selection guide with visual examples**
- **NEW: Speech bubble safe zone templates**
- Panel prompt templates for each composition type
- Character-in-scene consistency report
- Storyboard-to-generation workflow documentation

---

## Phase 5: Generate Images with Panel Composition

### 5.1 Objectives

- Generate final panel images by combining all previous phase outputs
- Integrate character references, style specifications, backgrounds, and **artifact references**
- **NEW: Generate panels with correct shapes (not just rectangles)**
- **NEW: Respect speech bubble safe zones in composition**
- **NEW: Handle panel shapes as part of page layout**
- Test full pipeline from storyboard to finished webtoon panels
- Implement quality control and consistency validation
- Establish batch generation workflow with error handling

### 5.2 Enhanced Generation Pipeline

```
INPUT ASSEMBLY
+------------------------------------------------------------------+
|  Panel Spec  +  Character Refs  +  Artifact Refs  +  Style Guide  |
|  + Background  +  Safe Zones  +  Panel Shape Mask                  |
+------------------------------------------------------------------+
                                |
                                v
PANEL SHAPE PROCESSING (NEW)
+------------------------------------------------------------------+
|  1. Generate base image at specified aspect ratio                  |
|  2. Apply panel shape mask if non-rectangular                      |
|  3. Ensure safe zones are respected in composition                 |
+------------------------------------------------------------------+
                                |
                                v
PROMPT CONSTRUCTION
+------------------------------------------------------------------+
|  Claude Agent SDK: Compose optimized prompt with:                  |
|  - Character reference instructions                                |
|  - Artifact reference instructions (NEW)                           |
|  - Safe zone avoidance instructions (NEW)                          |
|  - Panel shape composition instructions (NEW)                      |
+------------------------------------------------------------------+
                                |
                                v
IMAGE GENERATION
+------------------------------------------------------------------+
|  Google Gemini API: Generate panel image                           |
+------------------------------------------------------------------+
                                |
                                v
POST-PROCESSING (NEW)
+------------------------------------------------------------------+
|  1. Apply panel shape mask                                         |
|  2. Validate safe zones are clear                                  |
|  3. Quality validation                                             |
+------------------------------------------------------------------+
                                |
                        +-------+-------+
                        v               v
                     [PASS]          [FAIL]
                        |               |
                        v               v
                  Save to output   Regenerate with
                                   adjusted prompt
```

### 5.3 Panel Shape Processing System

**NEW SECTION**: Handle non-rectangular panel shapes.

#### 5.3.1 Panel Shape Masks

```python
from PIL import Image, ImageDraw
import numpy as np

class PanelShapeProcessor:
    """Generate and apply panel shape masks."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def create_mask(self, shape: PanelShape, params: dict = None) -> Image:
        """Create a mask for the specified panel shape."""

        mask = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(mask)

        if shape == PanelShape.RECTANGLE_WIDE or \
           shape == PanelShape.RECTANGLE_STANDARD or \
           shape == PanelShape.RECTANGLE_TALL:
            # Standard rectangle - full mask
            draw.rectangle([0, 0, self.width, self.height], fill=255)

        elif shape == PanelShape.DIAGONAL_LEFT:
            # Diagonal cut from top-right to bottom-left
            offset = params.get('offset', self.width * 0.15)
            points = [
                (offset, 0),
                (self.width, 0),
                (self.width, self.height),
                (0, self.height),
                (0, offset)
            ]
            draw.polygon(points, fill=255)

        elif shape == PanelShape.DIAGONAL_RIGHT:
            # Diagonal cut from top-left to bottom-right
            offset = params.get('offset', self.width * 0.15)
            points = [
                (0, 0),
                (self.width - offset, 0),
                (self.width, offset),
                (self.width, self.height),
                (0, self.height)
            ]
            draw.polygon(points, fill=255)

        elif shape == PanelShape.IRREGULAR_JAGGED:
            # Jagged edges for impact
            points = self._generate_jagged_polygon(params)
            draw.polygon(points, fill=255)

        elif shape == PanelShape.CIRCULAR:
            # Circular panel
            margin = params.get('margin', 0.05)
            cx, cy = self.width // 2, self.height // 2
            radius = min(cx, cy) * (1 - margin)
            draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=255)

        elif shape == PanelShape.BORDERLESS:
            # Full image, no border (handled in post-processing)
            draw.rectangle([0, 0, self.width, self.height], fill=255)

        return mask

    def apply_mask(self, image: Image, mask: Image) -> Image:
        """Apply mask to image, making masked areas transparent."""

        result = image.copy()
        result.putalpha(mask)
        return result

    def _generate_jagged_polygon(self, params: dict) -> list:
        """Generate jagged polygon points for impact panels."""

        jaggedness = params.get('jaggedness', 0.1)
        num_points = params.get('num_points', 12)

        points = []
        # Generate irregular polygon
        for i in range(num_points):
            angle = (2 * np.pi * i) / num_points
            radius = 0.45 + np.random.uniform(-jaggedness, jaggedness)
            x = self.width/2 + radius * self.width * np.cos(angle)
            y = self.height/2 + radius * self.height * np.sin(angle)
            points.append((int(x), int(y)))

        return points
```

#### 5.3.2 Composition-Aware Generation

```python
async def generate_panel_with_shape(
    panel_spec: EnhancedPanelSpec,
    character_refs: dict,
    artifact_refs: dict,  # NEW
    style_guide: dict
) -> str:
    """Generate panel with shape and safe zone awareness."""

    # Build composition instructions based on safe zones
    safe_zone_instructions = build_safe_zone_instructions(panel_spec.safe_zones)

    # Build artifact reference instructions
    artifact_instructions = build_artifact_instructions(
        panel_spec.artifacts,
        artifact_refs
    )

    # Determine generation aspect ratio based on panel shape
    gen_ratio = get_generation_ratio(panel_spec.panel_shape, panel_spec.aspect_ratio)

    # Build complete prompt
    prompt = f"""
Korean webtoon panel illustration:

[SCENE CONTEXT]
- Panel purpose: {panel_spec.context.narrative_purpose}
- Previous moment: {panel_spec.context.previous_panel_summary}
- Emotional state: {panel_spec.context.emotional_state}

[CAMERA DIRECTION]
- Shot type: {panel_spec.shot_type.value}
- Camera angle: {panel_spec.camera_angle.value}
- Camera movement suggestion: {panel_spec.camera_movement.value}
- Focus point: {panel_spec.focus_point}

[COMPOSITION - CRITICAL]
{safe_zone_instructions}

[CHARACTERS]
{build_character_block(panel_spec.characters)}

[ARTIFACTS - USE REFERENCE IMAGES]
{artifact_instructions}

[ACTION/MOTION]
{build_action_block(panel_spec.action) if panel_spec.action else "Static scene"}

[TEMPO]
- Panel tempo: {panel_spec.tempo.value}
- Duration feel: {panel_spec.panel_duration}

[ENVIRONMENT]
- Location: {panel_spec.location_id}
- Time: {panel_spec.time_of_day}
- Lighting: {panel_spec.lighting_preset}
- Effects: {', '.join(panel_spec.effects)}

[MOOD]
- Atmosphere: {panel_spec.mood}
- Color emphasis: {panel_spec.color_emphasis or 'standard palette'}

[TECHNICAL]
- Style: Korean webtoon, wuxia genre
- Quality: High detail, publication ready
- No text or speech bubbles (will be added separately)
"""

    # Collect reference images
    reference_images = []

    # Add character references
    for char in panel_spec.characters:
        if char.character_id in character_refs:
            reference_images.append(character_refs[char.character_id])

    # Add artifact references (NEW)
    for artifact in panel_spec.artifacts:
        if artifact.artifact_id in artifact_refs:
            reference_images.append(artifact_refs[artifact.artifact_id])

    # Generate image
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

    contents = reference_images + [prompt]

    response = client.models.generate_content(
        model='gemini-3-pro-image-preview',
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=gen_ratio,
                image_size="2K"
            ),
        )
    )

    # Save base image
    base_path = save_generated_image(response, panel_spec.panel_id)

    # Apply panel shape mask if non-rectangular
    if panel_spec.panel_shape not in [
        PanelShape.RECTANGLE_WIDE,
        PanelShape.RECTANGLE_STANDARD,
        PanelShape.RECTANGLE_TALL,
        PanelShape.SQUARE
    ]:
        final_path = apply_panel_shape(base_path, panel_spec.panel_shape)
    else:
        final_path = base_path

    return final_path


def build_safe_zone_instructions(safe_zones: List[SpeechBubbleSafeZone]) -> str:
    """Build composition instructions to avoid safe zones."""

    if not safe_zones:
        return "No specific composition restrictions."

    instructions = ["IMPORTANT - Leave these areas clear for dialogue:"]

    for zone in safe_zones:
        instructions.append(
            f"- {zone.position}: Keep area from ({zone.x_percent}%, {zone.y_percent}%) "
            f"to ({zone.x_percent + zone.width_percent}%, {zone.y_percent + zone.height_percent}%) "
            f"relatively clear/simple for {zone.bubble_type} bubble"
        )

    instructions.append(
        "\nDo NOT place important visual elements (faces, artifacts, action) in these zones."
    )

    return '\n'.join(instructions)


def build_artifact_instructions(
    artifacts: List[ArtifactPlacement],
    artifact_refs: dict
) -> str:
    """Build instructions for artifact consistency."""

    if not artifacts:
        return "No artifacts in this panel."

    instructions = []

    for artifact in artifacts:
        ref_note = ""
        if artifact.artifact_id in artifact_refs:
            ref_note = " (REFERENCE IMAGE PROVIDED - match exactly)"

        instructions.append(f"""
Artifact: {artifact.artifact_id}{ref_note}
- Position: {artifact.position}
- Visibility: {artifact.visibility}
- State: {artifact.state}
- Importance: {artifact.importance}
- CRITICAL: Design must match reference image exactly (shape, proportions, details)
""")

    return '\n'.join(instructions)
```

### 5.4 Test Cases

#### Test 5.4.1: Artifact Consistency Test

Generate the same artifact across multiple panels and verify consistency.

```python
async def test_artifact_consistency():
    """Test that twin crescent blades look identical across panels."""

    # Load artifact reference
    artifact_ref = Image.open("poc/phase3_artifacts/twin_crescent_blades/base_reference.png")

    # Generate panel s3_p01 (artifact focus)
    panel_01 = await generate_panel_with_shape(
        panel_spec=scene3_panels[0],
        character_refs={},
        artifact_refs={"twin_crescent_blades": artifact_ref},
        style_guide=style_guide
    )

    # Generate panel s3_p02 (artifact being handed over)
    panel_02 = await generate_panel_with_shape(
        panel_spec=scene3_panels[1],
        character_refs=character_refs,
        artifact_refs={"twin_crescent_blades": artifact_ref},
        style_guide=style_guide
    )

    # Validate artifact consistency
    consistency_score = await validate_artifact_consistency(
        panel_01, panel_02,
        artifact_id="twin_crescent_blades",
        artifact_ref=artifact_ref
    )

    return consistency_score
```

**Success Criteria**:
- Blade shape identical across both panels
- Handle design consistent
- Proportions maintained regardless of context
- Consistency score > 85%

#### Test 5.4.2: Panel Shape Variety Test

Generate panels with different shapes for action sequence.

```python
action_sequence_shapes = [
    {
        "panel_id": "action_setup",
        "panel_shape": "rectangle_wide",
        "purpose": "Establish scene, calm before storm"
    },
    {
        "panel_id": "action_tension",
        "panel_shape": "diagonal_right",
        "purpose": "Building tension, something about to happen"
    },
    {
        "panel_id": "action_strike",
        "panel_shape": "diagonal_left",
        "purpose": "Action strike, dynamic movement"
    },
    {
        "panel_id": "action_impact",
        "panel_shape": "irregular_jagged",
        "purpose": "Impact moment, chaos and shock"
    },
    {
        "panel_id": "action_aftermath",
        "panel_shape": "rectangle_standard",
        "purpose": "Return to stability, aftermath"
    }
]
```

**Success Criteria**:
- All panel shapes render correctly
- Diagonal cuts enhance sense of movement
- Jagged edges convey impact appropriately
- Visual flow reads naturally across shapes

#### Test 5.4.3: Safe Zone Validation Test

Verify that generated images respect speech bubble safe zones.

```python
async def test_safe_zone_compliance():
    """Test that important content avoids safe zones."""

    # Panel with multiple safe zones
    test_panel = EnhancedPanelSpec(
        panel_id="safe_zone_test",
        # ... other specs ...
        safe_zones=[
            SpeechBubbleSafeZone(
                zone_id="top_speech",
                position="top_left",
                x_percent=5,
                y_percent=5,
                width_percent=35,
                height_percent=20,
                speaker_id="dokma",
                bubble_type="speech",
                text_preview="Test dialogue here"
            ),
            SpeechBubbleSafeZone(
                zone_id="bottom_speech",
                position="bottom_right",
                x_percent=60,
                y_percent=75,
                width_percent=35,
                height_percent=20,
                speaker_id="jin_sohan",
                bubble_type="speech",
                text_preview="Response dialogue"
            )
        ]
    )

    result = await generate_panel_with_shape(test_panel, ...)

    # Analyze generated image for content in safe zones
    compliance = analyze_safe_zone_compliance(result, test_panel.safe_zones)

    return compliance
```

**Success Criteria**:
- No faces in safe zones
- No important artifacts in safe zones
- Safe zones have simple/low-detail backgrounds suitable for text overlay
- Compliance score > 90%

### 5.5 Quality Control System

#### 5.5.1 Enhanced Quality Checks

```python
class EnhancedQualityChecker:
    def __init__(self, style_guide: dict, character_refs: dict, artifact_refs: dict):
        self.style_guide = style_guide
        self.character_refs = character_refs
        self.artifact_refs = artifact_refs  # NEW

    async def validate_panel(self, image_path: str, panel_spec: EnhancedPanelSpec) -> dict:
        """Run all quality checks including new requirements."""

        image = Image.open(image_path)

        checks = {
            "resolution": self.check_resolution(image, panel_spec),
            "aspect_ratio": self.check_aspect_ratio(image, panel_spec),
            "color_palette": self.check_color_palette(image),
            "composition": self.check_composition(image, panel_spec),
            "overall_quality": self.check_overall_quality(image),
            # NEW checks
            "artifact_consistency": self.check_artifact_consistency(image, panel_spec),
            "safe_zone_compliance": self.check_safe_zones(image, panel_spec),
            "panel_shape": self.check_panel_shape(image, panel_spec),
        }

        passed = all(c['passed'] for c in checks.values())

        return {
            "passed": passed,
            "checks": checks,
            "recommendations": self.get_recommendations(checks)
        }

    def check_artifact_consistency(self, image: Image, panel_spec: EnhancedPanelSpec) -> dict:
        """NEW: Check if artifacts match their references."""

        if not panel_spec.artifacts:
            return {"passed": True, "note": "No artifacts to check"}

        # Implementation would use image analysis to compare artifact regions
        # with reference images

        return {
            "passed": True,
            "artifacts_checked": [a.artifact_id for a in panel_spec.artifacts],
            "consistency_scores": {},  # Would contain per-artifact scores
            "note": "Artifact consistency validation"
        }

    def check_safe_zones(self, image: Image, panel_spec: EnhancedPanelSpec) -> dict:
        """NEW: Check if safe zones are clear of important content."""

        if not panel_spec.safe_zones:
            return {"passed": True, "note": "No safe zones defined"}

        # Implementation would analyze image regions for content density

        return {
            "passed": True,
            "zones_checked": len(panel_spec.safe_zones),
            "compliance_score": 0.95,
            "note": "Safe zones appear clear"
        }

    def check_panel_shape(self, image: Image, panel_spec: EnhancedPanelSpec) -> dict:
        """NEW: Verify panel shape was applied correctly."""

        # For non-rectangular panels, check alpha channel
        if panel_spec.panel_shape in [
            PanelShape.DIAGONAL_LEFT,
            PanelShape.DIAGONAL_RIGHT,
            PanelShape.IRREGULAR_JAGGED,
            PanelShape.CIRCULAR
        ]:
            if image.mode != 'RGBA':
                return {"passed": False, "note": "Non-rectangular panel missing alpha channel"}

            # Check that mask is properly applied
            alpha = image.split()[-1]
            # Verify non-trivial transparency exists

        return {"passed": True, "note": "Panel shape validated"}
```

### 5.6 Output Organization

#### 5.6.1 Enhanced Generated Assets Structure

```
poc/phase5_generation/
├── scene_01_request/
│   ├── panels/
│   │   ├── s1_p01_establishing.png
│   │   ├── s1_p01_establishing_mask.png  # NEW: Shape mask
│   │   ├── s1_p02_medium.png
│   │   └── ...
│   ├── metadata/
│   │   ├── s1_p01_metadata.json
│   │   └── ...
│   └── scene_manifest.json
├── scene_02_storytelling/
│   └── ...
├── scene_03_departure/
│   ├── panels/
│   │   ├── s3_p01_artifact_focus.png     # Blades close-up
│   │   ├── s3_p02_handover.png           # Blades being given
│   │   └── ...
│   └── artifact_consistency_report.json  # NEW
├── action_sequence/
│   ├── panels/
│   │   ├── action_01_setup.png           # Wide rectangle
│   │   ├── action_02_tension_diagonal.png # Diagonal shape
│   │   ├── action_03_impact_jagged.png   # Irregular shape
│   │   └── ...
│   └── shape_variants_report.json        # NEW
├── reports/
│   ├── batch_results.json
│   ├── quality_report.json
│   ├── consistency_report.json
│   ├── artifact_consistency_report.json  # NEW
│   ├── safe_zone_compliance_report.json  # NEW
│   └── cost_summary.json
└── failed/
    ├── retry_queue.json
    └── failed_panels/
```

#### 5.6.2 Enhanced Panel Metadata Format

```json
{
  "panel_id": "s3_p02_handover",
  "scene_id": "scene_03_departure",
  "sequence_number": 2,
  "generation": {
    "timestamp": "2025-12-31T10:00:00Z",
    "model": "gemini-3-pro-image-preview",
    "prompt_hash": "abc123...",
    "attempts": 1,
    "generation_time_ms": 3420,
    "reference_images_used": [
      "jin_sohan/base_reference.png",
      "dokma/base_reference.png",
      "twin_crescent_blades/base_reference.png"
    ]
  },
  "specifications": {
    "panel_type": "medium_shot",
    "panel_shape": "rectangle_standard",
    "aspect_ratio": "4:3",
    "camera_angle": "eye_level",
    "shot_type": "medium_shot",
    "characters": ["Jin Sohan", "Dokma"],
    "artifacts": ["twin_crescent_blades"],
    "location": "Magic Tower interior",
    "safe_zones_defined": 1
  },
  "quality_validation": {
    "passed": true,
    "resolution_check": true,
    "color_palette_match": 0.92,
    "character_consistency": 0.88,
    "artifact_consistency": 0.91,
    "safe_zone_compliance": 0.95,
    "panel_shape_correct": true
  },
  "file_info": {
    "path": "scene_03_departure/panels/s3_p02_handover.png",
    "size_bytes": 1245678,
    "dimensions": "2048x1536",
    "has_alpha": false
  }
}
```

### 5.7 Deliverables

- Complete panel images for all 3 test scenes (18+ panels)
- **NEW: Artifact consistency validation across panels**
- **NEW: Varied panel shapes (diagonal, irregular, circular)**
- **NEW: Safe zone compliance reports**
- 4-panel action sequence with motion effects and varied shapes
- 3-panel emotional sequence with atmosphere
- Batch generation system code
- Quality validation reports
- Character consistency analysis
- **NEW: Artifact consistency analysis**
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
| Phase 3 | Backgrounds + Artifacts | Location library + Artifact reference sheets |
| Phase 4 | Enhanced Storyboarding | Detailed panel specifications with camera/shape/zones |
| Phase 5 | Image Generation | Final panels with shapes and artifact consistency |

### Technical Requirements

#### Environment Setup

```bash
# Required packages
pip install google-genai
pip install claude-agent-sdk
pip install python-dotenv
pip install pillow
pip install numpy
```

#### Environment Variables

```bash
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### File Structure for PoC v2

```
novel-to-toon/
├── poc/
│   ├── phase1_characters/
│   │   ├── jin_sohan/
│   │   │   ├── base_reference.png
│   │   │   ├── variations/
│   │   │   └── metadata.json
│   │   ├── dokma/
│   │   ├── uiseon/
│   │   └── prompts.md
│   ├── phase2_style/
│   │   ├── style_spec.json
│   │   ├── prompt_templates.json
│   │   └── agent_outputs/
│   ├── phase3_backgrounds_artifacts/  # RENAMED
│   │   ├── locations/
│   │   │   ├── magic_tower/
│   │   │   ├── inn/
│   │   │   └── black_path/
│   │   ├── artifacts/                  # NEW
│   │   │   ├── twin_crescent_blades/
│   │   │   │   ├── base_reference.png
│   │   │   │   ├── variation_held.png
│   │   │   │   ├── variation_action.png
│   │   │   │   └── design_spec.json
│   │   │   ├── white_fan/
│   │   │   └── artifact_registry.json
│   │   ├── materials/
│   │   └── lighting_tests/
│   ├── phase4_storyboard/
│   │   ├── scene_01_request/
│   │   │   ├── enhanced_panel_specs.json  # NEW format
│   │   │   ├── safe_zone_layouts.json     # NEW
│   │   │   └── shape_selections.json      # NEW
│   │   ├── scene_02_storytelling/
│   │   ├── scene_03_departure/
│   │   ├── panel_shape_guide.md           # NEW
│   │   └── camera_angle_guide.md          # NEW
│   ├── phase5_generation/
│   │   ├── scene_01_request/
│   │   │   ├── panels/
│   │   │   ├── masks/                     # NEW: Panel shape masks
│   │   │   └── metadata/
│   │   ├── scene_02_storytelling/
│   │   ├── scene_03_departure/
│   │   ├── action_sequence/
│   │   ├── reports/
│   │   │   ├── batch_results.json
│   │   │   ├── quality_report.json
│   │   │   ├── consistency_report.json
│   │   │   ├── artifact_consistency_report.json  # NEW
│   │   │   ├── safe_zone_compliance_report.json  # NEW
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
│   ├── artifact_generator.py      # NEW
│   ├── storyboard_generator.py
│   ├── panel_generator.py
│   └── panel_shape_processor.py   # NEW
└── docs/
    ├── poc-specification.md
    └── poc-specification-v2.md (this file)
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

### Phase 3: Backgrounds and Artifacts

- [ ] 5 key locations generated
- [ ] Location consistency maintained across variations
- [ ] Material textures suitable for integration
- [ ] Lighting presets documented with examples
- [ ] **NEW: 5 key artifacts have reference sheets**
- [ ] **NEW: Artifact consistency score > 85% across variations**
- [ ] **NEW: Artifact design specifications documented**

### Phase 4: Enhanced Storyboarding

- [ ] 18 panel specifications created across 3 scenes
- [ ] **NEW: All panels have detailed camera angle specifications**
- [ ] **NEW: All panels have appropriate shape selections**
- [ ] **NEW: All dialogue panels have safe zone definitions**
- [ ] **NEW: Context fields populated for all panels**
- [ ] Panel layouts follow webtoon conventions
- [ ] Scene-to-panel conversion workflow documented

### Phase 5: Image Generation

- [ ] 18+ panels generated from storyboards
- [ ] Character consistency score > 80% across panels
- [ ] **NEW: Artifact consistency score > 85% across panels**
- [ ] Quality validation pass rate > 90%
- [ ] **NEW: Safe zone compliance > 90%**
- [ ] **NEW: Varied panel shapes implemented correctly**
- [ ] Action sequence (4 panels) with motion effects
- [ ] Emotional sequence (3 panels) with atmosphere
- [ ] Batch generation system functional
- [ ] API cost tracking implemented
- [ ] Failed generation retry system tested

### Overall PoC v2 Success

- [ ] All 5 phases completed with deliverables
- [ ] End-to-end pipeline validated (novel -> panels)
- [ ] **NEW: Artifact consistency problem solved**
- [ ] **NEW: Panel variety achieved (shapes, compositions)**
- [ ] **NEW: Speech bubble integration ready**
- [ ] Technical recommendations documented
- [ ] API cost estimates calculated
- [ ] Production workflow design finalized
- [ ] Quality benchmarks established
- [ ] Cost per panel reduced to < $0.05
- [ ] Spending tracking system operational

---

## Cost Optimization Strategy

### Model Selection

Use a hybrid approach to balance quality and cost:

| Use Case | Model | Cost/Image | When to Use |
|----------|-------|-----------|-------------|
| Regular panels | gemini-2.5-flash-image | $0.039 | 80% of generation |
| Character introductions | gemini-3-pro-image-preview | $0.134 | Complex multi-character scenes |
| Reference sheets | gemini-3-pro-image-preview | $0.134 | Initial character/artifact creation |

### Resolution Strategy

| Asset Type | Resolution | Rationale |
|------------|-----------|-----------|
| Character references | 2K (2048px) | High detail needed for consistency |
| Artifact references | 2K (2048px) | Detail preservation |
| Panel generation | 1K (1024px) | Sufficient for mobile webtoon viewing |
| Backgrounds | 1K (1024px) | Will be composited, not focal point |

Webtoon platforms require max 800x1280px for upload. 1K resolution provides adequate quality margin.

### Batch Processing

Enable 50% discount through batch processing:

```python
# Batch configuration for overnight processing
batch_config = {
    "mode": "batch",
    "priority": "low",
    "callback_url": "https://your-webhook.com/batch-complete"
}
```

Use batch processing for:
- Chapter panel generation (non-urgent)
- Background variations
- Artifact reference sheets

Reserve real-time processing for:
- Interactive iteration during development
- Urgent corrections

### Context Caching

Cache repeated content for 90% token discount:

```python
# Cache style guide and character specs
cached_context = client.caches.create(
    model="gemini-2.5-flash-image",
    contents=[
        style_specification,
        character_descriptions,
        artifact_specifications
    ],
    ttl="3600s"  # 1 hour cache
)

# Use cache in generation
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    cached_content=cached_context.name,
    contents=[panel_specific_prompt]
)
```

### Cost Targets

| Metric | v1 Actual | v2 Target | Savings |
|--------|-----------|-----------|---------|
| Cost per panel | $0.134 | $0.03-0.05 | 63-78% |
| Cost per chapter (20 panels) | $2.68 | $0.60-1.00 | 63-78% |
| POC total (~90 images) | $12.00 | $2.70-4.50 | 63-78% |

---

## Spending Tracking

### API Response Metadata

Extract usage data from every API response:

```python
response = client.models.generate_content(...)

# Available metadata
usage = response.usage_metadata
prompt_tokens = usage.prompt_token_count
output_tokens = usage.candidates_token_count
cached_tokens = usage.cached_content_token_count or 0
total_tokens = usage.total_token_count
```

### Cost Tracker Implementation

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
import json

@dataclass
class APICallRecord:
    timestamp: str
    model: str
    panel_id: str
    prompt_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_usd: float
    generation_time_ms: int

class CostTracker:
    PRICING = {
        "gemini-3-pro-image-preview": {"1k_2k": 0.134, "4k": 0.24},
        "gemini-2.5-flash-image": {"default": 0.039}
    }

    def __init__(self):
        self.calls: List[APICallRecord] = []
        self.total_cost = 0.0

    def track(self, model: str, response, panel_id: str, time_ms: int):
        cost = self.PRICING.get(model, {}).get("default", 0.05)

        record = APICallRecord(
            timestamp=datetime.utcnow().isoformat(),
            model=model,
            panel_id=panel_id,
            prompt_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            cached_tokens=response.usage_metadata.cached_content_token_count or 0,
            cost_usd=cost,
            generation_time_ms=time_ms
        )

        self.calls.append(record)
        self.total_cost += cost
        return record

    def summary(self) -> Dict[str, Any]:
        by_model = {}
        for call in self.calls:
            if call.model not in by_model:
                by_model[call.model] = {"count": 0, "cost": 0.0}
            by_model[call.model]["count"] += 1
            by_model[call.model]["cost"] += call.cost_usd

        return {
            "total_calls": len(self.calls),
            "total_cost_usd": round(self.total_cost, 4),
            "by_model": by_model
        }

    def export(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump({
                "summary": self.summary(),
                "calls": [vars(c) for c in self.calls]
            }, f, indent=2)
```

### Log Format

Per-call log entry:

```json
{
  "timestamp": "2025-12-31T14:30:45Z",
  "model": "gemini-2.5-flash-image",
  "panel_id": "s1_p02",
  "scene_id": "scene_01_request",
  "tokens": {
    "prompt": 28,
    "output": 1290,
    "cached": 0
  },
  "cost_usd": 0.039,
  "generation_time_ms": 3200,
  "status": "success"
}
```

Session summary:

```json
{
  "session_id": "poc-v2-run-001",
  "timestamp": "2025-12-31T18:00:00Z",
  "total_calls": 45,
  "total_cost_usd": 2.34,
  "by_model": {
    "gemini-2.5-flash-image": {"count": 36, "cost": 1.40},
    "gemini-3-pro-image-preview": {"count": 9, "cost": 0.94}
  },
  "by_phase": {
    "character_generation": {"count": 12, "cost": 0.61},
    "artifact_generation": {"count": 5, "cost": 0.20},
    "panel_generation": {"count": 28, "cost": 1.53}
  }
}
```

### Integration Points

1. Wrap all `generate_content` calls with tracking
2. Export logs after each phase completion
3. Generate cost report at POC completion
4. Store logs in `poc/reports/cost_summary.json`

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Character inconsistency | High | Use base reference images as input for all variations |
| **NEW: Artifact inconsistency** | High | **Dedicated artifact reference workflow** |
| API rate limiting | Medium | Implement retry logic, batch processing |
| Style drift across panels | High | Use reference images + strict prompt templates |
| **NEW: Complex panel shapes** | Medium | **Pre-generate shape masks, test variety** |
| **NEW: Safe zone violation** | Medium | **Include explicit zone instructions in prompts** |

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
The man in black robes was called Dokma (Poison Demon), with a dark complexion,
while the man in white robes was called Uiseon (Medicine Sage), with a scholarly atmosphere.
```

#### Excerpt 2: Setting Description

```
The fog-shrouded Magic Tower.
Hidden in fog so thick that one couldn't even tell people lived there,
the eccentric twin brothers known as the Magic Sages lived in seclusion.
```

#### Excerpt 3: Action Scene

```
Jin Sohan's calm voice flowed out. "Duhyang..."
Something flashed past Oh Je-cheol's eyes.
Then came a 'thud' sound.
When the startled Oh Je-cheol looked back at Oh Je-gwang,
whom he had been grabbing by the collar, a chopstick was embedded in his forehead.
```

### B. Panel Shape Visual Reference

```
RECTANGLE_WIDE (21:9, 16:9)
+------------------------------------------+
|                                          |
|          Establishing, Calm              |
|                                          |
+------------------------------------------+

RECTANGLE_STANDARD (4:3)
+------------------------+
|                        |
|    Standard Dialogue   |
|                        |
+------------------------+

RECTANGLE_TALL (9:16, 3:4)
+----------+
|          |
|  Power   |
|  Height  |
|  Focus   |
|          |
+----------+

DIAGONAL_LEFT
    +----------------------------------+
   /                                  /
  /        Action Left               /
 /                                  /
+----------------------------------+

DIAGONAL_RIGHT
+----------------------------------+
 \                                  \
  \        Action Right              \
   \                                  \
    +----------------------------------+

IRREGULAR_JAGGED
   /\    /\
  /  \  /  \
 /    \/    \
|   IMPACT   |
|            |
 \    /\    /
  \  /  \  /
   \/    \/

CIRCULAR
     ____
   /      \
  |  Focus  |
  | Memory  |
   \      /
     ----
```

### C. Camera Angle Visual Reference

```
EYE LEVEL          LOW ANGLE          HIGH ANGLE
   o                  o                   O
  /|\                /|\ ^               /|\
  / \               / \ |               / \ v
[camera]         [camera]            [camera]
 (=)               (^)                 (v)

DUTCH ANGLE        BIRD'S EYE         WORM'S EYE
   o                  O                  o
  /|\ /             [   ]               /|\
  / \              (camera)             / \
[camera]              |               _______
  (/)              [scene]            [cam] ^
```

### D. Safe Zone Layout Examples

```
DIALOGUE PANEL - Two Speakers
+------------------------------------------+
| [Safe Zone A - Speaker 1]                |
|     _______                              |
|                                          |
|         [Character 1]  [Character 2]     |
|                                          |
|                    [Safe Zone B - Speaker 2] |
|                         _______          |
+------------------------------------------+

NARRATION PANEL
+------------------------------------------+
| [Safe Zone - Narration Box]              |
| ________________________________________ |
|                                          |
|              [Scene Content]             |
|                                          |
+------------------------------------------+

ACTION PANEL - SFX Only
+------------------------------------------+
|                                          |
|    [SFX Zone]     [Action Scene]         |
|      SLASH!                              |
|                                          |
+------------------------------------------+
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-30 | Initial | Created PoC specification document |
| 1.1 | 2025-12-30 | Update | Added Phase 5: Generate Images with full pipeline |
| 1.2 | 2025-12-30 | Update | Added reference image-based generation workflow |
| 1.3 | 2025-12-30 | Update | Standardized on gemini-3-pro-image-preview |
| 2.0 | 2025-12-31 | Major Revision | v2 Release: Added artifact reference workflow (Phase 3), enhanced panel specifications with camera angles/positions/actions/tempo/context (Phase 4), panel shape variety system, speech bubble safe zones, comprehensive data structures for panel specs |
| 2.1 | 2025-12-31 | Update | Added Cost Optimization Strategy section (hybrid model selection, resolution strategy, batch processing, context caching). Added Spending Tracking section (API metadata extraction, CostTracker implementation, log formats). Updated objectives and success criteria. |
