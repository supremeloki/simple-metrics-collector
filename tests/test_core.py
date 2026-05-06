import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from metrics_collector import (
    MetricsCollector,
    MetricsError,
    MetricTypeError,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 500.0

    def __call__(self) -> float:
        self.now += 1.0
        return self.now


@pytest.fixture
def collector():
    return MetricsCollector(clock=FakeClock())


def test_counter_increments_accumulate(collector):
    collector.inc("requests")
    collector.inc("requests", 4)
    assert collector.counter_summary("requests").value == 5.0


def test_negative_increment_rejected(collector):
    with pytest.raises(MetricsError):
        collector.inc("bad", -1)


def test_gauge_records_latest_with_timestamp(collector):
    collector.gauge("queue_depth", 12)
    latest = collector.gauge("queue_depth", 7)
    summary = collector.gauge_summary("queue_depth")
    assert summary.value == 7
    assert latest == 7
    assert summary.last_updated_at > 500


def test_histogram_observations_sorted_stats(collector):
    for value in [10, 2, 8, 4, 6]:
        collector.observe("latency", value)
    stats = collector.histogram_summary("latency")
    assert stats.count == 5
    assert stats.minimum == 2
    assert stats.maximum == 10
    assert stats.mean == 6.0
    assert stats.median == 6.0


def test_percentiles_monotonic(collector):
    for value in range(1, 101):
        collector.observe("spread", value)
    stats = collector.histogram_summary("spread")
    assert stats.p95 <= stats.p99
    assert 94 < stats.p95 < 97
    assert 98 < stats.p99 <= 100


def test_non_numeric_observation_rejected(collector):
    with pytest.raises(MetricsError):
        collector.observe("x", "fast")


def test_nan_inf_rejected(collector):
    with pytest.raises(MetricsError):
        collector.observe("x", float("nan"))
    with pytest.raises(MetricsError):
        collector.observe("x", float("inf"))


def test_wrong_kind_access_raises(collector):
    collector.inc("only_counter")
    with pytest.raises(MetricTypeError):
        collector.histogram_summary("only_counter")
    with pytest.raises(MetricTypeError):
        collector.gauge_summary("only_counter")


def test_empty_histogram_raises(collector):
    collector._histograms["empty"] = []
    with pytest.raises(MetricsError):
        collector.histogram_summary("empty")


def test_snapshot_groups_by_kind(collector):
    collector.inc("hits")
    collector.gauge("temp", 3)
