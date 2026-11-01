from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app import database
from app.models import PLATFORMS, Task
from app.ui.components import add_page_header
from app.ui.themes import THEMES, load_theme_key
from app.ui.worker import PublishWorker


def task_from_row(row):
    return Task(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        tags=row["tags"],
        media_path=row["media_path"],
        kind=row["kind"],
        images=[p for p in row["images"].split(";") if p],
        platforms=[p for p in row["platforms"].split(",") if p],
        scheduled_at=row["scheduled_at"],
        tid=(row.get("tid") or "249") if hasattr(row, "get") else "249",
    )


class SchedulePage(QWidget):
    def __init__(self, on_changed):
        super().__init__()
        self.on_changed = on_changed
        self.workers = []
        self.show_all = False
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        add_page_header(
            layout, "发布计划", "用日历安排内容节奏，确保每个平台持续稳定更新。",
        )
        self.reminder = QLabel()
        self.reminder.setObjectName("Notice")
        self.reminder.setWordWrap(True)
        layout.addWidget(self.reminder)

        splitter = QSplitter()
        calendar_box = QGroupBox("排期日历")
        calendar_layout = QVBoxLayout(calendar_box)
        calendar_layout.setContentsMargins(8, 12, 8, 8)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMaximumWidth(420)
        self.calendar.selectionChanged.connect(self.reload)
        calendar_layout.addWidget(self.calendar)
        splitter.addWidget(calendar_box)
        table_box = QGroupBox("发布列表")
        table_layout = QVBoxLayout(table_box)
        table_layout.setContentsMargins(0, 10, 0, 0)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "标题", "类型", "平台", "计划发布时间"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for column in (0, 2, 3, 4):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.empty_label = QLabel("这一天还没有发布计划\n\n从发布中心创建定时任务后会显示在这里", self.table.viewport())
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName("Caption")
        self.empty_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_box)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        actions = QHBoxLayout()
        now_btn = QPushButton("立即发布选中")
        now_btn.setObjectName("PrimaryButton")
        now_btn.clicked.connect(self._publish_now)
        cancel_btn = QPushButton("取消排期（转为草稿）")
        cancel_btn.clicked.connect(self._cancel)
        self.all_btn = QPushButton("查看全部排期")
        self.all_btn.setCheckable(True)
        self.all_btn.toggled.connect(self._toggle_all)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.reload)
        actions.addWidget(now_btn)
        actions.addWidget(cancel_btn)
        actions.addWidget(self.all_btn)
        actions.addStretch(1)
        actions.addWidget(refresh_btn)
        layout.addLayout(actions)
        self.reload()

    def _toggle_all(self, checked):
        self.show_all = checked
        self.all_btn.setText("查看全部排期" if not checked else "仅看选中日期")
        self.reload()

    def _mark_calendar(self, tasks):
        default_format = QTextCharFormat()
        for date in self._marked_dates if hasattr(self, "_marked_dates") else []:
            self.calendar.setDateTextFormat(date, default_format)
        self._marked_dates = set()
        mark = QTextCharFormat()
        palette = THEMES[load_theme_key()]
        marker_color = QColor(palette["primary"])
        marker_color.setAlpha(42)
        mark.setBackground(marker_color)
        mark.setForeground(QColor(palette["primary"]))
        mark.setFontWeight(700)
        for task in tasks:
            date = QDate.fromString(task["scheduled_at"].split(" ")[0], "yyyy-MM-dd")
            if date.isValid():
                self.calendar.setDateTextFormat(date, mark)
                self._marked_dates.add(date)

    def reload(self):
        all_tasks = database.query("SELECT * FROM tasks WHERE status='scheduled' ORDER BY scheduled_at")
        self._mark_calendar(all_tasks)
        if self.show_all:
            tasks = all_tasks
        else:
            selected = self.calendar.selectedDate().toString("yyyy-MM-dd")
            tasks = [t for t in all_tasks if t["scheduled_at"].startswith(selected)]
        self.table.setRowCount(len(tasks))
        self.empty_label.setGeometry(self.table.viewport().rect())
        self.empty_label.setVisible(not tasks)
        for row, task in enumerate(tasks):
            platforms = "、".join(PLATFORMS[p]["name"] for p in task["platforms"].split(",") if p in PLATFORMS)
            values = [str(task["id"]), task["title"],
                      "图文" if task["kind"] == "note" else "视频", platforms, task["scheduled_at"]]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
        upcoming = database.query(
            "SELECT count(*) AS n FROM tasks WHERE status='scheduled' "
            "AND scheduled_at <= datetime('now', 'localtime', '+3 days')")[0]["n"]
        if all_tasks and upcoming:
            self.reminder.setText(f"未来 3 天已排期 {upcoming} 条，共 {len(all_tasks)} 条待发布；日历中红色日期为有排期的日子。")
        else:
            self.reminder.setText("未来 3 天暂无发布计划，记得去素材库挑素材排期，避免断更。")

    def _selected_task(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        task_id = int(self.table.item(row, 0).text())
        rows = database.query("SELECT * FROM tasks WHERE id=?", (task_id,))
        return task_from_row(rows[0]) if rows else None

    def _publish_now(self):
        task = self._selected_task()
        if task is None:
            return
        database.execute("UPDATE tasks SET scheduled_at='' WHERE id=?", (task.id,))
        task.scheduled_at = ""
        worker = PublishWorker(task.id, task, "sau", {"tid": task.tid or "249"})
        worker.finished_all.connect(lambda _: self.on_changed())
        worker.finished_all.connect(lambda _: QMessageBox.information(
            self, "发布", "发布任务已结束，请在发布任务页查看结果。"))
        self.workers.append(worker)
        worker.start()

    def _cancel(self):
        task = self._selected_task()
        if task is None:
            return
        database.execute("UPDATE tasks SET status='draft', scheduled_at='' WHERE id=?", (task.id,))
        self.on_changed()
