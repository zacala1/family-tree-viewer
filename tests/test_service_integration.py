"""Service layer가 main_window에 실제 통합됐는지 + 신규 메서드 회귀 가드."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.repositories.person_repository import PersonRepository
from src.repositories.relationship_repository import RelationshipRepository
from src.services.family_tree_service import FamilyTreeService


@pytest.fixture
def service(empty_tree):
    return FamilyTreeService(
        PersonRepository(empty_tree),
        RelationshipRepository(empty_tree),
    )


class TestServiceWiredInMainWindow:
    """MainWindow가 Service 인스턴스를 실제 보유하는지."""

    def test_main_window_exposes_service(self, qapp):
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            assert win.service is not None
            assert isinstance(win.service, FamilyTreeService)
            # repository도 노출 (test 또는 향후 직접 호출용)
            assert win._person_repo is not None
            assert win._rel_repo is not None
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()

    def test_service_uses_main_window_tree(self, qapp):
        """Service가 main_window의 family_tree를 가리키는지."""
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            win.family_tree.add_person(Person(id="p1", name="홍길동"))
            # Service는 동일 트리를 통해 동일 인물 보임
            assert win.service.get_person("p1") is not None
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()


class TestRebuildServiceForTree:
    """트리 교체 시 service가 재생성되는지 — stale 참조 방지."""

    def test_load_tree_rebuilds_service(self, qapp):
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            original_service = win.service
            new_tree = FamilyTree()
            new_tree.add_person(Person(id="newp", name="새사람"))
            win.load_tree(new_tree)

            # service가 새로 생성됐어야 (identity check)
            assert win.service is not original_service
            # 새 트리의 데이터가 service를 통해 조회됨
            assert win.service.get_person("newp") is not None
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()

    def test_on_new_rebuilds_service(self, qapp):
        from src.views.main_window import MainWindow
        win = MainWindow()
        try:
            win.family_tree.add_person(Person(id="old", name="old"))
            win.family_tree.mark_saved()  # _check_save가 modal 안 띄우게
            original_service = win.service
            win.file_io.new_tree()
            # 새 트리 → 새 service → "old" 인물 없음
            assert win.service is not original_service
            assert win.service.get_person("old") is None
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()


class TestNewServiceMethods:
    """신규 추가된 service 메서드들 회귀 가드."""

    def test_remove_relationship_success(self, service, empty_tree):
        empty_tree.add_person(Person(id="h", name="남편"))
        empty_tree.add_person(Person(id="w", name="아내"))
        rel = empty_tree.set_spouse("h", "w")
        ok, err = service.remove_relationship(rel.id)
        assert ok
        # 양방향 정리 확인
        assert "w" not in empty_tree.get_person("h").spouse_ids

    def test_get_spouse_relationship(self, service, empty_tree):
        empty_tree.add_person(Person(id="h", name="h"))
        empty_tree.add_person(Person(id="w", name="w"))
        empty_tree.set_spouse("h", "w")
        rel = service.get_spouse_relationship("h", "w")
        assert rel is not None

    def test_find_relationships_by_person(self, service, sample_family):
        tree, ids = sample_family
        svc = FamilyTreeService(PersonRepository(tree), RelationshipRepository(tree))
        rels = svc.find_relationships_by_person(ids["father"])
        # 부 → 2 부모 + 1 배우자 + 2 자녀 = 5
        assert len(rels) == 5

    def test_get_direct_family_ids(self, service, sample_family):
        tree, ids = sample_family
        svc = FamilyTreeService(PersonRepository(tree), RelationshipRepository(tree))
        family = svc.get_direct_family_ids(ids["child1"])
        # 부모, 형제 등 포함
        assert isinstance(family, set)
        assert ids["father"] in family or ids["mother"] in family

    def test_person_count_property(self, service):
        assert service.person_count == 0
        from src.models.person import Person as P
        # service에는 add_person이 있지만, repo를 직접 쓰는 테스트
        service.add_person(P(id="p1", name="A"))
        assert service.person_count == 1

    def test_relationship_count_property(self, service):
        from src.models.person import Person as P
        service.add_person(P(id="h", name="H"))
        service.add_person(P(id="w", name="W"))
        service.add_spouse_relationship("h", "w")
        assert service.relationship_count == 1


class TestServiceFlowsThroughViews:
    """기존 family_tree 직접 호출과 동등한 결과를 service가 보장."""

    def test_add_person_through_service_visible_in_tree(self, qapp):
        from src.views.main_window import MainWindow
        from src.models.person import Person as P
        win = MainWindow()
        try:
            ok, err = win.service.add_person(P(id="via_svc", name="서비스경유"))
            assert ok
            # main_window의 family_tree에서도 보여야
            assert win.family_tree.get_person("via_svc") is not None
        finally:
            win.family_tree.mark_saved()
            win.close()
            win.deleteLater()
