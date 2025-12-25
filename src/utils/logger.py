"""중앙집중식 로깅 시스템."""
import logging
import sys
from pathlib import Path
from typing import Optional


class AppLogger:
    """애플리케이션 로거 관리 클래스."""

    _instance: Optional['AppLogger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is not None:
            return

        self._logger = logging.getLogger('FamilyTree')
        self._logger.setLevel(logging.DEBUG)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # 파일 핸들러 (선택적)
        try:
            log_dir = Path.home() / '.familytree' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'familytree.log'

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            self._logger.warning(f"Failed to create log file: {e}")

    @property
    def logger(self) -> logging.Logger:
        """로거 인스턴스 반환."""
        return self._logger


_app_logger: Optional[AppLogger] = None


def get_logger() -> logging.Logger:
    """애플리케이션 로거 반환 (싱글톤)."""
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger.logger


def debug(msg: str):
    """디버그 로그."""
    get_logger().debug(msg)


def info(msg: str):
    """정보 로그."""
    get_logger().info(msg)


def warning(msg: str):
    """경고 로그."""
    get_logger().warning(msg)


def error(msg: str):
    """오류 로그."""
    get_logger().error(msg)


def critical(msg: str):
    """치명적 오류 로그."""
    get_logger().critical(msg)
