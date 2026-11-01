import os

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSizePolicy, QTextEdit, QToolButton, QVBoxLayout, QWidget,
)

from app import database
from app.models import PLATFORMS, Task, platform_issues
from app.publishers import sau
from app.ui.components import add_page_header
from app.ui.materials_page import MaterialPickerDialog
from app.ui.preview_dialog import PreviewDialog
from app.ui.worker import PublishWorker


class PublishPage(QWidget):
    def __init__(self, on_task_changed):
        super().__init__()
        self.on_task_changed = on_task_changed
        self.workers = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        add_page_header(
            layout, "发布中心", "一次编辑内容，选择目标平台并完成发布或排期。",
        )
        content_box = QGroupBox("作品内容")
        form = QFormLayout(content_box)
        form.setContentsMargins(12, 14, 12, 12)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(9)
        self.kind_combo = QComboBox()
        self.kind_combo.setMaximumWidth(180)
        self.kind_combo.addItem("视频", "video")
        self.kind_combo.addItem("图文笔记", "note")
        self.kind_combo.currentIndexChanged.connect(self._kind_changed)
        form.addRow("内容类型", self.kind_combo)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("作品标题")
        form.addRow("标题", self.title_edit)
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("正文 / 简介 / 文案")
        self.content_edit.setMaximumHeight(120)
        form.addRow("正文", self.content_edit)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("标签，用逗号分隔")
        form.addRow("标签", self.tags_edit)
        media_row = QHBoxLayout()
        self.media_edit = QLineEdit()
        self.media_edit.setPlaceholderText("视频或封面文件路径（可选）")
        browse_btn = QPushButton("浏览…")
        browse_btn.clicked.connect(self._browse)
        library_btn = QPushButton("素材库…")
        library_btn.clicked.connect(self._pick_from_library)
        media_row.addWidget(self.media_edit)
        media_row.addWidget(browse_btn)
        media_row.addWidget(library_btn)
        form.addRow("素材", media_row)
        layout.addWidget(content_box)

        settings_box = QGroupBox("发布设置")
        settings_layout = QVBoxLayout(settings_box)
        settings_layout.setContentsMargins(12, 14, 12, 12)
        settings_layout.setSpacing(10)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("发布方式"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("自动发布（social-auto-upload）", "sau")
        self.mode_combo.addItem("半自动（打开创作者后台）", "manual")
        if not sau.available():
            self.mode_combo.setCurrentIndex(1)
        self.mode_combo.currentIndexChanged.connect(self._update_hint)
        mode_row.addWidget(self.mode_combo)
        mode_row.addWidget(QLabel("B站分区 tid"))
        self.tid_edit = QLineEdit("249")
        self.tid_edit.setFixedWidth(70)
        mode_row.addWidget(self.tid_edit)
        mode_row.addStretch(1)
        settings_layout.addLayout(mode_row)

        platform_layout = QHBoxLayout()
        platform_layout.setSpacing(10)
        platform_layout.addWidget(QLabel("目标平台"))
        self.platform_checks = {}
        for key, info in PLATFORMS.items():
            check = QToolButton()
            check.setObjectName("PlatformButton")
            check.setText(info["name"])
            check.setCheckable(True)
            check.setChecked(True)
            check.setMinimumSize(96, 36)
            check.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.platform_checks[key] = check
            platform_layout.addWidget(check)
        platform_layout.addStretch(1)
        settings_layout.addLayout(platform_layout)

        schedule_row = QHBoxLayout()
        self.schedule_check = QCheckBox("定时发布")
        self.schedule_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.schedule_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.schedule_edit.setCalendarPopup(True)
        self.schedule_edit.setMinimumWidth(180)
        self.schedule_edit.setEnabled(False)
        self.schedule_check.toggled.connect(self.schedule_edit.setEnabled)
        schedule_row.addWidget(self.schedule_check)
        schedule_row.addWidget(self.schedule_edit)
        schedule_row.addStretch(1)
        settings_layout.addLayout(schedule_row)
        layout.addWidget(settings_box)

        btn_row = QHBoxLayout()
        draft_btn = QPushButton("保存草稿")
        draft_btn.clicked.connect(lambda: self._save("draft"))
        preview_btn = QPushButton("预览效果")
        preview_btn.clicked.connect(self._preview)
        publish_btn = QPushButton("发布")
        publish_btn.setObjectName("PrimaryButton")
        publish_btn.setDefault(True)
        publish_btn.clicked.connect(self._publish)
        btn_row.addStretch(1)
        btn_row.addWidget(draft_btn)
        btn_row.addWidget(preview_btn)
        btn_row.addWidget(publish_btn)
        layout.addLayout(btn_row)

        self.hint = QLabel()
        self.hint.setObjectName("Caption")
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        self._update_hint()
        layout.addStretch(1)

    def _platform_scope(self):
        parts = []
        for info in PLATFORMS.values():
            kinds = "、".join("图文" if kind == "note" else "视频" for kind in info["kinds"])
            parts.append(f"{info['name']}（{kinds}）")
        return " · ".join(parts)

    def _update_hint(self):
        scope = f"支持范围：{self._platform_scope()}；标题与话题会按各平台上限自动截断。"
        if self.mode_combo.currentData() == "sau":
            self.hint.setText(
                "自动发布：调用 social-auto-upload 后台上传，需先在账号管理中完成扫码登录；"
                "视频选择视频文件，图文笔记选择多张图片。" + scope)
        else:
            self.hint.setText(
                "半自动模式：点击发布后自动打开各平台创作者后台，上传动作在浏览器中完成。" + scope)

    def _browse(self):
        if self.kind_combo.currentData() == "note":
            paths, _ = QFileDialog.getOpenFileNames(
                self, "选择图片（可多选）", "", "图片文件 (*.png *.jpg *.jpeg *.webp)")
            if paths:
                self.media_edit.setText(";".join(paths))
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择视频", "", "视频文件 (*.mp4 *.mov *.mkv *.flv *.avi);;所有文件 (*)")
            if path:
                self.media_edit.setText(path)

    def _kind_changed(self):
        self.media_edit.clear()
        is_note = self.kind_combo.currentData() == "note"
        self.media_edit.setPlaceholderText("图片路径，多张用 ; 分隔" if is_note else "视频文件路径")
        bilibili_check = self.platform_checks["bilibili"]
        bilibili_check.setEnabled(not is_note)
        if is_note:
            bilibili_check.setChecked(False)
        self._update_hint()

    def _pick_from_library(self):
        is_note = self.kind_combo.currentData() == "note"
        dialog = MaterialPickerDialog(multi=is_note, kind="" if is_note else "video", parent=self)
        if dialog.exec():
            paths = dialog.selected_paths()
            if paths:
                self.media_edit.setText(";".join(paths))

    def set_media(self, paths):
        is_note = len(paths) > 1 or paths[0].lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"))
        self.kind_combo.setCurrentIndex(1 if is_note else 0)
        self.media_edit.setText(";".join(paths))

    def _selected_platforms(self):
        return [key for key, check in self.platform_checks.items() if check.isChecked()]

    def _collect(self):
        kind = self.kind_combo.currentData()
        raw_media = self.media_edit.text().strip()
        return Task(
            title=self.title_edit.text().strip(),
            content=self.content_edit.toPlainText().strip(),
            tags=self.tags_edit.text().strip(),
            media_path=raw_media if kind == "video" else "",
            kind=kind,
            images=[p for p in raw_media.split(";") if p] if kind == "note" else [],
            platforms=self._selected_platforms(),
            scheduled_at=self.schedule_edit.dateTime().toString("yyyy-MM-dd HH:mm")
            if self.schedule_check.isChecked() else "",
            tid=self.tid_edit.text().strip() or "249",
        )

    def _validate(self, task):
        if not task.title:
            QMessageBox.warning(self, "提示", "请填写标题")
            return False
        if not task.platforms:
            QMessageBox.warning(self, "提示", "请至少选择一个平台")
            return False

        # 平台之间规则不同：B 站不收图文、小红书/抖音标题 20 字、图片张数也有上限。
        blocking, warnings = [], []
        for platform in task.platforms:
            for level, text in platform_issues(
                    platform, task.kind, task.title, len(task.images), task.tags):
                (blocking if level == "error" else warnings).append(text)
        if blocking:
            QMessageBox.warning(self, "平台限制", "\n".join(dict.fromkeys(blocking)))
            return False
        if warnings:
            QMessageBox.information(
                self, "平台限制",
                "\n".join(["以下内容会按各平台规则自动调整：", *dict.fromkeys(warnings)]))
        if self.mode_combo.currentData() == "sau":
            if task.kind == "note":
                if not task.images or any(not os.path.isfile(p) for p in task.images):
                    QMessageBox.warning(self, "提示", "图文笔记需要选择至少一张存在的图片")
                    return False
            elif not task.media_path or not os.path.isfile(task.media_path):
                QMessageBox.warning(self, "提示", "自动发布需要选择存在的视频文件")
                return False
            if not sau.available():
                QMessageBox.warning(self, "提示", "未检测到 social-auto-upload，请检查 vendor 目录安装")
                return False
        return True

    def _save(self, status):
        task = self._collect()
        if not self._validate(task):
            return None
        paths = task.images if task.kind == "note" else [task.media_path]
        material_ids = []
        for path in paths:
            if not path:
                continue
            rows = database.query("SELECT id FROM materials WHERE path=?", (path,))
            material_ids += [str(row["id"]) for row in rows]
        task_id = database.execute(
            "INSERT INTO tasks (title, content, tags, media_path, kind, images, platforms, material_ids, scheduled_at, tid, status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task.title, task.content, task.tags, task.media_path, task.kind,
             ";".join(task.images), ",".join(task.platforms), ",".join(material_ids),
             task.scheduled_at, task.tid, status),
        )
        task.id = task_id
        self.on_task_changed()
        return task

    def _publish(self):
        scheduled = (self.schedule_check.isChecked()
                     and self.schedule_edit.dateTime() > QDateTime.currentDateTime())
        if scheduled:
            task = self._save("scheduled")
            if task is not None:
                QMessageBox.information(self, "发布计划", f"已加入发布计划，将于 {task.scheduled_at} 自动发布。")
            return
        task = self._save("queued")
        if task is None:
            return
        publisher_name = self.mode_combo.currentData()
        worker = PublishWorker(task.id, task, publisher_name, {"tid": self.tid_edit.text().strip() or "249"})
        worker.finished_all.connect(lambda _: self.on_task_changed())
        if publisher_name == "sau":
            worker.finished_all.connect(lambda _: QMessageBox.information(
                self, "发布", "自动发布任务已结束，请在发布任务页查看各平台结果。"))
        else:
            worker.finished_all.connect(lambda _: QMessageBox.information(
                self, "发布", "已打开所选平台的创作者后台，请在浏览器中完成上传。"))
        self.workers.append(worker)
        worker.start()

    def _preview(self):
        task = self._collect()
        if not task.platforms:
            QMessageBox.information(self, "发布预览", "请先选择至少一个目标平台")
            return
        PreviewDialog(task, self).exec()
