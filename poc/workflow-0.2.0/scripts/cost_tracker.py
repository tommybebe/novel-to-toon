"""
Cost Tracker for Novel-to-Toon PoC

Tracks API spending for Google Gemini image generation calls.
Based on PoC Specification v2 spending tracking requirements.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import os


class ModelType(Enum):
    """Supported Gemini models for image generation."""
    GEMINI_3_PRO = "gemini-3-pro-image-preview"
    GEMINI_2_5_FLASH = "gemini-2.5-flash-image"


@dataclass
class APICallRecord:
    """Record of a single API call."""
    timestamp: str
    model: str
    panel_id: str
    scene_id: Optional[str]
    prompt_tokens: int
    output_tokens: int
    cached_tokens: int
    cost_usd: float
    generation_time_ms: int
    status: str  # "success", "failed", "retried"
    phase: Optional[str] = None  # "character_generation", "artifact_generation", "panel_generation", etc.
    resolution: Optional[str] = None  # "1K", "2K", "4K"
    error_message: Optional[str] = None


class CostTracker:
    """
    Tracks API costs for Gemini image generation.

    Pricing based on Google Gemini API rates (as of Dec 2025):
    - gemini-3-pro-image-preview: $0.134/image (1K-2K), $0.24/image (4K)
    - gemini-2.5-flash-image: $0.039/image
    """

    # Pricing per image by model and resolution
    PRICING = {
        ModelType.GEMINI_3_PRO.value: {
            "1K": 0.134,
            "2K": 0.134,
            "4K": 0.24,
            "default": 0.134
        },
        ModelType.GEMINI_2_5_FLASH.value: {
            "1K": 0.039,
            "2K": 0.039,
            "4K": 0.039,
            "default": 0.039
        }
    }

    # Batch processing discount (50% off)
    BATCH_DISCOUNT = 0.5

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the cost tracker.

        Args:
            session_id: Optional session identifier. Auto-generated if not provided.
        """
        self.session_id = session_id or f"session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        self.calls: List[APICallRecord] = []
        self.total_cost = 0.0
        self.start_time = datetime.utcnow().isoformat()

    def get_cost(self, model: str, resolution: str = "default", is_batch: bool = False) -> float:
        """
        Get the cost for a given model and resolution.

        Args:
            model: Model name (e.g., "gemini-3-pro-image-preview")
            resolution: Resolution ("1K", "2K", "4K", or "default")
            is_batch: Whether this is a batch processing call (50% discount)

        Returns:
            Cost in USD
        """
        model_pricing = self.PRICING.get(model, {"default": 0.05})
        cost = model_pricing.get(resolution, model_pricing.get("default", 0.05))

        if is_batch:
            cost *= self.BATCH_DISCOUNT

        return cost

    def track(
        self,
        model: str,
        panel_id: str,
        generation_time_ms: int,
        prompt_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        scene_id: Optional[str] = None,
        phase: Optional[str] = None,
        resolution: str = "1K",
        status: str = "success",
        is_batch: bool = False,
        error_message: Optional[str] = None
    ) -> APICallRecord:
        """
        Track an API call.

        Args:
            model: Model name used for generation
            panel_id: Identifier for the panel/asset being generated
            generation_time_ms: Time taken for generation in milliseconds
            prompt_tokens: Number of prompt tokens (from response metadata)
            output_tokens: Number of output tokens (from response metadata)
            cached_tokens: Number of cached tokens (from response metadata)
            scene_id: Optional scene identifier
            phase: Optional phase name (e.g., "character_generation")
            resolution: Resolution used ("1K", "2K", "4K")
            status: Call status ("success", "failed", "retried")
            is_batch: Whether this was a batch processing call
            error_message: Optional error message if failed

        Returns:
            The created APICallRecord
        """
        cost = self.get_cost(model, resolution, is_batch) if status == "success" else 0.0

        record = APICallRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            model=model,
            panel_id=panel_id,
            scene_id=scene_id,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            cost_usd=cost,
            generation_time_ms=generation_time_ms,
            status=status,
            phase=phase,
            resolution=resolution,
            error_message=error_message
        )

        self.calls.append(record)
        self.total_cost += cost

        return record

    def track_from_response(
        self,
        model: str,
        panel_id: str,
        response,
        generation_time_ms: int,
        scene_id: Optional[str] = None,
        phase: Optional[str] = None,
        resolution: str = "1K",
        is_batch: bool = False
    ) -> APICallRecord:
        """
        Track an API call using the response object directly.

        Args:
            model: Model name used for generation
            panel_id: Identifier for the panel/asset being generated
            response: The Gemini API response object
            generation_time_ms: Time taken for generation in milliseconds
            scene_id: Optional scene identifier
            phase: Optional phase name
            resolution: Resolution used
            is_batch: Whether this was a batch processing call

        Returns:
            The created APICallRecord
        """
        # Extract usage metadata from response
        usage = getattr(response, 'usage_metadata', None)

        prompt_tokens = getattr(usage, 'prompt_token_count', 0) if usage else 0
        output_tokens = getattr(usage, 'candidates_token_count', 0) if usage else 0
        cached_tokens = getattr(usage, 'cached_content_token_count', 0) if usage else 0

        return self.track(
            model=model,
            panel_id=panel_id,
            generation_time_ms=generation_time_ms,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            scene_id=scene_id,
            phase=phase,
            resolution=resolution,
            status="success",
            is_batch=is_batch
        )

    def summary(self) -> Dict[str, Any]:
        """
        Generate a summary of all tracked calls.

        Returns:
            Dictionary containing summary statistics
        """
        by_model: Dict[str, Dict[str, Any]] = {}
        by_phase: Dict[str, Dict[str, Any]] = {}
        by_status: Dict[str, int] = {"success": 0, "failed": 0, "retried": 0}

        total_tokens = {"prompt": 0, "output": 0, "cached": 0}
        total_time_ms = 0

        for call in self.calls:
            # Aggregate by model
            if call.model not in by_model:
                by_model[call.model] = {"count": 0, "cost": 0.0}
            by_model[call.model]["count"] += 1
            by_model[call.model]["cost"] += call.cost_usd

            # Aggregate by phase
            phase = call.phase or "unspecified"
            if phase not in by_phase:
                by_phase[phase] = {"count": 0, "cost": 0.0}
            by_phase[phase]["count"] += 1
            by_phase[phase]["cost"] += call.cost_usd

            # Aggregate by status
            by_status[call.status] = by_status.get(call.status, 0) + 1

            # Aggregate tokens
            total_tokens["prompt"] += call.prompt_tokens
            total_tokens["output"] += call.output_tokens
            total_tokens["cached"] += call.cached_tokens

            # Aggregate time
            total_time_ms += call.generation_time_ms

        # Round costs for readability
        for model_stats in by_model.values():
            model_stats["cost"] = round(model_stats["cost"], 4)
        for phase_stats in by_phase.values():
            phase_stats["cost"] = round(phase_stats["cost"], 4)

        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": datetime.utcnow().isoformat(),
            "total_calls": len(self.calls),
            "total_cost_usd": round(self.total_cost, 4),
            "by_model": by_model,
            "by_phase": by_phase,
            "by_status": by_status,
            "total_tokens": total_tokens,
            "total_generation_time_ms": total_time_ms,
            "average_generation_time_ms": round(total_time_ms / len(self.calls), 2) if self.calls else 0
        }

    def export(self, filepath: str, include_calls: bool = True) -> None:
        """
        Export tracking data to a JSON file.

        Args:
            filepath: Path to the output JSON file
            include_calls: Whether to include individual call records
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

        data = {
            "summary": self.summary()
        }

        if include_calls:
            data["calls"] = [asdict(c) for c in self.calls]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def print_summary(self) -> None:
        """Print a formatted summary to console."""
        summary = self.summary()

        print("\n" + "=" * 50)
        print("COST TRACKING SUMMARY")
        print("=" * 50)
        print(f"Session ID: {summary['session_id']}")
        print(f"Total Calls: {summary['total_calls']}")
        print(f"Total Cost: ${summary['total_cost_usd']:.4f}")
        print(f"Average Generation Time: {summary['average_generation_time_ms']:.0f}ms")

        print("\nBy Model:")
        for model, stats in summary['by_model'].items():
            print(f"  {model}: {stats['count']} calls, ${stats['cost']:.4f}")

        print("\nBy Phase:")
        for phase, stats in summary['by_phase'].items():
            print(f"  {phase}: {stats['count']} calls, ${stats['cost']:.4f}")

        print("\nBy Status:")
        for status, count in summary['by_status'].items():
            if count > 0:
                print(f"  {status}: {count}")

        print("=" * 50 + "\n")


# Global tracker instance for convenience
_global_tracker: Optional[CostTracker] = None


def get_tracker(session_id: Optional[str] = None) -> CostTracker:
    """
    Get or create the global cost tracker instance.

    Args:
        session_id: Optional session ID for new tracker

    Returns:
        The global CostTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker(session_id)
    return _global_tracker


