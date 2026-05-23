"""최근 파일 메뉴 회귀 가드.

QSettings는 OS 레지스트리/preferences에 저장되므로 테스트 격리를 위해
setApplicationName으로 별도 스코프를 사용.
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import QSettings, QCoreApplication


@pytest.fixture
def isolated_settings(qapp):
    """테스트마다 QSettings 스코프를 비워서 다른 테스트와 격리."""
    # 임시 application name으로 격리
    original_app_name = QCoreApplication.applicationName()
    original_org_name = QCoreApplication.organizationName()
    QCoreApplication.setOrganizationName("FamilyTreeTest")
    QCoreApplication.setApplicationName(f"FamilyTreeTest_{id(qapp)}")
    settings = QSettings("FamilyTree", "FamilyTree")
    settings.clear()
    yield settings
    settings.clear()
    QCoreApplication.setApplicationName(original_app_name)
    QCoreApplication.setOrganizationName(original_org_name)


@pytest.fixture
def main_window(qapp, isolated_settings):
    from src.views.main_window import MainWindow
    win = MainWindow()
    yield win
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


@pytest.fixture
def tmp_files(tmp_path):
    """5개의 임시 JSON 파일 경로."""
    paths = []
    for i in range(5):
        p = tmp_path / f"tree{i}.json"
        p.write_text("{}", encoding="utf-8")
        paths.append(str(p))
    return paths


class TestRecentFilesPersistence:
    def test_add_single_file(self, main_window, tmp_files):
        main_window._add_to_recent_files(tmp_files[0])
        recent = main_window._load_recent_files()
        assert recent == [os.path.abspath(tmp_files[0])]

    def test_most_recent_first(self, main_window, tmp_files):
        for p in tmp_files[:3]:
            main_window._add_to_recent_files(p)
        recent = main_window._load_recent_files()
        # 마지막 추가가 맨 앞
        assert recent[0] == os.path.abspath(tmp_files[2])
        assert recent[-1] == os.path.abspath(tmp_files[0])

    def test_duplicate_moves_to_front(self, main_window, tmp_files):
        main_window._add_to_recent_files(tmp_files[0])
        main_window._add_to_recent_files(tmp_files[1])
        main_window._add_to_recent_files(tmp_files[0])  # 재추가
        recent = main_window._load_recent_files()
        assert recent[0] == os.path.abspath(tmp_files[0])
        assert recent.count(os.path.abspath(tmp_files[0])) == 1  # 중복 없음

    def test_max_limit_enforced(self, main_window, tmp_path):
        """6개 추가하면 가장 오래된 1개 제거."""
        paths = []
        for i in range(7):
            p = tmp_path / f"file{i}.json"
            p.write_text("{}", encoding="utf-8")
            paths.append(str(p))
            main_window._add_to_recent_files(str(p))
        recent = main_window._load_recent_files()
        assert len(recent) == main_window._RECENT_FILES_MAX
        # 가장 최근 N개만
        expected = [os.path.abspath(p) for p in reversed(paths[-main_window._RECENT_FILES_MAX:])]
        assert recent == expected

    def test_missing_files_auto_pruned(self, main_window, tmp_path):
        """존재하지 않는 파일은 _load_recent_files에서 자동 제거."""
        p = tmp_path / "doomed.json"
        p.write_text("{}", encoding="utf-8")
        main_window._add_to_recent_files(str(p))
        os.remove(p)
        recent = main_window._load_recent_files()
        assert os.path.abspath(str(p)) not in recent

    def test_empty_string_path_ignored(self, main_window):
        main_window._add_to_recent_files("")
        assert main_window._load_recent_files() == []


class TestRecentMenu:
    def test_empty_menu_has_disabled_placeholder(self, main_window):
        # 초기 상태: 빈 메뉴 → "(empty)" 항목 1개, disabled
        actions = main_window.recent_menu.actions()
        assert len(actions) == 1
        assert actions[0].isEnabled() is False

    def test_menu_populated_after_add(self, main_window, tmp_files):
        main_window._add_to_recent_files(tmp_files[0])
        main_window._add_to_recent_files(tmp_files[1])
        actions = main_window.recent_menu.actions()
        # 파일 2개 + separator + clear action
        assert len(actions) == 4
        # 첫 두 항목은 enabled
        assert actions[0].isEnabled() is True
        assert actions[1].isEnabled() is True

    def test_clear_recent_empties_menu(self, main_window, tmp_files):
        for p in tmp_files[:3]:
            main_window._add_to_recent_files(p)
        main_window._clear_recent_files()
        assert main_window._load_recent_files() == []
        # 메뉴도 (empty) 단일 항목
        actions = main_window.recent_menu.actions()
        assert len(actions) == 1
        assert actions[0].isEnabled() is False
