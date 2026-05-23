"""메인 윈도우."""

import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QToolBar,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QComboBox,
    QMenu,
    QApplication,
    QProgressDialog,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from ..models.family_tree import FamilyTree
from ..models.person import Person
from ..models.command import (
    UndoRedoManager,
    AddPersonCommand,
    DeletePersonCommand,
    UpdatePersonCommand,
    AddRelationshipCommand,
    SetSpouseCommand,
)
from ..models.relationship import RelationshipRequestType
from ..utils.file_handler import FileHandler
from ..utils.theme_manager import get_theme_manager
from ..utils.search_index import PersonSearchIndex
from ..i18n import tr, set_language, get_available_languages, get_current_language
from ..config import MAX_SEARCH_QUERY_LENGTH, AUTO_BACKUP_INTERVAL_MINUTES, MAX_BACKUP_COUNT, BACKUP_DIR
from .tree_canvas import TreeCanvas
from .detail_panel import DetailPanel


def get_icon(name: str) -> QIcon:
    """아이콘 파일 로드."""
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")
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
        self.undo_manager = UndoRedoManager()
        self.search_index = PersonSearchIndex()  # Optimized search index

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._setup_accessibility()
        self._setup_auto_backup()

        self._update_title()
        self._check_startup_recovery()

    def _setup_ui(self):
        """UI 구성."""
        self.setWindowTitle(tr("app.name"))
        self.setMinimumSize(1024, 680)
        self.resize(1400, 900)
        self.setAcceptDrops(True)

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

        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_panel.setMinimumWidth(240)
        left_panel.setMaximumWidth(600)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 12, 12, 12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {tr('panel.search_placeholder')}")
        self.search_input.setObjectName("searchInput")
        search_layout.addWidget(self.search_input)

        self.advanced_search_btn = QPushButton("▼")
        self.advanced_search_btn.setFixedSize(28, 28)
        self.advanced_search_btn.setCheckable(True)
        self.advanced_search_btn.setToolTip(tr("label.advanced_search"))
        self.advanced_search_btn.clicked.connect(self._toggle_advanced_search)
        search_layout.addWidget(self.advanced_search_btn)

        left_layout.addWidget(search_frame)

        # 고급 검색 프레임 (접이식)
        self.advanced_search_frame = QFrame()
        self.advanced_search_frame.setObjectName("advancedSearchFrame")
        self.advanced_search_frame.setVisible(False)
        adv_layout = QVBoxLayout(self.advanced_search_frame)
        adv_layout.setContentsMargins(12, 4, 12, 8)
        adv_layout.setSpacing(4)

        # 성별 필터
        gender_row = QHBoxLayout()
        gender_row.addWidget(QLabel(tr("label.gender") + ":"))
        self.adv_gender_combo = QComboBox()
        self.adv_gender_combo.addItem(tr("filter.all"), "all")
        self.adv_gender_combo.addItem(tr("label.male"), "male")
        self.adv_gender_combo.addItem(tr("label.female"), "female")
        self.adv_gender_combo.currentIndexChanged.connect(lambda _: self._on_search())
        gender_row.addWidget(self.adv_gender_combo, 1)
        adv_layout.addLayout(gender_row)

        # 출생연도 범위
        year_row = QHBoxLayout()
        year_row.addWidget(QLabel(tr("label.birth_year_range") + ":"))
        self.adv_year_from = QSpinBox()
        self.adv_year_from.setRange(0, 2100)
        self.adv_year_from.setSpecialValueText("-")
        self.adv_year_from.setValue(0)
        self.adv_year_from.valueChanged.connect(lambda _: self._on_search())
        year_row.addWidget(self.adv_year_from)
        year_row.addWidget(QLabel("~"))
        self.adv_year_to = QSpinBox()
        self.adv_year_to.setRange(0, 2100)
        self.adv_year_to.setSpecialValueText("-")
        self.adv_year_to.setValue(0)
        self.adv_year_to.valueChanged.connect(lambda _: self._on_search())
        year_row.addWidget(self.adv_year_to)
        adv_layout.addLayout(year_row)

        # 지역 검색
        location_row = QHBoxLayout()
        location_row.addWidget(QLabel(tr("label.location") + ":"))
        self.adv_location_input = QLineEdit()
        self.adv_location_input.textChanged.connect(lambda _: self._on_search())
        location_row.addWidget(self.adv_location_input, 1)
        adv_layout.addLayout(location_row)

        left_layout.addWidget(self.advanced_search_frame)

        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(12, 8, 12, 8)

        self.list_header = QLabel(tr("panel.family_members"))
        self.list_header.setObjectName("sectionHeader")
        list_layout.addWidget(self.list_header)

        sort_filter_layout = QHBoxLayout()
        sort_filter_layout.setSpacing(4)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem(tr("sort.name_asc"), "name_asc")
        self.sort_combo.addItem(tr("sort.name_desc"), "name_desc")
        self.sort_combo.addItem(tr("sort.birth_year"), "birth_year")
        self.sort_combo.currentIndexChanged.connect(lambda _: self._update_person_list())
        sort_filter_layout.addWidget(self.sort_combo)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem(tr("filter.all"), "all")
        self.filter_combo.addItem(tr("filter.male"), "male")
        self.filter_combo.addItem(tr("filter.female"), "female")
        self.filter_combo.addItem(tr("filter.alive"), "alive")
        self.filter_combo.addItem(tr("filter.deceased"), "deceased")
        self.filter_combo.currentIndexChanged.connect(lambda _: self._update_person_list())
        sort_filter_layout.addWidget(self.filter_combo)

        list_layout.addLayout(sort_filter_layout)

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

        self.add_person_btn = QPushButton(tr("button.add_member"))
        self.add_person_btn.setObjectName("addPersonBtn")
        list_layout.addWidget(self.add_person_btn)

        left_layout.addWidget(list_frame, stretch=1)

        self.detail_panel = DetailPanel()
        left_layout.addWidget(self.detail_panel)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tree_canvas = TreeCanvas(self.family_tree)
        right_layout.addWidget(self.tree_canvas)

        zoom_frame = QFrame()
        zoom_frame.setObjectName("zoomFrame")
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(12, 8, 12, 8)

        zoom_layout.addStretch()

        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(get_icon("zoom_in"))
        self.zoom_in_btn.setObjectName("zoomBtn")
        self.zoom_in_btn.setFixedSize(36, 36)
        zoom_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(get_icon("zoom_out"))
        self.zoom_out_btn.setObjectName("zoomBtn")
        self.zoom_out_btn.setFixedSize(36, 36)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_reset_btn = QPushButton()
        self.zoom_reset_btn.setIcon(get_icon("zoom_reset"))
        self.zoom_reset_btn.setObjectName("zoomBtn")
        self.zoom_reset_btn.setFixedSize(36, 36)
        zoom_layout.addWidget(self.zoom_reset_btn)

        right_layout.addWidget(zoom_frame)

        splitter.addWidget(right_panel)

        splitter.setSizes([300, 1100])

    def _setup_menu(self):
        """메뉴바 구성."""
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu(tr("menu.file"))

        self.new_action = QAction(get_icon("new"), tr("menu_item.new"), self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.file_menu.addAction(self.new_action)

        self.open_action = QAction(get_icon("open"), tr("menu_item.open"), self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.file_menu.addAction(self.open_action)

        self.file_menu.addSeparator()

        self.save_action = QAction(get_icon("save"), tr("menu_item.save"), self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.file_menu.addAction(self.save_action)

        self.save_as_action = QAction(tr("menu_item.save_as"), self)
        self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.file_menu.addAction(self.save_as_action)

        self.file_menu.addSeparator()

        self.import_action = QAction(tr("menu_item.import"), self)
        self.file_menu.addAction(self.import_action)

        self.export_action = QAction(tr("menu_item.export"), self)
        self.file_menu.addAction(self.export_action)

        self.export_pdf_action = QAction(tr("menu_item.export_pdf"), self)
        self.export_pdf_action.setShortcut(QKeySequence("Ctrl+P"))
        self.file_menu.addAction(self.export_pdf_action)

        self.file_menu.addSeparator()

        self.manage_backups_action = QAction(tr("menu_item.manage_backups"), self)
        self.file_menu.addAction(self.manage_backups_action)

        self.file_menu.addSeparator()

        self.exit_action = QAction(tr("menu_item.exit"), self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.file_menu.addAction(self.exit_action)

        self.edit_menu = menubar.addMenu(tr("menu.edit"))

        self.add_person_action = QAction(get_icon("add_person"), tr("menu_item.add_person"), self)
        self.add_person_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.edit_menu.addAction(self.add_person_action)

        self.delete_person_action = QAction(get_icon("delete"), tr("menu_item.delete_person"), self)
        self.delete_person_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.edit_menu.addAction(self.delete_person_action)

        self.edit_menu.addSeparator()

        self.undo_action = QAction(tr("button.undo"), self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setEnabled(False)
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = QAction(tr("button.redo"), self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.setEnabled(False)
        self.edit_menu.addAction(self.redo_action)

        self.view_menu = menubar.addMenu(tr("menu.view"))

        self.zoom_in_action = QAction(get_icon("zoom_in"), tr("menu_item.zoom_in"), self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.view_menu.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(get_icon("zoom_out"), tr("menu_item.zoom_out"), self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.view_menu.addAction(self.zoom_out_action)

        self.zoom_reset_action = QAction(get_icon("zoom_reset"), tr("menu_item.zoom_reset"), self)
        self.zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        self.view_menu.addAction(self.zoom_reset_action)

        self.view_menu.addSeparator()

        self.theme_action = QAction(get_icon("theme"), tr("menu_item.toggle_theme"), self)
        self.theme_action.setShortcut(QKeySequence("Ctrl+T"))
        self.view_menu.addAction(self.theme_action)

        self.view_menu.addSeparator()

        self.language_menu = self.view_menu.addMenu(tr("menu_item.language"))
        self._setup_language_menu()

        self.help_menu = menubar.addMenu(tr("menu.help"))

        self.about_action = QAction(tr("menu_item.about"), self)
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
        self.file_menu.setTitle(tr("menu.file"))
        self.edit_menu.setTitle(tr("menu.edit"))
        self.view_menu.setTitle(tr("menu.view"))
        self.help_menu.setTitle(tr("menu.help"))

        self.new_action.setText(tr("menu_item.new"))
        self.open_action.setText(tr("menu_item.open"))
        self.save_action.setText(tr("menu_item.save"))
        self.save_as_action.setText(tr("menu_item.save_as"))
        self.import_action.setText(tr("menu_item.import"))
        self.export_action.setText(tr("menu_item.export"))
        self.export_pdf_action.setText(tr("menu_item.export_pdf"))
        self.exit_action.setText(tr("menu_item.exit"))
        self.add_person_action.setText(tr("menu_item.add_person"))
        self.delete_person_action.setText(tr("menu_item.delete_person"))
        self.undo_action.setText(tr("button.undo"))
        self.redo_action.setText(tr("button.redo"))
        self.zoom_in_action.setText(tr("menu_item.zoom_in"))
        self.zoom_out_action.setText(tr("menu_item.zoom_out"))
        self.zoom_reset_action.setText(tr("menu_item.zoom_reset"))
        self.theme_action.setText(tr("menu_item.toggle_theme"))
        self.about_action.setText(tr("menu_item.about"))
        self.language_menu.setTitle(tr("menu_item.language"))

    def _update_panel_texts(self):
        """패널 텍스트 업데이트."""
        self.list_header.setText(tr("panel.family_members"))
        self.search_input.setPlaceholderText(f"🔍 {tr('panel.search_placeholder')}")
        self.add_person_btn.setText(tr("button.add_member"))

        self.sort_combo.setItemText(0, tr("sort.name_asc"))
        self.sort_combo.setItemText(1, tr("sort.name_desc"))
        self.sort_combo.setItemText(2, tr("sort.birth_year"))
        self.filter_combo.setItemText(0, tr("filter.all"))
        self.filter_combo.setItemText(1, tr("filter.male"))
        self.filter_combo.setItemText(2, tr("filter.female"))
        self.filter_combo.setItemText(3, tr("filter.alive"))
        self.filter_combo.setItemText(4, tr("filter.deceased"))

    def _update_statusbar_texts(self):
        """상태바 텍스트 업데이트."""
        self.status_label.setText(tr("status.ready"))
        count = len(self.family_tree.get_all_persons())
        self.count_label.setText(tr("status.member_count", count=count))

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

        self.status_label = QLabel(tr("status.ready"))
        self.statusbar.addWidget(self.status_label)

        self.count_label = QLabel(tr("status.member_count", count=0))
        self.statusbar.addPermanentWidget(self.count_label)

    def _connect_signals(self):
        """시그널 연결."""
        self.new_action.triggered.connect(self._on_new)
        self.open_action.triggered.connect(self._on_open)
        self.save_action.triggered.connect(self._on_save)
        self.save_as_action.triggered.connect(self._on_save_as)
        self.import_action.triggered.connect(self._on_import)
        self.export_action.triggered.connect(self._on_export)
        self.export_pdf_action.triggered.connect(self._on_export_pdf)
        self.manage_backups_action.triggered.connect(self._on_manage_backups)
        self.exit_action.triggered.connect(self.close)

        self.add_person_action.triggered.connect(self._on_add_person)
        self.delete_person_action.triggered.connect(self._on_delete_person)
        self.undo_action.triggered.connect(self._on_undo)
        self.redo_action.triggered.connect(self._on_redo)

        self.zoom_in_action.triggered.connect(self.tree_canvas.zoom_in)
        self.zoom_out_action.triggered.connect(self.tree_canvas.zoom_out)
        self.zoom_reset_action.triggered.connect(self.tree_canvas.zoom_reset)
        self.theme_action.triggered.connect(self._on_toggle_theme)

        self.about_action.triggered.connect(self._on_about)

        self.add_person_btn.clicked.connect(self._on_add_person)
        self.zoom_in_btn.clicked.connect(self.tree_canvas.zoom_in)
        self.zoom_out_btn.clicked.connect(self.tree_canvas.zoom_out)
        self.zoom_reset_btn.clicked.connect(self.tree_canvas.zoom_reset)

        # 디바운스: 빠른 타이핑 중 매 키마다 search+render 호출되는 것을 방지
        # (큰 트리에서 체감 큰 차이). 마지막 입력 후 200ms 무입력 시 한 번 실행.
        self._search_debounce_timer = QTimer(self)
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.setInterval(200)
        self._search_debounce_timer.timeout.connect(self._on_search)
        self.search_input.textChanged.connect(self._search_debounce_timer.start)
        # Enter 키는 디바운스 우회해 즉시 검색
        self.search_input.returnPressed.connect(self._on_search)

        self.tree_canvas.person_selected.connect(self._on_person_selected)
        self.tree_canvas.person_double_clicked.connect(self._on_person_double_clicked)
        self.tree_canvas.context_menu_requested.connect(self._show_canvas_context_menu)

        self.detail_panel.person_updated.connect(self._on_person_updated)
        self.detail_panel.add_relationship_requested.connect(self._on_add_relationship)

    def _setup_accessibility(self):
        """접근성 설정 (accessible name, 툴팁, tab order)."""
        # Accessible names
        self.search_input.setAccessibleName(tr("accessibility.search_desc"))
        self.search_input.setAccessibleDescription(tr("accessibility.search_desc"))
        self.tree_canvas.setAccessibleName(tr("accessibility.tree_canvas"))
        self.detail_panel.setAccessibleName(tr("accessibility.detail_panel"))

        # 툴바 버튼 툴팁 (단축키 포함)
        self.zoom_in_btn.setToolTip(f"{tr('menu_item.zoom_in')} (Ctrl++)")
        self.zoom_out_btn.setToolTip(f"{tr('menu_item.zoom_out')} (Ctrl+-)")
        self.zoom_reset_btn.setToolTip(f"{tr('menu_item.zoom_reset')} (Ctrl+0)")
        self.add_person_btn.setToolTip(f"{tr('button.add_member')} (Ctrl+Shift+N)")

        # Tab order
        self.setTabOrder(self.search_input, self.sort_combo)
        self.setTabOrder(self.sort_combo, self.filter_combo)
        self.setTabOrder(self.filter_combo, self.add_person_btn)

    def _update_title(self):
        """창 제목 업데이트."""
        title = tr("app.name")
        if self.current_file_path:
            title += f" - {os.path.basename(self.current_file_path)}"
        if self.family_tree.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def load_tree(self, tree: FamilyTree):
        """외부에서 FamilyTree를 로드하는 공개 메서드."""
        self.family_tree = tree
        self.tree_canvas.set_family_tree(tree)
        self._update_person_list()
        self._update_title()

    def _has_advanced_filters_set(self) -> bool:
        """고급 필터가 하나라도 활성화됐는지 — 빈 목록 안내 분기용."""
        return (
            self.adv_gender_combo.currentData() != "all"
            or self.adv_year_from.value() > 0
            or self.adv_year_to.value() > 0
            or bool(self.adv_location_input.text().strip())
        )

    def _render_person_list(self, persons: list):
        """person 목록을 좌측 패널에 렌더링하는 헬퍼."""
        while self.person_list_layout.count() > 1:
            item = self.person_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 빈 상태 안내 — 트리 자체가 비었거나 검색 결과 0건일 때 사용자에게 다음 행동 안내
        if not persons:
            has_search = bool(self.search_input.text().strip())
            is_advanced_filtering = (
                self.advanced_search_frame.isVisible()
                and self._has_advanced_filters_set()
            )
            tree_empty = self.family_tree.person_count == 0

            if tree_empty:
                hint_text = tr("message.empty_list_no_members")
            elif has_search or is_advanced_filtering:
                hint_text = tr("message.empty_list_no_results")
            else:
                hint_text = ""

            if hint_text:
                hint = QLabel(hint_text)
                hint.setObjectName("personListEmptyHint")
                hint.setWordWrap(True)
                hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
                hint.setStyleSheet("color: gray; padding: 24px 12px;")
                self.person_list_layout.insertWidget(0, hint)
            return

        for person in persons:
            name = person.name or tr("label.no_name")

            if person.birth_date_str:
                display_name = f"👤 {name} ({person.birth_date_str})"
            else:
                display_name = f"👤 {name}"

            btn = QPushButton(display_name)
            btn.setObjectName("personListItem")
            btn.setProperty("person_id", person.id)
            btn.clicked.connect(lambda checked, pid=person.id: self._on_list_item_clicked(pid))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, pid=person.id, b=btn: self._show_person_context_menu(pos, pid, b)
            )
            self.person_list_layout.insertWidget(self.person_list_layout.count() - 1, btn)

    def _update_person_list(self):
        """가족 목록 업데이트 및 검색 인덱스 재구축."""
        all_persons = self.family_tree.get_all_persons()
        self.search_index.index_persons(all_persons)
        filtered = self._get_sorted_filtered_persons(list(all_persons))
        self._render_person_list(filtered)
        self.count_label.setText(tr("status.member_count", count=len(all_persons)))

    def _on_list_item_clicked(self, person_id: str):
        """목록 항목 클릭: 선택 + 캔버스 화면 중앙으로 자동 점프."""
        self.tree_canvas.select_person(person_id)
        # 검색 결과·필터 후에도 시야 밖일 수 있으므로 항상 줌 점프
        self.tree_canvas.zoom_to_person(person_id)

    def _on_person_selected(self, person_id: str):
        """캔버스에서 사람 선택됨."""
        person = self.family_tree.get_person(person_id)
        if person:
            self.detail_panel.set_person(person, self.family_tree)
            self.status_label.setText(tr("status.selected", name=person.name))

    def _on_person_double_clicked(self, person_id: str):
        """캔버스에서 사람 더블클릭."""
        self.detail_panel.start_edit()

    def _on_person_updated(self, person: Person):
        """상세 패널에서 사람 정보 업데이트됨."""
        # 이름 변경 시 중복 확인
        old_person = self.family_tree.get_person(person.id)
        if old_person and old_person.name != person.name:
            if not self._check_duplicate_name(person.name, person.id):
                return  # 사용자가 취소함

        command = UpdatePersonCommand(self.family_tree, person.id, person)
        self.undo_manager.execute(command)
        self._update_undo_redo_state()
        self._update_person_list()
        self.tree_canvas.refresh()
        self._update_title()

    def _on_add_relationship(self, person_id: str, rel_type: str):
        """관계 추가 요청."""
        from .relationship_dialog import SelectPersonDialog

        person = self.family_tree.get_person(person_id)
        if not person:
            return

        # 관계 타입에 따라 다이얼로그 제목 설정
        dialog_titles = {
            RelationshipRequestType.PARENT: tr("dialog.select_parent_title"),
            RelationshipRequestType.SPOUSE: tr("dialog.select_spouse_title"),
            RelationshipRequestType.CHILD: tr("dialog.select_child_title"),
        }

        title = dialog_titles.get(rel_type)
        if not title:
            return

        # 사람 선택 다이얼로그
        dialog = SelectPersonDialog(self.family_tree, title, self, exclude_id=person_id)
        if dialog.exec() == SelectPersonDialog.DialogCode.Accepted:
            selected_id = dialog.get_selected_person_id()
            if not selected_id:
                return

            try:
                selected_person = self.family_tree.get_person(selected_id)
                selected_name = selected_person.name if selected_person else "Unknown"

                # 관계 추가 (Undo/Redo 지원)
                if rel_type == RelationshipRequestType.PARENT:
                    command = AddRelationshipCommand(self.family_tree, selected_id, person_id)
                    self.undo_manager.execute(command)
                    self.status_label.setText(
                        tr("status.parent_added", parent=selected_name, child=person.name)
                    )
                elif rel_type == RelationshipRequestType.SPOUSE:
                    # SetSpouseCommand로 감싸 Undo/Redo 지원
                    command = SetSpouseCommand(self.family_tree, person_id, selected_id)
                    self.undo_manager.execute(command)
                    self.status_label.setText(
                        tr("status.spouse_added", person1=person.name, person2=selected_name)
                    )
                elif rel_type == RelationshipRequestType.CHILD:
                    command = AddRelationshipCommand(self.family_tree, person_id, selected_id)
                    self.undo_manager.execute(command)
                    self.status_label.setText(
                        tr("status.child_added", parent=person.name, child=selected_name)
                    )

                self._update_undo_redo_state()

                # UI 업데이트
                self._update_title()
                self.tree_canvas.refresh()
                self.detail_panel.load_person(person_id)

            except ValueError as e:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    tr("dialog.relationship_error_title"),
                    tr("dialog.relationship_error_message", error=str(e)),
                    QMessageBox.StandardButton.Ok,
                )

    def _on_search(self, text: str = None):
        """검색 (Trie 기반 최적화 + 고급 필터)."""
        if text is None:
            text = self.search_input.text()

        has_advanced = self.advanced_search_frame.isVisible()

        if not text.strip() and not has_advanced:
            self._update_person_list()
            return

        if len(text) > MAX_SEARCH_QUERY_LENGTH:
            text = text[:MAX_SEARCH_QUERY_LENGTH]

        if text.strip():
            matching_persons = self.search_index.search(text)
        else:
            matching_persons = self.family_tree.get_all_persons()

        # 고급 필터 적용
        if has_advanced:
            matching_persons = self._apply_advanced_filters(matching_persons)

        self._render_person_list(sorted(matching_persons, key=lambda p: (p.name or "").lower()))

        count = len(matching_persons)
        if count == 0:
            self.status_label.setText(tr("status.search_no_results", query=text or ""))
        else:
            self.status_label.setText(
                tr("status.search_results", count=count, query=text or "")
            )

    def _toggle_advanced_search(self):
        """고급 검색 패널 토글."""
        visible = self.advanced_search_btn.isChecked()
        self.advanced_search_frame.setVisible(visible)
        self.advanced_search_btn.setText("▲" if visible else "▼")
        if not visible:
            # 필터 초기화
            self.adv_gender_combo.setCurrentIndex(0)
            self.adv_year_from.setValue(0)
            self.adv_year_to.setValue(0)
            self.adv_location_input.clear()
        self._on_search()

    def _apply_advanced_filters(self, persons):
        """고급 검색 필터 적용."""
        # 성별 필터
        gender = self.adv_gender_combo.currentData()
        if gender == "male":
            persons = [p for p in persons if p.gender == "M"]
        elif gender == "female":
            persons = [p for p in persons if p.gender == "F"]

        # 출생연도 범위
        year_from = self.adv_year_from.value()
        year_to = self.adv_year_to.value()
        if year_from > 0:
            persons = [p for p in persons if p.birth_year and p.birth_year >= year_from]
        if year_to > 0:
            persons = [p for p in persons if p.birth_year and p.birth_year <= year_to]

        # 지역 검색
        location = self.adv_location_input.text().strip().lower()
        if location:
            persons = [
                p for p in persons
                if location in (p.birth_place or "").lower()
                or location in (p.current_address or "").lower()
            ]

        return persons

    # === 파일 작업 ===

    def _ensure_file_extension(self, file_path: str, selected_filter: str) -> str:
        """파일 경로에 적절한 확장자가 있는지 확인하고 없으면 추가."""
        if not file_path.endswith((".json", ".xlsx", ".ged")):
            if "Excel" in selected_filter:
                file_path += ".xlsx"
            elif "GEDCOM" in selected_filter:
                file_path += ".ged"
            else:
                file_path += ".json"
        return file_path

    def _on_new(self):
        """새로 만들기."""
        if not self._check_save():
            return

        self.family_tree = FamilyTree()
        self.current_file_path = None
        self.undo_manager.clear()
        self._update_undo_redo_state()
        self.tree_canvas.set_family_tree(self.family_tree)
        self.detail_panel.clear()
        self._update_person_list()
        self._update_title()
        self.status_label.setText(tr("status.new_created"))

    def _on_open(self):
        """파일 열기 (대화상자로 경로 선택)."""
        if not self._check_save():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.open_title"), "", FileHandler.get_open_filters()
        )

        if file_path:
            self._load_file(file_path)

    def _on_save(self):
        """저장."""
        if self.current_file_path:
            self._do_save(self.current_file_path)
        else:
            self._on_save_as()

    def _on_save_as(self):
        """다른 이름으로 저장."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, tr("dialog.save_title"), "", FileHandler.get_save_filters()
        )

        if file_path:
            file_path = self._ensure_file_extension(file_path, selected_filter)
            self._do_save(file_path)

    def _do_save(self, file_path: str):
        """실제 저장 수행 (I/O만 백그라운드, UI 업데이트는 메인 스레드)."""
        success = self._run_with_progress(
            tr("dialog.save_title"),
            tr("status.saving_file"),
            lambda: FileHandler.save_file(self.family_tree, file_path),
        )
        if success:
            self.current_file_path = file_path
            self.family_tree.mark_saved()
            self._update_title()
            self.status_label.setText(tr("status.saved", path=file_path))
        else:
            detail = FileHandler.get_last_error()
            msg = tr("error.save_failed")
            if detail:
                msg += f"\n\n{detail}"
            QMessageBox.warning(self, tr("error.save_failed"), msg)

    def _on_import(self):
        """가져오기."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("dialog.import_title"), "", FileHandler.get_open_filters()
        )

        if file_path:
            tree = self._run_with_progress(
                tr("dialog.import_title"),
                tr("status.importing"),
                lambda: FileHandler.load_file(file_path),
            )
            if tree:
                # 기존 데이터에 병합할지 물어봄
                if self.family_tree.get_all_persons():
                    buttons = (
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                        | QMessageBox.StandardButton.Cancel
                    )
                    reply = QMessageBox.question(
                        self,
                        tr("dialog.import_merge_title"),
                        tr("dialog.import_merge_message"),
                        buttons,
                    )

                    if reply == QMessageBox.StandardButton.Cancel:
                        return
                    elif reply == QMessageBox.StandardButton.No:
                        self.family_tree = tree
                    else:
                        # 병합 전 검증
                        current_count = len(self.family_tree.get_all_persons())
                        import_count = len(tree.get_all_persons())
                        if current_count + import_count > self.family_tree.MAX_PERSONS:
                            QMessageBox.warning(
                                self,
                                tr("dialog.import_merge_title"),
                                tr("error.file_too_large", max_size=self.family_tree.MAX_PERSONS),
                                QMessageBox.StandardButton.Ok,
                            )
                            return

                        # 병합 (persons와 relationships 모두)
                        try:
                            for person in tree.get_all_persons():
                                self.family_tree.add_person(person)
                            for relationship in tree.get_all_relationships():
                                self.family_tree.add_relationship(relationship)
                        except ValueError as e:
                            QMessageBox.critical(
                                self,
                                tr("dialog.import_merge_title"),
                                tr("dialog.relationship_error_message", error=str(e)),
                                QMessageBox.StandardButton.Ok,
                            )
                            return
                else:
                    self.family_tree = tree

                self.tree_canvas.set_family_tree(self.family_tree)
                self._update_person_list()
                self._update_title()
                self.status_label.setText(tr("status.import_complete", path=file_path))

    def _on_export(self):
        """내보내기."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, tr("dialog.export_title"), "", FileHandler.get_save_filters()
        )

        if file_path:
            file_path = self._ensure_file_extension(file_path, selected_filter)
            result = self._run_with_progress(
                tr("dialog.export_title"),
                tr("status.exporting"),
                lambda: FileHandler.save_file(self.family_tree, file_path),
            )
            if result:
                self.status_label.setText(tr("status.export_complete", path=file_path))
            else:
                detail = FileHandler.get_last_error()
                msg = tr("error.export_failed")
                if detail:
                    msg += f"\n\n{detail}"
                QMessageBox.warning(self, tr("error.export_failed"), msg)

    def _on_export_pdf(self):
        """PDF로 내보내기."""
        from ..utils.pdf_exporter import PdfExporter

        if not PdfExporter.is_available():
            QMessageBox.warning(self, tr("error.pdf_not_available"), tr("error.pdf_not_available"))
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog.export_pdf_title"), "", "PDF (*.pdf)"
        )

        if file_path:
            if not file_path.endswith(".pdf"):
                file_path += ".pdf"
            result = self._run_with_progress(
                tr("dialog.export_pdf_title"),
                tr("status.exporting"),
                lambda: PdfExporter.export(self.tree_canvas, file_path),
            )
            if result:
                self.status_label.setText(tr("status.pdf_exported", path=file_path))
            else:
                QMessageBox.warning(self, tr("error.pdf_export_failed"), tr("error.pdf_export_failed"))

    def _load_file(self, file_path: str) -> bool:
        """주어진 경로의 파일을 로드하고 UI를 갱신.

        드래그앤드롭(dropEvent)·백업 복구(_check_startup_recovery)·대화상자(_on_open)
        공통 진입점. 성공 시 True, 실패 시 사용자에게 경고를 표시하고 False 반환.
        """
        tree = self._run_with_progress(
            tr("dialog.open_title"),
            tr("status.loading_file"),
            lambda: FileHandler.load_file(file_path),
        )
        if tree:
            self.family_tree = tree
            self.current_file_path = file_path
            self.undo_manager.clear()
            self._update_undo_redo_state()
            self.tree_canvas.set_family_tree(self.family_tree)
            self.detail_panel.clear()
            self._update_person_list()
            self._update_title()
            self.status_label.setText(tr("status.file_opened", path=file_path))
            return True

        detail = FileHandler.get_last_error()
        msg = tr("error.file_open_failed")
        if detail:
            msg += f"\n\n{detail}"
        QMessageBox.warning(self, tr("error.file_open_failed"), msg)
        return False

    # _save_file 제거됨 — 저장은 _do_save에서 직접 수행

    def _check_save(self) -> bool:
        """저장 여부 확인. 계속 진행하면 True 반환."""
        if self.family_tree.is_modified:
            reply = QMessageBox.question(
                self,
                tr("dialog.save_confirm_title"),
                tr("dialog.save_confirm_message"),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Save:
                self._on_save()
                if self.family_tree.is_modified:
                    # 저장 실패 또는 취소 시 사용자에게 재선택 기회 제공
                    retry = QMessageBox.question(
                        self,
                        tr("dialog.save_confirm_title"),
                        tr("dialog.save_failed_continue", fallback="Save failed. Continue without saving?"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    return retry == QMessageBox.StandardButton.Yes
                return True
            elif reply == QMessageBox.StandardButton.Cancel:
                return False

        return True

    # === 편집 작업 ===

    def _on_add_person(self):
        """구성원 추가."""
        person = Person(name=tr("label.no_name"))

        # Use command pattern for undo/redo
        command = AddPersonCommand(self.family_tree, person)
        self.undo_manager.execute(command)
        self._update_undo_redo_state()

        self._update_person_list()
        self.tree_canvas.refresh()
        self.tree_canvas.select_person(person.id)
        self._update_title()
        self.status_label.setText(tr("status.new_member_added"))

    def _on_delete_person(self):
        """구성원 삭제."""
        selected_id = self.tree_canvas.selected_person_id
        if not selected_id:
            return

        person = self.family_tree.get_person(selected_id)
        if not person:
            return

        # 삭제 시 영향받는 관계 수 계산
        affected_relationships = [
            r
            for r in self.family_tree.get_all_relationships()
            if r.person1_id == selected_id or r.person2_id == selected_id
        ]
        rel_count = len(affected_relationships)

        # 경고 메시지에 관계 수 포함
        if rel_count > 0:
            message = tr(
                "dialog.delete_confirm_message_with_relationships",
                name=person.name,
                count=rel_count,
            )
        else:
            message = tr("dialog.delete_confirm_message", name=person.name)

        reply = QMessageBox.question(
            self,
            tr("dialog.delete_confirm_title"),
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Use command pattern for undo/redo
            command = DeletePersonCommand(self.family_tree, selected_id)
            self.undo_manager.execute(command)
            self._update_undo_redo_state()

            self._update_person_list()
            self.tree_canvas.refresh()
            self.detail_panel.clear()
            self._update_title()
            self.status_label.setText(tr("status.deleted", name=person.name))

    def _on_undo(self):
        """실행 취소."""
        description = self.undo_manager.undo()
        if description:
            self._update_undo_redo_state()
            self._update_person_list()
            self.tree_canvas.refresh()
            self._refresh_detail_panel()
            self.status_label.setText(tr("message.undo_success", action=description))

    def _on_redo(self):
        """다시 실행."""
        description = self.undo_manager.redo()
        if description:
            self._update_undo_redo_state()
            self._update_person_list()
            self.tree_canvas.refresh()
            self._refresh_detail_panel()
            self.status_label.setText(tr("message.redo_success", action=description))

    def _refresh_detail_panel(self):
        """Undo/Redo 후 detail_panel을 모델 현재 상태와 동기화.

        - 현재 선택된 인물이 삭제됐다면 패널을 비우고 선택 해제
        - 살아 있다면 새 Person 인스턴스로 재로드 (이름/속성 변경 반영)
        - 빈 트리가 됐다면 패널 비움
        """
        sel_id = self.tree_canvas.selected_person_id
        if not sel_id:
            self.detail_panel.clear()
            return
        person = self.family_tree.get_person(sel_id)
        if person:
            self.detail_panel.set_person(person, self.family_tree)
        else:
            # 선택된 인물이 사라짐 → 캔버스·패널 모두 정리
            self.tree_canvas.selected_person_id = None
            self.tree_canvas.refresh()
            self.detail_panel.clear()

    def _update_undo_redo_state(self):
        """Undo/Redo 버튼 상태 업데이트."""
        self.undo_action.setEnabled(self.undo_manager.can_undo())
        self.redo_action.setEnabled(self.undo_manager.can_redo())

        # 툴팁에 설명 추가
        if self.undo_manager.can_undo():
            desc = self.undo_manager.get_undo_description()
            self.undo_action.setToolTip(f"{tr('button.undo')}: {desc}")
        else:
            self.undo_action.setToolTip(tr("button.undo"))

        if self.undo_manager.can_redo():
            desc = self.undo_manager.get_redo_description()
            self.redo_action.setToolTip(f"{tr('button.redo')}: {desc}")
        else:
            self.redo_action.setToolTip(tr("button.redo"))

    # === 도움말 ===

    def _on_toggle_theme(self):
        """테마 토글."""
        theme_manager = get_theme_manager()
        new_theme = theme_manager.toggle_theme()
        self.status_label.setText(tr("status.theme_changed", theme=new_theme))

    def _on_about(self):
        """정보 대화상자."""
        QMessageBox.about(
            self,
            tr("about.title"),
            f"<h2>{tr('app.name')}</h2>"
            f"<p>{tr('app.version', version='1.0.0')}</p>"
            f"<p>{tr('about.description')}</p>"
            f"<p>{tr('about.formats')}</p>",
        )

    # === 사용자 피드백 ===

    def _run_with_progress(self, title: str, message: str, task):
        """프로그레스 다이얼로그와 함께 작업 실행 (백그라운드 스레드)."""
        from PyQt6.QtCore import QThread, pyqtSignal

        result_holder = [None]
        error_holder = [None]

        class WorkerThread(QThread):
            finished_signal = pyqtSignal()

            def __init__(self, task_fn):
                super().__init__()
                self.task_fn = task_fn

            def run(self):
                try:
                    result_holder[0] = self.task_fn()
                except Exception as e:
                    error_holder[0] = e

        progress = QProgressDialog(message, None, 0, 0, self)
        progress.setWindowTitle(title)
        progress.setMinimumDuration(300)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)

        worker = WorkerThread(task)
        worker.finished.connect(progress.close)
        worker.start()

        # 이벤트 루프 유지하며 대기 (UI 응답성 보장)
        while worker.isRunning():
            QApplication.processEvents()
            worker.wait(50)

        if error_holder[0]:
            from ..utils import logger
            logger.error(f"Background task failed: {error_holder[0]}")
            QMessageBox.critical(
                self,
                tr("error.operation_failed", fallback="Operation Failed"),
                str(error_holder[0]),
            )
            return None
        return result_holder[0]

    def _flash_status(self, message: str, duration: int = 3000):
        """임시 상태 메시지."""
        self.status_label.setText(message)
        QTimer.singleShot(duration, lambda: self.status_label.setText(tr("status.ready")))

    # === 정렬/필터 ===

    def _get_sorted_filtered_persons(self, persons):
        """정렬 및 필터 적용."""
        filter_key = self.filter_combo.currentData()
        if filter_key == "male":
            persons = [p for p in persons if p.gender == "M"]
        elif filter_key == "female":
            persons = [p for p in persons if p.gender == "F"]
        elif filter_key == "alive":
            persons = [p for p in persons if not p.death_year]
        elif filter_key == "deceased":
            persons = [p for p in persons if p.death_year]

        sort_key = self.sort_combo.currentData()
        if sort_key == "name_asc":
            persons.sort(key=lambda p: (p.name or "").lower())
        elif sort_key == "name_desc":
            persons.sort(key=lambda p: (p.name or "").lower(), reverse=True)
        elif sort_key == "birth_year":
            persons.sort(key=lambda p: p.birth_year or 9999)

        return persons

    # === 컨텍스트 메뉴 ===

    def _show_person_context_menu(self, pos, person_id: str, widget):
        """인물 목록 우클릭 메뉴."""
        menu = QMenu(self)
        select_action = menu.addAction(tr("context.select"))
        edit_action = menu.addAction(tr("context.edit"))
        menu.addSeparator()
        delete_action = menu.addAction(tr("context.delete"))

        action = menu.exec(widget.mapToGlobal(pos))
        if action == select_action:
            self.tree_canvas.select_person(person_id)
        elif action == edit_action:
            self.tree_canvas.select_person(person_id)
            self.detail_panel.start_edit()
        elif action == delete_action:
            self.tree_canvas.select_person(person_id)
            self._on_delete_person()

    def _show_canvas_context_menu(self, person_id: str, global_pos):
        """캔버스 우클릭 메뉴."""
        menu = QMenu(self)
        edit_action = menu.addAction(tr("context.edit"))
        set_parent_action = menu.addAction(tr("button.set_parent"))
        add_spouse_action = menu.addAction(tr("button.add_spouse"))
        add_child_action = menu.addAction(tr("button.add_child"))
        menu.addSeparator()
        zoom_action = menu.addAction(tr("context.zoom_to"))
        descendants_action = menu.addAction(tr("context.show_descendants"))
        ancestors_action = menu.addAction(tr("context.show_ancestors"))
        menu.addSeparator()
        delete_action = menu.addAction(tr("context.delete"))

        action = menu.exec(global_pos)
        if action == edit_action:
            self.tree_canvas.select_person(person_id)
            self.detail_panel.start_edit()
        elif action == set_parent_action:
            self.tree_canvas.select_person(person_id)
            self._on_add_relationship(person_id, RelationshipRequestType.PARENT)
        elif action == add_spouse_action:
            self.tree_canvas.select_person(person_id)
            self._on_add_relationship(person_id, RelationshipRequestType.SPOUSE)
        elif action == add_child_action:
            self.tree_canvas.select_person(person_id)
            self._on_add_relationship(person_id, RelationshipRequestType.CHILD)
        elif action == zoom_action:
            self.tree_canvas.select_person(person_id)
            self.tree_canvas.zoom_to_person(person_id)
        elif action == descendants_action:
            from .lineage_report_dialog import LineageReportDialog
            dlg = LineageReportDialog(self.family_tree, person_id, "descendants", self)
            dlg.exec()
        elif action == ancestors_action:
            from .lineage_report_dialog import LineageReportDialog
            dlg = LineageReportDialog(self.family_tree, person_id, "ancestors", self)
            dlg.exec()
        elif action == delete_action:
            self.tree_canvas.select_person(person_id)
            self._on_delete_person()

    # === 드래그앤드롭 ===

    def dragEnterEvent(self, event):
        """드래그 진입 이벤트 — 지원 파일이면 상태바에 안내 표시."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.json', '.xlsx', '.ged')):
                    event.acceptProposedAction()
                    filename = os.path.basename(path)
                    self.status_label.setText(
                        tr("status.drop_to_load", filename=filename)
                    )
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        """드래그가 창 밖으로 나가면 안내 메시지 원복."""
        self.status_label.setText(tr("status.ready"))
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """드롭 이벤트."""
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.json', '.xlsx', '.ged')):
                if self._check_save():
                    self._load_file(path)
                break

    # === 중복 감지 ===

    def _check_duplicate_name(self, name: str, exclude_id: str = "") -> bool:
        """유사한 이름의 인물이 있는지 확인. 계속하려면 True 반환."""
        from ..utils.duplicate_detector import find_similar_persons

        persons = self.family_tree.get_all_persons()
        similar = find_similar_persons(name, persons, threshold=2, exclude_id=exclude_id)

        if not similar:
            return True

        matches = "\n".join(f"  - {p.name}" for p, dist in similar)
        reply = QMessageBox.question(
            self,
            tr("dialog.duplicate_warning_title"),
            tr("dialog.duplicate_warning_message", name=name, matches=matches),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    # === 자동 백업 ===

    def _setup_auto_backup(self):
        """자동 백업 타이머 설정."""
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(self._perform_auto_backup)
        self._backup_timer.start(AUTO_BACKUP_INTERVAL_MINUTES * 60 * 1000)

    def _get_backup_dir(self) -> str:
        """백업 디렉토리 경로 반환."""
        return os.path.join(os.path.expanduser("~"), BACKUP_DIR)

    def _perform_auto_backup(self):
        """자동 백업 수행 (수정된 경우에만)."""
        if not self.family_tree.is_modified:
            return
        if not self.family_tree.get_all_persons():
            return

        from datetime import datetime

        backup_dir = self._get_backup_dir()
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"autosave_{timestamp}.json")

        FileHandler.save_json(self.family_tree, backup_path)
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        """오래된 백업 삭제 (최근 N개만 유지)."""
        backup_dir = self._get_backup_dir()
        if not os.path.exists(backup_dir):
            return

        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith("autosave_") and f.endswith(".json")],
            reverse=True,
        )

        for old_backup in backups[MAX_BACKUP_COUNT:]:
            try:
                os.remove(os.path.join(backup_dir, old_backup))
            except OSError:
                pass

    def _on_manage_backups(self):
        """백업 관리 다이얼로그 열기 — 사용자가 직접 복구/삭제/폴더 열기."""
        from .backup_manager_dialog import BackupManagerDialog

        dlg = BackupManagerDialog(self._get_backup_dir(), self)
        if dlg.exec() == BackupManagerDialog.DialogCode.Accepted and dlg.selected_path:
            # 복구 선택 시 현재 미저장 변경사항 확인 후 로드
            if self._check_save():
                if self._load_file(dlg.selected_path):
                    # 백업에서 복구한 경우 현재 파일 경로는 비워서
                    # 다음 저장이 Save As로 가도록 (실수 덮어쓰기 방지)
                    self.current_file_path = None
                    self._update_title()
                    self._flash_status(tr("status.recovered_from_backup"))

    def _check_startup_recovery(self):
        """시작 시 최근 백업에서 복구 제안."""
        from datetime import datetime, timedelta

        backup_dir = self._get_backup_dir()
        if not os.path.exists(backup_dir):
            return

        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith("autosave_") and f.endswith(".json")],
            reverse=True,
        )

        if not backups:
            return

        latest = backups[0]
        latest_path = os.path.join(backup_dir, latest)

        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(latest_path))
            if datetime.now() - mtime > timedelta(hours=1):
                return  # 1시간 이상 지난 백업은 무시
        except OSError:
            return

        time_str = mtime.strftime("%Y-%m-%d %H:%M")
        reply = QMessageBox.question(
            self,
            tr("dialog.recovery_title"),
            tr("dialog.recovery_message", time=time_str),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._load_file(latest_path)
            self.current_file_path = None  # 백업이므로 파일 경로 초기화
            self._update_title()
            self._flash_status(tr("status.recovered_from_backup"))

    def closeEvent(self, event):
        """창 닫기 이벤트."""
        self._backup_timer.stop()
        if self._check_save():
            self.tree_canvas.cleanup()
            event.accept()
        else:
            event.ignore()