def reset_tracker(session_id: Optional[str] = None) -> CostTracker:
    """
    Reset and return a new global cost tracker.

    Args:
        session_id: Optional session ID for new tracker

    Returns:
        A new CostTracker instance
    """
    global _global_tracker
    _global_tracker = CostTracker(session_id)
    return _global_tracker


# Example usage and testing
if __name__ == "__main__":
    # Create a tracker
    tracker = CostTracker(session_id="poc-v2-test-001")

    # Simulate some API calls
    print("Simulating API calls for testing...\n")

    # Character generation (Pro model, 2K)
    tracker.track(
        model=ModelType.GEMINI_3_PRO.value,
        panel_id="jin_sohan_base",
        generation_time_ms=3200,
        prompt_tokens=150,
        output_tokens=1290,
        cached_tokens=0,
        phase="character_generation",
        resolution="2K",
        status="success"
    )

    tracker.track(
        model=ModelType.GEMINI_3_PRO.value,
        panel_id="dokma_base",
        generation_time_ms=3100,
        prompt_tokens=145,
        output_tokens=1285,
        cached_tokens=0,
        phase="character_generation",
        resolution="2K",
        status="success"
    )

    # Artifact generation (Pro model, 2K)
    tracker.track(
        model=ModelType.GEMINI_3_PRO.value,
        panel_id="twin_blades_base",
        generation_time_ms=2800,
        prompt_tokens=120,
        output_tokens=1100,
        cached_tokens=0,
        phase="artifact_generation",
        resolution="2K",
        status="success"
    )

    # Panel generation (Flash model, 1K)
    for i in range(5):
        tracker.track(
            model=ModelType.GEMINI_2_5_FLASH.value,
            panel_id=f"s1_p0{i+1}",
            generation_time_ms=2000 + (i * 100),
            prompt_tokens=80,
            output_tokens=900,
            cached_tokens=50 if i > 0 else 0,  # Cached after first call
            scene_id="scene_01_request",
            phase="panel_generation",
            resolution="1K",
            status="success"
        )

    # Simulate a failed call
    tracker.track(
        model=ModelType.GEMINI_2_5_FLASH.value,
        panel_id="s1_p06_failed",
        generation_time_ms=1500,
        prompt_tokens=80,
        output_tokens=0,
        scene_id="scene_01_request",
        phase="panel_generation",
        resolution="1K",
        status="failed",
        error_message="Content filter triggered"
    )

    # Print summary
    tracker.print_summary()

    # Export to file
    output_path = "poc/reports/cost_tracking_test.json"
    tracker.export(output_path)
    print(f"Exported tracking data to: {output_path}")

    # Show the exported JSON
    with open(output_path, 'r') as f:
        print("\nExported JSON preview (summary only):")
        data = json.load(f)
        print(json.dumps(data['summary'], indent=2))
