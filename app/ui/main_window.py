from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QListWidget, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
)

from app import database
from app.ui.accounts_page import AccountsPage
from app.ui.dashboard_page import DashboardPage
from app.ui.materials_page import MaterialsPage
from app.ui.publish_page import PublishPage
from app.ui.schedule_page import SchedulePage, task_from_row
from app.ui.tasks_page import TasksPage
from app.ui.themes import THEMES, build_qss, load_theme_key, save_theme_key
from app.ui.worker import PublishWorker

from app.paths import asset_path
from app import autostart

ICON_PATH = asset_path("cat_round.png")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        database.init_db()
        self.setWindowTitle("猫后台助手")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(1280, 800)
        self.setMinimumSize(1080, 700)
        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.tasks_page = TasksPage()
        self.dashboard_page = DashboardPage()
        self.publish_page = PublishPage(self._refresh_views)
        self.accounts_page = AccountsPage()
        self.materials_page = MaterialsPage(self._use_materials)
        self.schedule_page = SchedulePage(self._refresh_views)
        for page in [self.publish_page, self.materials_page, self.schedule_page,
                     self.tasks_page, self.dashboard_page, self.accounts_page]:
            page.setObjectName("Page")
            page.layout().setContentsMargins(28, 24, 28, 24)
            self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.currentRowChanged.connect(self._refresh_views)
        self.nav.setCurrentRow(0)
        self._apply_theme(load_theme_key())
        self.scheduler_workers = []
        self.publish_scheduler = QTimer(self)
        self.publish_scheduler.setInterval(60000)
        self.publish_scheduler.timeout.connect(self._run_due_tasks)
        self.publish_scheduler.start()

    def _use_materials(self, paths):
        self.publish_page.set_media(paths)
        self.nav.setCurrentRow(0)

    def _run_due_tasks(self):
        due = database.query(
            "SELECT * FROM tasks WHERE status='scheduled' AND scheduled_at <= datetime('now', 'localtime')")
        for row in due:
            task = task_from_row(row)
            worker = PublishWorker(task.id, task, "sau", {"tid": task.tid or "249"})
            worker.finished_all.connect(lambda _: self._refresh_views())
            self.scheduler_workers.append(worker)
            worker.start()

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(216)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(10)
        brand = QHBoxLayout()
        brand.setSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(ICON_PATH).scaled(
            42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand.addWidget(icon_label)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        title = QLabel("猫后台助手")
        title.setObjectName("AppTitle")
        brand_text.addWidget(title)
        subtitle = QLabel("多平台社媒管理工作台")
        subtitle.setObjectName("AppSubtitle")
        brand_text.addWidget(subtitle)
        brand.addLayout(brand_text, 1)
        side_layout.addLayout(brand)
        side_layout.addSpacing(22)
        workspace_label = QLabel("工作区")
        workspace_label.setObjectName("SectionLabel")
        side_layout.addWidget(workspace_label)
        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        self.nav.addItems(["↗  发布中心", "▦  素材库", "◷  发布计划", "≡  发布任务", "◫  数据看板", "◎  账号管理"])
        self.nav.setSpacing(2)
        side_layout.addWidget(self.nav, 1)
        scope_label = QLabel("B站  ·  小红书  ·  抖音")
        scope_label.setObjectName("SidebarScope")
        side_layout.addWidget(scope_label)
        side_layout.addSpacing(8)
        theme_label = QLabel("界面主题")
        theme_label.setObjectName("SectionLabel")
        side_layout.addWidget(theme_label)
        self.theme_combo = QComboBox()
        for key, theme in THEMES.items():
            self.theme_combo.addItem(theme["name"], key)
        self.theme_combo.setCurrentIndex(list(THEMES).index(load_theme_key()))
        self.theme_combo.currentIndexChanged.connect(
            lambda _: self._apply_theme(self.theme_combo.currentData()))
        side_layout.addWidget(self.theme_combo)
        autostart_check = QCheckBox("开机自启")
        autostart_check.setChecked(autostart.is_enabled())
        autostart_check.toggled.connect(autostart.set_enabled)
        side_layout.addWidget(autostart_check)
        status_label = QLabel("●  本地工作区")
        status_label.setObjectName("WorkspaceStatus")
        side_layout.addWidget(status_label)
        return sidebar

    def _apply_theme(self, key):
        QApplication.instance().setStyleSheet(build_qss(key))
        save_theme_key(key)
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.reload()

    def _refresh_views(self):
        self.tasks_page.reload()
        self.dashboard_page.reload()
        if hasattr(self, "schedule_page"):
            self.schedule_page.reload()
