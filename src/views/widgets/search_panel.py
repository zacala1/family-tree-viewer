"""검색·필터·정렬 패널.

main_window에서 분리. 검색 input + advanced filters + sort/filter combos를
한 위젯으로 통합. 자체 디바운스 + Esc 클리어 단축키 포함.

사용 예:
    panel = SearchPanel(search_index)
    panel.filters_changed.connect(self._on_filters_changed)
    # 호스트에서 모든 인물 받아 필터 적용:
    filtered = panel.apply(self.family_tree.get_all_persons())
"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...config import MAX_SEARCH_QUERY_LENGTH
from ...i18n import tr
from ...utils.search_index import PersonSearchIndex


def _get_search_icon():
    """get_icon은 main_window에 있으므로 여기서 같은 path로 직접 로드."""
    import os
    from PyQt6.QtGui import QIcon
    icons_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "resources", "icons",
    )
    icon_path = os.path.join(icons_dir, "search.svg")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()


class SearchPanel(QWidget):
    """검색·필터·정렬 UI 위젯.

    Signals:
        filters_changed(): 검색 텍스트·필터·정렬 중 하나라도 변경되어 결과를
                           다시 계산해야 할 때 emit. 디바운스 적용 (200ms).
    """

    filters_changed = pyqtSignal()
    DEBOUNCE_MS = 200

    def __init__(self, search_index: PersonSearchIndex, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._search_index = search_index
        self._setup_ui()
        self._setup_debounce()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # === 검색 input + advanced 토글 ===
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_row = QHBoxLayout(search_frame)
        search_row.setContentsMargins(12, 12, 12, 12)

        self.search_input = QLineEdit()
        self.search_input.addAction(_get_search_icon(), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setPlaceholderText(tr("panel.search_placeholder"))
        self.search_input.setObjectName("searchInput")
        search_row.addWidget(self.search_input)

        self.advanced_search_btn = QPushButton("▼")
        self.advanced_search_btn.setFixedSize(28, 28)
        self.advanced_search_btn.setCheckable(True)
        self.advanced_search_btn.setToolTip(tr("tooltip.advanced_search_toggle"))
        self.advanced_search_btn.setAccessibleName(tr("label.advanced_search"))
        self.advanced_search_btn.clicked.connect(self._toggle_advanced)
        search_row.addWidget(self.advanced_search_btn)

        outer.addWidget(search_frame)

        # === Advanced filters (collapsible) ===
        self.advanced_search_frame = QFrame()
        self.advanced_search_frame.setObjectName("advancedSearchFrame")
        self.advanced_search_frame.setVisible(False)
        adv = QVBoxLayout(self.advanced_search_frame)
        adv.setContentsMargins(12, 4, 12, 8)
        adv.setSpacing(4)

        # 성별
        gender_row = QHBoxLayout()
        self._gender_label = QLabel(tr("label.gender") + ":")
        gender_row.addWidget(self._gender_label)
        self.adv_gender_combo = QComboBox()
        self._populate_gender_combo()
        self.adv_gender_combo.currentIndexChanged.connect(lambda _: self._emit_changed())
        gender_row.addWidget(self.adv_gender_combo, 1)
        adv.addLayout(gender_row)

        # 출생연도 범위
        self._year_label = QLabel(tr("label.birth_year_range") + ":")
        adv.addWidget(self._year_label)
        year_row = QHBoxLayout()
        year_row.setContentsMargins(0, 0, 0, 0)
        self.adv_year_from = QSpinBox()
        self.adv_year_from.setObjectName("compactSearchSpin")
        self.adv_year_from.setRange(0, 2100)
        self.adv_year_from.setSpecialValueText("-")
        self.adv_year_from.setFixedWidth(82)
        self.adv_year_from.valueChanged.connect(lambda _: self._emit_changed())
        year_row.addWidget(self.adv_year_from)
        year_row.addWidget(QLabel("~"))
        self.adv_year_to = QSpinBox()
        self.adv_year_to.setObjectName("compactSearchSpin")
        self.adv_year_to.setRange(0, 2100)
        self.adv_year_to.setSpecialValueText("-")
        self.adv_year_to.setFixedWidth(82)
        self.adv_year_to.valueChanged.connect(lambda _: self._emit_changed())
        year_row.addWidget(self.adv_year_to)
        year_row.addStretch()
        adv.addLayout(year_row)

        # 지역
        location_row = QHBoxLayout()
        self._location_label = QLabel(tr("label.location") + ":")
        location_row.addWidget(self._location_label)
        self.adv_location_input = QLineEdit()
        self.adv_location_input.textChanged.connect(lambda _: self._emit_changed())
        location_row.addWidget(self.adv_location_input, 1)
        adv.addLayout(location_row)

        outer.addWidget(self.advanced_search_frame)

        # === Sort + basic filter (목록 헤더 row) ===
        sort_row = QHBoxLayout()
        sort_row.setContentsMargins(12, 0, 12, 4)
        sort_row.setSpacing(4)

        self.sort_combo = QComboBox()
        self._populate_sort_combo()
        self.sort_combo.currentIndexChanged.connect(lambda _: self.filters_changed.emit())
        sort_row.addWidget(self.sort_combo)

        self.filter_combo = QComboBox()
        self._populate_filter_combo()
        self.filter_combo.currentIndexChanged.connect(lambda _: self.filters_changed.emit())
        sort_row.addWidget(self.filter_combo)

        outer.addLayout(sort_row)

    def _setup_debounce(self):
        """검색 입력 200ms 디바운스 + Enter 즉시 + Esc 클리어."""
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(self.DEBOUNCE_MS)
        self._debounce.timeout.connect(self.filters_changed)
        self.search_input.textChanged.connect(self._debounce.start)
        self.search_input.returnPressed.connect(self.filters_changed)

        self._esc_shortcut = QShortcut(QKeySequence("Esc"), self.search_input)
        self._esc_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self._esc_shortcut.activated.connect(self.clear_search)

    # === 콤보 초기화 (언어 변경 시 재호출) ===

    def _populate_gender_combo(self):
        self.adv_gender_combo.clear()
        self.adv_gender_combo.addItem(tr("filter.all"), "all")
        self.adv_gender_combo.addItem(tr("label.male"), "male")
        self.adv_gender_combo.addItem(tr("label.female"), "female")

    def _populate_sort_combo(self):
        self.sort_combo.clear()
        self.sort_combo.addItem(tr("sort.name_asc"), "name_asc")
        self.sort_combo.addItem(tr("sort.name_desc"), "name_desc")
        self.sort_combo.addItem(tr("sort.birth_year"), "birth_year")

    def _populate_filter_combo(self):
        self.filter_combo.clear()
        self.filter_combo.addItem(tr("filter.all"), "all")
        self.filter_combo.addItem(tr("filter.male"), "male")
        self.filter_combo.addItem(tr("filter.female"), "female")
        self.filter_combo.addItem(tr("filter.alive"), "alive")
        self.filter_combo.addItem(tr("filter.deceased"), "deceased")

    # === Public API ===

    def get_search_text(self) -> str:
        return self.search_input.text()

    def clear_search(self):
        """Esc 또는 외부 호출 — 검색창 비우고 즉시 filters_changed emit."""
        if not self.search_input.text():
            return
        self.search_input.clear()
        self._debounce.stop()
        self.filters_changed.emit()

    def has_advanced_filters_set(self) -> bool:
        """고급 필터(성별·연도·지역) 중 하나라도 활성화됐는지."""
        return (
            self.adv_gender_combo.currentData() != "all"
            or self.adv_year_from.value() > 0
            or self.adv_year_to.value() > 0
            or bool(self.adv_location_input.text().strip())
        )

    def is_advanced_visible(self) -> bool:
        return self.advanced_search_frame.isVisible()

    def apply(self, all_persons: List) -> List:
        """현재 검색 + 필터 + 정렬을 적용한 결과 반환."""
        text = self.get_search_text().strip()
        if len(text) > MAX_SEARCH_QUERY_LENGTH:
            text = text[:MAX_SEARCH_QUERY_LENGTH]

        # 1) 검색 텍스트 (Trie + 한글 초성 모두 지원)
        if text:
            results = self._search_index.search(text)
        else:
            results = list(all_persons)

        # 2) 고급 필터
        if self.is_advanced_visible():
            results = self._apply_advanced(results)

        # 3) 기본 정렬 + 필터 (sort_combo + filter_combo)
        return self._apply_sort_and_filter(results)

    def update_ui_texts(self):
        """언어 변경 시 모든 라벨·툴팁·콤보 항목 재번역."""
        self.search_input.setPlaceholderText(tr("panel.search_placeholder"))
        self.advanced_search_btn.setToolTip(tr("tooltip.advanced_search_toggle"))
        self.advanced_search_btn.setAccessibleName(tr("label.advanced_search"))
        self._gender_label.setText(tr("label.gender") + ":")
        self._year_label.setText(tr("label.birth_year_range") + ":")
        self._location_label.setText(tr("label.location") + ":")
        # 콤보는 currentIndex 보존하면서 항목 텍스트만 갱신
        prev_gender = self.adv_gender_combo.currentIndex()
        prev_sort = self.sort_combo.currentIndex()
        prev_filter = self.filter_combo.currentIndex()
        self._populate_gender_combo()
        self._populate_sort_combo()
        self._populate_filter_combo()
        self.adv_gender_combo.setCurrentIndex(prev_gender)
        self.sort_combo.setCurrentIndex(prev_sort)
        self.filter_combo.setCurrentIndex(prev_filter)

    # === Internal ===

    def _emit_changed(self):
        self.filters_changed.emit()

    def _toggle_advanced(self):
        visible = self.advanced_search_btn.isChecked()
        self.advanced_search_frame.setVisible(visible)
        self.advanced_search_btn.setText("▲" if visible else "▼")
        if not visible:
            # 필터 초기화 → emit
            self.adv_gender_combo.setCurrentIndex(0)
            self.adv_year_from.setValue(0)
            self.adv_year_to.setValue(0)
            self.adv_location_input.clear()
        self.filters_changed.emit()

    def _apply_advanced(self, persons: List) -> List:
        gender = self.adv_gender_combo.currentData()
        if gender == "male":
            persons = [p for p in persons if p.gender == "M"]
        elif gender == "female":
            persons = [p for p in persons if p.gender == "F"]

        year_from = self.adv_year_from.value()
        year_to = self.adv_year_to.value()
        if year_from > 0:
            persons = [p for p in persons if p.birth_year and p.birth_year >= year_from]
        if year_to > 0:
            persons = [p for p in persons if p.birth_year and p.birth_year <= year_to]

        location = self.adv_location_input.text().strip().lower()
        if location:
            persons = [
                p for p in persons
                if location in (p.birth_place or "").lower()
                or location in (p.current_address or "").lower()
            ]
        return persons

    def _apply_sort_and_filter(self, persons: List) -> List:
        # 기본 필터
        f = self.filter_combo.currentData()
        if f == "male":
            persons = [p for p in persons if p.gender == "M"]
        elif f == "female":
            persons = [p for p in persons if p.gender == "F"]
        elif f == "alive":
            persons = [p for p in persons if p.is_alive]
        elif f == "deceased":
            persons = [p for p in persons if not p.is_alive]

        # 정렬
        s = self.sort_combo.currentData()
        if s == "name_asc":
            persons = sorted(persons, key=lambda p: (p.name or "").lower())
        elif s == "name_desc":
            persons = sorted(persons, key=lambda p: (p.name or "").lower(), reverse=True)
        elif s == "birth_year":
            persons = sorted(persons, key=lambda p: (p.birth_year or 9999))
        return persons
