"""중앙집중식 로깅 시스템."""

import logging
import sys
import threading
from pathlib import Path
from typing import Optional


class AppLogger:
    """애플리케이션 로거 관리 클래스."""

    _instance: Optional["AppLogger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # 이미 초기화되었으면 스킵
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized: bool = True

        self._logger = logging.getLogger("FamilyTree")
        self._logger.setLevel(logging.DEBUG)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # 파일 핸들러 (선택적)
        try:
            log_dir = Path.home() / ".familytree" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "familytree.log"

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            self._logger.warning(f"Failed to create log file: {e}")

    @property
    def logger(self) -> logging.Logger:
        """로거 인스턴스 반환."""
        if self._logger is None:
            raise RuntimeError("Logger not initialized")
        return self._logger


_app_logger: Optional[AppLogger] = None
_lock = threading.Lock()


def get_logger() -> logging.Logger:
    """애플리케이션 로거 반환 (스레드 안전 싱글톤)."""
    global _app_logger
    if _app_logger is None:
        with _lock:
            # Double-check locking pattern
            if _app_logger is None:
                _app_logger = AppLogger()
    return _app_logger.logger


def debug(msg: str) -> None:
    """디버그 로그."""
    get_logger().debug(msg)


def info(msg: str) -> None:
    """정보 로그."""
    get_logger().info(msg)


def warning(msg: str) -> None:
    """경고 로그."""
    get_logger().warning(msg)


def error(msg: str) -> None:
    """오류 로그."""
    get_logger().error(msg)


def critical(msg: str) -> None:
    """치명적 오류 로그."""
    get_logger().critical(msg)
