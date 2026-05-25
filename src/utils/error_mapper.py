"""기술 예외 → 사용자 친화적 메시지 매퍼.

`str(exception)`을 그대로 UI에 노출하면 (1) Python 예외 type 명·stack trace 잔재,
(2) 절대 파일 경로 leak, (3) 비전문가 사용자가 이해 못 하는 영문 메시지가 보임.
이 모듈은 예외를 카테고리별로 분류해 i18n된 한 문장 메시지로 변환.
"""
from __future__ import annotations

import json
from typing import Optional

from ..i18n import tr


def humanize_exception(exc: BaseException, context: Optional[str] = None) -> str:
    """예외를 사용자에게 보여줄 한 줄 메시지로 변환.

    Args:
        exc: 발생한 예외
        context: 선택적 컨텍스트 ("saving photo", "loading file" 등)
                 i18n 메시지에 {context}로 치환됨. 없으면 generic.

    Returns:
        사용자 친화적 i18n 메시지. 디버그용 원본 메시지는 logger로만 기록.
    """
    ctx = context or tr("error.exc_context_default")

    # 파일/IO 카테고리
    if isinstance(exc, FileNotFoundError):
        return tr("error.exc_file_not_found", context=ctx)
    if isinstance(exc, PermissionError):
        return tr("error.exc_permission_denied", context=ctx)
    if isinstance(exc, IsADirectoryError):
        return tr("error.exc_is_directory", context=ctx)
    if isinstance(exc, OSError):
        # 디스크 가득참·네트워크 드라이브 분리 등 포괄
        return tr("error.exc_os_error", context=ctx)

    # 데이터 파싱
    if isinstance(exc, json.JSONDecodeError):
        return tr("error.exc_json_decode", context=ctx)
    if isinstance(exc, (UnicodeDecodeError, UnicodeEncodeError)):
        return tr("error.exc_encoding", context=ctx)

    # 값/타입 일반
    if isinstance(exc, ValueError):
        return tr("error.exc_invalid_value", context=ctx)
    if isinstance(exc, TypeError):
        return tr("error.exc_type_error", context=ctx)

    # 리소스
    if isinstance(exc, MemoryError):
        return tr("error.exc_memory_error", context=ctx)

    # 미분류 — generic 메시지 (원본은 logger.error로 별도 기록 권장)
    return tr("error.exc_generic", context=ctx)
