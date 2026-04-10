"""중복 인물 감지 유틸리티."""

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.person import Person


def normalize_name(name: str) -> str:
    """이름 정규화 (공백 제거, 소문자)."""
    return "".join(name.lower().split())


def levenshtein_distance(s1: str, s2: str) -> int:
    """두 문자열 간의 레벤슈타인 거리 계산."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr_row.append(min(
                curr_row[j] + 1,        # 삽입
                prev_row[j + 1] + 1,    # 삭제
                prev_row[j] + cost,      # 치환
            ))
        prev_row = curr_row

    return prev_row[-1]


def find_similar_persons(
    name: str,
    persons: List["Person"],
    threshold: int = 2,
    exclude_id: str = "",
) -> List[Tuple["Person", int]]:
    """유사한 이름의 인물 찾기.

    Args:
        name: 검색할 이름
        persons: 검색 대상 인물 목록
        threshold: 최대 레벤슈타인 거리 (이하면 유사)
        exclude_id: 제외할 인물 ID

    Returns:
        (Person, distance) 튜플 목록 (거리 오름차순)
    """
    normalized = normalize_name(name)
    if not normalized:
        return []

    results = []
    for person in persons:
        if person.id == exclude_id:
            continue
        p_normalized = normalize_name(person.name)
        if not p_normalized:
            continue

        dist = levenshtein_distance(normalized, p_normalized)
        if dist <= threshold:
            results.append((person, dist))

    results.sort(key=lambda x: x[1])
    return results
