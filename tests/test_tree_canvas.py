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

    def test_successful_navigation_accepts_event(self, canvas_with_family):
        """화살표 키로 성공적으로 이동했을 때 event.accept()가 호출돼 부모로 전파 방지."""
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["child1"]
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        canvas.keyPressEvent(event)
        assert event.isAccepted() is True

    def test_no_target_still_accepts_event(self, canvas_with_family):
        """이동할 곳이 없어도 accept() — 화살표 키는 캔버스에서 소비."""
        canvas, ids = canvas_with_family
        canvas.selected_person_id = ids["gf"]  # 부모 없음
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        canvas.keyPressEvent(event)
        assert event.isAccepted() is True


class TestEmptyTreeKeyPress:
    def test_empty_canvas_keypress_no_crash(self, qapp, empty_tree):
        canvas = TreeCanvas(empty_tree)
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        canvas.keyPressEvent(event)
        assert canvas.selected_person_id is None


class TestVisibleSceneRect:
    """Viewport culling의 _visible_scene_rect 계산 회귀 가드."""

    def test_default_viewport_at_origin(self, qapp, empty_tree):
        canvas = TreeCanvas(empty_tree)
        canvas.resize(800, 600)
        canvas.offset = QRectF(0, 0, 0, 0).topLeft()  # QPointF(0,0)
        canvas.scale = 1.0
        visible = canvas._visible_scene_rect()
        # offset 0, scale 1 → viewport 그대로, margin 50px 양쪽
        assert visible.x() == pytest.approx(-50)
        assert visible.y() == pytest.approx(-50)
        assert visible.width() == pytest.approx(900)
        assert visible.height() == pytest.approx(700)

    def test_zero_or_negative_scale_returns_huge_rect(self, qapp, empty_tree):
        """비정상 scale 방어 — 모든 노드를 그려서 화면 빔 방지."""
        canvas = TreeCanvas(empty_tree)
        canvas.scale = 0
        visible = canvas._visible_scene_rect()
        # 매우 큰 직사각형이어야
        assert visible.width() > 1e8
        assert visible.height() > 1e8


class TestCardPhotoCache:
    """카드 사진 캐시 회귀 가드."""

    def test_cache_starts_empty(self, qapp, empty_tree):
        canvas = TreeCanvas(empty_tree)
        assert canvas._card_photo_cache == {}

    def test_memoizes_load(self, qapp, empty_tree, monkeypatch):
        """동일 (photo_path, size) 호출은 load_thumbnail을 한 번만 부른다."""
        canvas = TreeCanvas(empty_tree)
        calls = []

        def fake_load(path, size):
            calls.append((path, size))
            from PyQt6.QtGui import QPixmap
            return QPixmap(10, 10)

        monkeypatch.setattr("src.utils.photo_manager.load_thumbnail", fake_load)

        canvas._get_card_photo("photos/p1.jpg", 44)
        canvas._get_card_photo("photos/p1.jpg", 44)
        canvas._get_card_photo("photos/p1.jpg", 44)
        assert len(calls) == 1  # 캐시 히트

    def test_different_sizes_cached_separately(self, qapp, empty_tree, monkeypatch):
        canvas = TreeCanvas(empty_tree)
        calls = []

        def fake_load(path, size):
            calls.append((path, size))
            from PyQt6.QtGui import QPixmap
            return QPixmap(size, size)

        monkeypatch.setattr("src.utils.photo_manager.load_thumbnail", fake_load)

        canvas._get_card_photo("photos/p1.jpg", 44)
        canvas._get_card_photo("photos/p1.jpg", 88)
        assert len(calls) == 2

    def test_failure_cached_as_none_no_repeat(self, qapp, empty_tree, monkeypatch):
        """로드 실패도 None으로 캐시 — 반복 호출에 비용 들지 않음."""
        canvas = TreeCanvas(empty_tree)
        calls = []

        def fake_load(path, size):
            calls.append(1)
            return None

        monkeypatch.setattr("src.utils.photo_manager.load_thumbnail", fake_load)

        assert canvas._get_card_photo("missing.jpg", 44) is None
        assert canvas._get_card_photo("missing.jpg", 44) is None
        assert len(calls) == 1

    def test_invalidate_all_clears_cache(self, qapp, empty_tree, monkeypatch):
        canvas = TreeCanvas(empty_tree)
        from PyQt6.QtGui import QPixmap
        monkeypatch.setattr(
            "src.utils.photo_manager.load_thumbnail",
            lambda p, s: QPixmap(s, s),
        )
        canvas._get_card_photo("a.jpg", 44)
        canvas._get_card_photo("b.jpg", 44)
        assert len(canvas._card_photo_cache) == 2
        canvas.invalidate_photo_cache()
        assert canvas._card_photo_cache == {}

    def test_invalidate_specific_path(self, qapp, empty_tree, monkeypatch):
        canvas = TreeCanvas(empty_tree)
        from PyQt6.QtGui import QPixmap
        monkeypatch.setattr(
            "src.utils.photo_manager.load_thumbnail",
            lambda p, s: QPixmap(s, s),
        )
        canvas._get_card_photo("a.jpg", 44)
        canvas._get_card_photo("a.jpg", 88)
        canvas._get_card_photo("b.jpg", 44)
        canvas.invalidate_photo_cache("a.jpg")
        # a.jpg는 모두 제거, b.jpg는 유지
        keys = list(canvas._card_photo_cache.keys())
        assert all(k[0] == "b.jpg" for k in keys)
        assert ("b.jpg", 44) in canvas._card_photo_cache


