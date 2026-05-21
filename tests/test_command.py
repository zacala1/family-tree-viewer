"""Command 패턴 (Undo/Redo) 유닛 테스트.

회귀 방지 대상:
- DeletePersonCommand.undo()의 RLock 보호
- SetSpouseCommand 신규 추가
- RemoveRelationshipCommand 신규 추가
- AddRelationshipCommand undo와 family_tree.remove_relationship 양방향 정리 통합
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.models.command import (
    UndoRedoManager,
    AddPersonCommand,
    DeletePersonCommand,
    UpdatePersonCommand,
    AddRelationshipCommand,
    SetSpouseCommand,
    RemoveRelationshipCommand,
)


class TestAddPersonCommand(unittest.TestCase):
    def setUp(self):
        self.tree = FamilyTree()
        self.manager = UndoRedoManager()

    def test_execute_then_undo_restores_empty(self):
        person = Person(name="홍길동")
        self.manager.execute(AddPersonCommand(self.tree, person))
        self.assertEqual(len(self.tree.get_all_persons()), 1)
        self.manager.undo()
        self.assertEqual(len(self.tree.get_all_persons()), 0)

    def test_redo_re_adds_person(self):
        person = Person(name="홍길동")
        self.manager.execute(AddPersonCommand(self.tree, person))
        self.manager.undo()
        self.manager.redo()
        self.assertEqual(len(self.tree.get_all_persons()), 1)


class TestDeletePersonCommand(unittest.TestCase):
    def setUp(self):
        self.tree = FamilyTree()
        self.manager = UndoRedoManager()

    def test_undo_restores_person_and_relationships(self):
        father = Person(id="f1", name="아버지", gender="M")
        child = Person(id="c1", name="자녀", gender="F")
        self.tree.add_person(father)
        self.tree.add_person(child)
        self.tree.set_parent_child("f1", "c1")

        # 부모-자녀 관계가 있는 상태에서 부모 삭제
        self.manager.execute(DeletePersonCommand(self.tree, "f1"))
        self.assertIsNone(self.tree.get_person("f1"))
        # 자녀의 father_id가 정리됐는지
        self.assertIsNone(self.tree.get_person("c1").father_id)

        # Undo 시 부모와 관계가 모두 복원
        self.manager.undo()
        self.assertIsNotNone(self.tree.get_person("f1"))
        restored_child = self.tree.get_person("c1")
        self.assertEqual(restored_child.father_id, "f1")
        father_restored = self.tree.get_person("f1")
        self.assertIn("c1", father_restored.children_ids)

    def test_undo_under_lock_does_not_deadlock(self):
        """RLock 보호 추가 후에도 재진입 안전 확인."""
        person = Person(id="p1", name="테스트")
        self.tree.add_person(person)
        cmd = DeletePersonCommand(self.tree, "p1")
        self.manager.execute(cmd)
        self.manager.undo()  # 데드락 없이 통과해야 함
        self.assertIsNotNone(self.tree.get_person("p1"))


class TestAddRelationshipCommandUndo(unittest.TestCase):
    def setUp(self):
        self.tree = FamilyTree()
        self.manager = UndoRedoManager()
        self.father = Person(id="f1", name="아버지", gender="M")
        self.child = Person(id="c1", name="자녀", gender="F")
        self.tree.add_person(self.father)
        self.tree.add_person(self.child)

    def test_undo_cleans_bidirectional_refs(self):
        self.manager.execute(AddRelationshipCommand(self.tree, "f1", "c1"))
        self.assertEqual(self.tree.get_person("c1").father_id, "f1")
        self.assertIn("c1", self.tree.get_person("f1").children_ids)

        self.manager.undo()
        # 양방향 정리 확인
        self.assertIsNone(self.tree.get_person("c1").father_id)
        self.assertNotIn("c1", self.tree.get_person("f1").children_ids)

    def test_undo_restores_previous_parent(self):
        old_father = Person(id="of", name="이전아버지", gender="M")
        self.tree.add_person(old_father)
        self.tree.set_parent_child("of", "c1")
        # 새 아버지로 교체
        self.manager.execute(AddRelationshipCommand(self.tree, "f1", "c1"))
        self.assertEqual(self.tree.get_person("c1").father_id, "f1")
        # Undo 시 이전 아버지로 복원
        self.manager.undo()
        self.assertEqual(self.tree.get_person("c1").father_id, "of")
        self.assertIn("c1", self.tree.get_person("of").children_ids)


class TestSetSpouseCommand(unittest.TestCase):
    def setUp(self):
        self.tree = FamilyTree()
        self.manager = UndoRedoManager()
        self.husband = Person(id="h1", name="남편", gender="M")
        self.wife = Person(id="w1", name="아내", gender="F")
        self.tree.add_person(self.husband)
        self.tree.add_person(self.wife)

    def test_execute_creates_spouse_relationship(self):
        self.manager.execute(SetSpouseCommand(self.tree, "h1", "w1"))
        h = self.tree.get_person("h1")
        w = self.tree.get_person("w1")
        self.assertIn("w1", h.spouse_ids)
        self.assertIn("h1", w.spouse_ids)
        self.assertEqual(len(self.tree.get_all_relationships()), 1)

    def test_undo_removes_spouse_bidirectionally(self):
        self.manager.execute(SetSpouseCommand(self.tree, "h1", "w1"))
        self.manager.undo()
        h = self.tree.get_person("h1")
        w = self.tree.get_person("w1")
        self.assertNotIn("w1", h.spouse_ids)
        self.assertNotIn("h1", w.spouse_ids)
        self.assertEqual(len(self.tree.get_all_relationships()), 0)

    def test_redo_re_creates_spouse(self):
        self.manager.execute(SetSpouseCommand(self.tree, "h1", "w1"))
        self.manager.undo()
        self.manager.redo()
        h = self.tree.get_person("h1")
        self.assertIn("w1", h.spouse_ids)


class TestRemoveRelationshipCommand(unittest.TestCase):
    def setUp(self):
        self.tree = FamilyTree()
        self.manager = UndoRedoManager()
        self.father = Person(id="f1", name="아버지", gender="M")
        self.child = Person(id="c1", name="자녀", gender="F")
        self.tree.add_person(self.father)
        self.tree.add_person(self.child)
        self.rel = self.tree.set_parent_child("f1", "c1")

    def test_execute_removes_relationship_and_undo_restores(self):
        self.assertIsNotNone(self.rel)
        self.manager.execute(RemoveRelationshipCommand(self.tree, self.rel.id))
        # 양방향 정리 확인
        self.assertIsNone(self.tree.get_person("c1").father_id)
        self.assertNotIn("c1", self.tree.get_person("f1").children_ids)

        # Undo 복원
        self.manager.undo()
        self.assertEqual(self.tree.get_person("c1").father_id, "f1")
        self.assertIn("c1", self.tree.get_person("f1").children_ids)


class TestRemoveRelationshipBidirectional(unittest.TestCase):
    """family_tree.remove_relationship 자체의 양방향 정리 동작 회귀 방지."""

    def test_spouse_removal_cleans_both_sides(self):
        tree = FamilyTree()
        h = Person(id="h1", name="남편", gender="M")
        w = Person(id="w1", name="아내", gender="F")
        tree.add_person(h)
        tree.add_person(w)
        rel = tree.set_spouse("h1", "w1")
        self.assertIsNotNone(rel)

        tree.remove_relationship(rel.id)
        self.assertNotIn("w1", tree.get_person("h1").spouse_ids)
        self.assertNotIn("h1", tree.get_person("w1").spouse_ids)

    def test_parent_child_removal_cleans_both_sides(self):
        tree = FamilyTree()
        f = Person(id="f1", name="아버지", gender="M")
        c = Person(id="c1", name="자녀", gender="F")
        tree.add_person(f)
        tree.add_person(c)
        rel = tree.set_parent_child("f1", "c1")

        tree.remove_relationship(rel.id)
        self.assertIsNone(tree.get_person("c1").father_id)
        self.assertNotIn("c1", tree.get_person("f1").children_ids)


if __name__ == "__main__":
    unittest.main()
