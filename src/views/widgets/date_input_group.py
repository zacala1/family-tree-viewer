"""날짜 입력 그룹 헬퍼 — year/month/day spinbox + lunar 체크박스 + 변환 라벨.

여러 위젯(detail_panel 생몰일, RelationshipsTab 결혼/이혼일)에서 공유.
detail_panel에서 분리해 widgets/로 이동.
"""
from __future__ import annotations

from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from ...config import (
    DAY_MAX,
    DAY_MIN,
    MONTH_MAX,
    MONTH_MIN,
    YEAR_MAX,
    YEAR_MIN,
)
from ...i18n import tr


class DateInputGroup:
    """date input — year/month/day SpinBox + is_lunar checkbox + (선택) conversion label.

    sentinel value (YEAR_MIN 등) = "비설정". get_values()에서 None으로 변환.
    """

    def __init__(
        self,
        year: QSpinBox,
        month: QSpinBox,
        day: QSpinBox,
        is_lunar: QCheckBox,
        year_label: QLabel,
        month_label: QLabel,
        day_label: QLabel,
        conversion_label: Optional[QLabel] = None,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.is_lunar = is_lunar
        self.year_label = year_label
        self.month_label = month_label
        self.day_label = day_label
        self.conversion_label = conversion_label

        # 값 변경 시 양력↔음력 변환 라벨 자동 갱신
        if conversion_label is not None:
            year.valueChanged.connect(self._update_conversion)
            month.valueChanged.connect(self._update_conversion)
            day.valueChanged.connect(self._update_conversion)
            is_lunar.toggled.connect(self._update_conversion)
            self._update_conversion()

    def _update_conversion(self):
        """현재 값의 반대 캘린더 표기를 conversion_label에 표시.

        - 음력 입력 → "→ 양력 YYYY.MM.DD"
        - 양력 입력 → "→ 음력 YYYY.MM.DD" (윤달이면 끝에 *)
        - 라이브러리 미설치·값 불완전·변환 실패 시 빈 문자열
        """
        if self.conversion_label is None:
            return
        from ...utils.lunar_calendar import LunarCalendarUtil

        if not LunarCalendarUtil.is_available():
            self.conversion_label.setText("")
            return

        year, month, day, is_lunar = self.get_values()
        if not (year and month and day):
            self.conversion_label.setText("")
            return

        if is_lunar:
            solar = LunarCalendarUtil.lunar_to_solar(year, month, day)
            if solar:
                self.conversion_label.setText(
                    f"→ {tr('label.solar')} {solar[0]}.{solar[1]:02d}.{solar[2]:02d}"
                )
            else:
                self.conversion_label.setText("")
        else:
            lunar = LunarCalendarUtil.solar_to_lunar(year, month, day)
            if lunar:
                leap_mark = "*" if lunar[3] else ""
                self.conversion_label.setText(
                    f"→ {tr('label.lunar')} {lunar[0]}.{lunar[1]:02d}{leap_mark}.{lunar[2]:02d}"
                )
            else:
                self.conversion_label.setText("")

    def set_values(
        self,
        year_val: Optional[int],
        month_val: Optional[int],
        day_val: Optional[int],
        is_lunar_val: bool,
    ):
        self.year.setValue(year_val or YEAR_MIN)
        self.month.setValue(month_val or MONTH_MIN)
        self.day.setValue(day_val or DAY_MIN)
        self.is_lunar.setChecked(is_lunar_val)

    def get_values(self) -> Tuple[Optional[int], Optional[int], Optional[int], bool]:
        year_val = self.year.value()
        month_val = self.month.value()
        day_val = self.day.value()
        year = year_val if year_val != YEAR_MIN else None
        month = month_val if month_val != MONTH_MIN else None
        day = day_val if day_val != DAY_MIN else None
        return year, month, day, self.is_lunar.isChecked()

    def clear(self):
        self.year.setValue(YEAR_MIN)
        self.month.setValue(MONTH_MIN)
        self.day.setValue(DAY_MIN)
        self.is_lunar.setChecked(False)

    def set_read_only(self, read_only: bool):
        self.year.setReadOnly(read_only)
        self.month.setReadOnly(read_only)
        self.day.setReadOnly(read_only)
        self.is_lunar.setEnabled(not read_only)

    def update_labels(self):
        self.year_label.setText(tr("label.year"))
        self.month_label.setText(tr("label.month"))
        self.day_label.setText(tr("label.day"))
        self.is_lunar.setText(tr("label.lunar"))
        self._update_conversion()


def create_date_input_widget() -> Tuple[QWidget, DateInputGroup]:
    """년/월/일 + 음력 + 변환라벨이 한 줄로 배치된 위젯 + 그룹 반환."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    year = QSpinBox()
    year.setRange(YEAR_MIN, YEAR_MAX)
    year.setSpecialValueText("-")
    year.setValue(YEAR_MIN)
    layout.addWidget(year)
    year_label = QLabel(tr("label.year"))
    layout.addWidget(year_label)

    month = QSpinBox()
    month.setRange(MONTH_MIN, MONTH_MAX)
    month.setSpecialValueText("-")
    layout.addWidget(month)
    month_label = QLabel(tr("label.month"))
    layout.addWidget(month_label)

    day = QSpinBox()
    day.setRange(DAY_MIN, DAY_MAX)
    day.setSpecialValueText("-")
    layout.addWidget(day)
    day_label = QLabel(tr("label.day"))
    layout.addWidget(day_label)

    is_lunar = QCheckBox(tr("label.lunar"))
    layout.addWidget(is_lunar)

    # 음력↔양력 자동 변환 표시 라벨
    from ...utils.theme_manager import get_theme_manager
    conversion_label = QLabel("")
    conversion_label.setObjectName("dateConversionLabel")
    _muted = get_theme_manager().get_tree_colors().get("text_muted", "#777777")
    conversion_label.setStyleSheet(f"color: {_muted}; padding-left: 8px;")
    layout.addWidget(conversion_label)
    layout.addStretch()

    group = DateInputGroup(
        year, month, day, is_lunar,
        year_label, month_label, day_label,
        conversion_label,
    )
    return widget, group
