from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


def add_page_header(layout, title, subtitle, actions=()):
    header = QHBoxLayout()
    header.setContentsMargins(0, 0, 0, 8)
    header.setSpacing(16)
    text = QVBoxLayout()
    text.setSpacing(4)
    title_label = QLabel(title)
    title_label.setObjectName("PageTitle")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("PageSubtitle")
    text.addWidget(title_label)
    text.addWidget(subtitle_label)
    header.addLayout(text)
    header.addStretch(1)
    for action in actions:
        header.addWidget(action, 0)
    layout.addLayout(header)


class StatCard(QFrame):
    def __init__(self, label, caption):
        super().__init__()
        self.setObjectName("StatCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(3)
        label_widget = QLabel(label)
        label_widget.setObjectName("StatLabel")
        self.value = QLabel("0")
        self.value.setObjectName("StatValue")
        caption_widget = QLabel(caption)
        caption_widget.setObjectName("StatCaption")
        layout.addWidget(label_widget)
        layout.addWidget(self.value)
        layout.addWidget(caption_widget)
