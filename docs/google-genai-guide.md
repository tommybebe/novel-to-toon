# Comprehensive Google GenAI Python SDK Usage Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation and Setup](#installation-and-setup)
3. [Authentication](#authentication)
4. [Available Models](#available-models)
5. [Image Generation with Imagen](#image-generation-with-imagen)
6. [Native Image Generation with Gemini](#native-image-generation-with-gemini)
7. [Configuration Options](#configuration-options)
8. [Response Handling](#response-handling)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)
11. [Complete Code Examples](#complete-code-examples)
12. [Advanced Features](#advanced-features)

---

## 1. Introduction

Google provides two primary approaches for image generation in Python:

### Imagen API
- **Purpose**: Dedicated high-fidelity image generation
- **Models**: Imagen 3.0 and Imagen 4.0
- **Features**: Realistic, high-quality images with SynthID watermarks
- **Best for**: Production-grade image generation

### Gemini Native Image Generation
- **Purpose**: Multi-modal generation with text and images
- **Models**: Gemini 2.5 Flash (aka "Nano Banana"), Gemini 3 Pro Preview
- **Features**: Image editing, thinking capabilities, search grounding, 4K resolution
- **Best for**: Interactive workflows with context

---

## 2. Installation and Setup

### Install the Google Gen AI SDK

```bash
pip install -q -U google-genai
```

Or for the older package (legacy support):

```bash
pip install -q -U google-generativeai
```

### Verify Installation

```python
import google.genai as genai
print("Google Gen AI SDK installed successfully")
```

---

## 3. Authentication

### Using API Key

The simplest authentication method uses a Google API key:

```python
from google import genai
import os

# Option 1: Set environment variable
os.environ['GOOGLE_API_KEY'] = 'your-api-key-here'

# Option 2: Pass directly to client
client = genai.Client(api_key='your-api-key-here')
```

### Best Practice: Environment Variables

Create a `.env` file in your project root:

```bash
GOOGLE_API_KEY=your_api_key_here
```

Then load it in your Python code:

```python
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Initialize client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
```

---

## 4. Available Models

### Imagen Models

| Model ID | Description | Max Resolution | Features |
|----------|-------------|----------------|----------|
| `imagen-3.0-generate-001` | Imagen 3.0 Standard | 1024x1024 (1K) | High-quality image generation |
| `imagen-3.0-generate-002` | Imagen 3.0 Enhanced | 2048x2048 (2K) | Enhanced quality and detail |
| `imagen-4.0-generate-001` | Imagen 4.0 (Latest) | 2048x2048 (2K) | Latest model with best quality |

### Gemini Models with Image Generation

| Model ID | Description | Features |
|----------|-------------|----------|
| `gemini-2.5-flash-image` | Gemini 2.5 Flash | Fast, efficient, supports thinking |
| `gemini-3-pro-preview` | Gemini 3 Pro | Advanced capabilities, 4K support |

---

## 5. Image Generation with Imagen

### Basic Image Generation

```python
from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key='your-api-key')

# Generate a single image
response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='A tranquil beach with crystal-clear water and colorful seashells on the shore.',
    config=types.GenerateImagesConfig(
        number_of_images=1
    )
)

# Display the image
response.generated_images[0].image.show()

# Or save to file
response.generated_images[0].image.save('output.png')
```

### Generate Multiple Images

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Generate 4 variations
response = client.models.generate_images(
    model='imagen-4.0-generate-001',
    prompt='A futuristic cityscape at sunset with flying cars',
    config=types.GenerateImagesConfig(
        number_of_images=4,
        image_size="2K"  # Higher resolution
    )
)

# Save all images
for idx, generated_image in enumerate(response.generated_images):
    generated_image.image.save(f'cityscape_{idx}.png')
    print(f"Saved image {idx}: {len(generated_image.image.image_bytes)} bytes")
```

### Specifying Image Size

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Generate with specific size
response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='A detailed portrait of a wise old owl',
    config=types.GenerateImagesConfig(
        image_size="2K",  # Options: "1K" or "2K"
        number_of_images=1
    )
)

response.generated_images[0].image.save('owl_portrait.png')
```

---

## 6. Native Image Generation with Gemini

### Basic Generation with Gemini

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Generate image using Gemini model
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='A cartoon infographic for flying sneakers',
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    )
)

# Access the generated image
if response.candidates:
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'image'):
            # Save or process the image
            with open('flying_sneakers.png', 'wb') as f:
                f.write(part.image.data)
```

### Image Generation with Aspect Ratio

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Generate with custom aspect ratio
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='A minimalist logo for a tech startup',
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",  # Options: "1:1", "4:3", "16:9", "9:16", etc.
        ),
    )
)

# Process response
for candidate in response.candidates:
    for part in candidate.content.parts:
        if hasattr(part, 'image'):
            with open('tech_logo.png', 'wb') as f:
                f.write(part.image.data)
```

### Multi-Image Generation

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Generate multiple images in sequence
prompts = [
    "A serene mountain landscape",
    "A bustling city street",
    "A peaceful zen garden"
]

for idx, prompt in enumerate(prompts):
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        )
    )

    # Save each image
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, 'image'):
                with open(f'scene_{idx}.png', 'wb') as f:
                    f.write(part.image.data)
```

---

## 7. Configuration Options

### GenerateImagesConfig (Imagen)

```python
from google.genai import types

config = types.GenerateImagesConfig(
    # Number of images to generate (1-4)
    number_of_images=2,

    # Image resolution: "1K" (1024x1024) or "2K" (2048x2048)
    image_size="2K",

    # Include RAI (Responsible AI) feedback
    include_rai_reason=True,

    # Output format
    output_mime_type="image/png",  # or "image/jpeg"
)
```

### GenerateContentConfig (Gemini)

```python
from google.genai import types

config = types.GenerateContentConfig(
    # Specify output modality
    response_modalities=["IMAGE"],  # or ["TEXT"], ["TEXT", "IMAGE"]

    # Image-specific configuration
    image_config=types.ImageConfig(
        aspect_ratio="16:9",  # Custom aspect ratio
    ),

    # Temperature for creativity (0.0 to 1.0)
    temperature=0.7,

    # Maximum output tokens
    max_output_tokens=1024,
)
```

### Safety Settings

```python
from google.genai import types

config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    safety_settings=[
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_MEDIUM_AND_ABOVE"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_MEDIUM_AND_ABOVE"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_MEDIUM_AND_ABOVE"
        ),
    ]
)
```

---

## 8. Response Handling

### Imagen Response Structure

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='A mystical forest',
    config=types.GenerateImagesConfig(number_of_images=2)
)

# Access generated images
for idx, generated_image in enumerate(response.generated_images):
    print(f"Image {idx}:")
    print(f"  Size: {len(generated_image.image.image_bytes)} bytes")
    print(f"  Format: {generated_image.image.format}")

    # Save image
    generated_image.image.save(f'forest_{idx}.png')

    # Or get bytes directly
    image_data = generated_image.image.image_bytes

    # Display (if in Jupyter/Colab)
    generated_image.image.show()
```

