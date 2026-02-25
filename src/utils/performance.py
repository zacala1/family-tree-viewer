"""성능 모니터링 및 프로파일링 유틸리티."""

import time
import functools
from collections import deque
from typing import Callable, Any, Optional
from contextlib import contextmanager

from .logger import get_logger, log_action

# Maximum number of metric samples to retain per operation
_MAX_METRIC_SAMPLES = 1000


class PerformanceMonitor:
    """성능 메트릭 수집 클래스."""

    def __init__(self):
        self._metrics: dict[str, deque[float]] = {}
        self._logger = get_logger()

    def record(self, operation: str, duration: float) -> None:
        """작업 수행 시간 기록."""
        if operation not in self._metrics:
            self._metrics[operation] = deque(maxlen=_MAX_METRIC_SAMPLES)
        self._metrics[operation].append(duration)

    def get_stats(self, operation: str) -> Optional[dict[str, float]]:
        """작업의 통계 반환."""
        if operation not in self._metrics or not self._metrics[operation]:
            return None

        durations = self._metrics[operation]
        return {
            "count": len(durations),
            "total": sum(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """모든 작업의 통계 반환."""
        return {op: self.get_stats(op) for op in self._metrics if self.get_stats(op)}

    def log_stats(self) -> None:
        """수집된 통계를 로그로 출력."""
        stats = self.get_all_stats()
        if not stats:
            return

        self._logger.info("=== Performance Statistics ===")
        for operation, metrics in stats.items():
            self._logger.info(
                f"{operation}: avg={metrics['average']:.3f}s, "
                f"min={metrics['min']:.3f}s, max={metrics['max']:.3f}s, "
                f"count={metrics['count']}"
            )

    def clear(self) -> None:
        """수집된 메트릭 초기화."""
        self._metrics.clear()


# 전역 성능 모니터 인스턴스
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """성능 모니터 인스턴스 반환."""
    return _performance_monitor


@contextmanager
def measure_time(operation: str, log_result: bool = False):
    """컨텍스트 매니저로 작업 시간 측정.

    Usage:
        with measure_time("load_file"):
            tree = FileHandler.load_file(path)
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        _performance_monitor.record(operation, duration)

        if log_result or duration > 1.0:  # 1초 이상 걸리면 자동 로그
            log_action(
                "performance_measured",
                operation=operation,
                duration=f"{duration:.3f}s",
            )


def profile(operation_name: Optional[str] = None) -> Callable:
    """데코레이터로 함수 실행 시간 측정.

    Usage:
        @profile("calculate_generations")
        def calculate_generations(self):
            ...
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                _performance_monitor.record(op_name, duration)

                # 느린 함수는 경고 로그
                if duration > 0.5:
                    get_logger().warning(
                        f"Slow operation: {op_name} took {duration:.3f}s"
                    )

        return wrapper

    return decorator


class MemoryTracker:
    """메모리 사용량 추적 (간단한 구현)."""

    @staticmethod
    def get_object_size(obj: Any) -> int:
        """객체의 대략적인 메모리 크기 반환 (바이트)."""
        import sys

        return sys.getsizeof(obj)

    @staticmethod
    def log_family_tree_size(family_tree: Any) -> None:
        """가계도 객체의 메모리 사용량 로그."""
        import sys

        persons_count = len(family_tree.get_all_persons())
        relationships_count = len(family_tree.get_all_relationships())

        # 대략적인 크기 계산
        total_size = sys.getsizeof(family_tree._persons) + sys.getsizeof(
            family_tree._relationships
        )

        log_action(
            "memory_usage",
            persons_count=persons_count,
            relationships_count=relationships_count,
            total_size_mb=f"{total_size / 1024 / 1024:.2f}",
        )


# 편의 함수
def log_performance_stats() -> None:
    """수집된 성능 통계 로그 출력."""
    _performance_monitor.log_stats()


def clear_performance_stats() -> None:
    """성능 통계 초기화."""
    _performance_monitor.clear()
