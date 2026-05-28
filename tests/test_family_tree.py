"""FamilyTree 모델 유닛 테스트."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.models.relationship import Relationship, RelationType


class TestFamilyTree(unittest.TestCase):
    """FamilyTree 클래스 테스트."""

    def setUp(self):
        """각 테스트 전 실행."""
        self.tree = FamilyTree()

    def test_add_person(self):
        """사람 추가 테스트."""
        person = Person(name="테스트")
        self.tree.add_person(person)

        self.assertEqual(len(self.tree.get_all_persons()), 1)
        self.assertTrue(self.tree.is_modified)

    def test_get_person(self):
        """사람 조회 테스트."""
        person = Person(id="test-id", name="테스트")
        self.tree.add_person(person)

        found = self.tree.get_person("test-id")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "테스트")

        not_found = self.tree.get_person("nonexistent")
        self.assertIsNone(not_found)

    def test_remove_person(self):
        """사람 삭제 테스트."""
        person = Person(id="to-delete", name="삭제대상")
        self.tree.add_person(person)

        self.tree.remove_person("to-delete")

        self.assertIsNone(self.tree.get_person("to-delete"))
        self.assertEqual(len(self.tree.get_all_persons()), 0)

    def test_update_person(self):
        """사람 정보 업데이트 테스트."""
        person = Person(id="update-id", name="원래이름")
        self.tree.add_person(person)

        person.name = "변경된이름"
        self.tree.update_person(person)

        found = self.tree.get_person("update-id")
        self.assertEqual(found.name, "변경된이름")

    def test_mark_saved(self):
        """저장 상태 테스트."""
        person = Person(name="테스트")
        self.tree.add_person(person)

        self.assertTrue(self.tree.is_modified)

        self.tree.mark_saved()
        self.assertFalse(self.tree.is_modified)


class TestFamilyRelationships(unittest.TestCase):
    """가족 관계 테스트."""

    def setUp(self):
        """테스트용 가족 트리 생성."""
        self.tree = FamilyTree()

        # 조부모
        self.grandfather = Person(id="gf", name="할아버지", gender='M')
        self.grandmother = Person(id="gm", name="할머니", gender='F')

        # 부모
        self.father = Person(id="f", name="아버지", gender='M')
        self.mother = Person(id="m", name="어머니", gender='F')

        # 자녀
        self.child1 = Person(id="c1", name="첫째", gender='M')
        self.child2 = Person(id="c2", name="둘째", gender='F')

        # 모두 추가
        for p in [self.grandfather, self.grandmother, self.father,
                  self.mother, self.child1, self.child2]:
            self.tree.add_person(p)

    def test_set_spouse(self):
        """배우자 관계 설정 테스트."""
        rel = self.tree.set_spouse("gf", "gm")

        self.assertIsNotNone(rel)
        self.assertEqual(rel.rel_type, RelationType.SPOUSE)

        # 양쪽에 배우자 ID 추가 확인
        gf = self.tree.get_person("gf")
        gm = self.tree.get_person("gm")

        self.assertIn("gm", gf.spouse_ids)
        self.assertIn("gf", gm.spouse_ids)

    def test_set_parent_child(self):
        """부모-자녀 관계 설정 테스트."""
        rel = self.tree.set_parent_child("f", "c1")

        self.assertIsNotNone(rel)
        self.assertEqual(rel.rel_type, RelationType.PARENT_CHILD)

        # 자녀에 부모 ID 설정 확인
        child = self.tree.get_person("c1")
        self.assertEqual(child.father_id, "f")

        # 부모에 자녀 ID 추가 확인
        father = self.tree.get_person("f")
        self.assertIn("c1", father.children_ids)

    def test_get_parents(self):
        """부모 조회 테스트."""
        self.tree.set_parent_child("f", "c1")
        self.tree.set_parent_child("m", "c1")

        parents = self.tree.get_parents("c1")

        self.assertEqual(len(parents), 2)
        parent_ids = [p.id for p in parents]
        self.assertIn("f", parent_ids)
        self.assertIn("m", parent_ids)

    def test_get_children(self):
        """자녀 조회 테스트."""
        self.tree.set_parent_child("f", "c1")
        self.tree.set_parent_child("f", "c2")

        children = self.tree.get_children("f")

        self.assertEqual(len(children), 2)
        child_ids = [c.id for c in children]
        self.assertIn("c1", child_ids)
        self.assertIn("c2", child_ids)

    def test_get_spouses(self):
        """배우자 조회 테스트."""
        self.tree.set_spouse("f", "m")

        father_spouses = self.tree.get_spouses("f")
        mother_spouses = self.tree.get_spouses("m")

        self.assertEqual(len(father_spouses), 1)
        self.assertEqual(father_spouses[0].id, "m")

        self.assertEqual(len(mother_spouses), 1)
        self.assertEqual(mother_spouses[0].id, "f")

    def test_get_siblings(self):
        """형제자매 조회 테스트."""
        self.tree.set_parent_child("f", "c1")
        self.tree.set_parent_child("f", "c2")
        self.tree.set_parent_child("m", "c1")
        self.tree.set_parent_child("m", "c2")

        c1_siblings = self.tree.get_siblings("c1")
        c2_siblings = self.tree.get_siblings("c2")

        self.assertEqual(len(c1_siblings), 1)
        self.assertEqual(c1_siblings[0].id, "c2")

        self.assertEqual(len(c2_siblings), 1)
        self.assertEqual(c2_siblings[0].id, "c1")

    def test_get_direct_family(self):
        """직계 가족 조회 테스트."""
        self.tree.set_spouse("f", "m")
        self.tree.set_parent_child("gf", "f")
        self.tree.set_parent_child("f", "c1")
        self.tree.set_parent_child("f", "c2")

        direct_family = self.tree.get_direct_family("f")
        direct_ids = {p.id for p in direct_family}

        # 부모(할아버지), 배우자, 자녀 2명
        self.assertIn("gf", direct_ids)
        self.assertIn("m", direct_ids)
        self.assertIn("c1", direct_ids)
        self.assertIn("c2", direct_ids)

    def test_remove_person_cleans_relationships(self):
        """사람 삭제 시 관계 정리 테스트."""
        self.tree.set_spouse("f", "m")
        self.tree.set_parent_child("f", "c1")

        # 아버지 삭제
        self.tree.remove_person("f")

        # 자녀의 부모 참조 제거 확인
        child = self.tree.get_person("c1")
        self.assertIsNone(child.father_id)

        # 배우자의 배우자 참조 제거 확인
        mother = self.tree.get_person("m")
        self.assertNotIn("f", mother.spouse_ids)


class TestGenerationCalculation(unittest.TestCase):
    """세대 계산 테스트."""

    def setUp(self):
        """3세대 가족 트리 생성."""
        self.tree = FamilyTree()

        # 1세대
        self.gf = Person(id="gf", name="할아버지", gender='M')
        self.gm = Person(id="gm", name="할머니", gender='F')

        # 2세대
        self.f = Person(id="f", name="아버지", gender='M')
        self.m = Person(id="m", name="어머니", gender='F')

        # 3세대
        self.c = Person(id="c", name="자녀", gender='M')

        for p in [self.gf, self.gm, self.f, self.m, self.c]:
            self.tree.add_person(p)

        # 관계 설정
        self.tree.set_spouse("gf", "gm")
        self.tree.set_parent_child("gf", "f")
        self.tree.set_parent_child("gm", "f")
        self.tree.set_spouse("f", "m")
        self.tree.set_parent_child("f", "c")
        self.tree.set_parent_child("m", "c")

    def test_calculate_generations(self):
        """세대 계산 테스트."""
        self.tree.calculate_generations()

        gf = self.tree.get_person("gf")
        gm = self.tree.get_person("gm")
        f = self.tree.get_person("f")
        m = self.tree.get_person("m")
        c = self.tree.get_person("c")

        # 조부모 세대
        self.assertEqual(gf.generation, 0)
        self.assertEqual(gm.generation, 0)

        # 부모 세대
        self.assertEqual(f.generation, 1)
        self.assertEqual(m.generation, 1)

        # 자녀 세대
        self.assertEqual(c.generation, 2)

    def test_get_persons_by_generation(self):
        """세대별 조회 테스트."""
        gen_dict = self.tree.get_persons_by_generation()

        self.assertIn(0, gen_dict)
        self.assertIn(1, gen_dict)
        self.assertIn(2, gen_dict)

        gen0_ids = {p.id for p in gen_dict[0]}
        gen1_ids = {p.id for p in gen_dict[1]}
        gen2_ids = {p.id for p in gen_dict[2]}

        self.assertEqual(gen0_ids, {"gf", "gm"})
        self.assertEqual(gen1_ids, {"f", "m"})
        self.assertEqual(gen2_ids, {"c"})


class TestFamilyTreeSerialization(unittest.TestCase):
    """FamilyTree 직렬화 테스트."""

    def test_to_dict(self):
        """딕셔너리 변환 테스트."""
        tree = FamilyTree()
        p1 = Person(id="p1", name="사람1")
        p2 = Person(id="p2", name="사람2")
        tree.add_person(p1)
        tree.add_person(p2)
        tree.set_spouse("p1", "p2")

        data = tree.to_dict()

        self.assertIn('persons', data)
        self.assertIn('relationships', data)
        self.assertEqual(len(data['persons']), 2)
        self.assertEqual(len(data['relationships']), 1)

    def test_from_dict(self):
        """딕셔너리에서 복원 테스트."""
        data = {
            'persons': [
                {'id': 'p1', 'name': '사람1', 'gender': 'M'},
                {'id': 'p2', 'name': '사람2', 'gender': 'F'}
            ],
            'relationships': [
                {
                    'id': 'r1',
                    'person1_id': 'p1',
                    'person2_id': 'p2',
                    'rel_type': 'spouse'
                }
            ]
        }

        tree = FamilyTree.from_dict(data)

        self.assertEqual(len(tree.get_all_persons()), 2)
        self.assertEqual(len(tree.get_all_relationships()), 1)

    def test_roundtrip(self):
        """직렬화 왕복 테스트."""
        original = FamilyTree()
        p1 = Person(id="p1", name="아버지", gender='M')
        p2 = Person(id="p2", name="어머니", gender='F')
        p3 = Person(id="p3", name="자녀", gender='M')

        original.add_person(p1)
        original.add_person(p2)
        original.add_person(p3)
        original.set_spouse("p1", "p2")
        original.set_parent_child("p1", "p3")
        original.set_parent_child("p2", "p3")

        # 직렬화 후 역직렬화
        data = original.to_dict()
        restored = FamilyTree.from_dict(data)

        # 검증
        self.assertEqual(len(restored.get_all_persons()), 3)

        child = restored.get_person("p3")
        self.assertEqual(child.father_id, "p1")
        self.assertEqual(child.mother_id, "p2")

    def test_clear(self):
        """전체 삭제 테스트."""
        tree = FamilyTree()
        tree.add_person(Person(name="테스트"))
        tree.clear()

        self.assertEqual(len(tree.get_all_persons()), 0)
        self.assertEqual(len(tree.get_all_relationships()), 0)
        self.assertFalse(tree.is_modified)


class TestCycleDetection(unittest.TestCase):
    """순환 관계 검증 테스트."""

    def setUp(self):
        """테스트용 트리 생성."""
        self.tree = FamilyTree()
        self.grandfather = Person(id="gf", name="할아버지", gender='M')
        self.father = Person(id="f", name="아버지", gender='M')
        self.child = Person(id="c", name="자녀", gender='M')

        for p in [self.grandfather, self.father, self.child]:
            self.tree.add_person(p)

        self.tree.set_parent_child("gf", "f")
        self.tree.set_parent_child("f", "c")

    def test_prevent_self_as_parent(self):
        """자기 자신을 부모로 설정 방지."""
        result = self.tree.set_parent_child("f", "f")
        self.assertIsNone(result)

    def test_prevent_child_as_parent(self):
        """자녀를 부모로 설정 방지 (순환)."""
        # c는 f의 자녀이므로 c를 f의 부모로 설정하면 안 됨
        result = self.tree.set_parent_child("c", "f")
        self.assertIsNone(result)

    def test_prevent_grandchild_as_ancestor(self):
        """손자를 조상으로 설정 방지."""
        result = self.tree.set_parent_child("c", "gf")
        self.assertIsNone(result)

    def test_valid_parent_child_allowed(self):
        """정상적인 부모-자녀 관계는 허용."""
        new_child = Person(id="c2", name="둘째", gender='F')
        self.tree.add_person(new_child)
        result = self.tree.set_parent_child("f", "c2")
        self.assertIsNotNone(result)


class TestMultipleSpouses(unittest.TestCase):
    """복수 배우자 테스트."""

    def setUp(self):
        """테스트용 트리 생성."""
        self.tree = FamilyTree()
        self.person = Person(id="p", name="본인", gender='M')
        self.spouse1 = Person(id="s1", name="배우자1", gender='F')
        self.spouse2 = Person(id="s2", name="배우자2", gender='F')

        for p in [self.person, self.spouse1, self.spouse2]:
            self.tree.add_person(p)

    def test_multiple_spouses(self):
        """여러 배우자 설정 테스트."""
        self.tree.set_spouse("p", "s1")
        self.tree.set_spouse("p", "s2")

        spouses = self.tree.get_spouses("p")
        self.assertEqual(len(spouses), 2)

        spouse_ids = {s.id for s in spouses}
        self.assertIn("s1", spouse_ids)
        self.assertIn("s2", spouse_ids)


class TestSpouseRelationshipQueries(unittest.TestCase):
    """배우자 관계 조회 테스트."""

    def setUp(self):
        """테스트용 트리 생성."""
        self.tree = FamilyTree()
        self.person = Person(id="p", name="본인", gender='M')
        self.spouse1 = Person(id="s1", name="첫째배우자", gender='F')
        self.spouse2 = Person(id="s2", name="둘째배우자", gender='F')

        for p in [self.person, self.spouse1, self.spouse2]:
            self.tree.add_person(p)

        # 첫 번째 배우자와 결혼 후 이혼
        rel1 = self.tree.set_spouse("p", "s1", marriage_year=2000)
        rel1.divorce_year = 2010

        # 두 번째 배우자와 결혼 (현재)
        self.tree.set_spouse("p", "s2", marriage_year=2015)

    def test_get_spouse_relationship(self):
        """특정 배우자와의 관계 조회."""
        rel = self.tree.get_spouse_relationship("p", "s1")
        self.assertIsNotNone(rel)
        self.assertEqual(rel.marriage_year, 2000)
        self.assertEqual(rel.divorce_year, 2010)

        # 역방향 조회도 동작
        rel2 = self.tree.get_spouse_relationship("s1", "p")
        self.assertEqual(rel.id, rel2.id)

        # 존재하지 않는 관계
        rel3 = self.tree.get_spouse_relationship("s1", "s2")
        self.assertIsNone(rel3)

    def test_get_spouse_relationships(self):
        """모든 배우자 관계 조회."""
        rels = self.tree.get_spouse_relationships("p")
        self.assertEqual(len(rels), 2)

    def test_get_current_spouse(self):
        """현재 배우자(이혼하지 않은) 조회."""
        current = self.tree.get_current_spouse("p")
        self.assertIsNotNone(current)
        self.assertEqual(current.id, "s2")
        self.assertEqual(current.name, "둘째배우자")

    def test_get_current_spouse_id(self):
        """현재 배우자 ID 조회."""
        current_id = self.tree.get_current_spouse_id("p")
        self.assertEqual(current_id, "s2")

    def test_no_current_spouse_all_divorced(self):
        """모두 이혼한 경우."""
        # 두 번째 배우자도 이혼 처리
        rel = self.tree.get_spouse_relationship("p", "s2")
        rel.divorce_year = 2020

        current = self.tree.get_current_spouse("p")
        self.assertIsNone(current)


class TestRelationship(unittest.TestCase):
    """Relationship 클래스 테스트."""

    def test_relationship_creation(self):
        """Relationship 생성 테스트."""
        from src.models.relationship import Relationship, RelationType

        rel = Relationship(
            person1_id="p1",
            person2_id="p2",
            rel_type=RelationType.SPOUSE,
            marriage_year=2020
        )

        self.assertEqual(rel.person1_id, "p1")
        self.assertEqual(rel.person2_id, "p2")
        self.assertEqual(rel.rel_type, RelationType.SPOUSE)
        self.assertEqual(rel.marriage_year, 2020)
        self.assertIsNotNone(rel.id)

    def test_is_divorced(self):
        """이혼 여부 테스트."""
        from src.models.relationship import Relationship, RelationType

        rel = Relationship("p1", "p2", RelationType.SPOUSE)
        self.assertFalse(rel.is_divorced)

        rel.divorce_year = 2023
        self.assertTrue(rel.is_divorced)

    def test_marriage_order_valid_without_dates(self):
        """결혼·이혼일 둘 다 없거나 한쪽만 있으면 True (검증 불가)."""
        from src.models.relationship import Relationship, RelationType
        rel = Relationship("p1", "p2", RelationType.SPOUSE)
        self.assertTrue(rel.is_valid_marriage_order())

        rel.marriage_year = 2020
        self.assertTrue(rel.is_valid_marriage_order())  # divorce 없음

        rel.marriage_year = None
        rel.divorce_year = 2020
        self.assertTrue(rel.is_valid_marriage_order())  # marriage 없음

    def test_marriage_before_divorce(self):
        from src.models.relationship import Relationship, RelationType
        rel = Relationship("p1", "p2", RelationType.SPOUSE,
                           marriage_year=2010, divorce_year=2020)
        self.assertTrue(rel.is_valid_marriage_order())

    def test_marriage_after_divorce_invalid(self):
        from src.models.relationship import Relationship, RelationType
        rel = Relationship("p1", "p2", RelationType.SPOUSE,
                           marriage_year=2020, divorce_year=2010)
        self.assertFalse(rel.is_valid_marriage_order())

    def test_same_year_month_day_comparison(self):
        from src.models.relationship import Relationship, RelationType
        rel_valid = Relationship("p1", "p2", RelationType.SPOUSE,
                                  marriage_year=2020, marriage_month=3, marriage_day=1,
                                  divorce_year=2020, divorce_month=8, divorce_day=15)
        self.assertTrue(rel_valid.is_valid_marriage_order())

        rel_invalid = Relationship("p1", "p2", RelationType.SPOUSE,
                                    marriage_year=2020, marriage_month=8, marriage_day=15,
                                    divorce_year=2020, divorce_month=3, divorce_day=1)
        self.assertFalse(rel_invalid.is_valid_marriage_order())

    def test_relationship_serialization(self):
        """Relationship 직렬화 테스트."""
        from src.models.relationship import Relationship, RelationType

        original = Relationship(
            id="rel-1",
            person1_id="p1",
            person2_id="p2",
            rel_type=RelationType.SPOUSE,
            marriage_year=2020,
            marriage_month=5,
            marriage_day=20,
            is_lunar_marriage=True,
            divorce_year=2023
        )

        data = original.to_dict()
        restored = Relationship.from_dict(data)

        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.person1_id, original.person1_id)
        self.assertEqual(restored.marriage_year, original.marriage_year)
        self.assertEqual(restored.is_lunar_marriage, original.is_lunar_marriage)
        self.assertEqual(restored.divorce_year, original.divorce_year)


class TestExtendedRelationships(unittest.TestCase):
    """확대 관계 쿼리 테스트 (3세대 가족 구성)."""

    def setUp(self):
        self.tree = FamilyTree()
        # 1세대: 조부모
        self.grandpa = Person(name="할아버지", gender="M")
        self.grandma = Person(name="할머니", gender="F")
        # 2세대: 부모 + 삼촌
        self.father = Person(name="아버지", gender="M")
        self.mother = Person(name="어머니", gender="F")
        self.uncle = Person(name="삼촌", gender="M")
        self.aunt_wife = Person(name="숙모", gender="F")  # 삼촌의 배우자
        # 3세대: 자녀 + 사촌
        self.child = Person(name="자녀", gender="M")
        self.cousin = Person(name="사촌", gender="F")

        for p in [self.grandpa, self.grandma, self.father, self.mother,
                  self.uncle, self.aunt_wife, self.child, self.cousin]:
            self.tree.add_person(p)

        # 관계 설정
        self.tree.set_spouse(self.grandpa.id, self.grandma.id)
        self.tree.set_parent_child(self.grandpa.id, self.father.id)
        self.tree.set_parent_child(self.grandma.id, self.father.id)
        self.tree.set_parent_child(self.grandpa.id, self.uncle.id)
        self.tree.set_parent_child(self.grandma.id, self.uncle.id)
        self.tree.set_spouse(self.father.id, self.mother.id)
        self.tree.set_spouse(self.uncle.id, self.aunt_wife.id)
        self.tree.set_parent_child(self.father.id, self.child.id)
        self.tree.set_parent_child(self.mother.id, self.child.id)
        self.tree.set_parent_child(self.uncle.id, self.cousin.id)
        self.tree.set_parent_child(self.aunt_wife.id, self.cousin.id)

    def test_get_grandparents(self):
        gps = self.tree.get_grandparents(self.child.id)
        gp_ids = {p.id for p in gps}
        self.assertEqual(gp_ids, {self.grandpa.id, self.grandma.id})

    def test_get_grandchildren(self):
        gcs = self.tree.get_grandchildren(self.grandpa.id)
        gc_ids = {p.id for p in gcs}
        self.assertIn(self.child.id, gc_ids)
        self.assertIn(self.cousin.id, gc_ids)

    def test_get_uncles_aunts(self):
        uas = self.tree.get_uncles_aunts(self.child.id)
        ua_ids = {p.id for p in uas}
        self.assertIn(self.uncle.id, ua_ids)

    def test_get_cousins(self):
        cousins = self.tree.get_cousins(self.child.id)
        cousin_ids = {p.id for p in cousins}
        self.assertIn(self.cousin.id, cousin_ids)

    def test_get_in_laws(self):
        # 어머니의 인척 = 아버지의 부모 (시부모)
        in_laws = self.tree.get_in_laws(self.mother.id)
        il_ids = {p.id for p in in_laws}
        self.assertIn(self.grandpa.id, il_ids)
        self.assertIn(self.grandma.id, il_ids)

    def test_empty_extended_relations(self):
        # 조부모는 확대 관계가 없어야 함 (더 위 세대 없음)
        gps = self.tree.get_grandparents(self.grandpa.id)
        self.assertEqual(len(gps), 0)
        cousins = self.tree.get_cousins(self.grandpa.id)
        self.assertEqual(len(cousins), 0)


class TestParentReplacement(unittest.TestCase):
    """다중 부모 교체 시 구 참조 정리 회귀 가드."""

    def setUp(self):
        self.tree = FamilyTree()
        self.old_father = Person(id="of", name="구父", gender="M")
        self.new_father = Person(id="nf", name="신父", gender="M")
        self.child = Person(id="c", name="자녀", gender="F")
        for p in (self.old_father, self.new_father, self.child):
            self.tree.add_person(p)
        self.tree.set_parent_child("of", "c")

    def test_replacing_father_clears_old_father_children_list(self):
        """구 아버지의 children_ids에서 자녀가 제거돼야 함."""
        self.tree.set_parent_child("nf", "c")
        self.assertEqual(self.tree.get_person("c").father_id, "nf")
        self.assertNotIn("c", self.tree.get_person("of").children_ids)
        self.assertIn("c", self.tree.get_person("nf").children_ids)
        relationships = self.tree.get_all_relationships()
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0].person1_id, "nf")
        self.assertEqual(relationships[0].person2_id, "c")


class TestDeleteMiddleNode(unittest.TestCase):
    """3세대 A→B→C 체인에서 중간 B 삭제 시 C의 참조 정리."""

    def test_delete_middle_clears_child_father_id(self):
        tree = FamilyTree()
        tree.add_person(Person(id="A", name="A", gender="M"))
        tree.add_person(Person(id="B", name="B", gender="M"))
        tree.add_person(Person(id="C", name="C", gender="M"))
        tree.set_parent_child("A", "B")
        tree.set_parent_child("B", "C")

        tree.remove_person("B")
        self.assertIsNone(tree.get_person("C").father_id)
        # A의 children_ids에서도 B 제거
        self.assertNotIn("B", tree.get_person("A").children_ids)


class TestCycleDetectionDepth(unittest.TestCase):
    """깊은 부모 체인에서 사이클 감지 동작 확인."""

    def test_deep_legitimate_chain_allowed(self):
        """30세대 깊이의 적법한 부모 체인 추가 가능."""
        tree = FamilyTree()
        person_ids = []
        for i in range(30):
            pid = f"gen{i}"
            tree.add_person(Person(id=pid, name=f"Gen{i}", gender="M"))
            person_ids.append(pid)

        for i, (parent_id, child_id) in enumerate(zip(person_ids, person_ids[1:]), start=1):
            rel = tree.set_parent_child(parent_id, child_id)
            self.assertIsNotNone(rel, f"Gen {i}에서 적법한 관계가 거부됨")

    def test_self_parent_blocked(self):
        tree = FamilyTree()
        tree.add_person(Person(id="x", name="X", gender="M"))
        rel = tree.set_parent_child("x", "x")
        self.assertIsNone(rel)


class TestSetParentChildNonExistent(unittest.TestCase):
    """존재하지 않는 인물 ID로 관계 설정 시 None 반환."""

    def test_returns_none_if_parent_missing(self):
        tree = FamilyTree()
        tree.add_person(Person(id="c", name="자"))
        rel = tree.set_parent_child("ghost", "c")
        self.assertIsNone(rel)

    def test_returns_none_if_child_missing(self):
        tree = FamilyTree()
        tree.add_person(Person(id="p", name="부"))
        rel = tree.set_parent_child("p", "ghost")
        self.assertIsNone(rel)


class TestRemoveRelationshipBidirectionalScenarios(unittest.TestCase):
    """remove_relationship 양방향 정리의 추가 시나리오."""

    def test_remove_one_spouse_keeps_others(self):
        """여러 배우자 중 한 명만 제거되는 케이스."""
        tree = FamilyTree()
        tree.add_person(Person(id="h", name="남편", gender="M"))
        tree.add_person(Person(id="w1", name="첫아내", gender="F"))
        tree.add_person(Person(id="w2", name="둘째아내", gender="F"))
        rel1 = tree.set_spouse("h", "w1")
        rel2 = tree.set_spouse("h", "w2")

        # 첫째와의 관계만 삭제
        tree.remove_relationship(rel1.id)

        husband = tree.get_person("h")
        self.assertNotIn("w1", husband.spouse_ids)
        self.assertIn("w2", husband.spouse_ids)  # 둘째는 유지
        self.assertNotIn("h", tree.get_person("w1").spouse_ids)
        self.assertIn("h", tree.get_person("w2").spouse_ids)

    def test_remove_nonexistent_rel_is_noop(self):
        tree = FamilyTree()
        tree.add_person(Person(id="p", name="P", gender="M"))
        # 예외 없이 조용히 통과해야 함
        tree.remove_relationship("nonexistent-id")
        self.assertEqual(len(tree.get_all_relationships()), 0)
        self.assertIsNotNone(tree.get_person("p"))


if __name__ == '__main__':
    unittest.main()
