# Cost Analysis - PoC v0.2.0

## Executive Summary

**v0.1.0 Reality:** $2.70 for 18 panels = **$0.15/panel** (3x over target)

**v0.2.0 Target:** $4.50-6.00 for 68 panels = **$0.066-0.088/panel**

**Improvement:** 56-60% cost reduction through optimizations

---

## v0.1.0 Actual Data

From `poc/workflow-0.1.0/phase5_generation/reports/cost_summary.json`:

```json
{
  "total_calls": 18,
  "successful_calls": 18,
  "estimated_cost_usd": 2.70,
  "model": "gemini-3-pro-image-preview",
  "resolution": "likely 2K"
}
```

**Cost per panel:** $2.70 / 18 = **$0.15**

**Why so expensive:**
1. Used Pro model ($0.134/image) for ALL panels
2. No batch processing (no 50% discount)
3. No Flash model usage ($0.039/image)
4. Likely used 2K resolution everywhere
5. No context caching
6. No optimizations

---

## v0.2.0 Cost Scenarios

### Scenario 1: Naive (Like v0.1.0)

**If we did nothing differently:**

| Component | Quantity | Model | Cost/Unit | Total |
|-----------|----------|-------|-----------|-------|
| Characters (base) | 3 | Pro @ 2K | $0.15 | $0.45 |
| Character variations | 12 | Pro @ 2K | $0.15 | $1.80 |
| Artifacts (base) | 5 | Pro @ 2K | $0.15 | $0.75 |
| Artifact variations | 15 | Pro @ 2K | $0.15 | $2.25 |
| Backgrounds | 5 | Pro @ 2K | $0.15 | $0.75 |
| Panels | 68 | Pro @ 1K | $0.134 | $9.11 |
| **TOTAL** | **108** | | | **$15.11** |

**Cost per panel:** $15.11 / 68 = **$0.22** ❌

---

### Scenario 2: Optimized (v0.2.0 Strategy)

**With ALL optimizations:**

| Component | Quantity | Model | Resolution | Batch? | Cost/Unit | Total |
|-----------|----------|-------|------------|--------|-----------|-------|
| **Phase 1: Characters** |
| Character base refs | 3 | Pro | 2K | No | $0.134 | $0.40 |
| Character variations | 12 | Flash | 1K | Yes | $0.0195 | $0.23 |
| | | | | | **Subtotal** | **$0.63** |
| **Phase 3: Artifacts** |
| Artifact base refs | 5 | Pro | 2K | No | $0.134 | $0.67 |
| Artifact variations | 15 | Flash | 1K | Yes | $0.0195 | $0.29 |
| | | | | | **Subtotal** | **$0.96** |
| **Phase 3: Backgrounds** |
| Background base | 5 | Pro | 2K | No | $0.134 | $0.67 |
| | | | | | **Subtotal** | **$0.67** |
| **Phase 5: Panel Generation** |
| Critical panels (20%) | 14 | Pro | 1K | Yes | $0.067 | $0.94 |
| Standard panels (80%) | 54 | Flash | 1K | Yes | $0.0195 | $1.05 |
| | | | | | **Subtotal** | **$1.99** |
| **Phase 5: Iteration** |
| Regenerations (~10%) | 7 | Flash | 1K | Yes | $0.0195 | $0.14 |
| | | | | | **Subtotal** | **$0.14** |
| | | | | | | |
| **TOTAL** | **115** | | | | | **$4.53** |

**Cost per panel:** $4.53 / 68 = **$0.067** ✅

**Savings vs Naive:** 70%
**Savings vs v0.1.0:** 56%

---

### Scenario 3: Aggressive (Maximum Optimization)

**Max cost reduction with some quality trade-offs:**

| Component | Strategy | Cost |
|-----------|----------|------|
| **Characters** | 3 base @ Pro, NO variations (reuse base) | $0.40 |
| **Artifacts** | 5 @ Flash 1K (NOT Pro) | $0.20 |
| **Backgrounds** | 5 @ Flash 1K | $0.20 |
| **Panels** | 10 critical @ Pro (batch), 58 @ Flash (batch) | $1.80 |
| **Iteration** | Minimal (5%) | $0.09 |
| **TOTAL** | | **$2.69** |

**Cost per panel:** $2.69 / 68 = **$0.040** ✅

**Trade-offs:**
- Lower reference quality (Flash for artifacts/backgrounds)
- Fewer variations (less reference diversity)
- Higher risk of consistency issues
- More regeneration needed

---

