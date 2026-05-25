"""UI 애니메이션 헬퍼.

작은 fade/slide 전환을 한 줄로 적용하기 위한 모듈. 각 위젯이 직접
QPropertyAnimation을 만들지 않고 헬퍼만 호출하면 일관된 duration과
easing curve(OutCubic 180ms)를 자동 사용.
"""
from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QObject
from PyQt6.QtWidgets import QWidget


# 모든 fade/slide의 기본 길이. config.ANIMATION_DURATION(300ms)보다
# 살짝 짧음 — dialog open이 너무 느려 보이는 것을 방지.
_DEFAULT_FADE_DURATION_MS = 180


def fade_in_widget(widget: QWidget, duration: int = _DEFAULT_FADE_DURATION_MS) -> None:
    """위젯의 windowOpacity를 0→1로 fade-in.

    QDialog, QWidget 모두 동작. 애니메이션 객체는 widget에 attribute로
    저장돼 garbage collection을 피한다 (Qt의 일반 패턴).

    Args:
        widget: 대상 위젯 (이미 표시 중이거나 곧 표시될)
        duration: 밀리초. 기본 180ms (OutCubic).
    """
    widget.setWindowOpacity(0.0)
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    # widget에 attach해 GC 방지
    widget._fade_in_anim = anim  # type: ignore[attr-defined]
    anim.start()


def fade_in_property(target: QObject, prop: bytes, end_value: float,
                     start_value: float = 0.0,
                     duration: int = _DEFAULT_FADE_DURATION_MS) -> QPropertyAnimation:
    """임의의 numeric property를 fade in.

    예: scroll value, opacity 외 transition에 사용 가능.
    호출자가 anim 참조를 보관해야 GC 안 됨.

    Returns:
        시작된 QPropertyAnimation. 호출자가 attribute 등에 저장 권장.
    """
    anim = QPropertyAnimation(target, prop)
    anim.setDuration(duration)
    anim.setStartValue(start_value)
    anim.setEndValue(end_value)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    return anim
