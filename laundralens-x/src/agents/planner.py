"""LaundraLens X — Adaptive Planner (minimal for now, extended in Phase 8)."""
from typing import Dict


class AdaptivePlanner:
    """Adaptive planning based on signal values."""

    def should_deep_dive_flow(self, flow_signal: float) -> bool:
        return flow_signal > 0.6

    def should_expand_graph(self, new_recipient_ratio: float) -> bool:
        return new_recipient_ratio > 0.5

    def should_trace_lineage(self, lineage_strength: float) -> bool:
        return lineage_strength > 0.3

    def should_skip_behavioral(self, behavior_signal: float) -> bool:
        return behavior_signal < 0.2
