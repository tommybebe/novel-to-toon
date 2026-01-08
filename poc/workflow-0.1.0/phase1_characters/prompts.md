# Phase 1: Character Design Prompt Templates

## Overview

This document contains the prompt templates used for character generation in the novel-to-webtoon PoC.
The workflow uses a two-step approach for consistency:

1. **Step 1**: Generate base reference image (no input reference)
2. **Step 2**: Generate variations using base reference as input

## Base Reference Template

Used for initial character generation without reference images.

```
Korean webtoon style character portrait:
- Character: {name} ({korean_name}), {age}, {role}
- Key Features: {features}
- Expression: Neutral, calm expression
- Pose: Front view, straight posture
- Attire: {clothing}
- Atmosphere: {atmosphere}
- Style: Korean webtoon (manhwa), clean detailed linework, cel-shaded with gradient accents
- Composition: Upper body portrait, centered
- Background: Simple neutral gradient
- Quality: High detail, publication ready, no text

IMPORTANT STYLE ELEMENTS TO ESTABLISH:
- Line weight: Medium with varied thickness for emphasis
- Shading: Cel-shaded with soft gradients
- Color palette: {color_info}
```

## Variation Templates

All variation templates use the base reference image as input.

### Neutral Variation

```
Generate the SAME character from the reference image with the following changes:
- Expression: Neutral, calm expression
- Pose: Front view, straight posture
- Background: Simple neutral gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette
```

### Angry Variation

```
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
```

### Smile Variation

```
Generate the SAME character from the reference image with the following changes:
- Expression: Subtle smile, relaxed expression
- Pose: Side profile view
- Background: Warm gradient

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette
```

### Action Variation

```
Generate the SAME character from the reference image with the following changes:
- Expression: Focused, battle-ready
- Pose: Dynamic action pose, martial arts stance
- Background: Action-oriented, motion effects

MAINTAIN EXACTLY from reference:
- Face shape and all facial features
- Hair style, length, and color
- Clothing design and colors
- Art style, line weight, and shading technique
- Color palette
```

## Twin Character Template

For generating twin characters with identical faces but different atmospheres.

```
Generate the SAME face from the reference image as a full character:
- Character: {name} ({korean_name})
- Expression: {expression}
- Attire: {clothing}
- Atmosphere: {atmosphere}
- Complexion: {complexion}

MAINTAIN EXACTLY from reference:
- Face shape and all facial features (this is a TWIN - must match exactly)
- Art style and line weight

Important: This is [twin name]'s identical twin brother, so the face must be EXACTLY the same.
```

## Character Specifications

### Jin Sohan

| Attribute | Value |
|-----------|-------|
| Korean Name | 진소한 (眞昭悍) |
| Age | 26 years old |
| Role | Main protagonist, former member of Sword Dance Troupe |
| Visual Features | Cloudy/murky eye color (poison exposure), sharp handsome features, athletic build |
| Clothing | Dark traditional martial arts robes (dark gray/navy) |
| Atmosphere | Determined, mysterious, hidden strength |
| Color Palette | #2d2d44, #4a4a6a, #6b6b8a, #8b8ba3 |

### Dokma (Poison Demon)

| Attribute | Value |
|-----------|-------|
| Korean Name | 독마 (毒魔) |
| Age | Middle-aged (appears 50s) |
| Role | One of the twin masters, Poison Master |
| Visual Features | Dark complexion, identical twin face with Uiseon, sinister knowing eyes, cynical smirk |
| Clothing | Black traditional robes (흑의), flowing dark fabric |
| Atmosphere | Dark, poisonous, mysterious, cynical |
| Color Palette | #0d0d0d, #1a1a1a, #333333, #4a4a4a |

### Uiseon (Medicine Sage)

| Attribute | Value |
|-----------|-------|
| Korean Name | 의선 (醫仙) |
| Age | Middle-aged (appears 50s) |
| Role | One of the twin masters, Medicine Sage |
| Visual Features | Fair/scholarly complexion, identical twin face with Dokma, gentle wise eyes, warm smile |
| Clothing | White traditional robes (백의), pristine and elegant |
| Atmosphere | Clean, healing, serene, scholarly |
| Color Palette | #f5f5f5, #e0e0e0, #cccccc, #b8b8b8 |

## API Configuration

- **Model**: gemini-3-pro-image-preview
- **Aspect Ratio**: 1:1 (portraits), 9:16 (action poses)
- **Response Modalities**: IMAGE
- **Reference Image Support**: Up to 14 images, 5 human subjects

## Results Summary

| Character | Base Reference | Variations | Total |
|-----------|---------------|------------|-------|
| Jin Sohan | 1 (540KB) | 4 (2.0MB) | 5 |
| Dokma | 1 (511KB) | 4 (2.0MB) | 5 |
| Uiseon | 1 (490KB) | 4 (1.9MB) | 5 |
| Twin Comparison | - | 1 (730KB) | 1 |
| **Total** | **3** | **13** | **16** |

Success Rate: 100% (16/16 images generated successfully)
