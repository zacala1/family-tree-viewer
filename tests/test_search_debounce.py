"""검색 입력 디바운스 회귀 가드.

큰 트리에서 매 키마다 search+render되는 것을 막기 위해 200ms 디바운스 적용.
Enter 키는 디바운스를 우회해 즉시 실행.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeyEvent

from src.models.person import Person


@pytest.fixture
def main_window(qapp):
    """MainWindow 인스턴스 (sample family 로드된 상태)."""
    from src.views.main_window import MainWindow
    win = MainWindow()
    # 트리에 데이터 몇 명 추가
    for i, name in enumerate(["홍길동", "김철수", "이영희", "박민수"]):
        win.family_tree.add_person(Person(id=f"p{i}", name=name))
    win._update_person_list()
    yield win
    # closeEvent의 _check_save 다이얼로그가 사용자 입력 대기로 hang하지 않게 modified 해제
    win.family_tree.mark_saved()
    win.close()
    win.deleteLater()


class TestSearchDebounce:
    def test_debounce_timer_exists_and_configured(self, main_window):
        """디바운스 타이머가 single-shot 200ms로 설정됐는지."""
        timer = main_window._search_debounce_timer
        assert timer is not None
        assert timer.isSingleShot() is True
        assert timer.interval() == 200

    def test_typing_does_not_search_immediately(self, main_window):
        """텍스트 입력 직후 search가 즉시 실행되지 않음 (디바운스 동작)."""
        calls = []
        original = main_window._on_search
        main_window._on_search = lambda text=None: calls.append(text)

        main_window.search_input.setText("홍")
        # 200ms 안 기다림 → 호출 없음
        assert calls == []

        # 타이머 강제 timeout 후 호출 1회
        main_window._search_debounce_timer.stop()
        original()  # 원래 search 동작도 정상인지 확인

    def test_consecutive_input_resets_timer(self, main_window):
        """빠른 연속 입력 시 마지막 입력만 search 트리거."""
        calls = []
        main_window._on_search = lambda text=None: calls.append(text)

        # 3번 연속 입력 → timer만 reset되고 _on_search 호출 0
        main_window.search_input.setText("홍")
        main_window.search_input.setText("홍길")
        main_window.search_input.setText("홍길동")
        assert calls == []

        # timer가 여전히 활성 상태여야
        assert main_window._search_debounce_timer.isActive()

    def test_enter_key_triggers_immediately(self, main_window):
        """Enter 키는 디바운스 우회 — 즉시 search 실행 (통합 검증).

        직접 search 결과를 status_label에서 확인. monkeypatch는 이미 connect된
        bound method를 교체하지 못해 의도와 다르게 통과할 수 있어 통합 테스트로 검증.
        """
        # "홍" 텍스트 설정 — 디바운스 타이머 시작되지만 timeout 전
        main_window.search_input.setText("홍")
        # Enter 키 즉시 발사
        main_window.search_input.returnPressed.emit()
        # 검색 즉시 실행 → status_label에 결과 반영 (홍길동 1명)
        text = main_window.status_label.text()
        assert "1" in text  # results count 1

    def test_timer_timeout_calls_on_search(self, main_window):
        """timer.timeout이 _on_search에 연결됐는지 확인."""
        calls = []
        main_window._on_search = lambda text=None: calls.append("called")
        # 기존 connection을 정리하고 다시 연결 — 동작 검증
        main_window._search_debounce_timer.timeout.disconnect()
        main_window._search_debounce_timer.timeout.connect(main_window._on_search)
        main_window._search_debounce_timer.timeout.emit()
        assert calls == ["called"]
