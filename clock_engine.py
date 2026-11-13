"""Small, UI-independent clock helpers backed by a monotonic time source."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from time import perf_counter
from typing import Callable
from zoneinfo import ZoneInfo


@dataclass
class Stopwatch:
    """A pauseable stopwatch; ``clock`` can be replaced for deterministic tests."""

    clock: Callable[[], float] = field(default=perf_counter, repr=False)
    running: bool = field(default=False, init=False)
    laps: list[float] = field(default_factory=list, init=False)
    _accumulated: float = field(default=0.0, init=False, repr=False)
    _started: float = field(default=0.0, init=False, repr=False)

    def elapsed(self) -> float:
        """Return accumulated seconds, including the current running interval."""
        return self._accumulated + (
            max(0.0, self.clock() - self._started) if self.running else 0.0
        )

    def toggle(self) -> None:
        """Pause a running stopwatch or resume a paused one."""
        if self.running:
            self._accumulated = self.elapsed()
            self.running = False
        else:
            self._started = self.clock()
            self.running = True

    def reset(self) -> None:
        """Stop and clear elapsed time and recorded laps."""
        self.running = False
        self._accumulated = 0.0
        self._started = 0.0
        self.laps.clear()

    def lap(self) -> float | None:
        """Record cumulative elapsed seconds while running; otherwise do nothing."""
        if not self.running:
            return None
        value = self.elapsed()
        self.laps.append(value)
        return value


@dataclass
class Countdown:
    """A countdown that measures deadlines rather than counting UI updates."""

    total_seconds: float = 1500.0
    clock: Callable[[], float] = field(default=perf_counter, repr=False)
    running: bool = field(default=False, init=False)
    finished: bool = field(default=False, init=False)
    _remaining: float = field(init=False, repr=False)
    _deadline: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.total_seconds = self._validate_seconds(self.total_seconds)
        self._remaining = self.total_seconds

    @staticmethod
    def _validate_seconds(seconds: float) -> float:
        value = float(seconds)
        if not isfinite(value) or value < 0:
            raise ValueError("Countdown duration must be a finite, non-negative number.")
        return value

    def remaining(self) -> float:
        """Return remaining seconds and latch completion when its deadline passes."""
        if self.running:
            self._remaining = max(0.0, self._deadline - self.clock())
            if self._remaining == 0.0:
                self.running = False
                self.finished = True
        return self._remaining

    def tick(self) -> bool:
        """Refresh completion state and return whether this countdown has finished."""
        self.remaining()
        return self.finished

    def toggle(self) -> None:
        """Pause/resume; starting after completion begins the full duration again."""
        remaining = self.remaining()
        if self.running:
            self.running = False
            return
        if self.finished:
            self.reset()
            remaining = self._remaining
        self._deadline = self.clock() + remaining
        self.running = True
        self.remaining()

    def reset(self, seconds: float | None = None) -> None:
        """Stop and restore the configured duration, optionally replacing it."""
        if seconds is not None:
            self.total_seconds = self._validate_seconds(seconds)
        self.running = False
        self.finished = False
        self._remaining = self.total_seconds
        self._deadline = 0.0


def format_duration(seconds: float, centiseconds: bool = False) -> str:
    """Format a non-negative duration as MM:SS or HH:MM:SS, with optional .xx."""
    value = float(seconds)
    if not isfinite(value):
        raise ValueError("Duration must be finite.")
    # The tiny tolerance avoids rendering e.g. 1.15 as 1.14 because of binary
    # floating-point representation, without rounding a real fractional tick up.
    hundredths = int(max(0.0, value) * 100 + 1e-8)
    whole_seconds, fraction = divmod(hundredths, 100)
    minutes, second = divmod(whole_seconds, 60)
    hour, minute = divmod(minutes, 60)
    result = (
        f"{hour:02d}:{minute:02d}:{second:02d}"
        if hour
        else f"{minute:02d}:{second:02d}"
    )
    return f"{result}.{fraction:02d}" if centiseconds else result


def world_time(zone_name: str, now: datetime | None = None) -> datetime:
    """Return the current (or supplied) instant in an IANA timezone.

    Install ``tzdata`` on platforms such as Windows without an OS IANA database.
    As with ``datetime.astimezone``, a naive supplied datetime means local time.
    """
    return (now or datetime.now().astimezone()).astimezone(ZoneInfo(zone_name))
