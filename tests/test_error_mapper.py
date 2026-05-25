"""error_mapper 회귀 가드 — 기술 예외 → 사용자 친화적 메시지."""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.utils.error_mapper import humanize_exception


class TestExceptionMapping:
    """주요 예외 카테고리가 각각 다른 카테고리 메시지로 변환됨."""

    def test_file_not_found(self):
        msg = humanize_exception(FileNotFoundError("/secret/path"))
        assert msg
        # 메시지에 raw 경로가 포함되지 않아야
        assert "/secret/path" not in msg
        # "file" 키워드 또는 "파일" 포함
        assert any(k in msg.lower() for k in ("file", "파일"))

    def test_permission_denied(self):
        msg = humanize_exception(PermissionError("Access denied"))
        assert "Access denied" not in msg  # raw 메시지 미노출
        assert any(k in msg.lower() for k in ("permission", "권한"))

    def test_os_error(self):
        msg = humanize_exception(OSError("Disk full"))
        assert "Disk full" not in msg
        assert msg  # 빈 문자열 아님

    def test_json_decode_error(self):
        try:
            json.loads("not valid json")
        except json.JSONDecodeError as exc:
            msg = humanize_exception(exc)
        assert "Expecting" not in msg  # raw JSON error 미노출

    def test_unicode_decode_error(self):
        try:
            b"\xff\xfe\x00".decode("utf-8")
        except UnicodeDecodeError as exc:
            msg = humanize_exception(exc)
        assert "0xff" not in msg.lower()  # raw 바이트 미노출

    def test_value_error(self):
        msg = humanize_exception(ValueError("foo"))
        assert "foo" not in msg

    def test_type_error(self):
        msg = humanize_exception(TypeError("bar"))
        assert "bar" not in msg

    def test_memory_error(self):
        msg = humanize_exception(MemoryError())
        assert msg

    def test_generic_exception_falls_through(self):
        """미분류 예외도 메시지를 받음 (빈 문자열 아님)."""
        class CustomError(Exception):
            pass
        msg = humanize_exception(CustomError("internal secret"))
        assert msg
        assert "internal secret" not in msg


class TestContextInjection:
    def test_context_appears_in_message(self):
        msg = humanize_exception(FileNotFoundError(), context="loading config")
        assert "loading config" in msg

    def test_default_context_used_when_none(self):
        msg = humanize_exception(FileNotFoundError())
        # 기본 context도 메시지 안에 표시
        assert msg  # 빈 문자열 아님
        # default context (한글 "작업" 또는 영문 "operation") 포함
        assert any(k in msg for k in ("작업", "operation"))


class TestSensitiveDataRedaction:
    """raw 예외 메시지가 노출되지 않는지 — 보안·UX 핵심."""

    def test_path_not_leaked(self):
        msg = humanize_exception(
            FileNotFoundError("/home/user/.ssh/id_rsa not found"),
            context="loading file",
        )
        assert ".ssh" not in msg
        assert "id_rsa" not in msg

    def test_stack_trace_text_not_leaked(self):
        try:
            raise OSError("Errno 28: No space left on device — /dev/sda1")
        except OSError as e:
            msg = humanize_exception(e)
        assert "/dev/sda1" not in msg
        assert "Errno" not in msg
