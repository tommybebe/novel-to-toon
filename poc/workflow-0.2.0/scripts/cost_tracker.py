"""
Cost Tracker for Novel-to-Toon PoC v0.2.0

Tracks API spending for fal.ai image generation calls.
Supports flat per-image pricing (Kontext) and megapixel-based pricing (Flux 2).
Auto-saves a live cost file for real-time monitoring via Claude Code hooks.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os


LIVE_COST_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "cost_live.json"
)

DEFAULT_BUDGET_USD = 10.0


@dataclass
class APICallRecord:
    """Record of a single fal.ai API call."""
    timestamp: str
    platform: str
    model: str
    panel_id: str
    cost_usd: float
    generation_time_ms: int
    image_dimensions: str
    megapixels: float
    status: str  # "success", "failed", "retried"
    phase: Optional[str] = None
    scene_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FalCostTracker:
    """
    Track fal.ai API costs for image generation.

    Pricing models:
    - Flat per-image: Kontext pro ($0.04), Kontext max ($0.08)
    - Per-megapixel: Flash ($0.005/MP), Turbo ($0.008/MP), Dev ($0.012/MP), Flex ($0.06/MP)
    - Tiered: Flux 2 Pro (first MP $0.03, additional $0.015/MP)
    """

    PRICING = {
        # Per-image flat pricing
        "fal-ai/flux-pro/kontext": 0.04,
        "fal-ai/flux-pro/kontext/multi": 0.04,
        "fal-ai/flux-pro/kontext/text-to-image": 0.04,
        "fal-ai/flux-pro/kontext/max": 0.08,
        "fal-ai/flux-pro/kontext/max/multi": 0.08,
        # Per-megapixel pricing
        "fal-ai/flux-2/flash": {"per_mp": 0.005},
        "fal-ai/flux-2/turbo": {"per_mp": 0.008},
        "fal-ai/flux-2/dev": {"per_mp": 0.012},
        "fal-ai/flux-2-pro": {"first_mp": 0.03, "additional_mp": 0.015},
        "fal-ai/flux-2-flex": {"per_mp": 0.06},
    }

    def __init__(self, session_id: Optional[str] = None, budget_usd: float = DEFAULT_BUDGET_USD,
                 live_file: Optional[str] = LIVE_COST_FILE):
        self.session_id = session_id or f"session-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        self.budget_usd = budget_usd
        self.live_file = live_file
        self.calls: List[APICallRecord] = []
        self.total_cost = 0.0
        self.start_time = datetime.utcnow().isoformat()

    def calculate_megapixels(self, width: int, height: int) -> float:
        """Calculate megapixels from dimensions."""
        return (width * height) / 1_000_000

    def calculate_cost(self, model: str, width: int = 1024, height: int = 1440) -> float:
        """Calculate cost for a single generation."""
        pricing = self.PRICING.get(model)
        if pricing is None:
            return 0.05  # Default fallback for unknown models

        if isinstance(pricing, (int, float)):
            return float(pricing)  # Flat per-image pricing

        # Megapixel-based pricing
        mp = self.calculate_megapixels(width, height)
        mp_rounded = max(1, int(mp + 0.99))  # Round up to nearest MP

        if "first_mp" in pricing:
            # Flux 2 Pro tiered pricing
            cost = pricing["first_mp"]
            if mp_rounded > 1:
                cost += (mp_rounded - 1) * pricing["additional_mp"]
            return cost
        else:
            return mp_rounded * pricing["per_mp"]

    def track(
        self,
        model: str,
        panel_id: str,
        generation_time_ms: int,
        width: int = 1024,
        height: int = 1440,
        phase: Optional[str] = None,
        scene_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> APICallRecord:
        """
        Track an API call and auto-save live cost file.

        Args:
            model: fal.ai endpoint (e.g. "fal-ai/flux-pro/kontext")
            panel_id: Identifier for the panel/asset being generated
            generation_time_ms: Time taken for generation in milliseconds
            width: Image width in pixels
            height: Image height in pixels
            phase: Workflow phase (e.g. "character_generation", "panel_generation")
            scene_id: Optional scene identifier
            status: Call status ("success", "failed", "retried")
            error_message: Optional error message if failed
            metadata: Optional extra metadata dict

        Returns:
            The created APICallRecord
        """
        mp = self.calculate_megapixels(width, height)
        cost = self.calculate_cost(model, width, height) if status == "success" else 0.0

        record = APICallRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            platform="fal.ai",
            model=model,
            panel_id=panel_id,
            cost_usd=round(cost, 6),
            generation_time_ms=generation_time_ms,
            image_dimensions=f"{width}x{height}",
            megapixels=round(mp, 2),
            status=status,
            phase=phase,
            scene_id=scene_id,
            error_message=error_message,
            metadata=metadata or {},
        )

        self.calls.append(record)
        self.total_cost += cost

        # Auto-save live cost file for hook monitoring
        if self.live_file:
            self._save_live(record)

        return record

    def _save_live(self, last_record: APICallRecord) -> None:
        """Save live cost summary to JSON file for real-time monitoring."""
        os.makedirs(os.path.dirname(self.live_file), exist_ok=True)

        by_phase: Dict[str, Dict[str, Any]] = {}
        by_model: Dict[str, Dict[str, Any]] = {}

        for call in self.calls:
            # By phase
            phase = call.phase or "unspecified"
            if phase not in by_phase:
                by_phase[phase] = {"count": 0, "cost_usd": 0.0}
            by_phase[phase]["count"] += 1
            by_phase[phase]["cost_usd"] = round(by_phase[phase]["cost_usd"] + call.cost_usd, 6)

            # By model
            short_model = call.model.split("/")[-1]
            if call.model not in by_model:
                by_model[call.model] = {"short_name": short_model, "count": 0, "cost_usd": 0.0}
            by_model[call.model]["count"] += 1
            by_model[call.model]["cost_usd"] = round(by_model[call.model]["cost_usd"] + call.cost_usd, 6)

        data = {
            "session_id": self.session_id,
            "total_cost_usd": round(self.total_cost, 4),
            "budget_usd": self.budget_usd,
            "percent_used": round((self.total_cost / self.budget_usd) * 100, 1) if self.budget_usd > 0 else 0,
            "total_calls": len(self.calls),
            "last_call": {
                "model": last_record.model,
                "cost_usd": last_record.cost_usd,
                "panel_id": last_record.panel_id,
                "status": last_record.status,
            },
            "by_phase": by_phase,
            "by_model": by_model,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        with open(self.live_file, "w") as f:
            json.dump(data, f, indent=2)

    def summary(self) -> Dict[str, Any]:
        """Generate a summary of all tracked calls."""
        by_model: Dict[str, Dict[str, Any]] = {}
        by_phase: Dict[str, Dict[str, Any]] = {}
        by_status: Dict[str, int] = {"success": 0, "failed": 0, "retried": 0}
        total_time_ms = 0

        for call in self.calls:
            # By model
            if call.model not in by_model:
                by_model[call.model] = {"count": 0, "cost_usd": 0.0}
            by_model[call.model]["count"] += 1
            by_model[call.model]["cost_usd"] += call.cost_usd

            # By phase
            phase = call.phase or "unspecified"
            if phase not in by_phase:
                by_phase[phase] = {"count": 0, "cost_usd": 0.0}
            by_phase[phase]["count"] += 1
            by_phase[phase]["cost_usd"] += call.cost_usd

            # By status
            by_status[call.status] = by_status.get(call.status, 0) + 1

            total_time_ms += call.generation_time_ms

        # Round costs
        for stats in by_model.values():
            stats["cost_usd"] = round(stats["cost_usd"], 4)
        for stats in by_phase.values():
            stats["cost_usd"] = round(stats["cost_usd"], 4)

        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": datetime.utcnow().isoformat(),
            "total_calls": len(self.calls),
            "total_cost_usd": round(self.total_cost, 4),
            "budget_usd": self.budget_usd,
            "percent_used": round((self.total_cost / self.budget_usd) * 100, 1) if self.budget_usd > 0 else 0,
            "by_model": by_model,
            "by_phase": by_phase,
            "by_status": by_status,
            "total_generation_time_ms": total_time_ms,
            "average_generation_time_ms": round(total_time_ms / len(self.calls), 2) if self.calls else 0,
        }

    def export(self, filepath: str, include_calls: bool = True) -> None:
        """Export full tracking data to a JSON file."""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

        data = {"summary": self.summary()}
        if include_calls:
            data["calls"] = [asdict(c) for c in self.calls]

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def print_summary(self) -> None:
        """Print a formatted summary to console."""
        s = self.summary()

        print("\n" + "=" * 55)
        print("FAL.AI COST TRACKING SUMMARY")
        print("=" * 55)
        print(f"Session:  {s['session_id']}")
        print(f"Budget:   ${s['budget_usd']:.2f}")
        print(f"Spent:    ${s['total_cost_usd']:.4f} ({s['percent_used']}%)")
        print(f"Calls:    {s['total_calls']}")
        print(f"Avg Time: {s['average_generation_time_ms']:.0f}ms")

        print("\nBy Model:")
        for model, stats in s["by_model"].items():
            print(f"  {model}: {stats['count']} calls, ${stats['cost_usd']:.4f}")

        print("\nBy Phase:")
        for phase, stats in s["by_phase"].items():
            print(f"  {phase}: {stats['count']} calls, ${stats['cost_usd']:.4f}")

        print("\nBy Status:")
        for status, count in s["by_status"].items():
            if count > 0:
                print(f"  {status}: {count}")

        print("=" * 55 + "\n")


# Global tracker instance for convenience
_global_tracker: Optional[FalCostTracker] = None


def get_tracker(session_id: Optional[str] = None) -> FalCostTracker:
    """Get or create the global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = FalCostTracker(session_id)
    return _global_tracker


