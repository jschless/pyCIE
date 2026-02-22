"""Simulation clock utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimClock:
    """Monotonic simulation clock in milliseconds."""

    now_ms: float = 0.0

    def advance_to(self, new_time_ms: float) -> None:
        if new_time_ms < self.now_ms:
            raise ValueError("cannot move simulation clock backwards")
        self.now_ms = new_time_ms

    def advance_by(self, delta_ms: float) -> None:
        if delta_ms < 0:
            raise ValueError("delta must be non-negative")
        self.now_ms += delta_ms
