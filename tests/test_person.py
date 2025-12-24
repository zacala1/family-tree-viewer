"""Person 모델 유닛 테스트."""
import unittest
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.person import Person


class TestPerson(unittest.TestCase):
    """Person 클래스 테스트."""

    def test_create_person_default(self):
        """기본값으로 Person 생성 테스트."""
        person = Person()

        self.assertIsNotNone(person.id)
        self.assertEqual(person.name, "")
        self.assertEqual(person.gender, 'M')
        self.assertIsNone(person.birth_year)
        self.assertFalse(person.is_lunar_birth)
        self.assertEqual(person.spouse_ids, [])
        self.assertEqual(person.children_ids, [])

    def test_create_person_with_values(self):
        """값을 지정하여 Person 생성 테스트."""
        person = Person(
            id="test-id",
            name="홍길동",
            gender='M',
            birth_year=1990,
            birth_month=5,
            birth_day=15,
            is_lunar_birth=True,
            occupation="개발자"
        )

        self.assertEqual(person.id, "test-id")
        self.assertEqual(person.name, "홍길동")
        self.assertEqual(person.gender, 'M')
        self.assertEqual(person.birth_year, 1990)
        self.assertEqual(person.birth_month, 5)
        self.assertEqual(person.birth_day, 15)
        self.assertTrue(person.is_lunar_birth)
        self.assertEqual(person.occupation, "개발자")

    def test_birth_date_str(self):
        """생년월일 문자열 테스트."""
        # 전체 날짜
        person = Person(birth_year=1990, birth_month=5, birth_day=15)
        self.assertEqual(person.birth_date_str, "1990.05.15")

        # 음력
        person.is_lunar_birth = True
        self.assertEqual(person.birth_date_str, "1990.05.15 (음력)")

        # 연도만
        person2 = Person(birth_year=1990)
        self.assertEqual(person2.birth_date_str, "1990")

        # 없음
        person3 = Person()
        self.assertEqual(person3.birth_date_str, "")

    def test_death_date_str(self):
        """사망일 문자열 테스트."""
        person = Person(death_year=2020, death_month=12, death_day=25)
        self.assertEqual(person.death_date_str, "2020.12.25")

        person.is_lunar_death = True
        self.assertEqual(person.death_date_str, "2020.12.25 (음력)")

    def test_lifespan_str(self):
        """생몰년 문자열 테스트."""
        # 생존
        person = Person(birth_year=1990)
        self.assertEqual(person.lifespan_str, "1990 -")

        # 사망
        person.death_year = 2020
        self.assertEqual(person.lifespan_str, "1990 - 2020")

        # 생년 없음
        person2 = Person()
        self.assertEqual(person2.lifespan_str, "")

    def test_is_alive(self):
        """생존 여부 테스트."""
        person = Person(birth_year=1990)
        self.assertTrue(person.is_alive)

        person.death_year = 2020
        self.assertFalse(person.is_alive)

    def test_get_direct_family_ids(self):
        """직계 가족 ID 목록 테스트."""
        person = Person(
            father_id="father-1",
            mother_id="mother-1",
            spouse_ids=["spouse-1", "spouse-2"],
            children_ids=["child-1", "child-2", "child-3"]
        )

        family_ids = person.get_direct_family_ids()

        self.assertIn("father-1", family_ids)
        self.assertIn("mother-1", family_ids)
        self.assertIn("spouse-1", family_ids)
        self.assertIn("spouse-2", family_ids)
        self.assertIn("child-1", family_ids)
        self.assertIn("child-2", family_ids)
        self.assertIn("child-3", family_ids)
        self.assertEqual(len(family_ids), 7)

    def test_to_dict(self):
        """딕셔너리 변환 테스트."""
        person = Person(
            id="test-id",
            name="테스트",
            gender='F',
            birth_year=1985,
            is_lunar_birth=True
        )

        data = person.to_dict()

        self.assertEqual(data['id'], "test-id")
        self.assertEqual(data['name'], "테스트")
        self.assertEqual(data['gender'], 'F')
        self.assertEqual(data['birth_year'], 1985)
        self.assertTrue(data['is_lunar_birth'])

    def test_from_dict(self):
        """딕셔너리에서 생성 테스트."""
        data = {
            'id': 'dict-id',
            'name': '김철수',
            'gender': 'M',
            'birth_year': 1970,
            'birth_month': 3,
            'birth_day': 20,
            'is_lunar_birth': False,
            'occupation': '교수',
            'spouse_ids': ['spouse-1'],
            'children_ids': ['child-1', 'child-2']
        }

        person = Person.from_dict(data)

        self.assertEqual(person.id, 'dict-id')
        self.assertEqual(person.name, '김철수')
        self.assertEqual(person.gender, 'M')
        self.assertEqual(person.birth_year, 1970)
        self.assertEqual(person.occupation, '교수')
        self.assertEqual(len(person.spouse_ids), 1)
        self.assertEqual(len(person.children_ids), 2)

    def test_from_dict_missing_fields(self):
        """누락된 필드가 있는 딕셔너리에서 생성 테스트."""
        data = {
            'name': '최소정보'
        }

        person = Person.from_dict(data)

        self.assertEqual(person.name, '최소정보')
        self.assertEqual(person.gender, 'M')  # 기본값
        self.assertIsNone(person.birth_year)
        self.assertEqual(person.spouse_ids, [])

    def test_unique_id_generation(self):
        """고유 ID 자동 생성 테스트."""
        person1 = Person(name="Person 1")
        person2 = Person(name="Person 2")

        self.assertNotEqual(person1.id, person2.id)


class TestPersonSerialization(unittest.TestCase):
    """Person 직렬화 테스트."""

    def test_roundtrip(self):
        """직렬화 후 역직렬화 일관성 테스트."""
        original = Person(
            name="원본",
            gender='F',
            birth_year=1980,
            birth_month=6,
            birth_day=10,
            is_lunar_birth=True,
            death_year=2050,
            birth_place="서울",
            occupation="의사",
            education="서울대학교",
            phone="010-1234-5678",
            email="test@test.com",
            notes="메모입니다",
            father_id="father-id",
            mother_id="mother-id",
            spouse_ids=["spouse-1"],
            children_ids=["child-1"],
            generation=2
        )

        # 직렬화 후 역직렬화
        data = original.to_dict()
        restored = Person.from_dict(data)

        # 모든 필드 검증
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.gender, original.gender)
        self.assertEqual(restored.birth_year, original.birth_year)
        self.assertEqual(restored.birth_month, original.birth_month)
        self.assertEqual(restored.birth_day, original.birth_day)
        self.assertEqual(restored.is_lunar_birth, original.is_lunar_birth)
        self.assertEqual(restored.death_year, original.death_year)
        self.assertEqual(restored.birth_place, original.birth_place)
        self.assertEqual(restored.occupation, original.occupation)
        self.assertEqual(restored.education, original.education)
        self.assertEqual(restored.phone, original.phone)
        self.assertEqual(restored.email, original.email)
        self.assertEqual(restored.notes, original.notes)
        self.assertEqual(restored.father_id, original.father_id)
        self.assertEqual(restored.mother_id, original.mother_id)
        self.assertEqual(restored.spouse_ids, original.spouse_ids)
        self.assertEqual(restored.children_ids, original.children_ids)
        self.assertEqual(restored.generation, original.generation)


if __name__ == '__main__':
    unittest.main()
