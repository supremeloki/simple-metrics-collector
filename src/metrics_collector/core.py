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
