"""가족 트리 캔버스 - 그래프 시각화."""

from typing import Dict, List, Optional, Set
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint, pyqtSignal, QEasingCurve, QVariantAnimation
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPainterPath,
    QMouseEvent,
    QWheelEvent,
    QLinearGradient,
    QRadialGradient,
)

from ..models.family_tree import FamilyTree
from ..models.person import Person
from ..i18n import tr
from ..utils.theme_manager import get_theme_manager
from ..config import (
    CARD_WIDTH,
    CARD_HEIGHT,
    CARD_SPACING_X,
    CARD_SPACING_Y,
    SPOUSE_SPACING,
    ANIMATION_DURATION,
)


class TreeCanvas(QWidget):
    """가족 트리를 그래픽으로 표시하는 캔버스."""

    # 시그널
    person_selected = pyqtSignal(str)  # person_id
    person_double_clicked = pyqtSignal(str)  # person_id
    context_menu_requested = pyqtSignal(str, QPoint)  # person_id, global_pos

    # 상수
    CARD_WIDTH = CARD_WIDTH
    CARD_HEIGHT = CARD_HEIGHT
    CARD_SPACING_X = CARD_SPACING_X
    CARD_SPACING_Y = CARD_SPACING_Y
    SPOUSE_SPACING = SPOUSE_SPACING

    def __init__(self, family_tree: FamilyTree, parent=None):
        super().__init__(parent)

        self.family_tree = family_tree
        self.selected_person_id: Optional[str] = None
        self.highlighted_ids: Set[str] = set()

        # 뷰 변환
        self.scale = 1.0
        self._target_scale = 1.0
        self.offset = QPointF(0, 0)
        self._target_offset = QPointF(0, 0)
        self.dragging = False
        self.last_mouse_pos = QPointF()

        # 애니메이션
        self._scale_animation: Optional[QVariantAnimation] = None
        self._offset_animation: Optional[QVariantAnimation] = None

        # 노드 위치 캐시
        self._node_positions: Dict[str, QPointF] = {}
        self._node_rects: Dict[str, QRectF] = {}

        # 연결선 캐시 (레이아웃 변경 시에만 무효화)
        self._connections_dirty = True

        # 카드 사진 캐시 — (photo_path, size) → QPixmap (or None when load failed)
        # LRU: OrderedDict로 접근 순서를 추적하고 max 크기 초과 시 가장 오래된 항목 제거.
        # 대형 가족트리에서 모든 사진이 캐싱돼 메모리가 누적되지 않도록 한계.
        from collections import OrderedDict
        self._card_photo_cache: "OrderedDict" = OrderedDict()
        self._card_photo_cache_max: int = 256

        # 설정
        self.setMinimumSize(480, 350)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 테마 관리자 연결
        self._theme_manager = get_theme_manager()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

        # 색상 테마 초기화
        self._update_colors()

        # 초기 레이아웃 계산
        self._calculate_layout()

        # closeEvent에서 애니메이션 정리 (destroyed는 C++ 소멸 시점이라 안전하지 않음)

    def _cleanup_all_animations(self):
        """위젯 파괴 시 모든 애니메이션 정리."""
        if self._scale_animation is not None:
            self._scale_animation.stop()
            try:
                self._scale_animation.valueChanged.disconnect()
            except TypeError:
                pass
            self._scale_animation.setParent(None)
            self._scale_animation.deleteLater()
            self._scale_animation = None

        if self._offset_animation is not None:
            self._offset_animation.stop()
            try:
                self._offset_animation.valueChanged.disconnect()
            except TypeError:
                pass
            self._offset_animation.setParent(None)
            self._offset_animation.deleteLater()
            self._offset_animation = None

    def cleanup(self):
        """외부에서 호출하여 애니메이션 안전하게 정리 (MainWindow.closeEvent에서 호출)."""
        self._cleanup_all_animations()

    def _update_colors(self):
        """테마에 맞는 색상 업데이트."""
        theme_colors = self._theme_manager.get_tree_colors()
        self.colors = {key: QColor(value) for key, value in theme_colors.items()}

    def _on_theme_changed(self, theme: str):
        """테마 변경 시 호출."""
        self._update_colors()
        self.update()

    def set_family_tree(self, family_tree: FamilyTree):
        """가족 트리 설정."""
        self.family_tree = family_tree
        self.selected_person_id = None
        self.highlighted_ids.clear()
        self._calculate_layout()
        self.update()

    def refresh(self):
        """화면 갱신 (트리 구조 변경 시)."""
        self._calculate_layout()
        self._connections_dirty = True
        self.update()

    def select_person(self, person_id: str):
        """사람 선택."""
        self.selected_person_id = person_id

        # 직계 가족 하이라이트
        self.highlighted_ids = self.family_tree.get_direct_family_ids(person_id)
        self.highlighted_ids.add(person_id)

        self.person_selected.emit(person_id)
        self.update()

        # 선택된 노드로 스크롤
        self._scroll_to_person(person_id)

    def _scroll_to_person(self, person_id: str):
        """선택된 사람이 보이도록 부드럽게 스크롤 (애니메이션)."""
        if person_id not in self._node_positions:
            return

        pos = self._node_positions[person_id]
        center = QPointF(self.width() / 2, self.height() / 2)
        target_offset = center - pos * self.scale

        self._animate_offset(target_offset)

    def _animate_offset(self, target: QPointF, duration: int = ANIMATION_DURATION):
        """오프셋 애니메이션 (메모리 누수 방지)."""
        if self._offset_animation is not None:
            self._offset_animation.stop()
            try:
                self._offset_animation.valueChanged.disconnect()
            except TypeError:
                pass  # 연결된 시그널이 없음
            # 즉시 삭제로 메모리 누수 방지
            self._offset_animation.setParent(None)
            self._offset_animation.deleteLater()
            self._offset_animation = None

        self._offset_animation = QVariantAnimation(self)
        self._offset_animation.setDuration(duration)
        self._offset_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._offset_animation.setStartValue(self.offset)
        self._offset_animation.setEndValue(target)
        self._offset_animation.valueChanged.connect(self._on_offset_changed)
        self._offset_animation.finished.connect(lambda: self._cleanup_animation("offset"))
        self._offset_animation.start()

    def _on_offset_changed(self, value):
        """오프셋 애니메이션 값 변경."""
        self.offset = value
        self.update()

    def _animate_scale(self, target: float, center: QPointF, duration: int = ANIMATION_DURATION):
        """줌 애니메이션 (중심점 유지, 메모리 누수 방지)."""
        if self._scale_animation is not None:
            self._scale_animation.stop()
            try:
                self._scale_animation.valueChanged.disconnect()
            except TypeError:
                pass  # 연결된 시그널이 없음
            # 즉시 삭제로 메모리 누수 방지
            self._scale_animation.setParent(None)
            self._scale_animation.deleteLater()
            self._scale_animation = None

        start_scale = self.scale
        start_offset = self.offset

        self._scale_animation = QVariantAnimation(self)
        self._scale_animation.setDuration(duration)
        self._scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scale_animation.setStartValue(0.0)
        self._scale_animation.setEndValue(1.0)

        # 시작/종료 씬 좌표 저장
        scene_pos = (center - start_offset) / start_scale

        def update_scale(progress):
            # 선형 보간으로 스케일 계산
            self.scale = start_scale + (target - start_scale) * progress
            # 중심점 유지를 위한 오프셋 조정
            self.offset = center - scene_pos * self.scale
            self.update()

        self._scale_animation.valueChanged.connect(update_scale)
        self._scale_animation.finished.connect(lambda: self._cleanup_animation("scale"))
        self._scale_animation.start()

    def _cleanup_animation(self, animation_type: str):
        """애니메이션 정리."""
        if animation_type == "offset" and self._offset_animation is not None:
            self._offset_animation.deleteLater()
            self._offset_animation = None
        elif animation_type == "scale" and self._scale_animation is not None:
            self._scale_animation.deleteLater()
            self._scale_animation = None

    def _calculate_layout(self):
        """노드 위치 계산 (세대별 배치)."""
        self._node_positions.clear()
        self._node_rects.clear()

        if not self.family_tree.get_all_persons():
            return

        # 세대별 그룹화
        gen_groups = self.family_tree.get_persons_by_generation()

        if not gen_groups:
            return

        # 각 세대의 시작 Y 위치
        y = 50

        for gen in sorted(gen_groups.keys()):
            persons = gen_groups[gen]

            # 배우자 쌍 찾기
            spouse_pairs = self._find_spouse_pairs(persons)
            processed = set()

            x = 50

            for person in persons:
                if person.id in processed:
                    continue

                # 배우자가 있으면 함께 배치
                if person.id in spouse_pairs:
                    spouse_id = spouse_pairs[person.id]
                    spouse = self.family_tree.get_person(spouse_id)

                    if spouse and spouse_id not in processed:
                        # 두 사람을 나란히 배치
                        self._node_positions[person.id] = QPointF(x, y)
                        self._node_rects[person.id] = QRectF(
                            x, y, self.CARD_WIDTH, self.CARD_HEIGHT
                        )

                        x += self.CARD_WIDTH + self.SPOUSE_SPACING

                        self._node_positions[spouse_id] = QPointF(x, y)
                        self._node_rects[spouse_id] = QRectF(
                            x, y, self.CARD_WIDTH, self.CARD_HEIGHT
                        )

                        processed.add(person.id)
                        processed.add(spouse_id)

                        x += self.CARD_WIDTH + self.CARD_SPACING_X
                        continue

                # 단독 배치
                self._node_positions[person.id] = QPointF(x, y)
                self._node_rects[person.id] = QRectF(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)
                processed.add(person.id)

                x += self.CARD_WIDTH + self.CARD_SPACING_X

            y += self.CARD_HEIGHT + self.CARD_SPACING_Y

        # 자녀 위치 조정 (부모 중앙에 오도록)
        self._adjust_children_positions()

    def _find_spouse_pairs(self, persons: List[Person]) -> Dict[str, str]:
        """배우자 쌍 찾기 (현재 배우자 우선)."""
        pairs = {}
        person_ids = {p.id for p in persons}

        for person in persons:
            if person.id in pairs:
                continue

            # 현재 배우자(이혼하지 않은) 우선 선택
            current_spouse_id = self.family_tree.get_current_spouse_id(person.id)

            if current_spouse_id and current_spouse_id in person_ids:
                pairs[person.id] = current_spouse_id
                pairs[current_spouse_id] = person.id
            else:
                # 현재 배우자가 없으면 첫 번째 배우자 사용
                for spouse_id in person.spouse_ids:
                    if spouse_id in person_ids and spouse_id not in pairs:
                        pairs[person.id] = spouse_id
                        pairs[spouse_id] = person.id
                        break

        return pairs

    def _adjust_children_positions(self):
        """자녀들이 부모 중앙에 오도록 위치 조정."""
        gen_groups = self.family_tree.get_persons_by_generation()

        for gen in sorted(gen_groups.keys()):
            if gen == 0:
                continue

            # 같은 부모를 가진 자녀들을 그룹화
            parent_to_children: Dict[frozenset, List[str]] = {}
            for person in gen_groups[gen]:
                parents = self.family_tree.get_parents(person.id)
                if not parents:
                    continue
                parent_key = frozenset(p.id for p in parents)
                if parent_key not in parent_to_children:
                    parent_to_children[parent_key] = []
                parent_to_children[parent_key].append(person.id)

            # 각 자녀 그룹을 부모 중앙에 정렬
            for parent_ids, child_ids in parent_to_children.items():
                parent_xs = [
                    self._node_positions[pid].x() + self.CARD_WIDTH / 2
                    for pid in parent_ids
                    if pid in self._node_positions
                ]
                if not parent_xs:
                    continue

                parent_center = sum(parent_xs) / len(parent_xs)

                child_positions = [
                    (cid, self._node_positions[cid])
                    for cid in child_ids
                    if cid in self._node_positions
                ]
                if not child_positions:
                    continue

                # 자녀 그룹의 현재 중앙 계산
                child_xs = [pos.x() + self.CARD_WIDTH / 2 for _, pos in child_positions]
                children_center = sum(child_xs) / len(child_xs)

                # 부모 중앙으로 이동할 오프셋
                dx = parent_center - children_center
                for cid, pos in child_positions:
                    new_pos = QPointF(pos.x() + dx, pos.y())
                    self._node_positions[cid] = new_pos
                    self._node_rects[cid] = QRectF(
                        new_pos.x(), new_pos.y(), self.CARD_WIDTH, self.CARD_HEIGHT
                    )

    def paintEvent(self, event):
        """그리기 이벤트."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        painter.fillRect(self.rect(), self.colors["background"])

        # 빈 트리 안내 — 새 사용자에게 다음 행동을 명확히 안내
        if not self.family_tree or not self.family_tree.get_all_persons():
            painter.setPen(self.colors["text_secondary"])
            hint_font = QFont("Malgun Gothic", 14)
            painter.setFont(hint_font)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                tr("message.empty_tree_hint"),
            )
            return

        # 변환 적용
        painter.translate(self.offset)
        painter.scale(self.scale, self.scale)

        # 연결선 그리기
        self._draw_connections(painter)

        # 노드 그리기
        self._draw_nodes(painter)

    def _draw_connections(self, painter: QPainter):
        """연결선 그리기."""
        for person in self.family_tree.get_all_persons():
            if person.id not in self._node_positions:
                continue

            pos = self._node_positions[person.id]
            center = QPointF(pos.x() + self.CARD_WIDTH / 2, pos.y() + self.CARD_HEIGHT / 2)
            bottom = QPointF(pos.x() + self.CARD_WIDTH / 2, pos.y() + self.CARD_HEIGHT)

            # 배우자 연결선 (수평)
            for spouse_id in person.spouse_ids:
                if spouse_id in self._node_positions:
                    spouse_pos = self._node_positions[spouse_id]

                    # 이미 그린 선은 건너뛰기
                    if spouse_pos.x() < pos.x():
                        continue

                    spouse_center = QPointF(
                        spouse_pos.x() + self.CARD_WIDTH / 2, spouse_pos.y() + self.CARD_HEIGHT / 2
                    )

                    # 이혼 여부 확인
                    rel = self.family_tree.get_spouse_relationship(person.id, spouse_id)
                    is_divorced = rel.is_divorced if rel else False

                    # 하이라이트 여부
                    is_highlighted = (
                        person.id in self.highlighted_ids and spouse_id in self.highlighted_ids
                    )

                    # 이혼한 경우 다른 색상, 점선 사용
                    if is_divorced:
                        pen = QPen(self.colors["spouse_line_divorced"])
                        pen.setStyle(Qt.PenStyle.DashLine)
                        pen.setWidth(1)
                    elif is_highlighted:
                        pen = QPen(self.colors["line_highlighted"])
                        pen.setWidth(3)
                    else:
                        pen = QPen(self.colors["spouse_line"])
                        pen.setWidth(2)

                    painter.setPen(pen)

                    # 이중선으로 배우자 관계 표시
                    offset = 2
                    painter.drawLine(
                        QPointF(pos.x() + self.CARD_WIDTH, center.y() - offset),
                        QPointF(spouse_pos.x(), spouse_center.y() - offset),
                    )
                    painter.drawLine(
                        QPointF(pos.x() + self.CARD_WIDTH, center.y() + offset),
                        QPointF(spouse_pos.x(), spouse_center.y() + offset),
                    )

            # 자녀 연결선 (수직)
            for child_id in person.children_ids:
                if child_id in self._node_positions:
                    child_pos = self._node_positions[child_id]
                    child_top = QPointF(child_pos.x() + self.CARD_WIDTH / 2, child_pos.y())

                    # 하이라이트 여부
                    is_highlighted = (
                        person.id in self.highlighted_ids and child_id in self.highlighted_ids
                    )

                    pen = QPen(
                        self.colors["line_highlighted"] if is_highlighted else self.colors["line"]
                    )
                    pen.setWidth(3 if is_highlighted else 2)
                    painter.setPen(pen)

                    # 꺾인 선으로 연결
                    mid_y = (bottom.y() + child_top.y()) / 2

                    path = QPainterPath()
                    path.moveTo(bottom)
                    path.lineTo(QPointF(bottom.x(), mid_y))
                    path.lineTo(QPointF(child_top.x(), mid_y))
                    path.lineTo(child_top)

                    painter.drawPath(path)

    def _get_card_photo(self, photo_path: str, size: int):
        """카드용 작은 사진을 로드해 캐시.

        (photo_path, size) 키로 메모이즈. 사진 경로가 바뀌면 자동으로 새 키 사용.
        load_thumbnail이 EXIF 회전 적용 + scaled 결과를 줌.

        Returns:
            QPixmap (성공) 또는 None (사진 없음/실패).
        """
        cache_key = (photo_path, size)
        if cache_key in self._card_photo_cache:
            # LRU: 최근 사용한 항목을 끝으로 이동 (move_to_end)
            self._card_photo_cache.move_to_end(cache_key)
            return self._card_photo_cache[cache_key]

        try:
            from ..utils.photo_manager import load_thumbnail
            pixmap = load_thumbnail(photo_path, size * 2)  # 2x for HiDPI
        except Exception:
            pixmap = None

        # 실패는 None으로 캐시해 반복 시도 비용 방지
        self._card_photo_cache[cache_key] = pixmap
        # 최대 크기 초과 시 가장 오래된 항목 제거 (FIFO of least-recently-used)
        if len(self._card_photo_cache) > self._card_photo_cache_max:
            self._card_photo_cache.popitem(last=False)
        return pixmap

    def invalidate_photo_cache(self, photo_path: str = None) -> None:
        """사진 캐시 무효화. photo_path가 None이면 전체 클리어.

        OrderedDict의 항목 순서를 보존하기 위해 새 dict를 만들지 않고
        in-place pop. 대형 캐시에서 새 dict 할당을 회피.
        """
        if photo_path is None:
            self._card_photo_cache.clear()
            return
        # 해당 path를 키로 갖는 모든 항목 (사이즈별) 제거
        keys_to_remove = [k for k in self._card_photo_cache if k[0] == photo_path]
        for k in keys_to_remove:
            self._card_photo_cache.pop(k, None)

    def _visible_scene_rect(self) -> QRectF:
        """현재 화면(widget viewport)을 씬 좌표계로 환산.

        화면 밖 노드를 그리지 않는 viewport culling용. 약간의 여유 마진을
        두어 줌·팬 중 노드가 갑자기 사라지는 인상을 방지.
        """
        if self.scale <= 0:
            # 비정상 값 방어 — 전 영역 반환
            return QRectF(-1e9, -1e9, 2e9, 2e9)
        margin_px = 50
        top_left = (QPointF(-margin_px, -margin_px) - self.offset) / self.scale
        bottom_right = (
            QPointF(self.width() + margin_px, self.height() + margin_px) - self.offset
        ) / self.scale
        return QRectF(top_left, bottom_right)

    def _draw_nodes(self, painter: QPainter):
        """노드 카드 그리기 (viewport 안의 노드만 그려 큰 트리에서 성능 확보)."""
        visible = self._visible_scene_rect()
        for person in self.family_tree.get_all_persons():
            if person.id not in self._node_rects:
                continue

            rect = self._node_rects[person.id]
            # viewport 밖 노드는 스킵 — 1만+ 인원 트리에서 큰 차이
            if not visible.intersects(rect):
                continue

            is_selected = person.id == self.selected_person_id
            is_highlighted = person.id in self.highlighted_ids

            self._draw_person_card(painter, person, rect, is_selected, is_highlighted)

    def _draw_person_card(
        self,
        painter: QPainter,
        person: Person,
        rect: QRectF,
        is_selected: bool,
        is_highlighted: bool,
    ):
        """개인 카드 그리기 (그림자 + 그라데이션 적용)."""
        # 그림자 효과 (카드 아래 오프셋)
        shadow_offset = 4
        shadow_rect = QRectF(
            rect.x() + shadow_offset, rect.y() + shadow_offset, rect.width(), rect.height()
        )
        shadow_color = self.colors.get("shadow", QColor(0, 0, 0, 32))
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 12, 12)

        # 카드 배경 (미세한 그라데이션)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        card_bg = self.colors["card_bg"]
        gradient.setColorAt(0, card_bg)
        gradient.setColorAt(1, card_bg.darker(105))
        painter.setBrush(QBrush(gradient))

        if is_selected:
            pen = QPen(self.colors["card_selected_border"])
            pen.setWidth(3)
        elif is_highlighted:
            pen = QPen(self.colors["card_highlighted_border"])
            pen.setWidth(2)
        else:
            pen = QPen(self.colors["card_border"])
            pen.setWidth(1)

        painter.setPen(pen)

        # 둥근 사각형 (더 둥글게)
        painter.drawRoundedRect(rect, 12, 12)

        # 성별에 따른 아이콘 색상
        is_male = person.gender == "M"
        if self._theme_manager.is_dark:
            icon_bg = QColor("#3B4261") if is_male else QColor("#5C3D5C")
            icon_fg = QColor("#89B4FA") if is_male else QColor("#F5C2E7")
        else:
            icon_bg = QColor("#E3EDF7") if is_male else QColor("#F7E3EE")
            icon_fg = QColor("#4A7AB0") if is_male else QColor("#B04A7A")

        # 아이콘 영역 (더 크게)
        icon_size = 44
        icon_rect = QRectF(
            rect.x() + (rect.width() - icon_size) / 2, rect.y() + 6, icon_size, icon_size
        )

        # 사진이 있으면 사진으로 아이콘 자리 채우기 (원형 마스크). 없으면 기존 그라데이션 아이콘.
        photo_pixmap = None
        if person.photo_path:
            photo_pixmap = self._get_card_photo(person.photo_path, int(icon_size))

        if photo_pixmap is not None and not photo_pixmap.isNull():
            # 원형 클리핑으로 그려 카드 디자인 일관성 유지
            painter.save()
            clip = QPainterPath()
            clip.addEllipse(icon_rect)
            painter.setClipPath(clip)
            painter.drawPixmap(icon_rect, photo_pixmap, QRectF(photo_pixmap.rect()))
            painter.restore()
            # 사진 테두리 (성별 색상으로 미세하게)
            border_pen = QPen(icon_bg.darker(115))
            border_pen.setWidth(1)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(icon_rect)
        else:
            # 아이콘 배경 (그라데이션 원)
            icon_gradient = QRadialGradient(icon_rect.center(), icon_size / 2)
            icon_gradient.setColorAt(0, icon_bg.lighter(110))
            icon_gradient.setColorAt(1, icon_bg)
            painter.setBrush(QBrush(icon_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(icon_rect)

            # 사람 아이콘 그리기 (더 세련되게)
            painter.setBrush(QBrush(icon_fg))

            # 머리
            head_size = 14
            head_rect = QRectF(
                icon_rect.x() + (icon_size - head_size) / 2, icon_rect.y() + 6, head_size, head_size
            )
            painter.drawEllipse(head_rect)

            # 몸통 (더 부드러운 곡선)
            body_path = QPainterPath()
            body_center_x = icon_rect.x() + icon_size / 2
            body_path.moveTo(body_center_x - 12, icon_rect.y() + icon_size - 4)
            body_path.quadTo(
                body_center_x, icon_rect.y() + 18, body_center_x + 12, icon_rect.y() + icon_size - 4
            )
            body_path.closeSubpath()
            painter.drawPath(body_path)

        # 이름 (긴 이름은 말줄임 처리, 전체 이름은 호버 툴팁에서 확인)
        name_font = QFont("Malgun Gothic", 10, QFont.Weight.Bold)
        painter.setFont(name_font)
        painter.setPen(self.colors["text"])

        name_rect = QRectF(rect.x() + 4, rect.y() + 52, rect.width() - 8, 18)
        display_name = person.name or tr("label.no_name")
        metrics = QFontMetrics(name_font)
        elided_name = metrics.elidedText(
            display_name, Qt.TextElideMode.ElideRight, int(name_rect.width())
        )
        painter.drawText(
            name_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            elided_name,
        )

        # 생몰년
        date_font = QFont("Malgun Gothic", 8)
        painter.setFont(date_font)
        painter.setPen(self.colors["text_secondary"])

        date_rect = QRectF(rect.x() + 4, rect.y() + 66, rect.width() - 8, 14)
        painter.drawText(
            date_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            person.lifespan_str or "",
        )

    def mousePressEvent(self, event: QMouseEvent):
        """마우스 누름 이벤트."""
        if event.button() == Qt.MouseButton.LeftButton:
            # 노드 클릭 확인
            clicked_id = self._get_person_at(event.position())

            if clicked_id:
                self.select_person(clicked_id)
            else:
                # 빈 공간 클릭 - 드래그 시작
                self.dragging = True
                self.last_mouse_pos = event.position()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """마우스 놓음 이벤트."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동 이벤트."""
        if self.dragging:
            delta = event.position() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.position()
            self.update()
        else:
            # 호버 커서 + 인물 이름 툴팁 (말줄임된 카드 텍스트의 전체 이름 노출)
            hovered_id = self._get_person_at(event.position())
            if hovered_id:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                if self.family_tree:
                    person = self.family_tree.get_person(hovered_id)
                    if person:
                        tooltip = person.name or tr("label.no_name")
                        if person.lifespan_str:
                            tooltip += f"\n{person.lifespan_str}"
                        self.setToolTip(tooltip)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self.setToolTip("")

    def keyPressEvent(self, event):
        """화살표 키로 인접 인물 탐색.

        - Up: 첫 번째 부모로
        - Down: 첫 번째 자녀로
        - Left/Right: 같은 세대(y좌표 근처)에서 x 방향으로 가장 가까운 인물

        선택된 인물이 없거나 탐색 결과가 없으면 기본 동작.
        """
        if not self.selected_person_id or not self.family_tree:
            super().keyPressEvent(event)
            return

        key = event.key()
        new_target = None

        if key == Qt.Key.Key_Up:
            parents = self.family_tree.get_parents(self.selected_person_id)
            if parents:
                new_target = parents[0].id
        elif key == Qt.Key.Key_Down:
            children = self.family_tree.get_children(self.selected_person_id)
            if children:
                new_target = children[0].id
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            new_target = self._sibling_in_direction(
                self.selected_person_id,
                +1 if key == Qt.Key.Key_Right else -1,
            )
        else:
            super().keyPressEvent(event)
            return

        if new_target:
            self.select_person(new_target)
            self.zoom_to_person(new_target)
            # 이벤트가 처리됐음을 명시 — 부모 위젯의 화살표 키 핸들러로 전파 방지
            event.accept()
        else:
            event.accept()

    def _sibling_in_direction(self, person_id: str, direction: int):
        """같은 세대(y±카드높이 이내)에서 x 방향으로 가장 가까운 노드 ID 반환.

        Args:
            person_id: 기준 인물 ID
            direction: +1이면 오른쪽, -1이면 왼쪽

        Returns:
            인접 노드 ID 또는 None
        """
        if person_id not in self._node_rects:
            return None

        current_rect = self._node_rects[person_id]
        current_cx = current_rect.center().x()
        current_cy = current_rect.center().y()
        y_tolerance = self.CARD_HEIGHT

        best = None
        best_dist = None
        for pid, rect in self._node_rects.items():
            if pid == person_id:
                continue
            if abs(rect.center().y() - current_cy) > y_tolerance:
                continue
            dx = rect.center().x() - current_cx
            if (direction > 0 and dx <= 0) or (direction < 0 and dx >= 0):
                continue
            d = abs(dx)
            if best_dist is None or d < best_dist:
                best = pid
                best_dist = d
        return best

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """더블클릭 이벤트."""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_id = self._get_person_at(event.position())
            if clicked_id:
                self.person_double_clicked.emit(clicked_id)

    def contextMenuEvent(self, event):
        """우클릭 컨텍스트 메뉴."""
        clicked_id = self._get_person_at(QPointF(event.position()))
        if clicked_id:
            self.context_menu_requested.emit(clicked_id, event.globalPosition().toPoint())
        else:
            super().contextMenuEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """휠 이벤트 (줌)."""
        delta = event.angleDelta().y()

        # 줌 중심점
        mouse_pos = event.position()

        # 줌 전 마우스 위치의 씬 좌표
        old_scene_pos = (mouse_pos - self.offset) / self.scale

        # 줌 조정
        if delta > 0:
            self.scale *= 1.1
        else:
            self.scale /= 1.1

        # 줌 범위 제한
        self.scale = max(0.3, min(3.0, self.scale))

        # 줌 후 마우스 위치가 같은 씬 좌표를 가리키도록 오프셋 조정
        new_scene_pos = (mouse_pos - self.offset) / self.scale
        self.offset += (new_scene_pos - old_scene_pos) * self.scale

        self.update()

    def _get_person_at(self, pos: QPointF) -> Optional[str]:
        """주어진 화면 좌표에 있는 사람 ID 반환."""
        # 화면 좌표를 씬 좌표로 변환
        scene_pos = (pos - self.offset) / self.scale

        for person_id, rect in self._node_rects.items():
            if rect.contains(scene_pos):
                return person_id

        return None

    def zoom_in(self):
        """확대 (애니메이션)."""
        target_scale = min(3.0, self.scale * 1.2)
        center = QPointF(self.width() / 2, self.height() / 2)
        self._animate_scale(target_scale, center)

    def zoom_out(self):
        """축소 (애니메이션)."""
        target_scale = max(0.3, self.scale / 1.2)
        center = QPointF(self.width() / 2, self.height() / 2)
        self._animate_scale(target_scale, center)

    def zoom_reset(self):
        """줌 리셋 (애니메이션)."""
        center = QPointF(self.width() / 2, self.height() / 2)
        self._animate_scale(1.0, center)
        self._animate_offset(QPointF(50, 50))

    def zoom_to_person(self, person_id: str):
        """특정 인물 위치로 이동."""
        if person_id in self._node_rects:
            rect = self._node_rects[person_id]
            center = rect.center()
            target_offset = QPointF(self.width() / 2, self.height() / 2) - center * self.scale
            self._animate_offset(target_offset)