### Gemini Response Structure

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='A futuristic robot',
    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
)

# Check response structure
print(f"Number of candidates: {len(response.candidates)}")

for candidate in response.candidates:
    print(f"Finish reason: {candidate.finish_reason}")

    for part in candidate.content.parts:
        if hasattr(part, 'image'):
            print(f"Image data size: {len(part.image.data)} bytes")
            with open('robot.png', 'wb') as f:
                f.write(part.image.data)
        elif hasattr(part, 'text'):
            print(f"Text: {part.text}")
```

### Handling RAI Feedback

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='Your prompt here',
    config=types.GenerateImagesConfig(
        include_rai_reason=True  # Enable RAI feedback
    )
)

# Check for RAI information
for generated_image in response.generated_images:
    if hasattr(generated_image, 'rai_info'):
        print(f"RAI Info: {generated_image.rai_info}")
```

---

## 9. Error Handling

### Basic Error Handling

```python
from google import genai
from google.genai import types
import time

def generate_image_with_retry(prompt, max_retries=3):
    """Generate image with retry logic"""
    client = genai.Client(api_key='your-api-key')

    for attempt in range(max_retries):
        try:
            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            return response

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached")
                raise

# Usage
try:
    response = generate_image_with_retry("A beautiful sunset")
    response.generated_images[0].image.save('sunset.png')
except Exception as e:
    print(f"Failed to generate image: {e}")
```

### Handling Specific Errors

