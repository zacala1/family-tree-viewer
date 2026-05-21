"""Logger 유닛 테스트.

회귀 방지 핵심:
- log_action()이 LogRecord 예약 속성 키(name, msg, args, etc.)를
  kwargs로 받아도 KeyError 없이 동작 (직전 fix 회귀 가드).
- JSONFormatter가 비직렬화 객체를 repr로 폴백.
"""
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import log_action, JSONFormatter


class TestLogActionReservedKeys:
    """LogRecord 예약 속성 충돌 회귀 가드."""

    def test_name_kwarg_does_not_crash(self, caplog):
        """과거: log_action(..., name='X') → KeyError. 현재: ctx_name으로 안전 변환."""
        with caplog.at_level(logging.INFO, logger="FamilyTree"):
            log_action("person_added", person_id="p1", name="홍길동")
        assert any("Action: person_added" in r.message for r in caplog.records)
        # ctx_name으로 prefix됐는지 확인
        record = next(r for r in caplog.records if "person_added" in r.message)
        assert getattr(record, "ctx_name", None) == "홍길동"

    def test_normal_kwargs_pass_through(self, caplog):
        with caplog.at_level(logging.INFO, logger="FamilyTree"):
            log_action("delete", person_id="p1", custom_field="value")
        record = next(r for r in caplog.records if "delete" in r.message)
        assert getattr(record, "custom_field", None) == "value"
        assert getattr(record, "person_id", None) == "p1"

    def test_multiple_reserved_keys_all_prefixed(self, caplog):
        """msg·module·filename·levelname 등 여러 reserved key 동시 전달."""
        with caplog.at_level(logging.INFO, logger="FamilyTree"):
            log_action(
                "test",
                name="X",
                module="my_module",
                filename="my_file.py",
                levelname="OVERRIDE",
            )
        record = next(r for r in caplog.records if "Action: test" in r.message)
        assert getattr(record, "ctx_name", None) == "X"
        assert getattr(record, "ctx_module", None) == "my_module"
        assert getattr(record, "ctx_filename", None) == "my_file.py"
        assert getattr(record, "ctx_levelname", None) == "OVERRIDE"

    def test_no_kwargs_works(self, caplog):
        with caplog.at_level(logging.INFO, logger="FamilyTree"):
            log_action("simple")
        assert any("Action: simple" in r.message for r in caplog.records)


class TestJSONFormatter:
    def _make_record(self, **extra) -> logging.LogRecord:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="x.py",
            lineno=42,
            msg="hello %s",
            args=("world",),
            exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_basic_format_has_required_fields(self):
        formatter = JSONFormatter()
        record = self._make_record()
        data = json.loads(formatter.format(record))
        assert data["level"] == "INFO"
        assert data["message"] == "hello world"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_extra_fields_included(self):
        formatter = JSONFormatter()
        record = self._make_record(person_id="p1", action="add")
        data = json.loads(formatter.format(record))
        assert data["person_id"] == "p1"
        assert data["action"] == "add"

    def test_non_serializable_falls_back_to_repr(self):
        formatter = JSONFormatter()

        class Custom:
            def __repr__(self):
                return "<Custom obj>"

        record = self._make_record(custom_obj=Custom())
        data = json.loads(formatter.format(record))
        assert data["custom_obj"] == "<Custom obj>"

    def test_standard_attributes_excluded_from_extra(self):
        """LogRecord의 표준 속성은 extra로 노출되지 않아야 함."""
        formatter = JSONFormatter()
        record = self._make_record()
        data = json.loads(formatter.format(record))
        # 'pathname'은 표준 속성이지만 'filename'만 표준에 포함되어 노출 안 됨
        assert "args" not in data
        assert "levelno" not in data

    def test_korean_characters_not_escaped(self):
        formatter = JSONFormatter()
        record = self._make_record(person_name="홍길동")
        result = formatter.format(record)
        # ensure_ascii=False로 한글 그대로 표현
        assert "홍길동" in result
