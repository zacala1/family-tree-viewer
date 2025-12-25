"""날짜 포맷팅 유틸리티."""
from typing import Optional


def format_date(year: Optional[int], month: Optional[int], day: Optional[int],
                is_lunar: bool = False) -> str:
    """날짜를 문자열로 포맷팅.

    Args:
        year: 연도
        month: 월
        day: 일
        is_lunar: 음력 여부

    Returns:
        포맷된 날짜 문자열. 예: "1985.03.15", "1985.03.15 (음력)"
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

    return date_str


def format_lifespan(birth_year: Optional[int], death_year: Optional[int]) -> str:
    """생몰년 범위를 문자열로 포맷팅.

    Args:
        birth_year: 출생년도
        death_year: 사망년도

    Returns:
        포맷된 생몰년 문자열. 예: "1950 - 2020", "1950 -"
    """
    if not birth_year:
        return ""

    birth = str(birth_year)
    if death_year:
        return f"{birth} - {death_year}"
    return f"{birth} -"
