"""메인 윈도우."""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from ..models.family_tree import FamilyTree
from ..models.person import Person
from ..utils.file_handler import FileHandler
from ..utils.theme_manager import get_theme_manager
from ..i18n import tr, set_language, get_available_languages, get_current_language
from .tree_canvas import TreeCanvas
from .detail_panel import DetailPanel


def get_icon(name: str) -> QIcon:
    """아이콘 파일 로드."""
    icons_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'resources', 'icons'
    )
    icon_path = os.path.join(icons_dir, f"{name}.svg")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()


class MainWindow(QMainWindow):
    """메인 윈도우 클래스."""

    def __init__(self):
        super().__init__()

        self.family_tree = FamilyTree()
        self.current_file_path = None

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        self._update_title()

    def _setup_ui(self):
        """UI 구성."""
        self.setWindowTitle(tr('app.name'))
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # === 왼쪽 패널 (가족 목록 + 상세정보) ===
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # 검색 영역
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 12, 12, 12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {tr('panel.search_placeholder')}")
        self.search_input.setObjectName("searchInput")
        search_layout.addWidget(self.search_input)

        left_layout.addWidget(search_frame)

        # 가족 목록
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(12, 8, 12, 8)

        self.list_header = QLabel(tr('panel.family_members'))
        self.list_header.setObjectName("sectionHeader")
        list_layout.addWidget(self.list_header)

        # 목록 스크롤 영역
        self.person_list_scroll = QScrollArea()
        self.person_list_scroll.setObjectName("personListScroll")
        self.person_list_scroll.setWidgetResizable(True)
        self.person_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.person_list_widget = QWidget()
        self.person_list_layout = QVBoxLayout(self.person_list_widget)
        self.person_list_layout.setContentsMargins(0, 0, 0, 0)
        self.person_list_layout.setSpacing(4)
        self.person_list_layout.addStretch()

        self.person_list_scroll.setWidget(self.person_list_widget)
        list_layout.addWidget(self.person_list_scroll)

        # 추가 버튼
        self.add_person_btn = QPushButton(tr('button.add_member'))
        self.add_person_btn.setObjectName("addPersonBtn")
        list_layout.addWidget(self.add_person_btn)

        left_layout.addWidget(list_frame, stretch=1)

        # 상세 정보 패널
        self.detail_panel = DetailPanel()
        left_layout.addWidget(self.detail_panel)

        splitter.addWidget(left_panel)

        # === 오른쪽 패널 (트리 캔버스) ===
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 트리 캔버스
        self.tree_canvas = TreeCanvas(self.family_tree)
        right_layout.addWidget(self.tree_canvas)

        # 줌 컨트롤
        zoom_frame = QFrame()
        zoom_frame.setObjectName("zoomFrame")
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(12, 8, 12, 8)

        zoom_layout.addStretch()

        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(get_icon('zoom_in'))
        self.zoom_in_btn.setObjectName("zoomBtn")
        self.zoom_in_btn.setFixedSize(36, 36)
        zoom_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(get_icon('zoom_out'))
        self.zoom_out_btn.setObjectName("zoomBtn")
        self.zoom_out_btn.setFixedSize(36, 36)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_reset_btn = QPushButton()
        self.zoom_reset_btn.setIcon(get_icon('zoom_reset'))
        self.zoom_reset_btn.setObjectName("zoomBtn")
        self.zoom_reset_btn.setFixedSize(36, 36)
        zoom_layout.addWidget(self.zoom_reset_btn)

        right_layout.addWidget(zoom_frame)

        splitter.addWidget(right_panel)

        # 스플리터 초기 비율
        splitter.setSizes([300, 1100])

    def _setup_menu(self):
        """메뉴바 구성."""
        menubar = self.menuBar()

        # 파일 메뉴
        self.file_menu = menubar.addMenu(tr('menu.file'))

        self.new_action = QAction(get_icon('new'), tr('menu_item.new'), self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.file_menu.addAction(self.new_action)

        self.open_action = QAction(get_icon('open'), tr('menu_item.open'), self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.file_menu.addAction(self.open_action)

        self.file_menu.addSeparator()

        self.save_action = QAction(get_icon('save'), tr('menu_item.save'), self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.file_menu.addAction(self.save_action)

        self.save_as_action = QAction(tr('menu_item.save_as'), self)
        self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.file_menu.addAction(self.save_as_action)

        self.file_menu.addSeparator()

        self.import_action = QAction(tr('menu_item.import'), self)
        self.file_menu.addAction(self.import_action)

        self.export_action = QAction(tr('menu_item.export'), self)
        self.file_menu.addAction(self.export_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction(tr('menu_item.exit'), self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.file_menu.addAction(self.exit_action)

        # 편집 메뉴
        self.edit_menu = menubar.addMenu(tr('menu.edit'))

        self.add_person_action = QAction(get_icon('add_person'), tr('menu_item.add_person'), self)
        self.add_person_action.setShortcut(QKeySequence("Ctrl+N"))
        self.edit_menu.addAction(self.add_person_action)

        self.delete_person_action = QAction(get_icon('delete'), tr('menu_item.delete_person'), self)
        self.delete_person_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.edit_menu.addAction(self.delete_person_action)

        # 보기 메뉴
        self.view_menu = menubar.addMenu(tr('menu.view'))

        self.zoom_in_action = QAction(get_icon('zoom_in'), tr('menu_item.zoom_in'), self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.view_menu.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(get_icon('zoom_out'), tr('menu_item.zoom_out'), self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.view_menu.addAction(self.zoom_out_action)

        self.zoom_reset_action = QAction(get_icon('zoom_reset'), tr('menu_item.zoom_reset'), self)
        self.zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        self.view_menu.addAction(self.zoom_reset_action)

        self.view_menu.addSeparator()

        # 테마 토글
        self.theme_action = QAction(get_icon('theme'), tr('menu_item.toggle_theme'), self)
        self.theme_action.setShortcut(QKeySequence("Ctrl+T"))
        self.view_menu.addAction(self.theme_action)

        self.view_menu.addSeparator()

        # 언어 하위 메뉴
        self.language_menu = self.view_menu.addMenu(tr('menu_item.language'))
        self._setup_language_menu()

        # 도움말 메뉴
        self.help_menu = menubar.addMenu(tr('menu.help'))

        self.about_action = QAction(tr('menu_item.about'), self)
        self.help_menu.addAction(self.about_action)

    def _setup_language_menu(self):
        """언어 메뉴 구성."""
        self.language_menu.clear()
        self.language_actions = {}

        current_lang = get_current_language()
        for lang_code, lang_name in get_available_languages().items():
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.setChecked(lang_code == current_lang)
            action.triggered.connect(lambda checked, lc=lang_code: self._on_language_changed(lc))
            self.language_menu.addAction(action)
            self.language_actions[lang_code] = action

    def _on_language_changed(self, lang_code: str):
        """언어 변경."""
        set_language(lang_code)
        self._update_ui_texts()

        # 체크 상태 업데이트
        for code, action in self.language_actions.items():
            action.setChecked(code == lang_code)

    def _update_ui_texts(self):
        """UI 텍스트 업데이트 (언어 변경 시)."""
        self._update_title()
        self._update_menu_texts()
        self._update_panel_texts()
        self._update_statusbar_texts()
        self.detail_panel.update_ui_texts()
        self._update_person_list()

    def _update_menu_texts(self):
        """메뉴 텍스트 업데이트."""
        self.file_menu.setTitle(tr('menu.file'))
        self.edit_menu.setTitle(tr('menu.edit'))
        self.view_menu.setTitle(tr('menu.view'))
        self.help_menu.setTitle(tr('menu.help'))

        self.new_action.setText(tr('menu_item.new'))
        self.open_action.setText(tr('menu_item.open'))
        self.save_action.setText(tr('menu_item.save'))
        self.save_as_action.setText(tr('menu_item.save_as'))
        self.import_action.setText(tr('menu_item.import'))
        self.export_action.setText(tr('menu_item.export'))
        self.exit_action.setText(tr('menu_item.exit'))
        self.add_person_action.setText(tr('menu_item.add_person'))
        self.delete_person_action.setText(tr('menu_item.delete_person'))
        self.zoom_in_action.setText(tr('menu_item.zoom_in'))
        self.zoom_out_action.setText(tr('menu_item.zoom_out'))
        self.zoom_reset_action.setText(tr('menu_item.zoom_reset'))
        self.theme_action.setText(tr('menu_item.toggle_theme'))
        self.about_action.setText(tr('menu_item.about'))
        self.language_menu.setTitle(tr('menu_item.language'))

    def _update_panel_texts(self):
        """패널 텍스트 업데이트."""
        self.list_header.setText(tr('panel.family_members'))
        self.search_input.setPlaceholderText(f"🔍 {tr('panel.search_placeholder')}")
        self.add_person_btn.setText(tr('button.add_member'))

    def _update_statusbar_texts(self):
        """상태바 텍스트 업데이트."""
        self.status_label.setText(tr('status.ready'))
        count = len(self.family_tree.get_all_persons())
        self.count_label.setText(tr('status.member_count', count=count))

    def _setup_toolbar(self):
        """툴바 구성."""
        toolbar = QToolBar()
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.add_person_action)

    def _setup_statusbar(self):
        """상태바 구성."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel(tr('status.ready'))
        self.statusbar.addWidget(self.status_label)

        self.count_label = QLabel(tr('status.member_count', count=0))
        self.statusbar.addPermanentWidget(self.count_label)

    def _connect_signals(self):
        """시그널 연결."""
        # 파일 메뉴
        self.new_action.triggered.connect(self._on_new)
        self.open_action.triggered.connect(self._on_open)
        self.save_action.triggered.connect(self._on_save)
        self.save_as_action.triggered.connect(self._on_save_as)
        self.import_action.triggered.connect(self._on_import)
        self.export_action.triggered.connect(self._on_export)
        self.exit_action.triggered.connect(self.close)

        # 편집 메뉴
        self.add_person_action.triggered.connect(self._on_add_person)
        self.delete_person_action.triggered.connect(self._on_delete_person)

        # 보기 메뉴
        self.zoom_in_action.triggered.connect(self.tree_canvas.zoom_in)
        self.zoom_out_action.triggered.connect(self.tree_canvas.zoom_out)
        self.zoom_reset_action.triggered.connect(self.tree_canvas.zoom_reset)
        self.theme_action.triggered.connect(self._on_toggle_theme)

        # 도움말 메뉴
        self.about_action.triggered.connect(self._on_about)

        # 버튼
        self.add_person_btn.clicked.connect(self._on_add_person)
        self.zoom_in_btn.clicked.connect(self.tree_canvas.zoom_in)
        self.zoom_out_btn.clicked.connect(self.tree_canvas.zoom_out)
        self.zoom_reset_btn.clicked.connect(self.tree_canvas.zoom_reset)

        # 검색
        self.search_input.textChanged.connect(self._on_search)

        # 캔버스 시그널
        self.tree_canvas.person_selected.connect(self._on_person_selected)
        self.tree_canvas.person_double_clicked.connect(self._on_person_double_clicked)

        # 상세 패널 시그널
        self.detail_panel.person_updated.connect(self._on_person_updated)
        self.detail_panel.add_relationship_requested.connect(self._on_add_relationship)

    def _update_title(self):
        """창 제목 업데이트."""
        title = tr('app.name')
        if self.current_file_path:
            import os
            title += f" - {os.path.basename(self.current_file_path)}"
        if self.family_tree.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def _update_person_list(self):
        """가족 목록 업데이트."""
        # 기존 항목 제거
        while self.person_list_layout.count() > 1:
            item = self.person_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 새 항목 추가
        for person in self.family_tree.get_all_persons():
            name = person.name or tr('label.no_name')
            btn = QPushButton(f"👤 {name}")
            btn.setObjectName("personListItem")
            btn.setProperty("person_id", person.id)
            btn.clicked.connect(lambda checked, pid=person.id: self._on_list_item_clicked(pid))
            self.person_list_layout.insertWidget(self.person_list_layout.count() - 1, btn)

        # 카운트 업데이트
        count = len(self.family_tree.get_all_persons())
        self.count_label.setText(tr('status.member_count', count=count))

    def _on_list_item_clicked(self, person_id: str):
        """목록 항목 클릭."""
        self.tree_canvas.select_person(person_id)

    def _on_person_selected(self, person_id: str):
        """캔버스에서 사람 선택됨."""
        person = self.family_tree.get_person(person_id)
        if person:
            self.detail_panel.set_person(person, self.family_tree)
            self.status_label.setText(tr('status.selected', name=person.name))

    def _on_person_double_clicked(self, person_id: str):
        """캔버스에서 사람 더블클릭."""
        self.detail_panel.start_edit()

    def _on_person_updated(self, person: Person):
        """상세 패널에서 사람 정보 업데이트됨."""
        self.family_tree.update_person(person)
        self._update_person_list()
        self.tree_canvas.refresh()
        self._update_title()

    def _on_add_relationship(self, person_id: str, rel_type: str):
        """관계 추가 요청."""
        # TODO: 관계 추가 다이얼로그 구현
        pass

    def _on_search(self, text: str):
        """검색."""
        # TODO: 검색 기능 구현
        pass

    # === 파일 작업 ===

    def _ensure_file_extension(self, file_path: str, selected_filter: str) -> str:
        """파일 경로에 적절한 확장자가 있는지 확인하고 없으면 추가."""
        if not file_path.endswith(('.json', '.xlsx')):
            if 'Excel' in selected_filter:
                file_path += '.xlsx'
            else:
                file_path += '.json'
        return file_path

    def _on_new(self):
        """새로 만들기."""
        if not self._check_save():
            return

        self.family_tree = FamilyTree()
        self.current_file_path = None
        self.tree_canvas.set_family_tree(self.family_tree)
        self.detail_panel.clear()
        self._update_person_list()
        self._update_title()
        self.status_label.setText(tr('status.new_created'))

    def _on_open(self):
        """파일 열기."""
        if not self._check_save():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, tr('dialog.open_title'), "",
            FileHandler.get_open_filters()
        )

        if file_path:
            self._load_file(file_path)

    def _on_save(self):
        """저장."""
        if self.current_file_path:
            self._save_file(self.current_file_path)
        else:
            self._on_save_as()

    def _on_save_as(self):
        """다른 이름으로 저장."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, tr('dialog.save_title'), "",
            FileHandler.get_save_filters()
        )

        if file_path:
            file_path = self._ensure_file_extension(file_path, selected_filter)
            self._save_file(file_path)

    def _on_import(self):
        """가져오기."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr('dialog.import_title'), "",
            FileHandler.get_open_filters()
        )

        if file_path:
            tree = FileHandler.load_file(file_path)
            if tree:
                # 기존 데이터에 병합할지 물어봄
                if self.family_tree.get_all_persons():
                    reply = QMessageBox.question(
                        self, tr('dialog.import_merge_title'),
                        tr('dialog.import_merge_message'),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                    )

                    if reply == QMessageBox.StandardButton.Cancel:
                        return
                    elif reply == QMessageBox.StandardButton.No:
                        self.family_tree = tree
                    else:
                        # 병합 (persons와 relationships 모두)
                        for person in tree.get_all_persons():
                            self.family_tree.add_person(person)
                        for relationship in tree.get_all_relationships():
                            self.family_tree.add_relationship(relationship)
                else:
                    self.family_tree = tree

                self.tree_canvas.set_family_tree(self.family_tree)
                self._update_person_list()
                self._update_title()
                self.status_label.setText(tr('status.import_complete', path=file_path))

    def _on_export(self):
        """내보내기."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, tr('dialog.export_title'), "",
            FileHandler.get_save_filters()
        )

        if file_path:
            file_path = self._ensure_file_extension(file_path, selected_filter)
            if FileHandler.save_file(self.family_tree, file_path):
                self.status_label.setText(tr('status.export_complete', path=file_path))
            else:
                QMessageBox.warning(self, tr('error.export_failed'), tr('error.export_failed'))

    def _load_file(self, file_path: str):
        """파일 로드."""
        tree = FileHandler.load_file(file_path)
        if tree:
            self.family_tree = tree
            self.current_file_path = file_path
            self.tree_canvas.set_family_tree(self.family_tree)
            self.detail_panel.clear()
            self._update_person_list()
            self._update_title()
            self.status_label.setText(tr('status.file_opened', path=file_path))
        else:
            QMessageBox.warning(self, tr('error.file_open_failed'), tr('error.file_open_failed'))

    def _save_file(self, file_path: str):
        """파일 저장."""
        if FileHandler.save_file(self.family_tree, file_path):
            self.current_file_path = file_path
            self.family_tree.mark_saved()
            self._update_title()
            self.status_label.setText(tr('status.saved', path=file_path))
        else:
            QMessageBox.warning(self, tr('error.save_failed'), tr('error.save_failed'))

    def _check_save(self) -> bool:
        """저장 여부 확인. 계속 진행하면 True 반환."""
        if self.family_tree.is_modified:
            reply = QMessageBox.question(
                self, tr('dialog.save_confirm_title'),
                tr('dialog.save_confirm_message'),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self._on_save()
                return not self.family_tree.is_modified
            elif reply == QMessageBox.StandardButton.Cancel:
                return False

        return True

    # === 편집 작업 ===

    def _on_add_person(self):
        """구성원 추가."""
        person = Person(name="새 구성원")
        self.family_tree.add_person(person)
        self._update_person_list()
        self.tree_canvas.refresh()
        self.tree_canvas.select_person(person.id)
        self._update_title()
        self.status_label.setText(tr('status.new_member_added'))

    def _on_delete_person(self):
        """구성원 삭제."""
        selected_id = self.tree_canvas.selected_person_id
        if not selected_id:
            return

        person = self.family_tree.get_person(selected_id)
        if not person:
            return

        reply = QMessageBox.question(
            self, tr('dialog.delete_confirm_title'),
            tr('dialog.delete_confirm_message', name=person.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.family_tree.remove_person(selected_id)
            self._update_person_list()
            self.tree_canvas.refresh()
            self.detail_panel.clear()
            self._update_title()
            self.status_label.setText(tr('status.deleted', name=person.name))

    # === 도움말 ===

    def _on_toggle_theme(self):
        """테마 토글."""
        theme_manager = get_theme_manager()
        new_theme = theme_manager.toggle_theme()
        self.status_label.setText(tr('status.theme_changed', theme=new_theme))

    def _on_about(self):
        """정보 대화상자."""
        QMessageBox.about(
            self, tr('about.title'),
            f"<h2>{tr('app.name')}</h2>"
            f"<p>{tr('app.version', version='1.0.0')}</p>"
            f"<p>{tr('about.description')}</p>"
            f"<p>{tr('about.formats')}</p>"
        )

    def closeEvent(self, event):
        """창 닫기 이벤트."""
        if self._check_save():
            event.accept()
        else:
            event.ignore()
