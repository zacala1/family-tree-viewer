"""Shared test fixtures."""

import os
import tempfile
import pytest
from PyQt6.QtWidgets import QApplication

from src.models.person import Person
from src.models.family_tree import FamilyTree


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure QApplication instance exists for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _suppress_welcome_dialog(qapp):
    """MainWindow가 첫 실행 환영 다이얼로그를 modal로 띄워 테스트가 hang하는 것을 방지.

    test_welcome_dialog.py는 자체 isolated_settings에서 별도 application name으로
    격리되므로 이 fixture의 영향을 받지 않음.
    """
    from PyQt6.QtCore import QSettings
    s = QSettings("FamilyTree", "FamilyTree")
    prev = s.value("welcomeDismissed", False, type=bool)
    s.setValue("welcomeDismissed", True)
    yield
    s.setValue("welcomeDismissed", prev)


@pytest.fixture
def empty_tree():
    """완전히 비어있는 FamilyTree 인스턴스."""
    return FamilyTree()


@pytest.fixture
def sample_family():
    """3세대 미니 가족 트리 (조부+조모, 부+모, 자녀 2명) 반환.

    Returns:
        (tree, ids) — ids는 dict 형태: {gf, gm, father, mother, child1, child2}
    """
    tree = FamilyTree()
    gf = Person(id="gf", name="할아버지", gender="M", birth_year=1940)
    gm = Person(id="gm", name="할머니", gender="F", birth_year=1942)
    father = Person(id="father", name="아버지", gender="M", birth_year=1965)
    mother = Person(id="mother", name="어머니", gender="F", birth_year=1967)
    child1 = Person(id="child1", name="첫째", gender="F", birth_year=1990)
    child2 = Person(id="child2", name="둘째", gender="M", birth_year=1993)

    for p in (gf, gm, father, mother, child1, child2):
        tree.add_person(p)

    # 조부모 - 부 결혼, 부모 - 자녀 결혼
    tree.set_spouse("gf", "gm")
    tree.set_spouse("father", "mother")

    # 부모-자녀 관계
    tree.set_parent_child("gf", "father")
    tree.set_parent_child("gm", "father")
    tree.set_parent_child("father", "child1")
    tree.set_parent_child("mother", "child1")
    tree.set_parent_child("father", "child2")
    tree.set_parent_child("mother", "child2")

    return tree, {
        "gf": "gf",
        "gm": "gm",
        "father": "father",
        "mother": "mother",
        "child1": "child1",
        "child2": "child2",
    }


@pytest.fixture
def tmp_json_path():
    """임시 JSON 파일 경로 (테스트 종료 후 자동 삭제)."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)  # 핸들러가 직접 생성하도록 빈 상태로 시작
    yield path
    # 정리 — 핸들러가 .backup 파일도 만들 수 있으니 함께 정리
    for cleanup_path in (path, path + ".backup"):
        try:
            if os.path.exists(cleanup_path):
                os.unlink(cleanup_path)
        except OSError:
            pass


@pytest.fixture
def tmp_excel_path():
    """임시 Excel 파일 경로 (테스트 종료 후 자동 삭제)."""
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    os.unlink(path)
    yield path
    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass
