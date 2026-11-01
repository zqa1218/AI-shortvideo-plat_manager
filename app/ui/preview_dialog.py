import os

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSlider, QStackedWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from app.models import PLATFORMS
from app.ui.components import add_page_header


def format_time(milliseconds):
    seconds = max(0, milliseconds // 1000)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class ImagePreviewLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setObjectName("PreviewMedia")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(330)
        self.source_pixmap = QPixmap()

    def set_image(self, path):
        self.source_pixmap = QPixmap(path) if path else QPixmap()
        self._scale_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_pixmap()

    def _scale_pixmap(self):
        if self.source_pixmap.isNull():
            return
        self.setPixmap(self.source_pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


class PreviewDialog(QDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.images = [path for path in task.images if os.path.isfile(path)]
        self.image_index = 0
        self.setWindowTitle("发布预览")
        self.resize(900, 720)
        self.setMinimumSize(780, 660)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)
        self.platform_combo = QComboBox()
        for key in task.platforms:
            if key in PLATFORMS:
                self.platform_combo.addItem(PLATFORMS[key]["name"], key)
        self.platform_combo.currentIndexChanged.connect(self._platform_changed)
        add_page_header(
            layout, "发布预览", "检查素材、文案与排版，确认无误后再发布。",
            [self.platform_combo],
        )

        content_row = QHBoxLayout()
        content_row.setSpacing(18)
        content_row.addWidget(self._build_phone(), 1)
        content_row.addWidget(self._build_summary())
        layout.addLayout(content_row, 1)
        note = QLabel("预览用于检查内容与素材，实际展示效果可能因平台客户端版本而有所不同。")
        note.setObjectName("Caption")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText("关闭")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._platform_changed()

    def _build_phone(self):
        phone = QFrame()
        phone.setObjectName("PreviewPhone")
        phone.setMaximumWidth(460)
        layout = QVBoxLayout(phone)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        self.platform_label = QLabel()
        self.platform_label.setObjectName("PreviewPlatform")
        layout.addWidget(self.platform_label)
        self.media_stack = QStackedWidget()
        layout.addWidget(self.media_stack, 1)
        if self.task.kind == "note":
            self._build_note_media()
        else:
            self._build_video_media()

        title = QLabel(self.task.title or "未填写标题")
        title.setObjectName("PreviewTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        body = QTextEdit(self.task.content or "未填写正文")
        body.setObjectName("PreviewBody")
        body.setReadOnly(True)
        body.setMaximumHeight(86)
        layout.addWidget(body)
        tags = [tag.strip().lstrip("#") for tag in self.task.tags.replace("，", ",").split(",") if tag.strip()]
        tag_label = QLabel(" ".join(f"#{tag}" for tag in tags) if tags else "暂无标签")
        tag_label.setObjectName("PreviewTags")
        tag_label.setWordWrap(True)
        layout.addWidget(tag_label)
        return phone

    def _build_note_media(self):
        self.image_label = ImagePreviewLabel()
        self.media_stack.addWidget(self.image_label)
        empty = QLabel("没有可预览的图片\n请返回发布中心选择素材")
        empty.setObjectName("PreviewMedia")
        empty.setAlignment(Qt.AlignCenter)
        self.media_stack.addWidget(empty)
        controls = QHBoxLayout()
        previous = QPushButton("上一张")
        previous.clicked.connect(lambda: self._change_image(-1))
        self.image_count = QLabel()
        self.image_count.setAlignment(Qt.AlignCenter)
        next_button = QPushButton("下一张")
        next_button.clicked.connect(lambda: self._change_image(1))
        controls.addWidget(previous)
        controls.addWidget(self.image_count, 1)
        controls.addWidget(next_button)
        self._note_controls = QWidget()
        self._note_controls.setLayout(controls)
        self.media_stack.parentWidget().layout().addWidget(self._note_controls)
        previous.setEnabled(len(self.images) > 1)
        next_button.setEnabled(len(self.images) > 1)
        self._show_image()

    def _build_video_media(self):
        self.video_widget = QVideoWidget()
        self.video_widget.setObjectName("PreviewVideo")
        self.video_widget.setMinimumHeight(300)
        self.media_stack.addWidget(self.video_widget)
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        controls = QHBoxLayout()
        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self._toggle_playback)
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.sliderMoved.connect(self.player.setPosition)
        self.time_label = QLabel("00:00 / 00:00")
        controls.addWidget(self.play_button)
        controls.addWidget(self.position_slider, 1)
        controls.addWidget(self.time_label)
        self.media_stack.parentWidget().layout().addLayout(controls)
        self.video_status = QLabel()
        self.video_status.setObjectName("Caption")
        self.media_stack.parentWidget().layout().addWidget(self.video_status)
        self.player.positionChanged.connect(self._position_changed)
        self.player.durationChanged.connect(self._duration_changed)
        self.player.playbackStateChanged.connect(self._playback_changed)
        self.player.errorOccurred.connect(
            lambda *_: self.video_status.setText("视频无法解码，请检查文件格式或重新选择素材。"))
        if self.task.media_path and os.path.isfile(self.task.media_path):
            self.player.setSource(QUrl.fromLocalFile(self.task.media_path))
            self.video_status.setText("视频加载中…")
        else:
            self.play_button.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.video_status.setText("没有可预览的视频，请返回发布中心选择素材。")

    def _build_summary(self):
        box = QGroupBox("内容信息")
        box.setMinimumWidth(230)
        box.setMaximumWidth(270)
        layout = QVBoxLayout(box)
        layout.setSpacing(12)
        kind = "图文笔记" if self.task.kind == "note" else "视频"
        if self.task.kind == "note":
            media = f"{len(self.images)} / {len(self.task.images)} 张图片可用"
        else:
            media = os.path.basename(self.task.media_path) if self.task.media_path else "未选择视频"
        rows = [
            ("内容类型", kind),
            ("素材", media),
            ("标题字数", str(len(self.task.title))),
            ("正文字数", str(len(self.task.content))),
            ("目标平台", "、".join(PLATFORMS[key]["name"] for key in self.task.platforms if key in PLATFORMS)),
        ]
        for label, value in rows:
            caption = QLabel(label)
            caption.setObjectName("Caption")
            value_label = QLabel(value)
            value_label.setObjectName("PreviewInfoValue")
            value_label.setWordWrap(True)
            layout.addWidget(caption)
            layout.addWidget(value_label)
        layout.addStretch(1)
        return box

    def _platform_changed(self):
        self.platform_label.setText(f"{self.platform_combo.currentText()} · 内容预览")

    def _show_image(self):
        if not self.images:
            self.media_stack.setCurrentIndex(1)
            self.image_count.setText("0 / 0")
            return
        self.media_stack.setCurrentWidget(self.image_label)
        self.image_label.set_image(self.images[self.image_index])
        self.image_count.setText(f"{self.image_index + 1} / {len(self.images)}")

    def _change_image(self, offset):
        if self.images:
            self.image_index = (self.image_index + offset) % len(self.images)
            self._show_image()

    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _position_changed(self, position):
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self.time_label.setText(
            f"{format_time(position)} / {format_time(self.player.duration())}")

    def _duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.video_status.setText("视频已就绪，点击播放检查画面与声音。")

    def _playback_changed(self, state):
        self.play_button.setText("暂停" if state == QMediaPlayer.PlayingState else "播放")

    def reject(self):
        self._stop_player()
        super().reject()

    def _stop_player(self):
        if hasattr(self, "player"):
            self.player.stop()

    def closeEvent(self, event):
        self._stop_player()
        super().closeEvent(event)