## Optimization Impact Analysis

### Key Optimizations

**⚠️ IMPORTANT: 1K and 2K cost THE SAME ($0.134 Pro, $0.039 Flash)**

Resolution does NOT affect cost. Focus on what actually saves money:

| Optimization | Cost Reduction | Complexity | Priority |
|--------------|---------------|------------|----------|
| **1. Hybrid Models** | 71% per image | Low | **CRITICAL** |
| Flash ($0.039) vs Pro ($0.134) | Saves $0.095/image | Just parameter change | **DO THIS** |
| **2. Batch Processing** | 50% | Medium | **CRITICAL** |
| Cuts cost in half for batch calls | | Async workflow | **DO THIS** |
| **3. Reduce Image Count** | Direct savings | Low | HIGH |
| Fewer variations = fewer images | | Planning decision | |
| **4. Context Caching** | 10-15% | Medium | MEDIUM |
| Cache style/character specs | | Cache management | |
| **5. Resolution Choice** | **0% (NO SAVINGS)** | N/A | **DON'T BOTHER** |
| ❌ 1K and 2K cost identical | | Myth busted | See RESOLUTION_PRICING.md |

**Combined Effect:** 70% reduction from naive approach

**See `RESOLUTION_PRICING.md` for detailed pricing breakdown.**

---

## Budget Allocation (Optimized Scenario: $4.50)

| Phase | Budget | % of Total | Critical Decisions |
|-------|--------|-----------|-------------------|
| Phase 1: Characters | $0.63 | 14% | 3 Pro bases, rest Flash |
| Phase 2: Style | $0 | 0% | No generation cost |
| Phase 3: Backgrounds & Artifacts | $1.63 | 36% | Biggest one-time cost |
| Phase 4: Storyboard | $0 | 0% | Manual/script-based |
| Phase 5: Generation | $1.99 | 44% | **Largest cost** - 80% Flash |
| Phase 5: Iteration | $0.14 | 3% | 10% regen buffer |
| **TOTAL** | **$4.53** | 100% | |

---

## Multi-Episode Economics

**The key to achieving $0.05/panel: Asset reuse across episodes**

### Cost Per Episode (Detailed)

| Episode | Characters | Artifacts | Backgrounds | Panels | Iteration | Total | $/Panel |
|---------|-----------|-----------|-------------|--------|-----------|-------|---------|
| **1 (PoC)** | $0.63 | $0.96 | $0.67 | $1.99 | $0.14 | **$4.53** | **$0.067** |
| 2 | $0 | $0.20 | $0 | $2.10 | $0.10 | $2.40 | $0.035 |
| 3 | $0 | $0 | $0 | $2.10 | $0.10 | $2.20 | $0.032 |
| 4 | $0.20 | $0.15 | $0 | $2.10 | $0.10 | $2.55 | $0.038 |
| 5 | $0 | $0 | $0 | $2.10 | $0.10 | $2.20 | $0.032 |
| 6-10 | $0 avg | $0 avg | $0 avg | $2.10 | $0.10 | $11.00 | $0.032 |
| | | | | | | | |
| **Total (10)** | | | | | | **$29.41** | **$0.043** ✅ |

**Break-even analysis:**
- Episode 1: High cost ($4.53) due to asset creation
- Episodes 2-3: Cost drops 50% due to asset reuse
- Episodes 4+: Stable at ~$2.20/episode
- **Average over 10 episodes: $0.043/panel** ← Sustainable

---

## Budget Monitoring

### Real-Time Tracking

Use the provided `cost_tracker.py`:

```python
from cost_tracker import CostTracker

tracker = CostTracker(session_id="poc-v2-episode-001")

# Track every generation
tracker.track(
    model="gemini-2.5-flash-image",
    panel_id="s1_p01",
    generation_time_ms=2000,
    prompt_tokens=80,
    output_tokens=900,
    scene_id="scene_01",
    phase="panel_generation",
    resolution="1K",
    status="success",
    is_batch=True  # 50% discount
)

# Check budget at any time
tracker.print_summary()
```

### Budget Alerts

```python
class BudgetMonitor:
    def __init__(self, tracker: CostTracker, budget: float):
        self.tracker = tracker
        self.budget = budget
    
    def check(self):
        spent = self.tracker.total_cost
        remaining = self.budget - spent
        percent = (spent / self.budget) * 100
        
        if percent > 90:
            print(f"🚨 CRITICAL: {percent:.1f}% budget used!")
        elif percent > 75:
            print(f"⚠️  WARNING: {percent:.1f}% budget used")
        
        return {
            "spent": spent,
            "remaining": remaining,
            "percent": percent
        }

# Usage
monitor = BudgetMonitor(tracker, budget=5.00)
monitor.check()  # After each phase
```