```python
from google import genai
from google.genai import types
from google.api_core import exceptions

client = genai.Client(api_key='your-api-key')

try:
    response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt='A magical castle',
        config=types.GenerateImagesConfig(number_of_images=1)
    )

except exceptions.InvalidArgument as e:
    print(f"Invalid argument: {e}")
    print("Check your prompt and configuration")

except exceptions.PermissionDenied as e:
    print(f"Permission denied: {e}")
    print("Check your API key and permissions")

except exceptions.ResourceExhausted as e:
    print(f"Quota exceeded: {e}")
    print("You've hit rate limits or quota")

except exceptions.ServiceUnavailable as e:
    print(f"Service unavailable: {e}")
    print("The service is temporarily unavailable")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Safety Filter Handling

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents='Your prompt here',
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    )

    # Check if content was blocked
    for candidate in response.candidates:
        if candidate.finish_reason == "SAFETY":
            print("Content blocked by safety filters")
            if hasattr(candidate, 'safety_ratings'):
                for rating in candidate.safety_ratings:
                    print(f"  {rating.category}: {rating.probability}")
        else:
            # Process successful generation
            for part in candidate.content.parts:
                if hasattr(part, 'image'):
                    with open('output.png', 'wb') as f:
                        f.write(part.image.data)

except Exception as e:
    print(f"Error: {e}")
```

---

## 10. Best Practices

### 1. Prompt Engineering

```python
# Good: Specific, descriptive prompts
prompt = "A photorealistic image of a golden retriever puppy sitting in a field of wildflowers during golden hour, with soft bokeh background"

# Avoid: Vague prompts
# prompt = "dog"
```

### 2. Resource Management

```python
from google import genai
from google.genai import types
import os

def generate_and_save_image(prompt, output_path):
    """Generate image and handle resources properly"""
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

    try:
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1)
        )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save image
        response.generated_images[0].image.save(output_path)
        print(f"Image saved to {output_path}")

    except Exception as e:
        print(f"Failed to generate image: {e}")
        raise
    finally:
        # Cleanup if needed
        pass

# Usage
generate_and_save_image(
    "A serene lake at dawn",
    "output/images/lake.png"
)
```

### 3. Batch Processing

```python
from google import genai
from google.genai import types
import time

def batch_generate_images(prompts, output_dir="output", delay=1):
    """Generate multiple images with rate limiting"""
    client = genai.Client(api_key='your-api-key')

    os.makedirs(output_dir, exist_ok=True)
    results = []

    for idx, prompt in enumerate(prompts):
        try:
            print(f"Generating image {idx + 1}/{len(prompts)}: {prompt[:50]}...")

            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )

            output_path = f"{output_dir}/image_{idx:03d}.png"
            response.generated_images[0].image.save(output_path)

            results.append({
                'prompt': prompt,
                'output': output_path,
                'success': True
            })

            # Rate limiting
            time.sleep(delay)

        except Exception as e:
            print(f"Failed to generate image {idx}: {e}")
            results.append({
                'prompt': prompt,
                'output': None,
                'success': False,
                'error': str(e)
            })

    return results

# Usage
prompts = [
    "A mountain landscape",
    "A city skyline",
    "A forest path"
]

results = batch_generate_images(prompts)
print(f"Successfully generated {sum(r['success'] for r in results)} images")
```

### 4. Caching Client

```python
from google import genai
import os

# Create client once and reuse
_client = None

def get_client():
    """Get or create a cached client instance"""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
    return _client

# Usage
def generate_image(prompt):
    client = get_client()  # Reuses existing client
    response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1)
    )
    return response
```

---

## 11. Complete Code Examples

### Example 1: Story Illustration Generator

