# AI Image Generation Platforms - Complete Comparison

## Executive Summary

**Key Discovery:** fal.ai offers the **cheapest Flux access** at $0.005-0.030/MP, significantly undercutting both BFL.ai and other platforms.

**Decision Point:** User will add $10 credit to either fal.ai or BFL.ai for testing.

---

## Platform Comparison Overview

### Quick Reference Table

| Platform | Type | Pricing Model | Best Models | Free Trial | Notes |
|----------|------|---------------|-------------|------------|-------|
| **fal.ai** | Marketplace | Pay-per-MP | Flux 2, SD, Grok, etc. | ❌ None (as of Feb 2026) | Cheapest Flux access |
| **BFL.ai** | Official API | Pay-per-MP | FLUX.2 family | ❌ None (as of Feb 2026) | Multi-ref support (up to 10) |
| **Replicate** | Marketplace | Pay-per-run | Various | ❌ Pay-as-you-go | 10-25% markup vs source |
| **Gemini API** | Direct API | Fixed price | Imagen 4 | ❌ Pay-as-you-go | Google ecosystem |

---

## Platform Details

### 1. fal.ai - AI Model Marketplace

**What it is:** Multi-vendor platform hosting models from various providers (BFL, Stability AI, Google, xAI, Tencent, etc.)

#### Available FLUX Models

| Model | Pricing | Best For |
|-------|---------|----------|
| **Flux 2 Flash** | $0.005/MP | Ultra-fast, lowest cost ⭐ |
| **Flux 2 Turbo** | $0.008/MP | Balanced speed/quality |
| **Flux 2 [dev]** | $0.012/MP | Standard quality, LoRA compatible |
| **Flux 2 [pro]** | $0.030/MP | Professional grade |
| **Flux 2 Flex** | $0.060/MP | Typography specialist |

#### Other Notable Models

- **SDXL Lightning/Turbo**: $0.0015/MP (extremely cheap, legacy)
- **SD 3.5 Medium**: $0.030/image
- **Grok Imagine Image**: Available (pricing TBD)
- **Nano Banana Pro**: $0.0398/image (product photography)
- **Hunyuan 3D**: Various (3D generation)

#### Pros
- ✅ **Cheapest Flux access** available
- ✅ **Wide model selection** (100+ models)
- ✅ **No subscription required** (pay-as-you-go)
- ✅ **Fast deployment** (optimized infrastructure)
- ✅ **LoRA training available** ($2/hour on H100)

#### Cons
- ❌ **No free trial** (as of Feb 2026)
- ❌ **May not support multi-reference** (need to verify)
- ❌ **Third-party hosting** (slight delay vs official)

#### Pricing Formula (Megapixel Based)
```
1024x1024 = 1.05 MP
1024x1440 = 1.47 MP
2048x2048 = 4.19 MP

Example (Flux 2 Flash):
1024x1440 panel = 1.47 MP × $0.005 = $0.00735/panel
```

---

### 2. BFL.ai - Official Flux API

**What it is:** Black Forest Labs' official API platform (creators of Flux, former Stability AI team)

#### FLUX.2 Models (Feb 2025 Release)

| Model | Pricing | Multi-Reference | Best For |
|-------|---------|-----------------|----------|
| **FLUX.2 [klein] 9B** | 1st MP: $0.015, +$0.002/MP | 4 refs | Budget + consistency |
| **FLUX.2 [klein] 4B** | Similar pricing | 4 refs | Faster variant |
| **FLUX.2 [pro]** | 1st MP: $0.03, +$0.015/MP | 10 refs | Production grade ⭐ |
| **FLUX.2 [max]** | 1st MP: $0.07, +$0.03/MP | 10 refs | Highest quality |
| **FLUX.2 [flex]** | TBD | 10 refs | Typography |

#### Multi-Reference Feature (KILLER FEATURE)

**Load up to 10 reference images simultaneously:**
```python
references = [
    {'image_url': 'char1.png', 'label': 'char1', 'strength': 0.8},
    {'image_url': 'char2.png', 'label': 'char2', 'strength': 0.8},
    {'image_url': 'artifact.png', 'label': 'weapon', 'strength': 0.7},
    {'image_url': 'background.png', 'label': 'bg', 'strength': 0.5}
]
```

**Consistency: 90-95%** according to BFL documentation

#### Pros
- ✅ **Multi-reference support** (up to 10 images!)
- ✅ **Official source** (latest features first)
- ✅ **Best for character consistency** (90-95%)
- ✅ **Hex color control** (brand colors)
- ✅ **Text rendering** (speech bubbles)
- ✅ **10-25% cheaper than Replicate**

#### Cons
- ❌ **No free trial** (as of Feb 2026)
- ❌ **More expensive than fal.ai** (for same Flux models)
- ❌ **Only Flux models** (no diversity)

#### Pricing Formula
```
First megapixel: Base price
Additional MPs: Incremental price

Example (FLUX.2 [pro]):
1024x1440 = 1.47 MP
Cost = $0.03 + (0.47 × $0.015) = $0.037/panel
```

