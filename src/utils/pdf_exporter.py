"""PDF 내보내기 유틸리티."""

from typing import TYPE_CHECKING

try:
    from PyQt6.QtPrintSupport import QPrinter
    from PyQt6.QtCore import QRectF, QMarginsF, Qt
    from PyQt6.QtGui import QPainter

    HAS_PRINT_SUPPORT = True
except ImportError:
    HAS_PRINT_SUPPORT = False

if TYPE_CHECKING:
    from ..views.tree_canvas import TreeCanvas


class PdfExporter:
    """가계도를 PDF로 내보내기."""

    @staticmethod
    def is_available() -> bool:
        """PDF 내보내기 가능 여부."""
        return HAS_PRINT_SUPPORT

    @staticmethod
    def export(canvas: "TreeCanvas", file_path: str, landscape: bool = True) -> bool:
        """캔버스를 PDF로 내보내기.

        Args:
            canvas: TreeCanvas 인스턴스
            file_path: 저장할 PDF 경로
            landscape: 가로 방향 여부

        Returns:
            성공 여부
        """
        if not HAS_PRINT_SUPPORT:
            return False

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)

            if landscape:
                from PyQt6.QtGui import QPageLayout
                printer.setPageOrientation(QPageLayout.Orientation.Landscape)

            # 여백 설정
            printer.setPageMargins(QMarginsF(15, 15, 15, 15), QPrinter.Unit.Millimeter)

            # 바운딩박스 계산
            bounding = PdfExporter._get_bounding_rect(canvas)
            if bounding.isEmpty():
                return False

            # 페이지 영역
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)

            # 스케일 계산 (페이지에 맞추기)
            scale_x = page_rect.width() / bounding.width()
            scale_y = page_rect.height() / bounding.height()
            scale = min(scale_x, scale_y, 3.0)  # 최대 3배

            painter = QPainter()
            if not painter.begin(printer):
                return False

            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                # 중앙 정렬
                offset_x = (page_rect.width() - bounding.width() * scale) / 2
                offset_y = (page_rect.height() - bounding.height() * scale) / 2

                painter.translate(offset_x, offset_y)
                painter.scale(scale, scale)
                painter.translate(-bounding.x(), -bounding.y())

                # 캔버스의 그리기 메서드 직접 호출
                canvas._draw_connections(painter)
                canvas._draw_nodes(painter)
            finally:
                painter.end()

            return True

        except Exception:
            from .logger import error
            import traceback
            error(f"PDF export error: {traceback.format_exc()}")
            return False

    @staticmethod
    def _get_bounding_rect(canvas: "TreeCanvas") -> QRectF:
        """캔버스의 모든 노드를 포함하는 바운딩 박스 계산."""
        if not canvas._node_rects:
            return QRectF()

        rects = list(canvas._node_rects.values())
        result = QRectF(rects[0])
        for rect in rects[1:]:
            result = result.united(rect)

        # 여백 추가
        margin = 30
        result.adjust(-margin, -margin, margin, margin)
        return result