```python
from google import genai
from google.genai import types
import os

class StoryIllustrator:
    """Generate illustrations for story scenes"""

    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def illustrate_scene(self, scene_description, style="photorealistic"):
        """Generate an illustration for a story scene"""
        # Enhance prompt with style
        enhanced_prompt = f"{style} illustration: {scene_description}"

        response = self.client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                image_size="2K"
            )
        )

        return response.generated_images[0].image

    def illustrate_story(self, scenes, output_dir="story_illustrations"):
        """Generate illustrations for multiple scenes"""
        os.makedirs(output_dir, exist_ok=True)
        illustrations = []

        for idx, scene in enumerate(scenes):
            print(f"Illustrating scene {idx + 1}/{len(scenes)}...")

            try:
                image = self.illustrate_scene(scene)
                output_path = f"{output_dir}/scene_{idx:02d}.png"
                image.save(output_path)

                illustrations.append({
                    'scene': scene,
                    'path': output_path,
                    'success': True
                })

            except Exception as e:
                print(f"Failed to illustrate scene {idx}: {e}")
                illustrations.append({
                    'scene': scene,
                    'path': None,
                    'success': False,
                    'error': str(e)
                })

        return illustrations

# Usage
illustrator = StoryIllustrator(api_key=os.getenv('GOOGLE_API_KEY'))

scenes = [
    "A young wizard standing at the entrance of a mysterious forest",
    "The wizard discovering a glowing magical artifact in a cave",
    "A dramatic battle with a dragon in the mountains"
]

results = illustrator.illustrate_story(scenes)
print(f"Generated {sum(r['success'] for r in results)} illustrations")
```

### Example 2: Concept Art Generator

```python
from google import genai
from google.genai import types
import os

class ConceptArtGenerator:
    """Generate multiple variations of concept art"""

    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def generate_variations(self, concept, num_variations=4, output_dir="concepts"):
        """Generate multiple variations of a concept"""
        os.makedirs(output_dir, exist_ok=True)

        response = self.client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=concept,
            config=types.GenerateImagesConfig(
                number_of_images=num_variations,
                image_size="2K"
            )
        )

        paths = []
        for idx, generated_image in enumerate(response.generated_images):
            output_path = f"{output_dir}/variation_{idx:02d}.png"
            generated_image.image.save(output_path)
            paths.append(output_path)
            print(f"Saved variation {idx + 1} to {output_path}")

        return paths

    def iterative_refinement(self, base_concept, refinements):
        """Generate increasingly refined versions"""
        results = []

        for idx, refinement in enumerate(refinements):
            prompt = f"{base_concept}, {refinement}"
            print(f"Generating refinement {idx + 1}: {refinement}")

            response = self.client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1, image_size="2K")
            )

            results.append({
                'refinement': refinement,
                'image': response.generated_images[0].image
            })

        return results

# Usage
generator = ConceptArtGenerator(api_key=os.getenv('GOOGLE_API_KEY'))

# Generate variations
concept = "A futuristic electric vehicle with sleek design"
variations = generator.generate_variations(concept, num_variations=4)

# Iterative refinement
refinements = [
    "concept sketch",
    "with detailed lighting",
    "photorealistic render",
    "in urban environment"
]
refined = generator.iterative_refinement(concept, refinements)
```

### Example 3: Product Mockup Generator

```python
from google import genai
from google.genai import types
import os
from typing import List, Dict

class ProductMockupGenerator:
    """Generate product mockup images"""

    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash-image'

    def generate_mockup(self, product_description, context="white background", aspect_ratio="1:1"):
        """Generate a single product mockup"""
        prompt = f"Professional product photography: {product_description}, {context}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=aspect_ratio)
            )
        )

        # Extract image
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'image'):
                    return part.image.data

        return None

    def generate_product_series(self, product, contexts, output_dir="mockups"):
        """Generate mockups in different contexts"""
        os.makedirs(output_dir, exist_ok=True)
        results = []

        for idx, context in enumerate(contexts):
            print(f"Generating mockup {idx + 1}/{len(contexts)}: {context}")

            try:
                image_data = self.generate_mockup(product, context=context)

                if image_data:
                    output_path = f"{output_dir}/mockup_{idx:02d}.png"
                    with open(output_path, 'wb') as f:
                        f.write(image_data)

                    results.append({
                        'context': context,
                        'path': output_path,
                        'success': True
                    })

            except Exception as e:
                print(f"Failed to generate mockup {idx}: {e}")
                results.append({
                    'context': context,
                    'path': None,
                    'success': False,
                    'error': str(e)
                })

        return results

# Usage
generator = ProductMockupGenerator(api_key=os.getenv('GOOGLE_API_KEY'))

product = "sleek wireless headphones in matte black"
contexts = [
    "white background with soft shadows",
    "on a wooden desk with laptop",
    "lifestyle shot with person using them",
    "floating in minimalist studio setup"
]

results = generator.generate_product_series(product, contexts)
print(f"Generated {sum(r['success'] for r in results)} mockups")
```

