# Research: Character Consistency with Reference Images

## Problem Statement

Prompt-only image generation cannot guarantee style consistency across multiple generations. Each image has different:
- Line styles
- Color palettes
- Character appearances (hair length, facial features, etc.)
- Coloring techniques

## Solution: Reference Image-Based Generation

### Key Findings

The Gemini API supports **reference image input** for maintaining visual consistency:

| Feature | gemini-2.5-flash-image | gemini-3-pro-image-preview |
|---------|------------------------|----------------------------|
| Max reference images | 3 | 14 |
| Human subjects | Limited | Up to 5 with identity preservation |
| Object fidelity | Standard | Up to 6 high-fidelity objects |
| Resolution | 1K, 2K | 1K, 2K, 4K |
| Thinking mode | No | Yes (preserves reasoning context) |

### How It Works

1. **Provide reference image(s)** alongside the text prompt
2. Model "memorizes" visual characteristics from reference
3. Generates new images maintaining those characteristics

## Implementation Approach

### Step 1: Generate Base Character Image

First, generate a single high-quality reference image for each character with detailed prompt:

```python
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=["Detailed character prompt..."],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="2K"
        )
    )
)
```

### Step 2: Use Base Image for Variations

Pass the base image as reference for all subsequent generations:

```python
from PIL import Image

# Load base reference image
base_image = Image.open("character_base.png")

# Generate variation with reference
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        base_image,  # Reference image FIRST
        "Same character with angry expression, 3/4 view"
    ],
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
    )
)
```

### Step 3: Multi-Turn Editing (Alternative)

For iterative refinement, use conversation-based editing:

```python
# Turn 1: Generate base
response1 = model.generate("Create a martial artist in black robes...")

# Turn 2: Edit with context
response2 = model.generate("Now show the same character with angry expression")

# Turn 3: Continue editing
response3 = model.generate("Change the pose to action stance")
```

## Recommended Workflow for Character Consistency

```
1. Define Style Guide
   - Line weight specifications
   - Color palette (hex codes)
   - Shading technique description
   - Art style reference

2. Generate Master Reference
   - One high-quality image per character
   - Neutral pose, front view
   - Clear visibility of key features
   - 2K resolution minimum

3. Generate Variations with Reference
   - Always pass master reference as input
   - Request specific changes only
   - Maintain consistent prompt structure

4. Validate Consistency
   - Compare key features across images
   - Check color palette adherence
   - Verify line style consistency
```

## API Configuration

### For Character Reference Generation

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

config = types.GenerateContentConfig(
    response_modalities=['TEXT', 'IMAGE'],
    thinking_level="high",  # Better reasoning for character consistency
    image_config=types.ImageConfig(
        aspect_ratio="1:1",  # Square for character portraits
        image_size="2K"
    )
)
```

### For Variation with Reference Image

```python
from PIL import Image

reference_image = Image.open("base_character.png")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[
        reference_image,
        "Generate this exact character with [variation description]. Maintain the same face, hair style, clothing design, and art style."
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

## Best Practices

### Prompt Structure for Consistency

```
[Reference Image] + Text Prompt:

"Generate the SAME character from the reference image with the following changes:
- Expression: [new expression]
- Pose: [new pose]
- Angle: [camera angle]

MAINTAIN EXACTLY:
- Face shape and features
- Hair style and color
- Clothing design and colors
- Art style and line weight
- Color palette and shading technique"
```

### Key Points

1. **Reference image should come FIRST** in the contents array
2. **Explicitly state what to maintain** in the prompt
3. **Use thinking_level="high"** for better reasoning
4. **Keep base reference at 2K+ resolution** for detail preservation
5. **Use consistent aspect ratios** across generations

## Limitations

- Maximum 14 reference images per request (gemini-3-pro)
- Maximum 5 human subjects for identity preservation
- Some style drift may still occur - manual review recommended
- 4K output significantly more expensive ($0.24 vs $0.039)

## Sources

- [Image generation with Gemini - Google AI](https://ai.google.dev/gemini-api/docs/image-generation)
- [Generate and edit images with Gemini - Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-generation)
- [Gemini 3 Pro Image API Guide](https://www.cursor-ide.com/blog/gemini-3-pro-image-api)
- [Generating Consistent Imagery with Gemini - Towards Data Science](https://towardsdatascience.com/generating-consistent-imagery-with-gemini/)
- [Google Gemini Cookbook](https://github.com/google-gemini/cookbook)
