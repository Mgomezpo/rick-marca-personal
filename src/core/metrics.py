import time
import threading
from typing import Any, Dict, List, Optional

class MetricsTracker:
    """
    Recolector de métricas RED (Rate, Errors, Duration) en memoria.
    Thread-safe, con ventana deslizante para cálculo de percentiles (p50, p95)
    y desglose por canal de entrada y herramientas.
    """
    def __init__(self, max_samples: int = 1000):
        self._lock = threading.Lock()
        self._max_samples = max_samples
        self.start_time = time.time()
        self.requests_total = 0
        self.errors_total = 0
        self.latencies: List[float] = []
        self.by_channel: Dict[str, Dict[str, int]] = {}
        self.by_tool: Dict[str, Dict[str, int]] = {}

    def record_request(
        self,
        channel: str,
        duration_ms: float,
        is_error: bool = False,
        model: Optional[str] = None
    ) -> None:
        with self._lock:
            self.requests_total += 1
            if is_error:
                self.errors_total += 1

            self.latencies.append(round(duration_ms, 2))
            if len(self.latencies) > self._max_samples:
                self.latencies.pop(0)

            ch = channel or "unknown"
            if ch not in self.by_channel:
                self.by_channel[ch] = {"requests": 0, "errors": 0}
            self.by_channel[ch]["requests"] += 1
            if is_error:
                self.by_channel[ch]["errors"] += 1

    def record_tool_call(
        self,
        tool_name: str,
        duration_ms: float,
        is_error: bool = False
    ) -> None:
        with self._lock:
            t_name = tool_name or "unknown"
            if t_name not in self.by_tool:
                self.by_tool[t_name] = {"calls": 0, "errors": 0}
            self.by_tool[t_name]["calls"] += 1
            if is_error:
                self.by_tool[t_name]["errors"] += 1

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            uptime_seconds = int(now - self.start_time)
            error_rate = (
                round(self.errors_total / self.requests_total, 4)
                if self.requests_total > 0
                else 0.0
            )

            sorted_lat = sorted(self.latencies)
            count = len(sorted_lat)

            if count > 0:
                p50 = sorted_lat[int(count * 0.50)]
                p95_idx = min(int(count * 0.95), count - 1)
                p95 = sorted_lat[p95_idx]
                avg = round(sum(sorted_lat) / count, 2)
                min_lat = sorted_lat[0]
                max_lat = sorted_lat[-1]
            else:
                p50 = 0.0
                p95 = 0.0
                avg = 0.0
                min_lat = 0.0
                max_lat = 0.0

            return {
                "uptime_seconds": uptime_seconds,
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "error_rate": error_rate,
                "latency_ms": {
                    "p50": p50,
                    "p95": p95,
                    "avg": avg,
                    "min": min_lat,
                    "max": max_lat,
                    "samples": count,
                },
                "by_channel": dict(self.by_channel),
                "by_tool": dict(self.by_tool),
            }

    def reset(self) -> None:
        with self._lock:
            self.start_time = time.time()
            self.requests_total = 0
            self.errors_total = 0
            self.latencies.clear()
            self.by_channel.clear()
            self.by_tool.clear()

metrics_tracker = MetricsTracker()