def reset_tracker(session_id: Optional[str] = None) -> FalCostTracker:
    """Reset and return a new global cost tracker."""
    global _global_tracker
    _global_tracker = FalCostTracker(session_id)
    return _global_tracker


if __name__ == "__main__":
    # Simulate fal.ai API calls for testing
    tracker = FalCostTracker(session_id="poc-v2-fal-test-001")

    print("Simulating fal.ai API calls for testing...\n")

    # Character generation — Kontext pro (flat $0.04)
    tracker.track(
        model="fal-ai/flux-pro/kontext/text-to-image",
        panel_id="jin_sohan_base",
        generation_time_ms=4200,
        width=1024, height=1440,
        phase="character_generation",
    )

    tracker.track(
        model="fal-ai/flux-pro/kontext/text-to-image",
        panel_id="dokma_base",
        generation_time_ms=3900,
        width=1024, height=1440,
        phase="character_generation",
    )

    # Character consistency — Kontext pro edit (flat $0.04)
    tracker.track(
        model="fal-ai/flux-pro/kontext",
        panel_id="jin_sohan_angle_side",
        generation_time_ms=3800,
        width=1024, height=1440,
        phase="character_generation",
    )

    # Artifact generation — Kontext max for quality (flat $0.08)
    tracker.track(
        model="fal-ai/flux-pro/kontext/max",
        panel_id="twin_blades_base",
        generation_time_ms=6100,
        width=1024, height=1440,
        phase="artifact_generation",
    )

    # Panel generation — Flash for speed ($0.005/MP)
    for i in range(5):
        tracker.track(
            model="fal-ai/flux-2/flash",
            panel_id=f"s1_p{i+1:02d}",
            generation_time_ms=1800 + (i * 100),
            width=1024, height=1440,
            scene_id="scene_01",
            phase="panel_generation",
        )

    # Panel with Kontext edit for consistency (flat $0.04)
    tracker.track(
        model="fal-ai/flux-pro/kontext",
        panel_id="s1_p06",
        generation_time_ms=4000,
        width=1024, height=1440,
        scene_id="scene_01",
        phase="panel_generation",
    )

    # Test Flux 2 Pro tiered pricing (2 MP image)
    tracker.track(
        model="fal-ai/flux-2-pro",
        panel_id="hero_shot_01",
        generation_time_ms=5500,
        width=1440, height=1920,
        phase="panel_generation",
        metadata={"note": "hero panel, higher res"},
    )

    # Simulate a failed call (should cost $0)
    tracker.track(
        model="fal-ai/flux-2/flash",
        panel_id="s1_p07_failed",
        generation_time_ms=1200,
        width=1024, height=1440,
        scene_id="scene_01",
        phase="panel_generation",
        status="failed",
        error_message="NSFW filter triggered",
    )

    # Print summary
    tracker.print_summary()

    # Verify live file was created
    if os.path.exists(tracker.live_file):
        print(f"Live cost file: {tracker.live_file}")
        with open(tracker.live_file) as f:
            live = json.load(f)
        print(json.dumps(live, indent=2))
    else:
        print("ERROR: Live cost file was not created!")

    # Export full report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reports", "cost_tracking_test.json"
    )
    tracker.export(report_path)
    print(f"\nFull report exported to: {report_path}")
