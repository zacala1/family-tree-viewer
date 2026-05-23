"""ThemeManager 유닛 테스트."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.utils.theme_manager import ThemeManager, get_theme_manager


@pytest.fixture
def fresh_manager():
    """각 테스트마다 새 ThemeManager 인스턴스 (싱글톤 회피)."""
    return ThemeManager()


class TestThemeManagerBasics:
    def test_default_theme_is_light(self, fresh_manager):
        assert fresh_manager.current_theme == "light"
        assert fresh_manager.is_dark is False

    def test_set_dark_theme(self, fresh_manager):
        ok = fresh_manager.set_theme("dark")
        assert ok is True
        assert fresh_manager.current_theme == "dark"
        assert fresh_manager.is_dark is True

    def test_set_light_theme_returns_true(self, fresh_manager):
        # 이미 light인데 light로 다시 설정 → True 반환 (no-op)
        ok = fresh_manager.set_theme("light")
        assert ok is True

    def test_set_invalid_theme_returns_false(self, fresh_manager):
        ok = fresh_manager.set_theme("solarized")
        assert ok is False
        assert fresh_manager.current_theme == "light"  # 변하지 않음

    def test_toggle_theme(self, fresh_manager):
        # light → dark
        new_theme = fresh_manager.toggle_theme()
        assert new_theme == "dark"
        # dark → light
        new_theme = fresh_manager.toggle_theme()
        assert new_theme == "light"


class TestThemeChangedSignal:
    def test_signal_emitted_on_change(self, fresh_manager):
        received = []
        fresh_manager.theme_changed.connect(lambda t: received.append(t))
        fresh_manager.set_theme("dark")
        assert received == ["dark"]

    def test_signal_not_emitted_when_same_theme(self, fresh_manager):
        received = []
        fresh_manager.theme_changed.connect(lambda t: received.append(t))
        fresh_manager.set_theme("light")  # 이미 light → no emit
        assert received == []

    def test_signal_emitted_on_toggle(self, fresh_manager):
        received = []
        fresh_manager.theme_changed.connect(lambda t: received.append(t))
        fresh_manager.toggle_theme()
        fresh_manager.toggle_theme()
        assert received == ["dark", "light"]


class TestGetTreeColors:
    def test_light_and_dark_have_same_keys(self, fresh_manager):
        light_colors = fresh_manager.get_tree_colors()
        fresh_manager.set_theme("dark")
        dark_colors = fresh_manager.get_tree_colors()
        # 두 팔레트 키 집합 완전 일치 (코드가 한쪽만 알면 다른 테마에서 KeyError)
        assert set(light_colors.keys()) == set(dark_colors.keys())

    def test_required_keys_present(self, fresh_manager):
        colors = fresh_manager.get_tree_colors()
        required = {
            "background", "card_bg", "card_border",
            "card_selected_border", "text", "shadow",
        }
        assert required.issubset(set(colors.keys()))

    def test_dark_returns_dark_colors(self, fresh_manager):
        fresh_manager.set_theme("dark")
        colors = fresh_manager.get_tree_colors()
        # 다크 배경은 어두운 색이어야 함 (#181825 같은)
        assert colors["background"].startswith("#1") or colors["background"].startswith("#0")


class TestSingleton:
    def test_get_theme_manager_returns_same_instance(self):
        a = get_theme_manager()
        b = get_theme_manager()
        assert a is b