---

### 3. Google Gemini API

**What it is:** Google's direct API for Imagen 4 image generation

#### Models

| Model | Pricing | Best For |
|-------|---------|----------|
| **Gemini 2.0 Flash** | $0.039/image (1K-2K) | Speed + cost |
| **Gemini 2.0 Pro** | $0.134/image (1K-2K) | Quality + control |

**Note:** Resolution 1K-2K costs THE SAME ($0.039 or $0.134)

#### Pros
- ✅ **Reference image support** (1 image)
- ✅ **Google ecosystem** integration
- ✅ **Fast generation** (2-4s)
- ✅ **Batch pricing** (50% off)
- ✅ **API-first** design

#### Cons
- ❌ **Consistency unproven** for webtoons
- ❌ **Single reference only** (vs BFL's 10)
- ❌ **Strict content filters**
- ❌ **"AI plastic" look** sometimes
- ❌ **No LoRA support**

---

## Cost Analysis: Episode 1 (68 panels)

### Comparative Costs (All Platforms)

| Platform | Model | Panel Cost | Ep 1 Total | Notes |
|----------|-------|------------|------------|-------|
| **fal.ai** | **Flux 2 Flash** | **$0.012** | **$0.81** | CHEAPEST ⭐⭐⭐ |
| **fal.ai** | Flux 2 Turbo | $0.016 | $1.12 | Fast + cheap |
| **fal.ai** | Flux 2 [dev] | $0.022 | $1.52 | LoRA compatible |
| **BFL.ai** | FLUX.2 [klein] 9B | $0.030 | $2.01 | Multi-ref (4) |
| **fal.ai** | Flux 2 [pro] | $0.049 | $3.36 | At target! |
| **BFL.ai** | FLUX.2 [pro] | $0.081 | $5.54 | Multi-ref (10) ⭐ |
| **Gemini** | Flash + Pro mix | $0.067 | $4.53 | Original plan |
| **BFL.ai** | FLUX.2 [max] | $0.146 | $9.90 | Premium quality |

**Target: <$0.05/panel** (averaged over 10 episodes)

### 10-Episode Projections

| Platform | Model | Avg Cost/Panel | 10-Ep Total | Viable? |
|----------|-------|----------------|-------------|---------|
| **fal.ai** | Flux 2 Flash | **$0.009** | **$6.12** | ✅ BEST VALUE |
| **fal.ai** | Flux 2 [dev] | $0.017 | $11.56 | ✅ Excellent |
| **BFL.ai** | FLUX.2 [klein] | $0.020 | $13.89 | ✅ Great |
| **Gemini** | Optimized | $0.036 | $24.33 | ✅ Good |
| **fal.ai** | Flux 2 [pro] | $0.042 | $28.56 | ✅ At target |
| **BFL.ai** | FLUX.2 [pro] | $0.062 | $42.44 | ✅ Premium |

**All options achieve <$0.05/panel at scale!**

---

## Multi-Reference Support Comparison

### Single Reference (Gemini, fal.ai Flux 2)

**How it works:**
```python
generate_image(
    prompt="Jin Sohan talking to Dokma in Magic Tower",
    reference_image="jin_sohan.png"
)
```

**Limitation:** Can only reference 1 character/element at a time

**Workaround:** Generate panels with one character, then composite manually (adds time/cost)

### Multi-Reference (BFL.ai FLUX.2)

**How it works:**
```python
generate_image(
    prompt="Jin Sohan (char1) and Dokma (char2) in Magic Tower (bg1)",
    references=[
        {'image': 'jin_sohan.png', 'label': 'char1', 'strength': 0.8},
        {'image': 'dokma.png', 'label': 'char2', 'strength': 0.8},
        {'image': 'tower.png', 'label': 'bg1', 'strength': 0.5}
    ]
)
```

**Advantage:** All characters maintain consistency in single generation

**Value:** Saves time, reduces compositing, better scene coherence

---

## Free Trial Status (Feb 2026)

| Platform | Free Trial | Status |
|----------|------------|--------|
| **BFL.ai** | ❌ None | Removed ~2 months ago (Reddit confirmation) |
| **fal.ai** | ❌ None | Removed (user confirmation) |
| **Replicate** | ❌ None | Pay-per-use only |
| **Gemini API** | ❌ None | Pay-per-use only |
| **Together AI** | ✅ FREE FLUX.1 [schnell] | Older model, permanently free |
| **Hugging Face** | ✅ FREE Spaces | Queue-based, no API |

**Reality:** Must pay to test production models

---

## Testing Strategy with $10 Credit

### Option 1: Split Budget ($5 each)

Test both platforms:
- **fal.ai** ($5): Test Flux 2 Flash, Turbo, [dev]
- **BFL.ai** ($5): Test FLUX.2 [klein] 9B, [pro]

**Generations possible:**
- fal.ai: ~680 panels (Flux 2 Flash)
- BFL.ai: ~166 panels (FLUX.2 [klein])

### Option 2: All-in fal.ai ($10)

Maximum testing budget:
- Flux 2 Flash: ~1,360 panels
- Can test Flash, Turbo, [dev], [pro]
- Full PoC + 1-2 episodes possible

### Option 3: All-in BFL.ai ($10)

Focus on multi-reference:
- FLUX.2 [klein]: ~333 panels
- FLUX.2 [pro]: ~120 panels
- Full PoC possible with premium consistency

---

## Recommendation Matrix

### Quick Decision Tree

```
Primary concern: COST
├─ fal.ai Flux 2 Flash ($0.012/panel) ⭐
└─ Need multi-ref? → BFL.ai FLUX.2 [klein] ($0.030/panel)

Primary concern: QUALITY + CONSISTENCY
├─ BFL.ai FLUX.2 [pro] ($0.081/panel, 10-ref) ⭐
└─ Budget tight? → fal.ai Flux 2 [dev] ($0.022/panel)

Primary concern: EASE OF USE
├─ Gemini ($0.067/panel) - Simple API
└─ Don't care about cost? → fal.ai Flux 2 [pro] ($0.049/panel)

Need to test BOTH platforms?
├─ Split $10 budget ($5 each)
└─ Test 3-5 models total
```

### Final Recommendations (Priority Order)

#### 1. fal.ai Flux 2 Flash (BEST VALUE)
- **Cost:** $0.012/panel (76% under target!)
- **10-episode:** $6.12 total
- **Use if:** Budget is primary concern
- **Risk:** Consistency unknown (must test)

#### 2. BFL.ai FLUX.2 [pro] (BEST QUALITY)
- **Cost:** $0.081/panel
- **10-episode:** $42.44 total
- **Use if:** Need proven 90-95% consistency
- **Feature:** 10-reference support

#### 3. fal.ai Flux 2 [dev] (BEST BALANCE)
- **Cost:** $0.022/panel (56% under target!)
- **10-episode:** $11.56 total
- **Use if:** Want LoRA compatibility + low cost
- **Feature:** Can train custom LoRAs

#### 4. BFL.ai FLUX.2 [klein] 9B (MULTI-REF BUDGET)
- **Cost:** $0.030/panel (40% under target)
- **10-episode:** $13.89 total
- **Use if:** Need multi-ref but budget matters
- **Feature:** 4-reference support

---

## Week 1 Validation Test Plan

### Recommended Tests ($0.90 with $10 credit)

**Test Setup:**
1. Generate 1 character base reference
2. Generate 5-10 variations with that reference
3. Measure facial consistency (visual comparison)
4. Calculate actual cost

**Models to Test:**

| Platform | Model | Test Cost | Generations |
|----------|-------|-----------|-------------|
| fal.ai | Flux 2 Flash | $0.12 | 10 variations |
| fal.ai | Flux 2 [dev] | $0.22 | 10 variations |
| BFL.ai | FLUX.2 [klein] | $0.30 | 10 variations |
| BFL.ai | FLUX.2 [pro] | $0.81 | 10 variations |
| **Total** | **4 models** | **$1.45** | **40 images** |

**Remaining budget: $8.55** for PoC or additional testing

### Success Criteria

| Consistency | Action |
|-------------|--------|
| **>=90%** | Production ready, use immediately |
| **80-89%** | Acceptable, proceed with optimization |
| **70-79%** | Needs LoRA training or prompt refinement |
| **<70%** | Reject, try different model |

---

## Implementation Notes

### API Endpoints

**fal.ai:**
```python
import fal_client

result = fal_client.run(
    "fal-ai/flux-2/flash",  # or turbo, dev, pro
    arguments={
        "prompt": "...",
        "image_size": {"width": 1024, "height": 1440}
    }
)
```

**BFL.ai:**
```python
import requests

response = requests.post(
    'https://api.bfl.ai/v1/flux-2-pro',
    headers={'x-key': BFL_API_KEY},
    json={
        'prompt': '...',
        'width': 1024,
        'height': 1440,
        'references': [...]  # Multi-ref support
    }
)
```

**Gemini:**
```python
import google.generativeai as genai

model = genai.ImageGenerationModel("imagen-4")
result = model.generate_images(
    prompt="...",
    reference_images=["..."],  # Single ref only
    number_of_images=1
)
```

---

## Bottom Line

**Decision Point:** User will add $10 to either fal.ai or BFL.ai

**My Recommendation:**
1. **Add $10 to fal.ai** (more bang for buck)
2. Test Flux 2 Flash, [dev], and [pro]
3. If consistency passes → Use Flux 2 Flash ($0.012/panel)
4. If Flash fails → Use Flux 2 [dev] ($0.022/panel) + LoRA
5. Only add to BFL.ai if multi-ref (10 images) is critical

**Expected Outcome:**
- Flux 2 Flash will likely pass 80%+ consistency
- $10 covers full Week 1 validation + partial PoC
- Total project cost: <$10 for 10 episodes at scale

**fal.ai Flux 2 Flash is the likely winner** - test it first!
