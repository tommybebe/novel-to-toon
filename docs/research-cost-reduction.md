# Gemini API Cost Reduction Research

## Overview

This document summarizes research on reducing Google Gemini API spending for the novel-to-webtoon workflow. Current POC spending (~$12) is not sustainable for production use.

---

## 1. Image Size Optimization

### Supported Resolutions and Pricing

| Model | Resolution | Cost per Image |
|-------|-----------|----------------|
| gemini-3-pro-image-preview | 1K-2K (1024-2048px) | $0.134 |
| gemini-3-pro-image-preview | 4K (4096px) | $0.24 |
| gemini-2.5-flash-image | 1K (1024px) | $0.039 |

**Key Insight**: Gemini pricing is the same for 1K and 2K within the same tier ($0.134). No savings from reducing 2K to 1K on gemini-3-pro.

### Webtoon Resolution Requirements

- **WEBTOON platform max upload**: 800x1280 pixels
- **Recommended working size**: 1600x2560 pixels (2x for quality)
- **Mobile-first viewing**: Optimized for vertical scrolling on smartphones

**Recommendation**: 1K resolution (1024x1024) is sufficient for webtoon panels. 2K provides no benefit for mobile viewing and 4K is wasteful (80% premium).

---

## 2. Alternative Models

### Available Image Generation Models

| Model | Resolution | Cost/Image | Quality | Speed | Best For |
|-------|-----------|-----------|---------|-------|----------|
| gemini-2.5-flash-image | Up to 1024x1024 | **$0.039** | High | Very Fast | Rapid iteration, batch generation |
| gemini-3-pro-image-preview | Up to 4096x4096 | $0.134-$0.24 | Highest | Slower | Complex scenes, character consistency |
| imagen-4-fast | Variable | $0.02 | Good | Fastest | Budget-conscious work |
| imagen-4-standard | Variable | $0.04 | High | Standard | Balanced option |
| imagen-4-ultra | Variable | $0.06 | Excellent | Slower | Premium quality needs |

### Model Comparison: Gemini 3 Pro vs 2.5 Flash

| Feature | Gemini 3 Pro | Gemini 2.5 Flash |
|---------|-------------|------------------|
| Cost per image | $0.134 | $0.039 |
| Max reference images | 14 | Limited |
| Human identity preservation | Up to 5 subjects | Basic |
| Quality | Highest | High |
| Speed | 5-8 seconds | 3-4 seconds |
| Best use case | Character introductions, complex scenes | Regular panels, environments |

### Recommended Hybrid Approach

Use **80% Gemini 2.5 Flash + 20% Gemini 3 Pro**:

- **Gemini 2.5 Flash** ($0.039/image):
  - Regular panels and scene generation
  - Environment/background shots
  - Rapid prototyping and iterations
  - Minor character appearances

- **Gemini 3 Pro** ($0.134/image):
  - Character introduction scenes
  - Complex multi-character compositions
  - Scenes requiring strict character consistency
  - Final quality assurance passes

**Hybrid Cost**: (0.8 x $0.039) + (0.2 x $0.134) = **$0.058/image** (57% savings)

---

## 3. API Optimization Techniques

### 3.1 Batch Processing (50% Discount)

Google offers batch processing for non-urgent, asynchronous tasks at 50% discount.

**How to use**:
- Accumulate panel generation requests
- Submit as batch job for overnight processing
- Trade real-time response for significant savings

**Batch Pricing**:
| Model | Standard | Batch (50% off) |
|-------|----------|-----------------|
| gemini-2.5-flash-image | $0.039 | $0.0195 |
| gemini-3-pro-image-preview | $0.134 | $0.067 |

### 3.2 Context Caching (90% Discount on Cached Tokens)

Cache repeated content for 90% discount on input tokens:

**What to cache**:
- Character descriptions and reference specifications
- Art style guidelines and prompt templates
- Story context and scene descriptions
- System prompts for agents

