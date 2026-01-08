# Gemini API Spending Tracking Research

## Overview

This document describes how to track and log Google Gemini API spending for the novel-to-webtoon workflow.

---

## 1. Gemini Pricing Structure

### Image Generation Pricing

#### gemini-3-pro-image-preview

| Component | Price |
|-----------|-------|
| Text input | $2.00 per 1M tokens |
| Image input | $0.0011 per image (560 tokens) |
| Image output (1K-2K) | $0.134 per image (1120 tokens) |
| Image output (4K) | $0.24 per image (2000 tokens) |
| Text output | $12.00 per 1M tokens |

#### gemini-2.5-flash-image

| Component | Price |
|-----------|-------|
| Text input | $0.30 per 1M tokens |
| Image output (1024x1024) | $0.039 per image (1290 tokens) |
| Text output | $2.50 per 1M tokens |

### Pricing Factors

1. **Input tokens** - Text and image tokens in the prompt
2. **Output tokens** - Generated content (images have fixed token counts)
3. **Cached tokens** - 90% discount when using context caching
4. **Model version** - Newer models are more expensive

**Note**: Failed requests (400/500 errors) are NOT charged but count against quota.

---

## 2. API Response Metadata

### Available Usage Data

Every Gemini API response includes `usage_metadata`:

```python
response.usage_metadata:
    prompt_token_count: int          # Input tokens used
    candidates_token_count: int      # Output tokens generated
    total_token_count: int           # Sum of above
    cached_content_token_count: int  # Tokens from cache (if applicable)
```

### Key Points

- `total_token_count` excludes cached tokens for billing
- `prompt_token_count` includes cached tokens for accounting
- No charge for accessing `usage_metadata`
- `countTokens()` API is free (max 3000 requests/minute)

---

## 3. Pre-Request Token Estimation

Estimate tokens before making API calls:

```python
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def estimate_tokens(model: str, contents: list) -> int:
    """Estimate tokens before API call (free, no quota impact)."""
    response = client.models.count_tokens(
        model=model,
        contents=contents
    )
    return response.total_tokens
```

---

## 4. Cost Tracking Implementation

### GeminiCostTracker Class

```python
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APICallRecord:
    timestamp: str
    model: str
    operation: str
    prompt_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    cost_usd: float
    image_resolution: str
    generation_time_ms: int
    metadata: Dict[str, Any]


class GeminiCostTracker:
    """Track Gemini API costs for image generation."""

    # Pricing per image (as of 2025)
    PRICING = {
        "gemini-3-pro-image-preview": {
            "input_text_per_1m": 2.00,
            "output_text_per_1m": 12.00,
            "input_image": 0.0011,
            "output_image_1k_2k": 0.134,
            "output_image_4k": 0.24,
        },
        "gemini-2.5-flash-image": {
            "input_text_per_1m": 0.30,
            "output_text_per_1m": 2.50,
            "output_image": 0.039,
        }
    }

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.call_history: List[APICallRecord] = []
        self.total_cost = 0.0
        self.session_start = datetime.utcnow()

    def calculate_image_cost(
        self,
        model: str,
        resolution: str = "1k_2k"
    ) -> float:
        """Calculate cost for a single image generation."""
        if model not in self.PRICING:
            logger.warning(f"Unknown model: {model}, using default pricing")
            return 0.05

        pricing = self.PRICING[model]

        if "output_image" in pricing:
            return pricing["output_image"]
        elif resolution == "4k":
            return pricing.get("output_image_4k", 0.24)
        else:
            return pricing.get("output_image_1k_2k", 0.134)

    def track_generation(
        self,
        model: str,
        response: Any,
        resolution: str = "1k_2k",
        generation_time_ms: int = 0,
        metadata: Optional[Dict] = None
    ) -> APICallRecord:
        """Track a single image generation call."""

        usage = response.usage_metadata
        cost = self.calculate_image_cost(model, resolution)

        record = APICallRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            model=model,
            operation="image_generation",
            prompt_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count,
            cached_tokens=getattr(usage, 'cached_content_token_count', 0) or 0,
            total_tokens=usage.total_token_count,
            cost_usd=round(cost, 6),
            image_resolution=resolution,
            generation_time_ms=generation_time_ms,
            metadata=metadata or {}
        )

        self.call_history.append(record)
        self.total_cost += cost

        logger.info(
            f"API Call: {model} | "
            f"Tokens: {record.total_tokens} | "
            f"Cost: ${cost:.4f} | "
            f"Session Total: ${self.total_cost:.4f}"
        )

        return record

    def get_summary(self) -> Dict[str, Any]:
        """Get aggregated cost summary."""
        if not self.call_history:
            return {
                "session_start": self.session_start.isoformat(),
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "average_cost_per_call": 0.0,
                "calls_by_model": {}
            }

        calls_by_model = {}
        for record in self.call_history:
            model = record.model
            if model not in calls_by_model:
                calls_by_model[model] = {
                    "count": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            calls_by_model[model]["count"] += 1
            calls_by_model[model]["tokens"] += record.total_tokens
            calls_by_model[model]["cost"] += record.cost_usd

        return {
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": (datetime.utcnow() - self.session_start).total_seconds(),
            "total_calls": len(self.call_history),
            "total_tokens": sum(r.total_tokens for r in self.call_history),
            "total_cost_usd": round(self.total_cost, 4),
            "average_cost_per_call": round(self.total_cost / len(self.call_history), 6),
            "calls_by_model": calls_by_model
        }

    def export_logs(self, filepath: str) -> None:
        """Export call history and summary to JSON file."""
        export_data = {
            "summary": self.get_summary(),
            "calls": [asdict(r) for r in self.call_history]
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Cost logs exported to {filepath}")

    def print_summary(self) -> None:
        """Print formatted cost summary."""
        summary = self.get_summary()

        print("\n" + "=" * 50)
        print("GEMINI API COST SUMMARY")
        print("=" * 50)
        print(f"Session Start: {summary['session_start']}")
        print(f"Total Calls: {summary['total_calls']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
        print(f"Avg Cost/Call: ${summary['average_cost_per_call']:.6f}")
        print("-" * 50)
        print("By Model:")
        for model, stats in summary['calls_by_model'].items():
            print(f"  {model}:")
            print(f"    Calls: {stats['count']}")
            print(f"    Cost: ${stats['cost']:.4f}")
        print("=" * 50 + "\n")
```

