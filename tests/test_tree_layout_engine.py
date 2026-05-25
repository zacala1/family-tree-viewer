"""TreeLayoutEngine 회귀 가드 — 순수 레이아웃 로직 단위 테스트.

Qt 위젯 의존성 없이 동작하므로 빠르고 사이드이펙트 없음.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


CARD_W = 100
CARD_H = 60
SPACING_X = 40
SPACING_Y = 80
SPOUSE = 20


def _engine(tree):
    from src.views.tree_layout_engine import TreeLayoutEngine
    return TreeLayoutEngine(
        tree,
        card_width=CARD_W,
        card_height=CARD_H,
        spacing_x=SPACING_X,
        spacing_y=SPACING_Y,
        spouse_spacing=SPOUSE,
    )


class TestEmptyTree:
    def test_empty_returns_empty_dicts(self, empty_tree):
        positions, rects = _engine(empty_tree).compute()
        assert positions == {}
        assert rects == {}


class TestSampleFamily:
    def test_all_persons_have_position(self, sample_family):
        tree, ids = sample_family
        positions, rects = _engine(tree).compute()
        for key, pid in ids.items():
            assert pid in positions, f"{key}({pid})에 좌표 없음"
            assert pid in rects, f"{key}({pid})에 rect 없음"

    def test_rect_matches_position_and_dimensions(self, sample_family):
        tree, ids = sample_family
        positions, rects = _engine(tree).compute()
        for pid, pos in positions.items():
            r = rects[pid]
            assert r.x() == pos.x()
            assert r.y() == pos.y()
            assert r.width() == CARD_W
            assert r.height() == CARD_H

    def test_generations_have_distinct_y(self, sample_family):
        tree, ids = sample_family
        positions, _ = _engine(tree).compute()
        # gf/gm (gen 0), father/mother (gen 1), child1/child2 (gen 2)
        y_gen0 = positions[ids["gf"]].y()
        y_gen1 = positions[ids["father"]].y()
        y_gen2 = positions[ids["child1"]].y()
        assert y_gen0 < y_gen1 < y_gen2
        # 세대 간 간격: card_height + spacing_y
        assert y_gen1 - y_gen0 == CARD_H + SPACING_Y
        assert y_gen2 - y_gen1 == CARD_H + SPACING_Y

    def test_spouses_share_y(self, sample_family):
        tree, ids = sample_family
        positions, _ = _engine(tree).compute()
        # 부/모는 같은 세대 + 배우자 → 같은 y. (x 간격은 자녀-부모 정렬 단계에서
        # 한쪽 배우자만 부모를 가지면 정렬되며 SPOUSE_SPACING이 무너질 수 있음 —
        # 알려진 동작. y만 보장.)
        assert positions[ids["father"]].y() == positions[ids["mother"]].y()

    def test_gen0_spouses_remain_adjacent(self, sample_family):
        tree, ids = sample_family
        positions, _ = _engine(tree).compute()
        # gen 0은 부모가 없어 정렬 단계 영향 없음 → 인접 유지
        dx = abs(positions[ids["gf"]].x() - positions[ids["gm"]].x())
        assert dx == CARD_W + SPOUSE

    def test_children_centered_under_parents(self, sample_family):
        tree, ids = sample_family
        positions, _ = _engine(tree).compute()
        # child1·child2의 중앙 == father·mother의 중앙
        f_center = positions[ids["father"]].x() + CARD_W / 2
        m_center = positions[ids["mother"]].x() + CARD_W / 2
        parent_center = (f_center + m_center) / 2

        c1_center = positions[ids["child1"]].x() + CARD_W / 2
        c2_center = positions[ids["child2"]].x() + CARD_W / 2
        children_center = (c1_center + c2_center) / 2

        assert abs(parent_center - children_center) < 0.5


class TestCustomStartCoords:
    def test_start_x_y_offsets_layout(self, sample_family):
        from src.views.tree_layout_engine import TreeLayoutEngine
        tree, ids = sample_family
        engine = TreeLayoutEngine(
            tree,
            card_width=CARD_W,
            card_height=CARD_H,
            spacing_x=SPACING_X,
            spacing_y=SPACING_Y,
            spouse_spacing=SPOUSE,
            start_x=200,
            start_y=300,
        )
        positions, _ = engine.compute()
        # 첫 세대 첫 카드 (조부) y가 300이어야
        assert positions[ids["gf"]].y() == 300
        # 자녀 중앙 정렬이 후에 적용되므로 x는 정확한 200이 아닐 수 있음 — 최상위 세대로 검증
        gen0_xs = [positions[ids["gf"]].x(), positions[ids["gm"]].x()]
        assert min(gen0_xs) == 200


class TestSingleSpousePair:
    def test_no_spouse_only_pair(self, qapp):
        """배우자 없이 단독 인물이 여럿이면 SPACING_X 간격으로 좌→우 배치."""
        from src.models.family_tree import FamilyTree
        from src.models.person import Person
        tree = FamilyTree()
        a = Person(id="a", name="A")
        b = Person(id="b", name="B")
        tree.add_person(a)
        tree.add_person(b)
        positions, _ = _engine(tree).compute()
        # 같은 세대 + 배우자 아님 → SPACING_X 간격
        xs = sorted([positions["a"].x(), positions["b"].x()])
        assert xs[1] - xs[0] == CARD_W + SPACING_X
