"""성능 모니터링 유틸 테스트."""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.performance import (
    PerformanceMonitor,
    measure_time,
    profile,
    MemoryTracker,
    get_performance_monitor,
    clear_performance_stats,
    _MAX_METRIC_SAMPLES,
)


class TestPerformanceMonitor:
    def setup_method(self):
        self.monitor = PerformanceMonitor()

    def test_record_and_get_stats(self):
        self.monitor.record("op1", 0.1)
        self.monitor.record("op1", 0.2)
        self.monitor.record("op1", 0.3)
        stats = self.monitor.get_stats("op1")
        assert stats["count"] == 3
        assert abs(stats["average"] - 0.2) < 1e-9
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3
        assert abs(stats["total"] - 0.6) < 1e-9

    def test_get_stats_returns_none_for_missing(self):
        assert self.monitor.get_stats("nonexistent") is None

    def test_circular_buffer_evicts_oldest(self):
        """_MAX_METRIC_SAMPLES (1000) 초과 시 deque maxlen이 가장 오래된 샘플 제거."""
        # 1001번 기록 → count가 1000으로 capped
        for i in range(_MAX_METRIC_SAMPLES + 1):
            self.monitor.record("burst", float(i))
        stats = self.monitor.get_stats("burst")
        assert stats["count"] == _MAX_METRIC_SAMPLES
        # 가장 오래된 0.0이 evict됐어야 함
        assert stats["min"] == 1.0
        assert stats["max"] == float(_MAX_METRIC_SAMPLES)

    def test_multiple_operations_isolated(self):
        self.monitor.record("op1", 0.5)
        self.monitor.record("op2", 1.5)
        assert self.monitor.get_stats("op1")["max"] == 0.5
        assert self.monitor.get_stats("op2")["max"] == 1.5

    def test_get_all_stats(self):
        self.monitor.record("a", 0.1)
        self.monitor.record("b", 0.2)
        all_stats = self.monitor.get_all_stats()
        assert "a" in all_stats
        assert "b" in all_stats

    def test_clear_resets_all(self):
        self.monitor.record("op1", 0.5)
        self.monitor.clear()
        assert self.monitor.get_stats("op1") is None
        assert self.monitor.get_all_stats() == {}


class TestMeasureTimeContextManager:
    def setup_method(self):
        clear_performance_stats()

    def test_records_duration(self):
        with measure_time("ctx_op"):
            time.sleep(0.01)
        stats = get_performance_monitor().get_stats("ctx_op")
        assert stats is not None
        assert stats["count"] == 1
        assert stats["min"] > 0

    def test_records_even_on_exception(self):
        try:
            with measure_time("ctx_fail"):
                raise RuntimeError("oops")
        except RuntimeError:
            pass
        stats = get_performance_monitor().get_stats("ctx_fail")
        assert stats is not None
        assert stats["count"] == 1


class TestProfileDecorator:
    def setup_method(self):
        clear_performance_stats()

    def test_records_each_call(self):
        @profile("decorated_op")
        def my_func(x):
            return x * 2

        my_func(1)
        my_func(2)
        stats = get_performance_monitor().get_stats("decorated_op")
        assert stats["count"] == 2

    def test_preserves_return_value(self):
        @profile("returner")
        def returner():
            return "hello"
        assert returner() == "hello"

    def test_default_operation_name_is_qualified(self):
        @profile()
        def some_func():
            return None
        some_func()
        # operation name = module.function
        stats = get_performance_monitor().get_all_stats()
        # 정확한 이름은 모듈 경로에 의존 — some_func만 포함되는지 확인
        assert any("some_func" in op for op in stats.keys())

    def test_propagates_exception(self):
        @profile("error_op")
        def will_fail():
            raise ValueError("boom")
        import pytest
        with pytest.raises(ValueError):
            will_fail()
        # 그래도 기록은 됐어야 함
        assert get_performance_monitor().get_stats("error_op") is not None


class TestMemoryTracker:
    def test_get_object_size_returns_int(self):
        size = MemoryTracker.get_object_size("hello")
        assert isinstance(size, int)
        assert size > 0
