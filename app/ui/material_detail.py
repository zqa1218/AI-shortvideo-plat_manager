from PySide6.QtWidgets import (
    QDialog, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from app import database
from app.models import PLATFORMS, STATUS_LABELS


class MaterialDetailDialog(QDialog):
    def __init__(self, material, parent=None):
        super().__init__(parent)
        self.setWindowTitle("素材发布与表现")
        self.resize(860, 560)
        layout = QVBoxLayout(self)
        name = material["path"].replace("\\", "/").rsplit("/", 1)[-1]
        layout.addWidget(QLabel(f"{name}　[{material['tags'] or '未打标'}]"))

        pattern = f"%,{material['id']},%"
        tasks = database.query(
            "SELECT * FROM tasks WHERE (',' || material_ids || ',') LIKE ? ORDER BY id DESC", (pattern,))
        layout.addWidget(QLabel(f"关联发布任务（{len(tasks)}）"))
        self.tasks_table = QTableWidget(0, 4)
        self.tasks_table.setHorizontalHeaderLabels(["标题", "状态", "计划时间", "创建时间"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tasks_table)
        self.tasks_table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            values = [task["title"], STATUS_LABELS.get(task["status"], task["status"]),
                      task["scheduled_at"] or "-", task["created_at"]]
            for col, value in enumerate(values):
                self.tasks_table.setItem(row, col, QTableWidgetItem(value))

        titles = [task["title"] for task in tasks]
        metrics = []
        for title in titles:
            metrics += database.query("SELECT * FROM metrics WHERE work_title=?", (title,))
        layout.addWidget(QLabel(f"跨平台作品数据（{len(metrics)} 条快照，按任务标题匹配）"))
        self.metrics_table = QTableWidget(0, 6)
        self.metrics_table.setHorizontalHeaderLabels(["平台", "作品标题", "播放/阅读", "点赞", "评论", "记录时间"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.metrics_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.metrics_table)
        self.metrics_table.setRowCount(len(metrics))
        totals = {}
        for row, metric in enumerate(metrics):
            values = [PLATFORMS[metric["platform"]]["name"], metric["work_title"],
                      str(metric["plays"]), str(metric["likes"]), str(metric["comments"]),
                      metric["recorded_at"]]
            for col, value in enumerate(values):
                self.metrics_table.setItem(row, col, QTableWidgetItem(value))
            total = totals.setdefault(metric["platform"], [0, 0, 0])
            total[0] += metric["plays"]
            total[1] += metric["likes"]
            total[2] += metric["comments"]
        if totals:
            summary = "；".join(
                f"{PLATFORMS[p]['name']} 播放 {v[0]} / 点赞 {v[1]} / 评论 {v[2]}" for p, v in totals.items())
        else:
            summary = "暂无数据，可先在数据看板执行自动采集"
        layout.addWidget(QLabel(summary))
