"""PdfExporter 유닛 테스트.

실제 PDF 생성은 QtPrintSupport에 위임하므로 핵심 단위 테스트는:
- is_available 동작
- 빈 캔버스 (no nodes) 처리
- _get_bounding_rect 의 union·여백 계산
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import QRectF

from src.utils.pdf_exporter import PdfExporter, HAS_PRINT_SUPPORT


class _FakeCanvas:
    """_get_bounding_rect / export 테스트용 최소 캔버스 스텁."""

    def __init__(self, rects):
        # node_id → QRectF
        self._node_rects = rects


class TestIsAvailable:
    def test_returns_bool(self):
        # 환경에 따라 True/False 둘 다 가능 — 타입만 보장
        result = PdfExporter.is_available()
        assert isinstance(result, bool)

    def test_matches_module_flag(self):
        assert PdfExporter.is_available() == HAS_PRINT_SUPPORT


class TestGetBoundingRect:
    def test_empty_canvas_returns_empty_rect(self):
        canvas = _FakeCanvas({})
        bounding = PdfExporter._get_bounding_rect(canvas)
        assert bounding.isEmpty()

    def test_single_rect_includes_margin(self):
        rect = QRectF(0, 0, 100, 50)
        canvas = _FakeCanvas({"a": rect})
        bounding = PdfExporter._get_bounding_rect(canvas)
        # 마진 30 추가됨 → 좌상단은 -30, 폭은 100+60=160
        assert bounding.x() == -30
        assert bounding.y() == -30
        assert bounding.width() == 160
        assert bounding.height() == 110

    def test_multiple_rects_united(self):
        canvas = _FakeCanvas({
            "a": QRectF(0, 0, 100, 100),
            "b": QRectF(200, 100, 50, 50),
        })
        bounding = PdfExporter._get_bounding_rect(canvas)
        # union: (0,0)~(250,150) + margin 30 → (-30,-30)~(280,180)
        assert bounding.x() == -30
        assert bounding.y() == -30
        assert bounding.width() == 310
        assert bounding.height() == 210


@pytest.mark.skipif(not HAS_PRINT_SUPPORT, reason="QtPrintSupport unavailable")
class TestExportEdgeCases:
    def test_empty_canvas_returns_false(self, tmp_path):
        canvas = _FakeCanvas({})
        out_path = str(tmp_path / "out.pdf")
        # 빈 바운딩 박스 → 조용히 실패해야 함
        result = PdfExporter.export(canvas, out_path)
        assert result is False
        # 빈 경우 파일도 생성되면 안 됨 (또는 즉시 정리)
        # QtPrintSupport가 파일 생성 후 abort할 수 있어 존재 여부는 강제하지 않음
