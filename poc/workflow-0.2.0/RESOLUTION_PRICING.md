# Resolution vs Pricing - The Definitive Answer

## TL;DR: **1K and 2K cost THE SAME**

Reducing resolution from 2K to 1K will **NOT save money**. Only dropping to 512px or going up to 4K changes the cost.

---

## Official Gemini API Image Pricing

### Gemini Pro (gemini-3-pro-image-preview)

| Resolution | Pixel Size | Token Cost | Price (Standard) | Price (Batch 50% off) |
|------------|-----------|------------|------------------|----------------------|
| **1K** | 1024×1024 | 1,120 tokens | **$0.134** | $0.067 |
| **2K** | 2048×2048 | 1,120 tokens | **$0.134** | $0.067 |
| **4K** | 4096×4096 | 2,000 tokens | **$0.240** | $0.120 |

**Key Finding:** 1K and 2K use **identical token count** → **identical cost**

### Gemini Flash (gemini-2.5-flash-image)

| Resolution | Price (Standard) | Price (Batch 50% off) |
|------------|------------------|----------------------|
| **Any** | $0.039 | $0.0195 |

Flash has **flat pricing** regardless of resolution (within 1K-2K range).

---

## What This Means for Our PoC

### ❌ These Changes Don't Save Money

```
Changing 2K → 1K for panels: $0 savings
Changing 2K → 1K for references: $0 savings
```

**Why?** Both resolutions cost exactly $0.134 per image (Pro) or $0.039 (Flash).

### ✅ These Changes DO Save Money

| Change | Savings/Image | When to Use |
|--------|--------------|-------------|
| **Pro → Flash** | $0.095 | Most panels (80%) |
| **Real-time → Batch** | 50% (half cost) | Non-urgent generation |
| **Avoid 4K** | $0.106 | Never use 4K unless critical |
| **Use 512px for sketches** | ~$0.02-0.03 | Rough layouts only |

---

## Revised Optimization Strategy

### Current v0.2.0 Strategy (Still Correct)

Our cost projections already assumed 1K for panels and 2K for references, but now we know:

**This distinction doesn't matter for cost** - it's purely a quality decision.

### What Actually Matters

#### 1. Model Selection (Biggest Impact)

```
Pro:   $0.134/image
Flash: $0.039/image
Savings: $0.095/image (71% reduction) ✅
```

**Our 80/20 split saves:**
- 54 panels at Flash instead of Pro: 54 × $0.095 = **$5.13 saved**

#### 2. Batch Processing (Massive Impact)

```
Real-time: $0.134 (Pro) or $0.039 (Flash)
Batch:     $0.067 (Pro) or $0.0195 (Flash)
Savings: 50% ✅
```

**Using batch for 90% of generation saves:**
- ~100 images at 50% off: **$4.00+ saved**

#### 3. Resolution (Only for Quality)

Since 1K and 2K cost the same:

**Use 2K for:**
- Character base references (need detail for consistency)
- Artifact base references (need detail for consistency)
- Any "master reference" that will be reused

**Use 1K for:**
- Panel generation (sufficient for 800px platform requirement)
- Character/artifact variations (master already exists)
- Backgrounds (will be composited)

**This is a quality choice, not a cost choice.**

---

## Updated Cost Scenarios

### Scenario: What if we used 512px resolution?

**Estimated cost:** ~$0.02-0.03/image (lower token count)

| Component | Current (1K-2K) | With 512px | Savings |
|-----------|----------------|------------|---------|
| Characters | $0.63 | $0.30 | $0.33 |
| Artifacts | $0.96 | $0.45 | $0.51 |
| Backgrounds | $0.67 | $0.30 | $0.37 |
| Panels (68) | $1.99 | $0.90 | $1.09 |
| **TOTAL** | **$4.53** | **$2.16** | **$2.37 (52%)** ✅

**Trade-off:** Significantly lower quality
- 512px panels upscaled to 800px will look pixelated
- References won't have enough detail for consistency
- Professional platforms reject low-res content

**Verdict:** Not recommended for production, but viable for rough prototyping.

---

## Recommendations

### For v0.2.0 PoC

**Don't change resolution strategy** - it's already optimal:

```
✅ Use 2K for base references (quality, no extra cost)
✅ Use 1K for panels (sufficient quality, no cost savings anyway)
✅ Focus on model selection (Pro vs Flash) - this DOES save money
✅ Focus on batch processing - this DOES save money (50%)
```

### If Budget is Still Too High

**Instead of reducing resolution, do this:**

1. **Increase Flash usage** (Currently 80%, could go to 90%)
   - Use Pro only for character close-ups and emotional climaxes
   - Savings: ~$0.50-1.00

2. **Reduce variations** (Currently 12 char + 15 artifact variations)
   - Cut character variations from 12 → 6
   - Cut artifact variations from 15 → 8
   - Savings: ~$0.50

3. **Use Flash for artifact bases** (Currently Pro)
   - Artifacts don't need Pro quality
   - Savings: ~$0.47

4. **Skip rough sketches entirely** (If doing Phase 0.5)
   - Only needed if testing layout
   - Savings: ~$1.00-1.50

---

## The Resolution Myth - Busted

### Common Misconception

> "Let's use 1K instead of 2K to save money"

### Reality

**1K and 2K cost exactly the same** ($0.134 for Pro, $0.039 for Flash)

Both resolutions consume **1,120 tokens**, priced identically.

### What DOES Save Money

1. ✅ **Model choice** (Flash vs Pro): 71% savings
2. ✅ **Batch processing**: 50% savings
3. ✅ **Reducing image count** (fewer variations): Direct savings
4. ❌ **Resolution** (1K vs 2K): $0 savings

---

## API Pricing Table (Reference)

### Gemini 3 Pro Image Preview

| Config | Resolution | Batch? | Cost/Image | Use For |
|--------|-----------|--------|------------|---------|
| Standard | 1K-2K | No | $0.134 | Real-time critical images |
| Standard | 4K | No | $0.240 | Never (overkill) |
| Batch | 1K-2K | Yes | $0.067 | Most references |
| Batch | 4K | Yes | $0.120 | Never (overkill) |

### Gemini 2.5 Flash Image

| Config | Resolution | Batch? | Cost/Image | Use For |
|--------|-----------|--------|------------|---------|
| Standard | 1K-2K | No | $0.039 | Real-time standard panels |
| Batch | 1K-2K | Yes | $0.0195 | Most panels (80%) |

---

## Bottom Line

**Your question:** "If we reduce resolution, will it reduce spending?"

**Answer:** **NO** - 1K and 2K cost the same.

**What to do instead:**
1. ✅ Use more Flash (80% → 90%)
2. ✅ Use batch processing (50% discount)
3. ✅ Reduce variation count if needed
4. ❌ Don't waste time changing 2K → 1K (zero savings)

**Resolution is a quality decision, not a cost decision** (for 1K-2K range).
