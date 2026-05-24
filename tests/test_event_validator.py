"""EventValidator 회귀 가드.

PersonValidator처럼 비즈니스 검증이 UI에서 분리됐는지 + EVENT_TYPES 단일 소스
가 잘 동기화되는지 검증.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.validators import EventValidator
from src.models.event import EVENT_TYPES


class TestValidateTitle:
    def test_valid_title(self):
        ok, err = EventValidator.validate_title("졸업")
        assert ok and err == ""

    def test_empty_title_fails(self):
        ok, err = EventValidator.validate_title("")
        assert not ok and err

    def test_whitespace_only_fails(self):
        ok, err = EventValidator.validate_title("   ")
        assert not ok

    def test_long_title_fails(self):
        ok, err = EventValidator.validate_title("x" * 1000)
        assert not ok


class TestValidateEventType:
    def test_all_canonical_types_valid(self):
        for et in EVENT_TYPES:
            ok, err = EventValidator.validate_event_type(et)
            assert ok, f"{et} should be valid: {err}"

    def test_unknown_type_fails(self):
        ok, err = EventValidator.validate_event_type("unknown_type_xyz")
        assert not ok
        assert err  # 메시지가 있어야 함

    def test_empty_type_fails(self):
        ok, err = EventValidator.validate_event_type("")
        assert not ok


class TestValidateAll:
    def test_minimal_valid(self):
        ok, err = EventValidator.validate_all(title="졸업", event_type="graduation")
        assert ok

    def test_title_failure_short_circuits(self):
        ok, err = EventValidator.validate_all(title="", event_type="other")
        assert not ok

    def test_invalid_type_fails(self):
        ok, err = EventValidator.validate_all(title="t", event_type="bogus")
        assert not ok

    def test_invalid_date_fails(self):
        # YEAR_MAX 초과
        ok, err = EventValidator.validate_all(
            title="졸업", event_type="graduation", year=99999, month=1, day=1
        )
        assert not ok

    def test_valid_with_full_date(self):
        ok, err = EventValidator.validate_all(
            title="결혼", event_type="marriage", year=2020, month=6, day=15
        )
        assert ok


class TestSingleSourceOfTruth:
    """EVENT_TYPES 모듈 상수가 모든 곳에서 단일 소스로 쓰이는지."""

    def test_event_dataclass_default_in_valid(self):
        """Event 모델의 _VALID_EVENT_TYPES가 EVENT_TYPES와 동일한 집합."""
        from src.models.event import Event
        assert Event._VALID_EVENT_TYPES == set(EVENT_TYPES)

    def test_event_dialog_iterates_same_list(self, qapp):
        """EventDialog가 EVENT_TYPES와 같은 항목들로 콤보를 채우는지."""
        from src.views.event_dialog import EventDialog
        dlg = EventDialog()
        try:
            combo_types = [dlg.type_combo.itemData(i) for i in range(dlg.type_combo.count())]
            assert tuple(combo_types) == EVENT_TYPES
        finally:
            dlg.deleteLater()


class TestEventDialogUsesValidator:
    """event_dialog._save가 EventValidator를 통과해야만 accept하는지."""

    def test_save_rejected_for_empty_title(self, qapp, monkeypatch):
        from src.views.event_dialog import EventDialog
        from PyQt6.QtWidgets import QMessageBox
        # warning 다이얼로그를 mock해서 사용자 입력 대기 방지
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: None)
        dlg = EventDialog()
        try:
            dlg.title_input.setText("")  # 빈 제목
            dlg._save()
            # accept 안 됨 — result()는 0 (Rejected 또는 미설정)
            assert dlg.result() != dlg.DialogCode.Accepted
        finally:
            dlg.deleteLater()

    def test_save_accepted_for_valid_input(self, qapp):
        from src.views.event_dialog import EventDialog
        dlg = EventDialog()
        try:
            dlg.title_input.setText("졸업")
            dlg._save()
            assert dlg.result() == dlg.DialogCode.Accepted
            evt = dlg.get_event()
            assert evt is not None
            assert evt.title == "졸업"
        finally:
            dlg.deleteLater()