---

## 5. Recommended Logging Format

### Per-Call Log Entry

```json
{
  "timestamp": "2025-12-31T14:30:45.123456Z",
  "model": "gemini-3-pro-image-preview",
  "operation": "image_generation",
  "input": {
    "prompt_tokens": 28,
    "cached_tokens": 0,
    "reference_images": 2
  },
  "output": {
    "output_tokens": 1120,
    "total_tokens": 1148,
    "image_resolution": "1024x1024"
  },
  "cost": {
    "input_cost_usd": 0.000056,
    "output_cost_usd": 0.134,
    "total_cost_usd": 0.134056
  },
  "performance": {
    "generation_time_ms": 3200,
    "queue_time_ms": 150
  },
  "metadata": {
    "workflow_id": "webtoon-ch01-scene01",
    "panel_id": "s1_p02",
    "chapter": 1,
    "scene": "request_to_leave",
    "characters": ["jin_sohan", "dokma", "uiseon"]
  },
  "status": "success",
  "error": null
}
```

### Session Summary Format

```json
{
  "session_id": "sess-2025-12-31-abc123",
  "session_start": "2025-12-31T10:00:00Z",
  "session_end": "2025-12-31T12:30:00Z",
  "summary": {
    "total_calls": 45,
    "successful_calls": 43,
    "failed_calls": 2,
    "retry_calls": 3,
    "total_tokens": 52340,
    "total_cost_usd": 5.87
  },
  "by_model": {
    "gemini-2.5-flash-image": {
      "calls": 36,
      "cost": 1.40
    },
    "gemini-3-pro-image-preview": {
      "calls": 9,
      "cost": 4.47
    }
  },
  "by_phase": {
    "character_generation": {"calls": 12, "cost": 1.61},
    "background_generation": {"calls": 8, "cost": 0.31},
    "panel_generation": {"calls": 25, "cost": 3.95}
  }
}
```

---

## 6. Integration with Generation Pipeline

### Usage Example

```python
import os
import time
from google import genai
from google.genai import types

# Initialize tracker
tracker = GeminiCostTracker(api_key=os.getenv("GOOGLE_API_KEY"))

async def generate_panel_with_tracking(
    panel_spec: dict,
    character_refs: list,
    prompt: str
) -> str:
    """Generate panel with cost tracking."""

    model = select_model(panel_spec)  # Choose Flash vs Pro
    resolution = "1k_2k"

    start_time = time.time()

    response = tracker.client.models.generate_content(
        model=model,
        contents=character_refs + [prompt],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=panel_spec['aspect_ratio'],
                image_size="1K"
            )
        )
    )

    generation_time = int((time.time() - start_time) * 1000)

    # Track the call
    tracker.track_generation(
        model=model,
        response=response,
        resolution=resolution,
        generation_time_ms=generation_time,
        metadata={
            "panel_id": panel_spec['panel_id'],
            "scene_id": panel_spec['scene_id'],
            "characters": [c['character_id'] for c in panel_spec.get('characters', [])]
        }
    )

    # Save image and return path
    return save_image(response, panel_spec['panel_id'])


# After batch completion
tracker.print_summary()
tracker.export_logs("poc/reports/cost_summary.json")
```

---

## 7. Google Cloud Integration

For production deployments:

### Cloud Logging

View requests/responses in Cloud Logging dashboard:
- Filter by model, status, cost
- Set up alerts for cost thresholds

### Cloud Billing API

Programmatic access to billing data:

```python
from google.cloud import billing_v1

def get_billing_info(project_id: str):
    client = billing_v1.CloudBillingClient()
    # Query billing data...
```

### Budget Alerts

Set up budget alerts via Cloud Console:
1. Navigate to Billing > Budgets & alerts
2. Create budget for AI/ML services
3. Set threshold alerts (50%, 90%, 100%)

---

## 8. Key Recommendations

### For Development

1. Use free tier (1,500 images/day) during development
2. Log all API calls even in development
3. Review costs weekly during POC phase

### For Production

1. Implement cost tracking from day one
2. Set up budget alerts before launch
3. Export logs to BigQuery for analysis
4. Monitor cost-per-chapter metrics
5. Regular optimization reviews

### Cost Optimization Tracking

Track these metrics to measure optimization effectiveness:

| Metric | Target |
|--------|--------|
| Cost per panel | < $0.05 |
| Cost per chapter (20 panels) | < $1.00 |
| Flash vs Pro ratio | 80:20 |
| Cache hit rate | > 70% |
| Retry rate | < 5% |

---

## Sources

- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Token Counting Documentation](https://ai.google.dev/gemini-api/docs/tokens)
- [Gemini API Billing Guide](https://ai.google.dev/gemini-api/docs/billing)
- [Cloud Billing API](https://cloud.google.com/billing/docs/reference/rest)
- [Python GenAI SDK](https://googleapis.github.io/python-genai/)
