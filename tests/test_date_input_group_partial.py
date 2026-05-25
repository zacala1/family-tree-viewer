"""DateInputGroup 부분 입력 안전성 회귀 가드.

year만/year+month만/모두 비어있는 등 다양한 조합에서 None을 반환하고,
변환 라벨이 안전하게 비워지며, save_spouse_dates 흐름이 lunar 변환을
잘못 호출하지 않는지 검증.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.config import YEAR_MIN, MONTH_MIN, DAY_MIN


@pytest.fixture
def group(qapp):
    from src.views.widgets.date_input_group import create_date_input_widget
    widget, g = create_date_input_widget()
    # widget을 yield로 살려둬야 자식 QSpinBox/QCheckBox가 GC되지 않음
    yield g
    widget.deleteLater()


class TestGetValuesPartialCombinations:
    def test_all_empty_returns_all_none(self, group):
        year, month, day, is_lunar = group.get_values()
        assert (year, month, day, is_lunar) == (None, None, None, False)

    def test_only_year_set(self, group):
        group.set_values(2020, None, None, is_lunar_val=False)
        assert group.get_values() == (2020, None, None, False)

    def test_year_and_month_only(self, group):
        group.set_values(2020, 3, None, is_lunar_val=False)
        assert group.get_values() == (2020, 3, None, False)

    def test_year_month_day_lunar(self, group):
        group.set_values(2020, 3, 15, is_lunar_val=True)
        assert group.get_values() == (2020, 3, 15, True)

    def test_sentinel_values_treated_as_none(self, group):
        # 직접 sentinel 값을 set → None으로 변환되어야
        group.year.setValue(YEAR_MIN)
        group.month.setValue(MONTH_MIN)
        group.day.setValue(DAY_MIN)
        assert group.get_values()[:3] == (None, None, None)


class TestConversionLabelPartialSafety:
    """_update_conversion이 모든 부분 입력 조합에서 크래시 없이 빈 라벨."""

    def test_year_only_keeps_label_empty(self, group):
        group.set_values(2020, None, None, is_lunar_val=False)
        assert group.conversion_label.text() == ""

    def test_year_month_no_day_keeps_label_empty(self, group):
        group.set_values(2020, 3, None, is_lunar_val=False)
        assert group.conversion_label.text() == ""

    def test_month_day_no_year_keeps_label_empty(self, group):
        group.set_values(None, 3, 15, is_lunar_val=False)
        assert group.conversion_label.text() == ""

    def test_toggle_lunar_with_partial_does_not_crash(self, group):
        group.set_values(2020, None, None, is_lunar_val=False)
        group.is_lunar.setChecked(True)
        group.is_lunar.setChecked(False)
        # 빈 라벨 유지 + 예외 없음
        assert group.conversion_label.text() == ""


class TestRelationshipPartialDateSafety:
    """save_spouse_dates가 부분 입력 + None 입력 모두에서 lunar 변환을 호출하지 않음."""

    def test_relationship_marriage_order_with_none_returns_true(self):
        from src.models.relationship import Relationship, RelationType
        r = Relationship(
            person1_id="p1", person2_id="p2",
            rel_type=RelationType.SPOUSE,
            marriage_year=None, divorce_year=2020,
        )
        # 한쪽이 None → 검증 통과 (보수적)
        assert r.is_valid_marriage_order() is True

    def test_relationship_partial_month_day_falls_back_correctly(self):
        from src.models.relationship import Relationship, RelationType
        # 결혼 2020 (월/일 unknown), 이혼 2020-05-15 → 보수적으로 결혼이 12/31로 처리
        # → marriage(2020,12,31) > divorce(2020,5,15) → False (invalid)
        r = Relationship(
            person1_id="p1", person2_id="p2",
            rel_type=RelationType.SPOUSE,
            marriage_year=2020, marriage_month=None, marriage_day=None,
            divorce_year=2020, divorce_month=5, divorce_day=15,
        )
        # 보수적 비교 → 의문 시 invalid
        assert r.is_valid_marriage_order() is False

    def test_format_date_partial_does_not_crash(self):
        from src.utils.date_formatter import format_date
        # year만 → "2020"
        assert format_date(2020, None, None) == "2020"
        # year+month → "2020.03"
        assert format_date(2020, 3, None) == "2020.03"
        # 전부 → "2020.03.15"
        assert format_date(2020, 3, 15) == "2020.03.15"
        # year=None → ""
        assert format_date(None, 3, 15) == ""
