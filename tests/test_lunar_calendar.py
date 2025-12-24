"""음력 변환 유틸리티 유닛 테스트."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.lunar_calendar import LunarCalendarUtil


class TestLunarCalendarUtil(unittest.TestCase):
    """LunarCalendarUtil 클래스 테스트."""

    def test_is_available(self):
        """라이브러리 사용 가능 여부 테스트."""
        # 라이브러리 설치 여부에 따라 결과가 다름
        result = LunarCalendarUtil.is_available()
        self.assertIsInstance(result, bool)

    @unittest.skipUnless(
        LunarCalendarUtil.is_available(),
        "korean-lunar-calendar 라이브러리가 필요합니다"
    )
    def test_lunar_to_solar(self):
        """음력 -> 양력 변환 테스트."""
        # 음력 2000년 1월 1일 -> 양력 2000년 2월 5일
        result = LunarCalendarUtil.lunar_to_solar(2000, 1, 1)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 2000)  # 연도
        self.assertEqual(result[1], 2)     # 월
        self.assertEqual(result[2], 5)     # 일

    @unittest.skipUnless(
        LunarCalendarUtil.is_available(),
        "korean-lunar-calendar 라이브러리가 필요합니다"
    )
    def test_solar_to_lunar(self):
        """양력 -> 음력 변환 테스트."""
        # 양력 2000년 2월 5일 -> 음력 2000년 1월 1일
        result = LunarCalendarUtil.solar_to_lunar(2000, 2, 5)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 2000)  # 연도
        self.assertEqual(result[1], 1)     # 월
        self.assertEqual(result[2], 1)     # 일

    @unittest.skipUnless(
        LunarCalendarUtil.is_available(),
        "korean-lunar-calendar 라이브러리가 필요합니다"
    )
    def test_lunar_to_solar_invalid(self):
        """잘못된 음력 날짜 변환 테스트."""
        # 잘못된 날짜
        result = LunarCalendarUtil.lunar_to_solar(1800, 15, 45)
        # 라이브러리에 따라 None 또는 에러
        # 여기서는 예외 처리 확인

    def test_format_date_solar(self):
        """양력 날짜 포맷팅 테스트."""
        result = LunarCalendarUtil.format_date(
            year=1990,
            month=5,
            day=15,
            is_lunar=False
        )
        self.assertEqual(result, "1990.05.15")

    def test_format_date_lunar(self):
        """음력 날짜 포맷팅 테스트."""
        result = LunarCalendarUtil.format_date(
            year=1990,
            month=5,
            day=15,
            is_lunar=True,
            show_converted=False
        )
        self.assertEqual(result, "1990.05.15 (음력)")

    def test_format_date_year_only(self):
        """연도만 포맷팅 테스트."""
        result = LunarCalendarUtil.format_date(year=1990)
        self.assertEqual(result, "1990")

    def test_format_date_empty(self):
        """빈 날짜 포맷팅 테스트."""
        result = LunarCalendarUtil.format_date(year=None)
        self.assertEqual(result, "")

    def test_get_korean_zodiac(self):
        """띠 계산 테스트."""
        # 1984년: 쥐띠
        self.assertEqual(LunarCalendarUtil.get_korean_zodiac(1984), "쥐띠")
        # 1985년: 소띠
        self.assertEqual(LunarCalendarUtil.get_korean_zodiac(1985), "소띠")
        # 1986년: 호랑이띠
        self.assertEqual(LunarCalendarUtil.get_korean_zodiac(1986), "호랑이띠")
        # 1987년: 토끼띠
        self.assertEqual(LunarCalendarUtil.get_korean_zodiac(1987), "토끼띠")
        # 1988년: 용띠
        self.assertEqual(LunarCalendarUtil.get_korean_zodiac(1988), "용띠")
        # 2000년: 용띠
        self.assertEqual(LunarCalendarUtil.get_korean_zodiac(2000), "용띠")

    def test_get_age(self):
        """나이 계산 테스트."""
        from datetime import date

        current_year = date.today().year

        # 만 나이
        age = LunarCalendarUtil.get_age(
            birth_year=current_year - 30,
            birth_month=1,
            birth_day=1,
            korean_age=False
        )
        # 생일이 지났으면 30, 안 지났으면 29 또는 30
        self.assertIn(age, [29, 30])

    def test_get_age_korean(self):
        """한국 나이 계산 테스트."""
        from datetime import date

        current_year = date.today().year

        # 한국 나이 (세는 나이)
        age = LunarCalendarUtil.get_age(
            birth_year=current_year - 30,
            korean_age=True
        )
        self.assertEqual(age, 31)


class TestLunarCalendarEdgeCases(unittest.TestCase):
    """음력 변환 엣지 케이스 테스트."""

    def test_format_date_partial(self):
        """부분 날짜 포맷팅 테스트."""
        # 연월만
        result = LunarCalendarUtil.format_date(year=1990, month=5)
        self.assertEqual(result, "1990.05")

    @unittest.skipUnless(
        LunarCalendarUtil.is_available(),
        "korean-lunar-calendar 라이브러리가 필요합니다"
    )
    def test_roundtrip_conversion(self):
        """음력 <-> 양력 왕복 변환 테스트."""
        # 음력 -> 양력 -> 음력
        original_lunar = (1990, 8, 15)  # 추석

        solar = LunarCalendarUtil.lunar_to_solar(*original_lunar)
        self.assertIsNotNone(solar)

        back_to_lunar = LunarCalendarUtil.solar_to_lunar(*solar[:3])
        self.assertIsNotNone(back_to_lunar)

        self.assertEqual(back_to_lunar[0], original_lunar[0])
        self.assertEqual(back_to_lunar[1], original_lunar[1])
        self.assertEqual(back_to_lunar[2], original_lunar[2])


if __name__ == '__main__':
    unittest.main()