### Phase Budget Gates

```python
PHASE_BUDGETS = {
    "character_generation": 0.70,
    "artifact_generation": 1.00,
    "background_generation": 0.70,
    "panel_generation": 2.50,
    "iteration": 0.20
}

def check_phase_budget(tracker: CostTracker, phase: str):
    phase_calls = [c for c in tracker.calls if c.phase == phase]
    phase_cost = sum(c.cost_usd for c in phase_calls)
    budget = PHASE_BUDGETS.get(phase, 0)
    
    if phase_cost > budget:
        print(f"⚠️  Phase '{phase}' over budget!")
        print(f"   Spent: ${phase_cost:.2f} / ${budget:.2f}")
        return False
    
    return True
```

---

## Decision Gates

### After Phase 3 (Asset Creation)

**Budget Check:**
```
If asset_cost > $2.50:
  ├─ STOP and analyze
  │  └─ Assets shouldn't exceed 55% of budget
  └─ Likely issues:
      ├─ Too many variations
      ├─ Using Pro for everything
      └─ Not using batch processing

If asset_cost < $2.00:
  ├─ Excellent, under budget
  └─ Reallocate savings to panel generation quality
```

### After Phase 5 (Panel Generation)

**Final Budget Check:**
```
If total_cost > $6.00:
  ├─ Document overrun
  ├─ Analyze root cause by phase
  └─ Adjust strategy for next episode

If total_cost < $5.00:
  ├─ Success! Document what worked
  └─ Consider:
      ├─ Increase quality (more Pro usage)
      └─ Reduce budget for Episode 2
```

---

## Cost Comparison Summary

### v0.1.0 vs v0.2.0

| Metric | v0.1.0 Actual | v0.2.0 Target | Change |
|--------|--------------|---------------|--------|
| Panels | 18 | 68 | +278% |
| Total Cost | $2.70 | $4.50-6.00 | +67-122% |
| **Cost/Panel** | **$0.15** | **$0.066-0.088** | **-44% to -56%** ✅ |
| Model Mix | 100% Pro | 20% Pro, 80% Flash | Optimized |
| Batch Processing | No | Yes | 50% discount |
| Asset Reuse | No | Yes (future) | -65% Episode 2+ |

### If v0.1.0 Scaled to 68 Panels

Without any changes: 68 × $0.15 = **$10.20**
With v0.2.0 optimizations: **$4.50**
**Savings: 56%** ✅

---

## Recommendations

### For PoC v0.2.0 Execution

1. **Set Realistic Budget**
   - Target: $4.50-6.00 for 68 panels
   - Stretch goal: Under $5.00
   - Acceptable: Up to $6.00

2. **Implement Mandatory Optimizations**
   - ✅ Hybrid model (80% Flash, 20% Pro)
   - ✅ Batch processing for non-urgent
   - ✅ 1K resolution for panels
   - ✅ Real-time cost tracking

3. **Phase-by-Phase Budget Monitoring**
   - Track after each phase completes
   - Alert at 75% and 90% of phase budget
   - Stop if any phase exceeds 150% of budget

4. **Quality vs Cost Trade-offs**
   - Start with Optimized scenario
   - If cost exceeds $5.00 at Phase 3, reduce quality
   - If cost under $4.00 at Phase 3, increase Pro usage

5. **Document Everything**
   - Which optimizations worked best?
   - Where did cost overruns occur?
   - What would you change for Episode 2?

---

## Conclusion

**Can v0.2.0 achieve $0.05/panel for the PoC?**

❌ **No, not for Episode 1** - Realistic range: $0.066-0.088/panel

**But this is acceptable because:**

1. **Asset creation overhead** ($2.26) benefits all future episodes
2. **Episode 2-10 will achieve** $0.03-0.04/panel through asset reuse
3. **10-episode average** will be **$0.043/panel** - below target ✅
4. **This is sustainable economics**, not one-time magic

**Success metrics for v0.2.0:**
- ✅ Total cost < $6.00
- ✅ 56% cost reduction vs v0.1.0 approach
- ✅ Asset library enables Episode 2 at < $2.50
- ✅ Proof that optimizations work

**The honest story:** Episode 1 subsidizes future episodes. This is **multi-episode economics**, and it's the right approach.
