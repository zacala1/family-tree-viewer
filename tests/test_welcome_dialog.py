"""환영 다이얼로그 + first-run trigger 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import QSettings, QCoreApplication


@pytest.fixture
def isolated_settings(qapp):
    """다른 테스트와 격리된 QSettings."""
    original_app = QCoreApplication.applicationName()
    original_org = QCoreApplication.organizationName()
    QCoreApplication.setOrganizationName("FamilyTreeTest")
    QCoreApplication.setApplicationName(f"FamilyTreeWelcomeTest_{id(qapp)}")
    s = QSettings("FamilyTree", "FamilyTree")
    s.clear()
    yield s
    s.clear()
    QCoreApplication.setApplicationName(original_app)
    QCoreApplication.setOrganizationName(original_org)


class TestShouldShowWelcome:
    def test_first_run_returns_true(self, isolated_settings):
        from src.views.welcome_dialog import should_show_welcome
        assert should_show_welcome() is True

    def test_dismissed_returns_false(self, isolated_settings):
        from src.views.welcome_dialog import should_show_welcome
        isolated_settings.setValue("welcomeDismissed", True)
        assert should_show_welcome() is False

    def test_reset_clears_dismissed(self, isolated_settings):
        from src.views.welcome_dialog import (
            should_show_welcome,
            reset_welcome_dismissed,
        )
        isolated_settings.setValue("welcomeDismissed", True)
        assert should_show_welcome() is False
        reset_welcome_dismissed()
        assert should_show_welcome() is True


class TestWelcomeDialog:
    def test_dialog_creates_without_error(self, qapp, isolated_settings):
        from src.views.welcome_dialog import WelcomeDialog
        dlg = WelcomeDialog()
        try:
            assert dlg.windowTitle() != ""
            # 체크박스 기본값 True (한 번 봤으면 다시 안 보이게)
            assert dlg.dont_show_check.isChecked() is True
        finally:
            dlg.deleteLater()

    def test_accept_persists_choice(self, qapp, isolated_settings):
        from src.views.welcome_dialog import WelcomeDialog, should_show_welcome
        dlg = WelcomeDialog()
        try:
            # 체크박스 체크 → accept → dismissed 저장
            dlg.dont_show_check.setChecked(True)
            dlg.accept()
            assert should_show_welcome() is False
        finally:
            dlg.deleteLater()

    def test_accept_unchecked_keeps_showing(self, qapp, isolated_settings):
        from src.views.welcome_dialog import WelcomeDialog, should_show_welcome
        dlg = WelcomeDialog()
        try:
            dlg.dont_show_check.setChecked(False)
            dlg.accept()
            # dismissed=False — 다음에도 표시돼야
            assert should_show_welcome() is True
        finally:
            dlg.deleteLater()


class TestI18nKeysExist:
    def test_welcome_keys_in_both_locales(self):
        import json
        i18n_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "i18n",
        )
        for fn in ("en.json", "ko.json"):
            with open(os.path.join(i18n_dir, fn), encoding="utf-8") as f:
                data = json.load(f)
            assert "welcome" in data
            for k in ("title", "heading", "subtitle", "dont_show_again", "start_btn"):
                assert k in data["welcome"], f"{fn} missing welcome.{k}"
            # 4개 feature key 쌍
            for i in range(1, 5):
                assert f"feature_{i}_title" in data["welcome"]
                assert f"feature_{i}_desc" in data["welcome"]