class TestViewportCulling:
    """_draw_nodes가 viewport 밖 노드를 스킵하는지 (성능 회귀 가드)."""

    def test_far_away_node_not_drawn(self, qapp, sample_family, monkeypatch):
        tree, ids = sample_family
        canvas = TreeCanvas(tree)
        canvas.resize(800, 600)
        from PyQt6.QtCore import QPointF
        canvas.offset = QPointF(0, 0)
        canvas.scale = 1.0
        # 자녀1을 화면 안, 자녀2를 매우 멀리 배치
        canvas._node_rects = {
            ids["gf"]: QRectF(-10000, -10000, 100, 100),  # 화면 밖
            ids["gm"]: QRectF(-10000, -10000, 100, 100),  # 화면 밖
            ids["father"]: QRectF(-10000, -10000, 100, 100),
            ids["mother"]: QRectF(-10000, -10000, 100, 100),
            ids["child1"]: QRectF(100, 100, 100, 100),  # 화면 안
            ids["child2"]: QRectF(10000, 10000, 100, 100),  # 화면 밖
        }

        drawn = []
        monkeypatch.setattr(
            canvas, "_draw_person_card",
            lambda painter, person, rect, sel, hl: drawn.append(person.id),
        )
        canvas._draw_nodes(painter=None)

        # child1만 그려지고 나머지는 스킵
        assert ids["child1"] in drawn
        assert ids["child2"] not in drawn
        assert ids["gf"] not in drawn

    def test_all_visible_draws_all(self, qapp, sample_family, monkeypatch):
        """전 노드가 viewport 안이면 모두 그려짐."""
        tree, ids = sample_family
        canvas = TreeCanvas(tree)
        canvas.resize(800, 600)
        from PyQt6.QtCore import QPointF
        canvas.offset = QPointF(0, 0)
        canvas.scale = 1.0
        canvas._node_rects = {
            pid: QRectF(50 + i * 110, 50 + (i % 3) * 120, 100, 100)
            for i, pid in enumerate(ids.values())
        }

        drawn = []
        monkeypatch.setattr(
            canvas, "_draw_person_card",
            lambda painter, person, rect, sel, hl: drawn.append(person.id),
        )
        canvas._draw_nodes(painter=None)

        assert set(drawn) == set(ids.values())
