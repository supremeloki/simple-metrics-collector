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
        combined = set(self._counters) | set(self._gauges) | set(self._histograms)
        return tuple(sorted(combined))

    def _require_histogram(self, name: str) -> list[float]:
        if name not in self._histograms:
            raise MetricTypeError(name, "histogram")
        return self._histograms[name]

    def counter_summary(self, name: str) -> CounterSummary:
        if name not in self._counters:
            raise MetricTypeError(name, "counter")
        return CounterSummary(name=name, value=self._counters[name])

    def gauge_summary(self, name: str) -> GaugeSummary:
        entry = self._gauges.get(name)
        if entry is None:
            raise MetricTypeError(name, "gauge")
        return GaugeSummary(name=name, value=entry[0], last_updated_at=entry[1])

    def histogram_summary(self, name: str) -> HistogramSummary:
        values = sorted(self._require_histogram(name))
        if not values:
            raise MetricsError(f"histogram {name!r} has no observations")
        count = len(values)
        total = sum(values)
        return HistogramSummary(
            name=name,
            count=count,
            total=round(total, 6),
            mean=round(total / count, 6),
            median=round(_percentile(values, 50), 6),
            p95=round(_percentile(values, 95), 6),
            p99=round(_percentile(values, 99), 6),
            minimum=values[0],
            maximum=values[-1],
        )

    def snapshot(self) -> dict[str, dict]:
        output: dict[str, dict] = {}
        for name in sorted(set(self._counters)):
            summary = self.counter_summary(name)
            output[name] = {"kind": summary.kind, "value": summary.value}
        for name in sorted(self._gauges):
            summary = self.gauge_summary(name)
            output[name] = {"kind": summary.kind, "value": summary.value}
        for name in sorted(self._histograms):
            if not self._histograms[name]:
                continue
            summary = self.histogram_summary(name)
            output[name] = {
                "kind": summary.kind,
                "count": summary.count,
                "mean": summary.mean,
                "p95": summary.p95,
                "p99": summary.p99,
            }
        return output

    def reset(self, name: str | None = None) -> None:
        if name is None:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            return
        removed_any = False
        for store in (self._counters, self._gauges, self._histograms):
            if name in store:
                del store[name]
                removed_any = True
        if not removed_any:
            raise UnknownMetricError(name)


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        raise ValueError("empty values")
    rank = (len(sorted_values) - 1) * (percentile / 100.0)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return sorted_values[int(rank)]
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight
