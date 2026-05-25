"""트리 노드 배치 계산 — 렌더링·상호작용과 분리된 순수 레이아웃 엔진.

세대별 그룹화 → 배우자 쌍 찾기 → 좌→우 배치 → 부모 중앙으로 자녀 정렬.
결과로 노드 ID → 좌표/사각형 매핑 두 dict을 반환. Qt 위젯 의존성 없이
PDF 내보내기·미리보기·통계 등 다른 표면에서도 재사용 가능.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from PyQt6.QtCore import QPointF, QRectF

from ..models.family_tree import FamilyTree
from ..models.person import Person


class TreeLayoutEngine:
    """가족 트리의 노드 배치를 계산.

    Args:
        family_tree: 위치를 계산할 트리.
        card_width / card_height: 카드 한 장 크기.
        spacing_x / spacing_y: 인접 카드 사이 간격.
        spouse_spacing: 배우자 쌍 사이 좁은 간격.
        start_x / start_y: 첫 카드 좌상단 좌표.
    """

    def __init__(
        self,
        family_tree: FamilyTree,
        card_width: float,
        card_height: float,
        spacing_x: float,
        spacing_y: float,
        spouse_spacing: float,
        start_x: float = 50,
        start_y: float = 50,
    ):
        self.family_tree = family_tree
        self.card_width = card_width
        self.card_height = card_height
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.spouse_spacing = spouse_spacing
        self.start_x = start_x
        self.start_y = start_y

    # === 공개 API ===

    def compute(self) -> Tuple[Dict[str, QPointF], Dict[str, QRectF]]:
        """모든 노드의 좌표/사각형 계산. (positions, rects) 두 dict 반환.

        트리가 비어 있으면 빈 dict 두 개 반환.
        """
        positions: Dict[str, QPointF] = {}
        rects: Dict[str, QRectF] = {}

        if not self.family_tree.get_all_persons():
            return positions, rects

        gen_groups = self.family_tree.get_persons_by_generation()
        if not gen_groups:
            return positions, rects

        y = self.start_y
        for gen in sorted(gen_groups.keys()):
            persons = gen_groups[gen]
            spouse_pairs = self._find_spouse_pairs(persons)
            processed: set = set()

            x = self.start_x
            for person in persons:
                if person.id in processed:
                    continue

                # 배우자가 있고 같은 세대면 나란히 배치
                if person.id in spouse_pairs:
                    spouse_id = spouse_pairs[person.id]
                    spouse = self.family_tree.get_person(spouse_id)
                    if spouse and spouse_id not in processed:
                        positions[person.id] = QPointF(x, y)
                        rects[person.id] = QRectF(
                            x, y, self.card_width, self.card_height
                        )
                        x += self.card_width + self.spouse_spacing

                        positions[spouse_id] = QPointF(x, y)
                        rects[spouse_id] = QRectF(
                            x, y, self.card_width, self.card_height
                        )
                        processed.add(person.id)
                        processed.add(spouse_id)
                        x += self.card_width + self.spacing_x
                        continue

                # 단독 배치
                positions[person.id] = QPointF(x, y)
                rects[person.id] = QRectF(x, y, self.card_width, self.card_height)
                processed.add(person.id)
                x += self.card_width + self.spacing_x

            y += self.card_height + self.spacing_y

        # 자녀 위치를 부모 중앙으로 보정
        self._center_children_under_parents(gen_groups, positions, rects)

        return positions, rects

    # === 내부 ===

    def _find_spouse_pairs(self, persons: List[Person]) -> Dict[str, str]:
        """세대 내에서 배우자 쌍을 찾음 — 현재 배우자(이혼 X) 우선.

        손상된 데이터(person.id == spouse_id 자기-자신 배우자)는 무시 —
        그렇지 않으면 pairs[id]=id로 자녀 정렬·렌더링에서 무한 참조.

        Returns:
            person_id → spouse_id 양방향 매핑. 자기참조 spouse는 제외.
        """
        pairs: Dict[str, str] = {}
        person_ids = {p.id for p in persons}

        for person in persons:
            if person.id in pairs:
                continue

            current_spouse_id = self.family_tree.get_current_spouse_id(person.id)
            if (
                current_spouse_id
                and current_spouse_id != person.id  # 자기-자신 배우자 차단
                and current_spouse_id in person_ids
            ):
                pairs[person.id] = current_spouse_id
                pairs[current_spouse_id] = person.id
                continue

            # 현재 배우자가 없으면 첫 번째 배우자 사용 (legacy 데이터 호환)
            for spouse_id in person.spouse_ids:
                if (
                    spouse_id != person.id  # 자기-자신 spouse_id 차단
                    and spouse_id in person_ids
                    and spouse_id not in pairs
                ):
                    pairs[person.id] = spouse_id
                    pairs[spouse_id] = person.id
                    break

        return pairs

    def _center_children_under_parents(
        self,
        gen_groups: Dict[int, List[Person]],
        positions: Dict[str, QPointF],
        rects: Dict[str, QRectF],
    ) -> None:
        """자녀 그룹을 부모 중앙으로 이동 (in-place)."""
        for gen in sorted(gen_groups.keys()):
            if gen == 0:
                continue

            # 같은 부모 집합을 가진 자녀들을 그룹화
            parent_to_children: Dict[frozenset, List[str]] = {}
            for person in gen_groups[gen]:
                parents = self.family_tree.get_parents(person.id)
                if not parents:
                    continue
                parent_key = frozenset(p.id for p in parents)
                parent_to_children.setdefault(parent_key, []).append(person.id)

            for parent_ids, child_ids in parent_to_children.items():
                parent_xs = [
                    positions[pid].x() + self.card_width / 2
                    for pid in parent_ids
                    if pid in positions
                ]
                if not parent_xs:
                    continue
                parent_center = sum(parent_xs) / len(parent_xs)

                child_positions = [
                    (cid, positions[cid]) for cid in child_ids if cid in positions
                ]
                if not child_positions:
                    continue

                child_xs = [pos.x() + self.card_width / 2 for _, pos in child_positions]
                children_center = sum(child_xs) / len(child_xs)
                dx = parent_center - children_center

                for cid, pos in child_positions:
                    new_pos = QPointF(pos.x() + dx, pos.y())
                    positions[cid] = new_pos
                    rects[cid] = QRectF(
                        new_pos.x(),
                        new_pos.y(),
                        self.card_width,
                        self.card_height,
                    )