---

## 12. Advanced Features

### Aspect Ratio Control

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Different aspect ratios for different use cases
aspect_ratios = {
    'square': '1:1',        # Instagram posts
    'portrait': '9:16',     # Mobile, Stories
    'landscape': '16:9',    # Desktop, YouTube
    'wide': '21:9',         # Ultrawide displays
    'vertical': '4:5',      # Instagram portrait
}

for name, ratio in aspect_ratios.items():
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents='A minimalist mountain landscape',
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=ratio)
        )
    )

    # Save with descriptive name
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if hasattr(part, 'image'):
                with open(f'landscape_{name}_{ratio.replace(":", "x")}.png', 'wb') as f:
                    f.write(part.image.data)
```

### Interleaved Text and Image Output

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Generate both text description and image
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='Create a logo for a coffee shop called "Morning Brew" and explain the design',
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    )
)

# Process mixed response
for candidate in response.candidates:
    for part in candidate.content.parts:
        if hasattr(part, 'text'):
            print(f"Design explanation: {part.text}")
        elif hasattr(part, 'image'):
            with open('morning_brew_logo.png', 'wb') as f:
                f.write(part.image.data)
            print("Logo saved")
```

### Image Generation with Search Grounding

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='your-api-key')

# Use search grounding for factual accuracy
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='Generate an accurate architectural rendering of the Eiffel Tower',
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        # Note: Search grounding may require additional API setup
    )
)

for candidate in response.candidates:
    for part in candidate.content.parts:
        if hasattr(part, 'image'):
            with open('eiffel_tower.png', 'wb') as f:
                f.write(part.image.data)
```

---

## Resources

### Official Documentation
- [Image Generation with Gemini](https://ai.google.dev/gemini-api/docs/image-generation)
- [Imagen API Reference](https://ai.google.dev/gemini-api/docs/imagen)
- [Google Gen AI SDK Documentation](https://googleapis.github.io/python-genai/)
- [GitHub - Google Gemini Cookbook](https://github.com/google-gemini/cookbook)

### Tutorials and Guides
- [Imagen 3: A Guide With Examples](https://www.datacamp.com/tutorial/imagen-3)
- [Image Generation API - Google Cloud](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/imagen-api)

### Additional Resources
- [Google Gen AI Python SDK (GitHub)](https://github.com/googleapis/python-genai)
- [Vertex AI Image Generation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-generation)

---

## API Limits and Quotas

### Rate Limits
- **Imagen**: Varies by model and tier (check your API console)
- **Gemini**: Generally higher throughput than Imagen
- **Best Practice**: Implement exponential backoff retry logic

### Image Limits
- **Number of Images**: 1-4 per request (Imagen)
- **Image Size**: Up to 2K for Imagen, 4K for Gemini Pro
- **Format**: PNG, JPEG supported

### Cost Optimization
1. Use appropriate model for your needs (Imagen 3.0 vs 4.0)
2. Generate only the number of images you need
3. Use caching when possible
4. Batch requests efficiently

---

## Troubleshooting

### Common Issues

**Issue: "Invalid API Key"**
```python
# Solution: Verify API key is set correctly
import os
print(f"API Key set: {'GOOGLE_API_KEY' in os.environ}")
```

**Issue: "Quota Exceeded"**
```python
# Solution: Implement rate limiting and backoff
import time
time.sleep(2)  # Wait between requests
```

**Issue: "Content Blocked by Safety Filters"**
```python
# Solution: Review and adjust prompt, check safety settings
# Make prompts more specific and appropriate
```

**Issue: "Model Not Found"**
```python
# Solution: Verify model ID is correct
# Use: 'imagen-3.0-generate-002' or 'gemini-2.5-flash-image'
```

---

## Summary

Google's GenAI Python SDK provides powerful image generation capabilities through:

1. **Imagen**: For high-fidelity, production-grade images
2. **Gemini**: For context-aware, multi-modal generation

Key takeaways:
- Use Imagen for standalone image generation tasks
- Use Gemini for interactive, context-rich workflows
- Always handle errors and implement retry logic
- Follow rate limits and quota guidelines
- Write specific, descriptive prompts for best results
- Save API keys in environment variables
- Process responses carefully to extract images

Start with basic examples and gradually explore advanced features like aspect ratio control, batch processing, and multi-modal outputs.
