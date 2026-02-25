"""중앙집중식 로깅 시스템 (구조화된 로깅 지원)."""

import logging
import logging.handlers
import sys
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포매터."""

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 변환."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 예외 정보가 있으면 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 추가 컨텍스트 정보 (extra 파라미터로 전달된 것들)
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "person_id"):
            log_data["person_id"] = record.person_id
        if hasattr(record, "action"):
            log_data["action"] = record.action

        return json.dumps(log_data, ensure_ascii=False)


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

        # 콘솔 핸들러 (사람이 읽기 쉬운 형식)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # 파일 핸들러 (JSON 형식 - 분석 및 모니터링 용이)
        try:
            log_dir = Path.home() / ".familytree" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "familytree.log"

            file_handler = logging.handlers.RotatingFileHandler(
                log_file, encoding="utf-8",
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JSONFormatter())
            self._logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            self._logger.warning(f"Failed to create log file: {e}")

    def set_level(self, level: int) -> None:
        """로그 레벨 동적 설정."""
        if self._logger:
            self._logger.setLevel(level)
            # 모든 핸들러의 레벨도 조정
            for handler in self._logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    # 콘솔 핸들러는 INFO 이상 유지
                    handler.setLevel(max(level, logging.INFO))
                else:
                    handler.setLevel(level)

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


def log_action(action: str, person_id: Optional[str] = None, **kwargs: Any) -> None:
    """구조화된 액션 로그 (JSON 형식으로 저장)."""
    extra: Dict[str, Any] = {"action": action}
    if person_id:
        extra["person_id"] = person_id
    extra.update(kwargs)
    get_logger().info(f"Action: {action}", extra=extra)


def set_log_level(level_name: str) -> None:
    """로그 레벨 설정 (문자열).

    Args:
        level_name: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    level = level_map.get(level_name.upper(), logging.INFO)
    global _app_logger
    if _app_logger is not None:
        _app_logger.set_level(level)
