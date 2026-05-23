"""TreeCanvas 유닛 테스트.

핵심 회귀 가드:
- 화살표 키 인접 인물 탐색 (Up/Down: 부모/자녀, Left/Right: 같은 세대 형제)
- 빈 트리에서 keyPressEvent 크래시 금지
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QKeyEvent

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.views.tree_canvas import TreeCanvas


@pytest.fixture
def canvas_with_family(qapp, sample_family):
    """sample_family를 TreeCanvas에 로드 (layout은 _node_rects를 직접 주입해 결정론적)."""
    tree, ids = sample_family
    canvas = TreeCanvas(tree)
    # 자동 layout이 환경에 따라 흔들리지 않도록 수동 배치:
    # gen 0 (조부모) y=0, gen 1 (부모) y=200, gen 2 (자녀) y=400
    canvas._node_rects = {
        ids["gf"]: QRectF(0, 0, 100, 100),
        ids["gm"]: QRectF(120, 0, 100, 100),
        ids["father"]: QRectF(50, 200, 100, 100),
        ids["mother"]: QRectF(170, 200, 100, 100),
        ids["child1"]: QRectF(0, 400, 100, 100),
        ids["child2"]: QRectF(120, 400, 100, 100),
    }
    return canvas, ids


class TestSiblingInDirection:
    def test_right_finds_next_in_generation(self, canvas_with_family):
        canvas, ids = canvas_with_family
        # 자녀1의 오른쪽 → 자녀2
        result = canvas._sibling_in_direction(ids["child1"], +1)
        assert result == ids["child2"]

    def test_left_finds_previous_in_generation(self, canvas_with_family):
        canvas, ids = canvas_with_family
        # 자녀2의 왼쪽 → 자녀1
        result = canvas._sibling_in_direction(ids["child2"], -1)
        assert result == ids["child1"]

    def test_no_sibling_returns_none(self, canvas_with_family):
        canvas, ids = canvas_with_family
        # 자녀1의 왼쪽엔 아무도 없음
        assert canvas._sibling_in_direction(ids["child1"], -1) is None
        # 자녀2의 오른쪽엔 아무도 없음
        assert canvas._sibling_in_direction(ids["child2"], +1) is None

    def test_ignores_different_generation(self, canvas_with_family):
        canvas, ids = canvas_with_family
        # 부모(y=200)의 오른쪽 — 같은 세대의 어머니만 후보, 자녀(y=400)는 제외
        result = canvas._sibling_in_direction(ids["father"], +1)
        assert result == ids["mother"]

    def test_unknown_person_returns_none(self, canvas_with_family):
        canvas, _ = canvas_with_family
        assert canvas._sibling_in_direction("nonexistent", +1) is None


class TestKeyPressNavigation:
    def _send_key(self, canvas, key):
        event = QKeyEvent(QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
        canvas.keyPressEvent(event)

    def test_up_moves_to_parent(self, canvas_with_family):
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["child1"]
        self._send_key(canvas, Qt.Key.Key_Up)
        # 자녀1의 첫 부모 = 아버지 또는 어머니 (get_parents 순서: 부, 모)
        assert canvas.selected_person_id in (ids["father"], ids["mother"])

    def test_down_moves_to_child(self, canvas_with_family):
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["father"]
        self._send_key(canvas, Qt.Key.Key_Down)
        assert canvas.selected_person_id in (ids["child1"], ids["child2"])

    def test_right_moves_to_sibling(self, canvas_with_family):
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["child1"]
        self._send_key(canvas, Qt.Key.Key_Right)
        assert canvas.selected_person_id == ids["child2"]

    def test_left_moves_to_sibling(self, canvas_with_family):
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["child2"]
        self._send_key(canvas, Qt.Key.Key_Left)
        assert canvas.selected_person_id == ids["child1"]

    def test_no_selection_does_not_crash(self, canvas_with_family):
        canvas, _ = canvas_with_family
        canvas.selected_person_id = None
        # 예외 없이 통과해야 함
        self._send_key(canvas, Qt.Key.Key_Up)
        assert canvas.selected_person_id is None

    def test_up_with_no_parent_keeps_selection(self, canvas_with_family):
        canvas, ids = canvas_with_family
        # 조부는 부모가 없음
        canvas.selected_person_id = ids["gf"]
        self._send_key(canvas, Qt.Key.Key_Up)
        assert canvas.selected_person_id == ids["gf"]

    def test_other_key_falls_through(self, canvas_with_family):
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["child1"]
        self._send_key(canvas, Qt.Key.Key_A)
        # 'A'는 처리 안 됨 → 선택 그대로
        assert canvas.selected_person_id == ids["child1"]


class TestEmptyTreeKeyPress:
    def test_empty_canvas_keypress_no_crash(self, qapp, empty_tree):
        canvas = TreeCanvas(empty_tree)
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        canvas.keyPressEvent(event)
        assert canvas.selected_person_id is None
