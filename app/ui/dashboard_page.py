from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
from PySide6.QtCore import QDateTime, Qt, QThread, QTime, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QCheckBox, QMessageBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QTimeEdit, QVBoxLayout, QWidget,
)

from app import database
from app.collectors import collect_all
from app.models import PLATFORMS
from app.ui.components import StatCard, add_page_header
from app.ui.themes import THEMES, get_config_value, load_theme_key, set_config_value


class CollectWorker(QThread):
    finished_all = Signal(list)

    def run(self):
        self.finished_all.emit(collect_all())


class MetricDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("录入作品数据")
        form = QFormLayout(self)
        self.platform = QComboBox()
        for key, info in PLATFORMS.items():
            self.platform.addItem(info["name"], key)
        form.addRow("平台", self.platform)
        self.title = QLineEdit()
        form.addRow("作品标题", self.title)
        self.spins = {}
        for key, label in [("plays", "播放/阅读"), ("likes", "点赞"),
                           ("comments", "评论"), ("favorites", "收藏"), ("shares", "分享")]:
            spin = QSpinBox()
            spin.setMaximum(10 ** 9)
            self.spins[key] = spin
            form.addRow(label, spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        self.collect_btn = QPushButton("自动采集")
        self.collect_btn.setObjectName("PrimaryButton")
        self.collect_btn.clicked.connect(self._collect)
        add_btn = QPushButton("录入数据")
        add_btn.clicked.connect(self._add_metric)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.reload)
        add_page_header(
            layout, "数据看板", "查看跨平台作品表现，跟踪每一次内容发布后的反馈。",
            [refresh_btn, add_btn, self.collect_btn],
        )
        cards = QGridLayout()
        cards.setSpacing(12)
        self.cards = {}
        definitions = [
            ("tasks", "累计任务", "全部发布任务"),
            ("done", "已完成", "成功完成发布"),
            ("pending", "待手动确认", "需要继续处理"),
            ("works", "作品数据", "跨平台数据快照"),
        ]
        for index, (key, label, caption) in enumerate(definitions):
            card = StatCard(label, caption)
            self.cards[key] = card.value
            cards.addWidget(card, 0, index)
        layout.addLayout(cards)

        chart_box = QGroupBox("平台互动概览")
        chart_layout = QVBoxLayout(chart_box)
        chart_layout.setContentsMargins(8, 12, 8, 8)
        self.chart = QChart()
        self.chart.setBackgroundVisible(False)
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(210)
        self.chart_view.setStyleSheet("border: none; background: transparent;")
        self.chart_view.setBackgroundBrush(QColor(0, 0, 0, 0))
        chart_layout.addWidget(self.chart_view)
        layout.addWidget(chart_box)

        auto_row = QHBoxLayout()
        self.auto_check = QCheckBox("每天自动采集（需保持应用打开）")
        self.auto_check.setChecked(bool(get_config_value("auto_collect", True)))
        self.auto_check.toggled.connect(lambda checked: set_config_value("auto_collect", checked))
        self.time_edit = QTimeEdit(QTime.fromString(get_config_value("collect_time", "08:00"), "HH:mm"))
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.timeChanged.connect(
            lambda time: set_config_value("collect_time", time.toString("HH:mm")))
        self.last_run_label = QLabel()
        self.last_run_label.setObjectName("Caption")
        auto_row.addWidget(self.auto_check)
        auto_row.addWidget(self.time_edit)
        auto_row.addWidget(self.last_run_label)
        auto_row.addStretch(1)
        layout.addLayout(auto_row)

        table_box = QGroupBox("最近作品数据")
        table_layout = QVBoxLayout(table_box)
        table_layout.setContentsMargins(0, 10, 0, 0)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["平台", "作品标题", "播放/阅读", "点赞", "评论", "收藏", "分享", "记录时间"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        table_layout.addWidget(self.table)
        layout.addWidget(table_box, 1)
        self.collect_worker = None
        self._collect_auto = False
        self._update_last_run_label()
        self.scheduler = QTimer(self)
        self.scheduler.setInterval(30000)
        self.scheduler.timeout.connect(self._maybe_auto_collect)
        self.scheduler.start()
        self.reload()

    def _update_last_run_label(self):
        last_run = get_config_value("last_collect_run", "")
        self.last_run_label.setText(f"上次采集：{last_run}" if last_run else "尚未自动采集")

    def _maybe_auto_collect(self):
        if not self.auto_check.isChecked():
            return
        if self.collect_worker is not None and self.collect_worker.isRunning():
            return
        now = QDateTime.currentDateTime()
        if now.time() < self.time_edit.time():
            return
        today = now.toString("yyyy-MM-dd")
        if get_config_value("last_collect_date", "") == today:
            return
        set_config_value("last_collect_date", today)
        self._start_collect(auto=True)

    def _start_collect(self, auto=False):
        self._collect_auto = auto
        self.collect_btn.setEnabled(False)
        self.collect_btn.setText("采集中…")
        self.collect_worker = CollectWorker()
        self.collect_worker.finished_all.connect(self._collect_done)
        self.collect_worker.start()

    def _collect(self):
        self._start_collect(auto=False)

    def _collect_done(self, summaries):
        self.collect_btn.setEnabled(True)
        self.collect_btn.setText("自动采集作品数据")
        self.reload()
        total = sum(s["count"] for s in summaries)
        run_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm")
        set_config_value("last_collect_run", f"{run_time}，{total} 条作品")
        self._update_last_run_label()
        if self._collect_auto:
            return
        lines = [f"{s['account']}：{s['message']}" for s in summaries]
        QMessageBox.information(self, "采集结果", "\n".join(lines))

    def reload(self):
        stats = database.query(
            "SELECT count(*) AS total, "
            "sum(status='done') AS done, sum(status='manual_pending') AS pending FROM tasks")[0]
        self.cards["tasks"].setText(str(stats["total"] or 0))
        self.cards["done"].setText(str(stats["done"] or 0))
        self.cards["pending"].setText(str(stats["pending"] or 0))
        metrics = database.query("SELECT * FROM metrics ORDER BY id DESC")
        self.cards["works"].setText(str(len(metrics)))
        self._update_chart(metrics)
        self.table.setRowCount(len(metrics))
        for row, metric in enumerate(metrics):
            values = [
                PLATFORMS[metric["platform"]]["name"], metric["work_title"],
                str(metric["plays"]), str(metric["likes"]), str(metric["comments"]),
                str(metric["favorites"]), str(metric["shares"]), metric["recorded_at"],
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))
                if 2 <= col <= 6:
                    self.table.item(row, col).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _update_chart(self, metrics):
        palette = THEMES[load_theme_key()]
        text_color = QColor(palette["text"])
        self.chart.legend().setLabelColor(text_color)
        totals = {key: [0, 0, 0] for key in PLATFORMS}
        for metric in metrics:
            if metric["platform"] in totals:
                totals[metric["platform"]][0] += metric["plays"]
                totals[metric["platform"]][1] += metric["likes"]
                totals[metric["platform"]][2] += metric["comments"]
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        series = QBarSeries()
        colors = [palette["primary"], palette["accent"], palette["muted"]]
        for i, (label, color) in enumerate(zip(["播放/阅读", "点赞", "评论"], colors)):
            bar = QBarSet(label)
            bar.setColor(QColor(color))
            for key in PLATFORMS:
                bar.append(totals[key][i])
            series.append(bar)
        self.chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append([info["name"] for info in PLATFORMS.values()])
        axis_x.setLabelsColor(text_color)
        axis_x.setGridLineVisible(False)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(text_color)
        axis_y.setGridLineColor(QColor(palette["border"]))
        axis_y.applyNiceNumbers()
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

    def _add_metric(self):
        dialog = MetricDialog(self)
        if not dialog.exec():
            return
        title = dialog.title.text().strip()
        if not title:
            return
        database.execute(
            "INSERT INTO metrics (platform, work_title, plays, likes, comments, favorites, shares)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (dialog.platform.currentData(), title,
             dialog.spins["plays"].value(), dialog.spins["likes"].value(),
             dialog.spins["comments"].value(), dialog.spins["favorites"].value(),
             dialog.spins["shares"].value()),
        )
        self.reload()
