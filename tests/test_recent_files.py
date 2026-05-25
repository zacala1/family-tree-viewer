"""RecentFilesManager 위젯 + MainWindow 통합 회귀 가드.

이전 버전은 main_window 내부 _load_recent_files/_add_to_recent_files 등
private 메서드를 직접 호출했지만, 분리 후 RecentFilesManager가 모듈 단위로
독립 단위 테스트를 가짐. MainWindow는 wrapper(_add_to_recent_files,
_refresh_recent_menu)만 노출하여 file 저장/로드 호출처를 단순화.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import QSettings, QCoreApplication
from PyQt6.QtWidgets import QMenu


@pytest.fixture
def isolated_settings(qapp):
    """QSettings 격리 — application name 분리 + welcomeDismissed 미리 set."""
    original_app = QCoreApplication.applicationName()
    original_org = QCoreApplication.organizationName()
    QCoreApplication.setOrganizationName("FamilyTreeTest")
    QCoreApplication.setApplicationName(f"FamilyTreeTest_{id(qapp)}")
    s = QSettings("FamilyTree", "FamilyTree")
    s.clear()
    s.setValue("welcomeDismissed", True)
    yield s
    s.clear()
    QCoreApplication.setApplicationName(original_app)
    QCoreApplication.setOrganizationName(original_org)


@pytest.fixture
def manager(qapp, isolated_settings):
    from src.views.widgets.recent_files_manager import RecentFilesManager
    m = RecentFilesManager()
    yield m
    m.deleteLater()


@pytest.fixture
def tmp_files(tmp_path):
    paths = []
    for i in range(5):
        p = tmp_path / f"tree{i}.json"
        p.write_text("{}", encoding="utf-8")
        paths.append(str(p))
    return paths


class TestRecentFilesPersistence:
    def test_add_single_file(self, manager, tmp_files):
        manager.add(tmp_files[0])
        recent = manager.load()
        assert recent == [os.path.abspath(tmp_files[0])]

    def test_most_recent_first(self, manager, tmp_files):
        for p in tmp_files[:3]:
            manager.add(p)
        recent = manager.load()
        assert recent[0] == os.path.abspath(tmp_files[2])
        assert recent[-1] == os.path.abspath(tmp_files[0])

    def test_duplicate_moves_to_front(self, manager, tmp_files):
        manager.add(tmp_files[0])
        manager.add(tmp_files[1])
        manager.add(tmp_files[0])
        recent = manager.load()
        assert recent[0] == os.path.abspath(tmp_files[0])
        assert recent.count(os.path.abspath(tmp_files[0])) == 1

    def test_max_limit_enforced(self, manager, tmp_path):
        paths = []
        for i in range(7):
            p = tmp_path / f"file{i}.json"
            p.write_text("{}", encoding="utf-8")
            paths.append(str(p))
            manager.add(str(p))
        recent = manager.load()
        assert len(recent) == manager.DEFAULT_MAX
        expected = [os.path.abspath(p) for p in reversed(paths[-manager.DEFAULT_MAX:])]
        assert recent == expected

    def test_missing_files_auto_pruned(self, manager, tmp_path):
        p = tmp_path / "doomed.json"
        p.write_text("{}", encoding="utf-8")
        manager.add(str(p))
        os.remove(p)
        recent = manager.load()
        assert os.path.abspath(str(p)) not in recent

    def test_empty_string_path_ignored(self, manager):
        manager.add("")
        assert manager.load() == []


class TestRecentMenu:
    def test_empty_menu_shows_placeholder(self, manager):
        menu = QMenu()
        manager.bind_menu(menu)
        actions = menu.actions()
        assert len(actions) == 1
        assert actions[0].isEnabled() is False  # disabled "(empty)"

    def test_menu_populated_after_add(self, manager, tmp_files):
        menu = QMenu()
        manager.bind_menu(menu)
        manager.add(tmp_files[0])
        manager.add(tmp_files[1])
        actions = menu.actions()
        # 파일 2개 + separator + clear
        assert len(actions) == 4
        assert actions[0].isEnabled() is True
        assert actions[1].isEnabled() is True

    def test_clear_recent_empties_menu(self, manager, tmp_files):
        menu = QMenu()
        manager.bind_menu(menu)
        for p in tmp_files[:3]:
            manager.add(p)
        manager.clear()
        assert manager.load() == []
        actions = menu.actions()
        assert len(actions) == 1
        assert actions[0].isEnabled() is False


class TestSignal:
    def test_file_selected_signal_emitted(self, manager, tmp_files):
        emitted = []
        manager.file_selected.connect(lambda p: emitted.append(p))
        manager.add(tmp_files[0])
        # Manager의 menu가 없으면 _on_pick 호출 안 됨 — 직접 호출로 검증
        manager._on_pick(tmp_files[0])
        assert emitted == [tmp_files[0]]

    def test_missing_file_does_not_emit(self, manager, tmp_path, monkeypatch):
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: None)
        emitted = []
        manager.file_selected.connect(lambda p: emitted.append(p))
        manager._on_pick(str(tmp_path / "ghost.json"))
        assert emitted == []  # 없는 파일은 emit 안 함


class TestMainWindowIntegration:
    """MainWindow가 RecentFilesManager를 보유하고 wrapper가 작동하는지."""

    def test_main_window_has_manager(self, qapp):
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            from src.views.widgets.recent_files_manager import RecentFilesManager
            assert isinstance(win._recent_files, RecentFilesManager)
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()

    def test_add_wrapper_delegates(self, qapp, tmp_path):
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            p = tmp_path / "x.json"
            p.write_text("{}", encoding="utf-8")
            win._add_to_recent_files(str(p))
            assert os.path.abspath(str(p)) in win._recent_files.load()
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()
