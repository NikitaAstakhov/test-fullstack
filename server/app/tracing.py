import time
import psutil
import objgraph
from enum import Flag, auto
from typing import Any, Dict, Optional
from contextlib import ExitStack

from opentelemetry import trace
from opentelemetry.trace import Span, Tracer, Status, StatusCode


class TraceFeatures(Flag):
    TRANSACTION = auto()
    SPAN = auto()
    METRICS = auto()
    OBJGRAPH = auto()


class MetricsCollector:
    _start_time: Optional[float]
    _start_cpu: Optional[psutil._common.pcputimes]
    _start_mem: Any

    def __init__(self) -> None:
        self._start_time = None
        self._start_cpu = None
        self._start_mem = None

    def start(self) -> None:
        proc = psutil.Process()
        self._start_time = time.perf_counter()
        self._start_cpu = proc.cpu_times()
        self._start_mem = proc.memory_info()

    def finish(self) -> Dict[str, Any]:
        proc = psutil.Process()
        end_time = time.perf_counter()
        assert self._start_time is not None, "MetricsCollector.start() must be called first"
        assert self._start_cpu is not None, "MetricsCollector.start() must be called first"
        assert self._start_mem is not None, "MetricsCollector.start() must be called first"

        end_cpu = proc.cpu_times()
        end_mem = proc.memory_info()

        wall_s = end_time - self._start_time
        cpu_user = end_cpu.user - self._start_cpu.user
        cpu_sys = end_cpu.system - self._start_cpu.system
        rss_delta = end_mem.rss - self._start_mem.rss

        vm = psutil.virtual_memory()
        total_bytes = vm.total or 1
        rss_pct = (rss_delta / total_bytes) * 100

        return {
            "execution_time_s": round(wall_s, 4),
            "cpu.user_seconds": round(cpu_user, 4),
            "cpu.system_seconds": round(cpu_sys, 4),
            "memory.rss_delta_mb": round(rss_delta / 1024**2, 2),
            "memory.rss_pct_of_sys": round(rss_pct, 2),
            "system.total_memory_mb": round(total_bytes / 1024**2, 2),
        }


class ObjectGrowthCollector:
    _initial_stats: Optional[Dict[str, int]]

    def __init__(self) -> None:
        self._initial_stats = None

    def start(self) -> None:
        self._initial_stats = objgraph.typestats()

    def finish(self) -> Dict[str, int]:
        assert self._initial_stats is not None, "ObjectGrowthCollector.start() must be called first"
        final_stats = objgraph.typestats()
        growth: Dict[str, int] = {
            typ: final_stats.get(typ, 0) - self._initial_stats.get(typ, 0)
            for typ in final_stats
            if final_stats.get(typ, 0) > self._initial_stats.get(typ, 0)
        }
        return growth


class MemoryLeakDetector:
    _threshold_pct: float

    def __init__(self, threshold_pct: float = 10.0) -> None:
        self._threshold_pct = threshold_pct

    def check(self, rss_pct: float) -> bool:
        return rss_pct > self._threshold_pct

    @property
    def threshold_pct(self) -> float:
        return self._threshold_pct


class OpenTelemetryAsyncTrace:
    _name: str
    _op: str
    _features: TraceFeatures
    _stack: ExitStack
    _tracer: Tracer
    _transaction: Optional[Span]
    _span: Optional[Span]
    _metrics: Optional[MetricsCollector]
    _objg: Optional[ObjectGrowthCollector]
    _leak_detector: Optional[MemoryLeakDetector]

    def __init__(
        self,
        name: str,
        *,
        op: str = "task",
        features: TraceFeatures = (
            TraceFeatures.TRANSACTION
            | TraceFeatures.SPAN
            | TraceFeatures.METRICS
            | TraceFeatures.OBJGRAPH
        ),
        memory_threshold_pct: float = 10.0,
    ) -> None:
        self._name = name
        self._op = op
        self._features = features
        self._stack = ExitStack()
        self._tracer = trace.get_tracer(__name__)
        self._transaction = None
        self._span = None

        self._metrics = (
            MetricsCollector() if (features & TraceFeatures.METRICS) else None
        )
        self._objg = (
            ObjectGrowthCollector() if (features & TraceFeatures.OBJGRAPH) else None
        )
        self._leak_detector = (
            MemoryLeakDetector(memory_threshold_pct)
            if (features & TraceFeatures.METRICS)
            else None
        )

    async def __aenter__(self) -> "OpenTelemetryAsyncTrace":
        if self._features & TraceFeatures.TRANSACTION:
            tx_span = self._tracer.start_span(
                name=self._name,
                attributes={"operation": self._op, "type": "transaction"},
            )
            token = trace.use_span(tx_span, end_on_exit=True)
            self._stack.enter_context(token)
            self._transaction = tx_span

        if self._features & TraceFeatures.SPAN:
            parent_ctx = (
                trace.set_span_in_context(self._transaction)
                if self._transaction
                else None
            )
            sp = self._tracer.start_span(
                name=f"{self._name}.span",
                context=parent_ctx,
                attributes={"operation": self._op, "type": "span"},
            )
            token_sp = trace.use_span(sp, end_on_exit=True)
            self._stack.enter_context(token_sp)
            self._span = sp

        if self._metrics is not None:
            self._metrics.start()

        if self._objg is not None:
            self._objg.start()

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        target_span = self._span or self._transaction

        if self._metrics is not None and target_span is not None:
            metrics_data = self._metrics.finish()
            for key, value in metrics_data.items():
                target_span.set_attribute(key, value)

            rss_pct = metrics_data["memory.rss_pct_of_sys"]
            assert self._leak_detector is not None, "Leak detector must be initialized"
            if self._leak_detector.check(rss_pct):
                target_span.add_event(
                    name="memory.leak.detected",
                    attributes={
                        "threshold_pct": self._leak_detector.threshold_pct,
                        "rss_pct": rss_pct,
                    },
                )
                target_span.set_status(
                    Status(status_code=StatusCode.ERROR, description="Memory leak detected")
                )

        if self._objg is not None and target_span is not None:
            growth = self._objg.finish()
            for typ, delta in growth.items():
                target_span.set_attribute(f"objgraph.growth.{typ}", delta)

        self._stack.close()
        return False
