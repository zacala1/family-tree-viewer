"""Family Tree model - manages all persons and relationships."""

from collections import deque
from threading import RLock
from typing import Dict, List, Optional, Set
from .person import Person
from .relationship import Relationship, RelationType
from ..config import MAX_PERSONS, MAX_CYCLE_DEPTH


class FamilyTree:
    """가족 트리 전체를 관리하는 클래스.

    Thread-safe operations using RLock for concurrent access protection.
    """

    # 메모리 고갈 방지를 위한 최대 인원 제한
    MAX_PERSONS = MAX_PERSONS

    def __init__(self):
        self._persons: Dict[str, Person] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._modified: bool = False
        self._generations_valid: bool = False
        self._lock = RLock()  # Thread-safe operations

    @property
    def is_modified(self) -> bool:
        """수정 여부."""
        return self._modified

    def mark_modified(self):
        """수정됨으로 표시."""
        self._modified = True

    def mark_saved(self):
        """저장됨으로 표시."""
        self._modified = False

    # === Person 관리 ===

    def add_person(self, person: Person) -> None:
        """사람 추가 (최대 인원 제한 및 ID 중복 검증)."""
        with self._lock:
            if person.id in self._persons:
                raise ValueError(f"Person with ID {person.id} already exists")
            if len(self._persons) >= self.MAX_PERSONS:
                raise ValueError(f"Maximum number of persons ({self.MAX_PERSONS}) exceeded")
            self._persons[person.id] = person
            self._modified = True
            self._generations_valid = False

    def get_person(self, person_id: str) -> Optional[Person]:
        """ID로 사람 조회."""
        with self._lock:
            return self._persons.get(person_id)

    def get_all_persons(self) -> List[Person]:
        """모든 사람 목록 반환."""
        with self._lock:
            return list(self._persons.values())

    def remove_person(self, person_id: str) -> None:
        """사람 삭제 (관련 관계도 함께 삭제)."""
        if person_id not in self._persons:
            return

        # 관련된 모든 관계 삭제
        to_remove = []
        for rel_id, rel in self._relationships.items():
            if rel.person1_id == person_id or rel.person2_id == person_id:
                to_remove.append(rel_id)

        for rel_id in to_remove:
            del self._relationships[rel_id]

        # 다른 사람들의 참조에서 제거
        for person in self._persons.values():
            if person.father_id == person_id:
                person.father_id = None
            if person.mother_id == person_id:
                person.mother_id = None
            if person_id in person.spouse_ids:
                person.spouse_ids.remove(person_id)
            if person_id in person.children_ids:
                person.children_ids.remove(person_id)

        del self._persons[person_id]
        self._modified = True
        self._generations_valid = False

    def update_person(self, person: Person) -> None:
        """사람 정보 업데이트."""
        if person.id in self._persons:
            self._persons[person.id] = person
            self._modified = True

    # === Relationship 관리 ===

    def add_relationship(self, relationship: Relationship) -> None:
        """관계 추가."""
        self._relationships[relationship.id] = relationship
        self._modified = True

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """ID로 관계 조회."""
        return self._relationships.get(rel_id)

    def get_all_relationships(self) -> List[Relationship]:
        """모든 관계 목록 반환."""
        return list(self._relationships.values())

    def remove_relationship(self, rel_id: str) -> None:
        """관계 삭제."""
        if rel_id in self._relationships:
            del self._relationships[rel_id]
            self._modified = True

    # === 관계 설정 헬퍼 메서드 ===

    def _would_create_cycle(self, ancestor_id: str, descendant_id: str) -> bool:
        """순환 관계가 생기는지 확인 (descendant가 ancestor의 조상인지)."""
        visited = set()
        stack = [(ancestor_id, 0)]  # (person_id, depth)

        while stack:
            current_id, depth = stack.pop()

            # 깊이 제한 초과
            if depth > MAX_CYCLE_DEPTH:
                from ..utils.logger import warning

                warning(f"Cycle detection exceeded max depth ({MAX_CYCLE_DEPTH}) at person {current_id}")
                return True  # 안전하게 순환으로 간주

            if current_id == descendant_id:
                return True
            if current_id in visited:
                continue
            visited.add(current_id)

            person = self.get_person(current_id)
            if person:
                if person.father_id:
                    stack.append((person.father_id, depth + 1))
                if person.mother_id:
                    stack.append((person.mother_id, depth + 1))

        return False

    def set_parent_child(self, parent_id: str, child_id: str) -> Optional[Relationship]:
        """부모-자녀 관계 설정."""
        parent = self.get_person(parent_id)
        child = self.get_person(child_id)

        if not parent or not child:
            return None

        # 순환 관계 검증: child가 parent의 조상이면 안 됨
        if self._would_create_cycle(parent_id, child_id):
            return None

        # 자녀에게 부모 설정
        if parent.gender == "M":
            child.father_id = parent_id
        else:
            child.mother_id = parent_id

        # 부모에게 자녀 추가
        if child_id not in parent.children_ids:
            parent.children_ids.append(child_id)

        # 관계 객체 생성
        rel = Relationship(
            person1_id=parent_id, person2_id=child_id, rel_type=RelationType.PARENT_CHILD
        )
        self.add_relationship(rel)

        self._modified = True
        self._generations_valid = False
        return rel

    def set_spouse(
        self,
        person1_id: str,
        person2_id: str,
        marriage_year: Optional[int] = None,
        marriage_month: Optional[int] = None,
        marriage_day: Optional[int] = None,
        is_lunar: bool = False,
    ) -> Optional[Relationship]:
        """배우자 관계 설정."""
        person1 = self.get_person(person1_id)
        person2 = self.get_person(person2_id)

        if not person1 or not person2:
            return None

        # 양쪽에 배우자 추가
        if person2_id not in person1.spouse_ids:
            person1.spouse_ids.append(person2_id)
        if person1_id not in person2.spouse_ids:
            person2.spouse_ids.append(person1_id)

        # 관계 객체 생성
        rel = Relationship(
            person1_id=person1_id,
            person2_id=person2_id,
            rel_type=RelationType.SPOUSE,
            marriage_year=marriage_year,
            marriage_month=marriage_month,
            marriage_day=marriage_day,
            is_lunar_marriage=is_lunar,
        )
        self.add_relationship(rel)

        self._modified = True
        self._generations_valid = False
        return rel

    # === 조회 메서드 ===

    def get_parents(self, person_id: str) -> List[Person]:
        """부모 목록 반환."""
        person = self.get_person(person_id)
        if not person:
            return []

        parents = []
        if person.father_id:
            father = self.get_person(person.father_id)
            if father:
                parents.append(father)
        if person.mother_id:
            mother = self.get_person(person.mother_id)
            if mother:
                parents.append(mother)
        return parents

    def get_children(self, person_id: str) -> List[Person]:
        """자녀 목록 반환."""
        person = self.get_person(person_id)
        if not person:
            return []

        children = []
        for child_id in person.children_ids:
            child = self.get_person(child_id)
            if child:
                children.append(child)
        return children

    def get_spouses(self, person_id: str) -> List[Person]:
        """배우자 목록 반환."""
        person = self.get_person(person_id)
        if not person:
            return []

        spouses = []
        for spouse_id in person.spouse_ids:
            spouse = self.get_person(spouse_id)
            if spouse:
                spouses.append(spouse)
        return spouses

    def get_spouse_relationship(self, person1_id: str, person2_id: str) -> Optional[Relationship]:
        """두 사람 간의 배우자 관계 객체 반환."""
        for rel in self._relationships.values():
            if rel.rel_type == RelationType.SPOUSE:
                if (rel.person1_id == person1_id and rel.person2_id == person2_id) or (
                    rel.person1_id == person2_id and rel.person2_id == person1_id
                ):
                    return rel
        return None

    def get_spouse_relationships(self, person_id: str) -> List[Relationship]:
        """특정 사람의 모든 배우자 관계 객체 반환."""
        relationships = []
        for rel in self._relationships.values():
            if rel.rel_type == RelationType.SPOUSE:
                if rel.person1_id == person_id or rel.person2_id == person_id:
                    relationships.append(rel)
        return relationships

    def get_current_spouse(self, person_id: str) -> Optional[Person]:
        """현재 배우자(이혼하지 않은) 반환. 여러 명이면 가장 최근 결혼."""
        person = self.get_person(person_id)
        if not person:
            return None

        current_spouse = None
        latest_marriage_year = 0

        for spouse_id in person.spouse_ids:
            rel = self.get_spouse_relationship(person_id, spouse_id)
            if rel and not rel.is_divorced:
                spouse = self.get_person(spouse_id)
                if spouse:
                    # 가장 최근 결혼한 배우자 선택
                    marriage_year = rel.marriage_year or 0
                    if marriage_year >= latest_marriage_year:
                        latest_marriage_year = marriage_year
                        current_spouse = spouse
        return current_spouse

    def get_current_spouse_id(self, person_id: str) -> Optional[str]:
        """현재 배우자(이혼하지 않은)의 ID 반환."""
        spouse = self.get_current_spouse(person_id)
        return spouse.id if spouse else None

    def get_siblings(self, person_id: str) -> List[Person]:
        """형제자매 목록 반환."""
        person = self.get_person(person_id)
        if not person:
            return []

        siblings = set()
        parents = self.get_parents(person_id)

        for parent in parents:
            for child_id in parent.children_ids:
                if child_id != person_id:
                    siblings.add(child_id)

        return [self.get_person(sid) for sid in siblings if self.get_person(sid)]

    def get_direct_family(self, person_id: str) -> List[Person]:
        """직계 가족 목록 반환 (부모, 배우자, 자녀)."""
        result = []
        result.extend(self.get_parents(person_id))
        result.extend(self.get_spouses(person_id))
        result.extend(self.get_children(person_id))
        return result

    def get_direct_family_ids(self, person_id: str) -> Set[str]:
        """직계 가족 ID 집합 반환."""
        return {p.id for p in self.get_direct_family(person_id)}

    # === 세대 계산 ===

    def calculate_generations(self, force: bool = False) -> None:
        """모든 사람의 세대 정보 계산.

        Args:
            force: True면 캐시를 무시하고 재계산
        """
        if not self._persons:
            return

        if self._generations_valid and not force:
            return

        # 모든 세대 초기화
        for person in self._persons.values():
            person.generation = -1  # 미방문 표시

        # 진정한 루트 찾기: 부모가 없고, 배우자도 부모가 없거나 배우자가 없는 사람
        # 가장 오래된 세대부터 시작하기 위해 혈연으로 연결된 최상위 조상 찾기
        def is_true_root(p):
            """진정한 루트인지 확인 (부모도 없고 배우자의 부모도 없음)"""
            if p.father_id or p.mother_id:
                return False
            # 배우자가 있으면 배우자의 부모도 확인
            for spouse_id in p.spouse_ids:
                spouse = self.get_person(spouse_id)
                if spouse and (spouse.father_id or spouse.mother_id):
                    return False  # 배우자에게 부모가 있으면 이 사람은 루트가 아님
            return True

        true_roots = [p for p in self._persons.values() if is_true_root(p)]

        # 진정한 루트가 없으면 부모가 없는 사람들 중 선택
        if not true_roots:
            true_roots = [p for p in self._persons.values() if not p.father_id and not p.mother_id]

        if not true_roots and self._persons:
            # 루트가 없으면 첫 번째 사람을 루트로
            true_roots = [list(self._persons.values())[0]]
        elif not self._persons:
            # 빈 트리인 경우 조기 반환
            return

        # BFS로 세대 계산 (deque 사용으로 O(1) pop 성능)
        visited = set()
        queue = deque((r, 0) for r in true_roots)

        while queue:
            person, gen = queue.popleft()
            if person.id in visited:
                continue

            visited.add(person.id)
            person.generation = gen

            # 배우자들은 같은 세대
            for spouse in self.get_spouses(person.id):
                if spouse.id not in visited:
                    queue.append((spouse, gen))

            # 자녀들은 다음 세대
            for child in self.get_children(person.id):
                if child.id not in visited:
                    queue.append((child, gen + 1))

        # 아직 방문하지 않은 사람들 처리 (연결되지 않은 서브트리)
        for person in self._persons.values():
            if person.generation == -1:
                person.generation = 0

        self._generations_valid = True

    def get_persons_by_generation(self) -> Dict[int, List[Person]]:
        """세대별 사람 목록 반환."""
        self.calculate_generations()

        gen_dict: Dict[int, List[Person]] = {}
        for person in self._persons.values():
            gen = person.generation
            if gen not in gen_dict:
                gen_dict[gen] = []
            gen_dict[gen].append(person)

        return gen_dict

    # === 직렬화 ===

    def to_dict(self) -> dict:
        """딕셔너리로 변환."""
        return {
            "persons": [p.to_dict() for p in self._persons.values()],
            "relationships": [r.to_dict() for r in self._relationships.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FamilyTree":
        """딕셔너리에서 FamilyTree 객체 생성."""
        tree = cls()

        for p_data in data.get("persons", []):
            person = Person.from_dict(p_data)
            tree._persons[person.id] = person

        for r_data in data.get("relationships", []):
            rel = Relationship.from_dict(r_data)
            tree._relationships[rel.id] = rel

        tree._modified = False
        tree._generations_valid = False
        return tree

    def clear(self) -> None:
        """모든 데이터 삭제."""
        self._persons.clear()
        self._relationships.clear()
        self._modified = False
        self._generations_valid = False
