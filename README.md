# metrics-collector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

In-process metrics: monotonic counters, timestamped gauges, and histograms with percentile statistics (p50/p95/p99) — Prometheus-style semantics with zero dependencies.

## 🚀 Overview

You don't need a metrics stack to know your service is misbehaving. `metrics-collector` gives the three primitives that matter: **counters** that only go up, **gauges** that record the latest value with a timestamp, and **histograms** that keep every observation and compute mean, median, p95, p99, min/max on demand. Non-numeric, NaN, and infinite observations are rejected before they poison statistics. One call exports everything as a JSON-ready snapshot.

## ✨ Features

- **Counters:** monotonic accumulation; negative increments rejected
- **Gauges:** latest-value semantics with last-updated timestamps
- **Histograms:** full observation storage; interpolated percentiles (not nearest-rank lies)
- **Input guards:** strings/bools/NaN/inf rejected at observe-time
- **Kind-safe summaries:** asking a counter for histogram stats raises `MetricTypeError`
- **Snapshot export:** all metrics as one dict for `/metrics` endpoints
- **Selective reset:** one metric or the whole registry
- **Injectable clock** · zero dependencies

## 🚧 Structure

```
simple-metrics-collector/
├── src/metrics_collector/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/simple-metrics-collector.git
cd simple-metrics-collector
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from metrics_collector import MetricsCollector

metrics = MetricsCollector()

def handle_request():
    metrics.inc("requests_total")
    start = time.monotonic()
    ...
    metrics.observe("latency_ms", (time.monotonic() - start) * 1000)

print(metrics.histogram_summary("latency_ms").p95)
return metrics.snapshot()      # wire into GET /metrics
```

## 🔧 Error Handling

```text
MetricsError
├── MetricTypeError     # wrong-kind summary request (counter vs histogram vs gauge)
├── UnknownMetricError  # reset of an unregistered name
└── invalid input       # negative inc / non-numeric / non-finite observations
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen summaries
- Zero comments — names carry the meaning
- Percentile math asserted monotonic; input-poisoning vectors covered

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!
