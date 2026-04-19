from __future__ import annotations

import math
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field


class MetricsError(Exception):
    pass


class UnknownMetricError(MetricsError):
    def __init__(self, name: str) -> None:
        super().__init__(f"unknown metric: {name!r}")


class MetricTypeError(MetricsError):
    def __init__(self, name: str, expected: str) -> None:
        super().__init__(f"metric {name!r} is not a {expected}")


@dataclass(frozen=True)
class CounterSummary:
    name: str
    value: float

    @property
    def kind(self) -> str:
        return "counter"


@dataclass(frozen=True)
class GaugeSummary:
    name: str
    value: float
    last_updated_at: float

    @property
    def kind(self) -> str:
        return "gauge"


@dataclass(frozen=True)
class HistogramSummary:
    name: str
    count: int
    total: float
    mean: float
    median: float
    p95: float
    p99: float
    minimum: float
    maximum: float

    @property
    def kind(self) -> str:
        return "histogram"


class MetricsCollector:
    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.time
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, tuple[float, float]] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def inc(self, name: str, amount: float = 1.0) -> float:
        if amount < 0:
            raise MetricsError("counter increments must be non-negative")
        self._counters[name] += amount
        return self._counters[name]

    def gauge(self, name: str, value: float) -> float:
        stamped = (value, self._clock())
        self._gauges[name] = stamped
        return value

    def observe(self, name: str, value: float) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MetricsError(f"observation must be numeric, got {type(value).__name__}")
        if math.isnan(value) or math.isinf(value):
            raise MetricsError("observation must be finite")
        self._histograms[name].append(float(value))
        return len(self._histograms[name])

    @property
    def metric_names(self) -> tuple[str, ...]:
