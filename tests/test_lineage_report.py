"""LineageReportDialog 깊이 제한·순환 방지 회귀 가드.

매우 깊은 선형 계보가 Python 재귀 한계(~1000)에 닿기 전에 안전하게 truncate되는지 검증.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.models.person import Person
from src.models.family_tree import FamilyTree
from src.config import MAX_REPORT_DEPTH


@pytest.fixture
def deep_chain_tree(qapp):
    """150세대 선형 부모 체인 트리 생성 (MAX_REPORT_DEPTH=100 초과)."""
    tree = FamilyTree()
    prev_id = None
    for i in range(150):
        pid = f"gen{i}"
        tree.add_person(Person(id=pid, name=f"Gen{i}", gender="M"))
        if prev_id is not None:
            tree.set_parent_child(prev_id, pid)
        prev_id = pid
    return tree


class TestRecursionDepthGuard:
    def test_descendants_truncated_at_max_depth(self, deep_chain_tree):
        from src.views.lineage_report_dialog import LineageReportDialog
        dlg = LineageReportDialog(deep_chain_tree, "gen0", mode="descendants")
        text = dlg.text_edit.toPlainText()
        # truncated 메시지가 포함돼야 함
        assert "truncated" in text.lower() or "생략" in text
        # 깊이가 100을 넘지 않아야 — Gen100 이후는 표시 안 됨
        assert "Gen0" in text
        assert "Gen99" in text
        assert "Gen149" not in text
        dlg.deleteLater()

    def test_ancestors_truncated_at_max_depth(self, deep_chain_tree):
        from src.views.lineage_report_dialog import LineageReportDialog
        dlg = LineageReportDialog(deep_chain_tree, "gen149", mode="ancestors")
        text = dlg.text_edit.toPlainText()
        assert "truncated" in text.lower() or "생략" in text
        assert "Gen149" in text
        assert "Gen0" not in text  # 100세대 위는 잘림
        dlg.deleteLater()

    def test_shallow_tree_no_truncation(self, qapp, sample_family):
        """3세대 트리에서는 truncation 메시지가 없어야 함."""
        from src.views.lineage_report_dialog import LineageReportDialog
        tree, ids = sample_family
        dlg = LineageReportDialog(tree, ids["gf"], mode="descendants")
        text = dlg.text_edit.toPlainText()
        assert "truncated" not in text.lower()
        assert "생략" not in text
        assert "할아버지" in text
        dlg.deleteLater()

    def test_max_depth_is_safe_below_python_limit(self):
        """MAX_REPORT_DEPTH가 Python 기본 recursion limit보다 충분히 작은지."""
        # Python default ~1000. MAX_REPORT_DEPTH가 그보다 훨씬 작아야 안전
        assert MAX_REPORT_DEPTH < sys.getrecursionlimit() // 2

    def test_no_stack_overflow_at_200_generations(self, qapp):
        """MAX_REPORT_DEPTH(100)의 2배에서도 truncation 덕에 크래시 없이 처리.

        200세대는 MAX_REPORT_DEPTH를 명백히 초과하는 충분한 회귀 가드. 더 큰
        값은 트리 setup 자체가 set_parent_child의 cycle detection 때문에
        O(N²)로 매우 느림 — 가드 효과는 동일.
        """
        tree = FamilyTree()
        prev_id = None
        for i in range(200):
            pid = f"x{i}"
            tree.add_person(Person(id=pid, name=f"X{i}"))
            if prev_id is not None:
                tree.set_parent_child(prev_id, pid)
            prev_id = pid

        from src.views.lineage_report_dialog import LineageReportDialog
        # 예외 없이 통과해야 함 (이전에는 RecursionError 가능)
        dlg = LineageReportDialog(tree, "x0", mode="descendants")
        assert dlg.text_edit.toPlainText() != ""
        dlg.deleteLater()


class TestI18nKeysExist:
    """누락됐던 i18n 키들이 이제 두 파일에 모두 정의되는지."""

    def test_keys_resolve_without_fallback(self):
        import json
        i18n_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "i18n",
        )
        with open(os.path.join(i18n_dir, "en.json"), encoding="utf-8") as f:
            en = json.load(f)
        with open(os.path.join(i18n_dir, "ko.json"), encoding="utf-8") as f:
            ko = json.load(f)

        # 두 파일 모두에 존재해야 하는 키들
        required = [
            ("button", "close"),
            ("dialog", "save_failed_continue"),
            ("error", "file_not_found_title"),
            ("error", "file_not_found_message"),
            ("error", "operation_failed"),
            ("error", "validation_title"),
            ("error", "person_not_found"),
            ("error", "day_without_month"),
            ("error", "invalid_date_combination"),
            ("report", "truncated_too_deep"),
        ]
        for section, key in required:
            assert key in en.get(section, {}), f"en.json missing {section}.{key}"
            assert key in ko.get(section, {}), f"ko.json missing {section}.{key}"
