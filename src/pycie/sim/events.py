"""Event queue primitives for deterministic network simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
from typing import Any, Callable

EventCallback = Callable[..., None]


@dataclass(order=True)
class Event:
    """A scheduled callback in simulation time."""

    at: float
    priority: int
    seq: int
    callback: EventCallback = field(compare=False)
    args: tuple[Any, ...] = field(default_factory=tuple, compare=False)
    kwargs: dict[str, Any] = field(default_factory=dict, compare=False)
    cancelled: bool = field(default=False, compare=False)

    def run(self) -> None:
        """Execute event callback if not canceled."""
        if self.cancelled:
            return
        self.callback(*self.args, **self.kwargs)


@dataclass
class TimerHandle:
    """A cancellable reference to a scheduled event."""

    event: Event

    def cancel(self) -> None:
        self.event.cancelled = True

    @property
    def cancelled(self) -> bool:
        return self.event.cancelled


class EventQueue:
    """Priority queue of events ordered by (time, priority, sequence)."""

    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._sequence = 0

    def __len__(self) -> int:
        return len(self._heap)

    def schedule(
        self,
        at: float,
        callback: EventCallback,
        *args: Any,
        priority: int = 100,
        **kwargs: Any,
    ) -> TimerHandle:
        event = Event(
            at=at,
            priority=priority,
            seq=self._sequence,
            callback=callback,
            args=args,
            kwargs=kwargs,
        )
        self._sequence += 1
        heapq.heappush(self._heap, event)
        return TimerHandle(event=event)

    def pop_next(self) -> Event:
        """Pop the next event in priority order."""
        while self._heap:
            event = heapq.heappop(self._heap)
            if not event.cancelled:
                return event
        raise IndexError("event queue is empty")

    def has_events(self) -> bool:
        return any(not ev.cancelled for ev in self._heap)

    def peek_time(self) -> float | None:
        """Return time of next non-canceled event, if present."""
        while self._heap and self._heap[0].cancelled:
            heapq.heappop(self._heap)
        if not self._heap:
            return None
        return self._heap[0].at