**Implementation**:
```python
# First request establishes cache
cached_content = client.caches.create(
    model="gemini-2.5-flash",
    contents=[style_guide, character_specs, ...]
)

# Subsequent requests use cache at 90% discount
response = client.models.generate_content(
    model="gemini-2.5-flash",
    cached_content=cached_content.name,
    contents=[panel_specific_prompt]
)
```

### 3.3 Implicit Caching (Automatic)

For Gemini 2.5 models only:
- Automatically enabled
- Provides 90% discount when requests share common prefixes
- No setup required

### 3.4 Input Token Reduction

**Strategies**:
1. Use bullet points instead of prose descriptions
2. Create reusable prompt templates
3. Remove redundant style keywords
4. Use shorter, more direct language

**Estimated savings**: 10-15% reduction in input tokens

### 3.5 Minimize Multi-Turn Editing

Multi-turn editing accumulates context costs (each turn re-bills previous tokens).

**Optimization**:
- Generate complete panels in single turn
- Use detailed one-shot prompts instead of conversation
- Reserve multi-turn only for final QA adjustments

---

## 4. Cost Comparison Summary

### Cost Per Image Across Strategies

| Strategy | Model | Method | Cost/Image | vs Baseline |
|----------|-------|--------|-----------|-------------|
| Current (Baseline) | Gemini 3 Pro | Standard, 2K | $0.134 | - |
| Resolution only | Gemini 3 Pro | Standard, 1K | $0.134 | 0% |
| Model switch | Gemini 2.5 Flash | Standard | $0.039 | -71% |
| Model + Batch | Gemini 2.5 Flash | Batch | $0.0195 | -85% |
| Hybrid | 80% Flash + 20% Pro | Standard | $0.058 | -57% |
| Hybrid + Batch | 80% Flash + 20% Pro | Batch | $0.029 | -78% |
| Full optimization | Hybrid + Batch + Cache | All | $0.02-0.025 | -82% |

### Chapter Cost Estimates (20 panels)

| Scenario | Cost/Chapter | Monthly (15 ch) | Annual |
|----------|-------------|-----------------|--------|
| Current | $2.68 | $40.20 | $482 |
| Model switch only | $0.78 | $11.70 | $140 |
| Hybrid + Batch | $0.58 | $8.70 | $104 |
| Full optimization | $0.40-0.50 | $6-7.50 | $72-90 |

### POC Cost Comparison

- **Original POC** (~90 images): $12.06
- **With full optimization**: $1.80-2.25 (82% reduction)

---

## 5. Implementation Recommendations

### Phase 1: Immediate (Week 1) - 70% Savings

1. **Switch to Gemini 2.5 Flash** for 80% of generation
2. **Use 1K resolution** instead of 2K (no quality loss for mobile)
3. **Implement batch processing** for overnight runs

### Phase 2: Medium-term (Weeks 2-4) - Additional 10-15%

4. **Implement context caching** for style guides and character specs
5. **Optimize prompt structure** for token efficiency
6. **Strategic Gemini 3 Pro use** only when necessary

### Phase 3: Long-term - Operational Excellence

7. **Pre-compute reference library** (generate once, use forever)
8. **Monitor and analyze** which panels need premium models
9. **Regular cost audits** and optimization reviews

---

## 6. Migration Alert

**Important**: The following models will be retired on **October 31, 2025**:
- `gemini-2.0-flash-preview-image-generation`
- `gemini-2.5-flash-image-preview`

**Action Required**: Migrate to stable `gemini-2.5-flash-image` before retirement date.

---

## 7. Free Tier Value

Google AI Studio provides:
- **1,500 free image generations daily**
- Rate limit: ~10 requests per minute
- Perfect for development and testing

**Recommendation**: Use free tier during development, paid API for production batches.

---

## Sources

- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Image Generation Documentation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Context Caching Guide](https://ai.google.dev/gemini-api/docs/caching)
- [Batch Inference Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/batch-prediction-gemini)
- [WEBTOON Canvas Size Guidelines](https://webtooncanvas.zendesk.com/hc/en-us/articles/32913712749588)
