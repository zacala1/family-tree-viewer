"""DetailPanel 미저장 변경 가드 회귀 — 편집 중 person 전환 시 사용자 확인."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QMessageBox

from src.models.person import Person
from src.models.family_tree import FamilyTree


@pytest.fixture
def panel(qapp):
    from src.views.detail_panel import DetailPanel
    p = DetailPanel()
    yield p
    p.deleteLater()


@pytest.fixture
def two_persons():
    tree = FamilyTree()
    a = Person(id="a", name="Alpha")
    b = Person(id="b", name="Bravo")
    tree.add_person(a)
    tree.add_person(b)
    return tree, a, b


class TestNoGuardWhenNotEditing:
    def test_set_person_when_not_editing_is_silent(self, panel, two_persons, monkeypatch):
        tree, a, b = two_persons
        # 다이얼로그가 떴는지 추적
        called = []
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: called.append(True) or QMessageBox.StandardButton.Cancel,
        )
        panel.set_person(a, tree)
        panel.set_person(b, tree)  # edit 모드 아님 → 다이얼로그 안 떠야
        assert called == []
        assert panel.current_person is b


class TestGuardWhenEditing:
    def test_cancel_keeps_current_person(self, panel, two_persons, monkeypatch):
        tree, a, b = two_persons
        panel.set_person(a, tree)
        panel.start_edit()
        # 입력 수정 시뮬레이션
        panel.name_input.setText("수정된 이름")
        assert panel._is_editing

        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Cancel,
        )
        panel.set_person(b, tree)
        # Cancel → 현재 person 유지 + 편집 모드 유지
        assert panel.current_person is a
        assert panel._is_editing is True

    def test_discard_proceeds_and_exits_edit(self, panel, two_persons, monkeypatch):
        tree, a, b = two_persons
        panel.set_person(a, tree)
        panel.start_edit()
        panel.name_input.setText("버려질 이름")
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Discard,
        )
        panel.set_person(b, tree)
        assert panel.current_person is b
        assert panel._is_editing is False
        # 새 person 데이터로 input이 갱신됐어야
        assert panel.name_input.text() == "Bravo"

    def test_save_validation_failure_blocks_switch(self, panel, two_persons, monkeypatch):
        tree, a, b = two_persons
        panel.set_person(a, tree)
        panel.start_edit()
        # 이름을 비우면 validation 실패
        panel.name_input.setText("")
        monkeypatch.setattr(
            QMessageBox, "question",
            lambda *a, **kw: QMessageBox.StandardButton.Save,
        )
        # _save가 띄우는 validation warning도 무시
        monkeypatch.setattr(QMessageBox, "warning", lambda *a, **kw: None)
        panel.set_person(b, tree)
        # validation 실패 → 편집 모드 유지 + person 그대로
        assert panel.current_person is a
        assert panel._is_editing is True
