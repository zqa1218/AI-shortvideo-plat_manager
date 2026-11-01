from PySide6.QtWidgets import (
    QHeaderView, QPushButton, QTableWidget,
    QGroupBox, QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QColor

from app import database
from app.models import PLATFORMS, STATUS_LABELS
from app.ui.components import add_page_header

STATUS_COLORS = {
    "done": "#2E9E6B", "failed": "#E14B54", "scheduled": "#6E93B5",
    "manual_pending": "#D9A03F", "publishing": "#D9A03F",
}


class TasksPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.reload)
        add_page_header(
            layout, "发布任务", "追踪每个平台的执行状态，并快速定位需要处理的任务。",
            [refresh_btn],
        )
        tasks_box = QGroupBox("任务列表")
        tasks_layout = QVBoxLayout(tasks_box)
        tasks_layout.setContentsMargins(0, 10, 0, 0)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "标题", "类型", "平台", "状态", "定时", "创建时间"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        tasks_layout.addWidget(self.table)
        layout.addWidget(tasks_box, 3)
        detail_box = QGroupBox("选中任务的执行详情")
        detail_layout = QVBoxLayout(detail_box)
        detail_layout.setContentsMargins(0, 10, 0, 0)
        self.detail = QTableWidget(0, 4)
        self.detail.setHorizontalHeaderLabels(["平台", "状态", "说明", "时间"])
        self.detail.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.detail.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail.verticalHeader().setVisible(False)
        detail_layout.addWidget(self.detail)
        layout.addWidget(detail_box, 2)
        self.table.itemSelectionChanged.connect(self._show_detail)
        self.reload()

    def reload(self):
        tasks = database.query("SELECT * FROM tasks ORDER BY id DESC")
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            results = database.query("SELECT platform FROM task_results WHERE task_id=?", (task["id"],))
            platform_keys = [r["platform"] for r in results] or task["platforms"].split(",")
            platforms = "、".join(PLATFORMS[p]["name"] for p in platform_keys if p in PLATFORMS) or "-"
            values = [
                str(task["id"]), task["title"],
                "图文" if task["kind"] == "note" else "视频", platforms,
                STATUS_LABELS.get(task["status"], task["status"]),
                task["scheduled_at"] or "-", task["created_at"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 4:
                    item.setForeground(QColor(STATUS_COLORS.get(task["status"], "#8A7E78")))
                self.table.setItem(row, col, item)
        self.detail.setRowCount(0)

    def _show_detail(self):
        row = self.table.currentRow()
        if row < 0:
            return
        task_id = int(self.table.item(row, 0).text())
        results = database.query(
            "SELECT * FROM task_results WHERE task_id=? ORDER BY id DESC", (task_id,))
        self.detail.setRowCount(len(results))
        for i, result in enumerate(results):
            values = [
                PLATFORMS[result["platform"]]["name"],
                STATUS_LABELS.get(result["status"], result["status"]),
                result["message"], result["created_at"],
            ]
            for col, value in enumerate(values):
                self.detail.setItem(i, col, QTableWidgetItem(value))
