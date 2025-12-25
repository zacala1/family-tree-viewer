"""음력/양력 변환 유틸리티."""
from typing import Optional, Tuple
from datetime import date

try:
    from korean_lunar_calendar import KoreanLunarCalendar
    HAS_LUNAR_CALENDAR = True
except ImportError:
    HAS_LUNAR_CALENDAR = False


class LunarCalendarUtil:
    """한국 음력/양력 변환 유틸리티 클래스."""

    @staticmethod
    def is_available() -> bool:
        """음력 변환 라이브러리 사용 가능 여부."""
        return HAS_LUNAR_CALENDAR

    @staticmethod
    def lunar_to_solar(
        year: int,
        month: int,
        day: int,
        is_leap_month: bool = False
    ) -> Optional[Tuple[int, int, int]]:
        """
        음력을 양력으로 변환.

        Args:
            year: 음력 연도
            month: 음력 월
            day: 음력 일
            is_leap_month: 윤달 여부

        Returns:
            (양력 연도, 양력 월, 양력 일) 또는 None
        """
        if not HAS_LUNAR_CALENDAR:
            return None

        try:
            calendar = KoreanLunarCalendar()
            calendar.setLunarDate(year, month, day, is_leap_month)
            solar_date = calendar.SolarIsoFormat()  # YYYY-MM-DD
            parts = solar_date.split('-')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, AttributeError, IndexError) as e:
            from .logger import error
            error(f"Lunar to solar conversion failed: {year}/{month}/{day} - {e}")
            return None
        except Exception as e:
            from .logger import error
            error(f"Unexpected error in lunar_to_solar: {e}")
            return None

    @staticmethod
    def solar_to_lunar(
        year: int,
        month: int,
        day: int
    ) -> Optional[Tuple[int, int, int, bool]]:
        """
        양력을 음력으로 변환.

        Args:
            year: 양력 연도
            month: 양력 월
            day: 양력 일

        Returns:
            (음력 연도, 음력 월, 음력 일, 윤달 여부) 또는 None
        """
        if not HAS_LUNAR_CALENDAR:
            return None

        try:
            calendar = KoreanLunarCalendar()
            calendar.setSolarDate(year, month, day)
            lunar_date = calendar.LunarIsoFormat()  # YYYY-MM-DD
            parts = lunar_date.split('-')
            is_leap = calendar.isIntercalation
            return (int(parts[0]), int(parts[1]), int(parts[2]), is_leap)
        except (ValueError, AttributeError, IndexError) as e:
            from .logger import error
            error(f"Solar to lunar conversion failed: {year}/{month}/{day} - {e}")
            return None
        except Exception as e:
            from .logger import error
            error(f"Unexpected error in solar_to_lunar: {e}")
            return None

    @staticmethod
    def format_date(
        year: Optional[int],
        month: Optional[int] = None,
        day: Optional[int] = None,
        is_lunar: bool = False,
        show_converted: bool = True
    ) -> str:
        """
        날짜 문자열 포맷팅.

        Args:
            year: 연도
            month: 월
            day: 일
            is_lunar: 음력 여부
            show_converted: 변환된 날짜도 표시할지 여부

        Returns:
            포맷된 날짜 문자열
        """
        if not year:
            return ""

        parts = [str(year)]
        if month:
            parts.append(f"{month:02d}")
        if day:
            parts.append(f"{day:02d}")

        date_str = ".".join(parts)

        if is_lunar:
            date_str += " (음력)"

            # 양력 변환 표시
            if show_converted and month and day:
                solar = LunarCalendarUtil.lunar_to_solar(year, month, day)
                if solar:
                    date_str += f" → {solar[0]}.{solar[1]:02d}.{solar[2]:02d} (양력)"

        return date_str

    @staticmethod
    def get_korean_zodiac(year: int) -> str:
        """
        띠 계산.

        Args:
            year: 연도

        Returns:
            띠 이름
        """
        zodiac = ['원숭이', '닭', '개', '돼지', '쥐', '소',
                  '호랑이', '토끼', '용', '뱀', '말', '양']
        return zodiac[year % 12] + "띠"

    @staticmethod
    def get_age(
        birth_year: int,
        birth_month: Optional[int] = None,
        birth_day: Optional[int] = None,
        is_lunar: bool = False,
        korean_age: bool = False
    ) -> int:
        """
        나이 계산.

        Args:
            birth_year: 출생 연도
            birth_month: 출생 월
            birth_day: 출생 일
            is_lunar: 음력 여부
            korean_age: 한국 나이 여부 (만 나이가 아닌 세는 나이)

        Returns:
            나이
        """
        today = date.today()
        current_year = today.year

        if korean_age:
            # 한국 나이 (세는 나이) - 2023년부터 만 나이로 통일되었지만 옵션으로 제공
            return current_year - birth_year + 1

        # 만 나이
        age = current_year - birth_year

        # 음력인 경우 양력으로 변환
        if is_lunar and birth_month and birth_day:
            solar = LunarCalendarUtil.lunar_to_solar(birth_year, birth_month, birth_day)
            if solar:
                birth_month, birth_day = solar[1], solar[2]

        # 생일이 아직 안 지났으면 1살 빼기
        if birth_month and birth_day:
            if (today.month, today.day) < (birth_month, birth_day):
                age -= 1

        return age
