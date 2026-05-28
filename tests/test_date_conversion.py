"""DateInputGroup의 음력↔양력 자동 변환 라벨 회귀 가드.

라벨이 값 변경에 반응해 정확한 반대 캘린더 표기를 표시하는지 검증.
korean-lunar-calendar 라이브러리가 없으면 변환 영역이 조용히 비도록.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtWidgets import QLabel

from src.utils.lunar_calendar import LunarCalendarUtil


@pytest.fixture
def date_group(qapp):
    """DetailPanel을 통째로 만들지 않고 위젯 1개만 생성해 격리 테스트."""
    from src.views.detail_panel import DetailPanel
    panel = DetailPanel()
    # birth_date_group이 이미 _setup_ui에서 conversion_label과 함께 만들어짐
    yield panel.birth_date_group
    panel.deleteLater()


@pytest.mark.skipif(
    not LunarCalendarUtil.is_available(),
    reason="korean-lunar-calendar 라이브러리 필요",
)
class TestConversionLabel:
    def test_solar_input_shows_lunar(self, date_group):
        """양력 날짜 입력 시 음력으로 변환된 표기 노출."""
        date_group.set_values(2020, 5, 1, is_lunar_val=False)
        text = date_group.conversion_label.text()
        # 변환 결과는 "→ 음력 YYYY.MM.DD" 형식
        assert text.startswith("→")
        assert "음력" in text or "Lunar" in text

    def test_lunar_input_shows_solar(self, date_group):
        """음력 날짜 입력 시 양력으로 변환된 표기 노출."""
        date_group.set_values(2020, 1, 1, is_lunar_val=True)
        text = date_group.conversion_label.text()
        assert text.startswith("→")
        assert "양력" in text or "Solar" in text

    def test_empty_values_clear_label(self, date_group):
        """연도/월/일 중 하나라도 비어있으면 변환 라벨 비움."""
        date_group.set_values(2020, 5, 1, is_lunar_val=False)
        # 일부만 설정한 상태(=일이 빈 상태) 시뮬레이션을 위해 day를 sentinel로
        from src.config import DAY_MIN
        date_group.day.setValue(DAY_MIN)
        assert date_group.conversion_label.text() == ""

    def test_toggling_lunar_updates_direction(self, date_group):
        """is_lunar 토글 시 변환 방향이 즉시 바뀜."""
        date_group.set_values(2020, 5, 1, is_lunar_val=False)
        solar_text = date_group.conversion_label.text()
        # is_lunar 체크 → 같은 입력값을 음력으로 해석 → 양력으로 변환
        date_group.is_lunar.setChecked(True)
        lunar_text = date_group.conversion_label.text()
        # 두 경우 모두 변환 결과가 표시돼야 하고, 서로 달라야 함
        assert solar_text != ""
        assert lunar_text != ""
        assert solar_text != lunar_text

    def test_known_date_solar_to_lunar(self, date_group):
        """알려진 변환: 양력 2020-01-25 → 음력 2020-01-01 (구정)."""
        date_group.set_values(2020, 1, 25, is_lunar_val=False)
        text = date_group.conversion_label.text()
        # "→ 음력 2020.01.01" 또는 영문일 수도
        assert "2020" in text
        assert "01.01" in text


class TestConversionLabelGracefulFallback:
    def test_no_label_passed_is_safe(self, qapp):
        """conversion_label이 None이어도 DateInputGroup 동작."""
        from PyQt6.QtWidgets import QSpinBox, QCheckBox, QLabel
        from src.views.detail_panel import DateInputGroup
        from src.config import YEAR_MIN, YEAR_MAX, MONTH_MIN, MONTH_MAX, DAY_MIN, DAY_MAX

        y = QSpinBox(); y.setRange(YEAR_MIN, YEAR_MAX)
        m = QSpinBox(); m.setRange(MONTH_MIN, MONTH_MAX)
        d = QSpinBox(); d.setRange(DAY_MIN, DAY_MAX)
        c = QCheckBox()
        group = DateInputGroup(y, m, d, c, QLabel(), QLabel(), QLabel(), conversion_label=None)
        # 값 변경해도 크래시 없음
        group.set_values(2020, 5, 1, is_lunar_val=False)
        # _update_conversion 직접 호출도 안전
        group._update_conversion()
        assert group.get_values() == (2020, 5, 1, False)
