import json
from pathlib import Path

from app.paths import ROOT

CONFIG_PATH = ROOT / "data" / "config.json"

THEMES = {
    "coral_cloud": {
        "name": "珊瑚云 · 浅色暖白",
        "window": "#F7F4F1", "surface": "#FFFFFF", "surface_alt": "#F1ECE8",
        "border": "#E7DED8", "text": "#2B2624", "muted": "#8A7E78",
        "primary": "#E14B54", "primary_hover": "#C93D47", "on_primary": "#FFFFFF",
        "accent": "#6E93B5", "input_bg": "#FFFFFF",
        "nav_bg": "#F1EAE5", "nav_text": "#4A423D", "nav_muted": "#9A8C84",
        "nav_active_bg": "#E14B54", "nav_active_text": "#FFFFFF",
    },
    "neon_night": {
        "name": "霓虹夜航 · 深色科技",
        "window": "#14161C", "surface": "#1D2029", "surface_alt": "#262A36",
        "border": "#333948", "text": "#E8EAF2", "muted": "#8B93A8",
        "primary": "#FF5A64", "primary_hover": "#E14B54", "on_primary": "#14161C",
        "accent": "#7FB3E0", "input_bg": "#191C24",
        "nav_bg": "#101218", "nav_text": "#C6CCDD", "nav_muted": "#6B7485",
        "nav_active_bg": "#FF5A64", "nav_active_text": "#14161C",
    },
    "glacier": {
        "name": "冰川数据 · 冷蓝浅色",
        "window": "#F2F6FA", "surface": "#FFFFFF", "surface_alt": "#E8EFF6",
        "border": "#D8E2EC", "text": "#22303E", "muted": "#7286A0",
        "primary": "#5B87B0", "primary_hover": "#4A7299", "on_primary": "#FFFFFF",
        "accent": "#E14B54", "input_bg": "#FFFFFF",
        "nav_bg": "#E7EEF5", "nav_text": "#33465C", "nav_muted": "#8499B2",
        "nav_active_bg": "#5B87B0", "nav_active_text": "#FFFFFF",
    },
    "deep_sea": {
        "name": "深海墨蓝 · 专业暗色",
        "window": "#101B26", "surface": "#172634", "surface_alt": "#1F3040",
        "border": "#2A3E52", "text": "#DCE7F0", "muted": "#7E96AB",
        "primary": "#E14B54", "primary_hover": "#C93D47", "on_primary": "#FFFFFF",
        "accent": "#8FC7A4", "input_bg": "#13202C",
        "nav_bg": "#0C1520", "nav_text": "#B9CBDC", "nav_muted": "#5F7A93",
        "nav_active_bg": "#E14B54", "nav_active_text": "#FFFFFF",
    },
}

QSS_TEMPLATE = """
* { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 13px; }
QMainWindow, QWidget#Central { background: %(window)s; color: %(text)s; }
QWidget { color: %(text)s; }
QFrame#Sidebar { background: %(nav_bg)s; border: none; border-right: 1px solid %(border)s; }
QLabel#AppTitle { font-size: 18px; font-weight: 700; color: %(nav_text)s; }
QLabel#AppSubtitle { font-size: 11px; color: %(nav_muted)s; }
QLabel#SectionLabel { color: %(nav_muted)s; font-size: 11px; padding-left: 10px; }
QLabel#SidebarScope { color: %(nav_muted)s; font-size: 11px; padding: 8px 10px; border-top: 1px solid %(border)s; }
QLabel#WorkspaceStatus { color: %(accent)s; font-size: 11px; padding: 4px 10px 0 10px; }
QListWidget#Nav { background: transparent; border: none; outline: none; }
QListWidget#Nav::item { color: %(nav_text)s; padding: 10px 12px; margin: 1px 0; border: 1px solid transparent; border-radius: 7px; }
QListWidget#Nav::item:hover { background: %(surface_alt)s; color: %(text)s; }
QListWidget#Nav::item:selected { background: %(surface_alt)s; color: %(primary)s; border: 1px solid %(border)s; font-weight: 600; }
QWidget#Page { background: %(window)s; }
QLabel#PageTitle { font-size: 24px; font-weight: 700; color: %(text)s; }
QLabel#PageSubtitle { font-size: 12px; color: %(muted)s; }
QLabel#Caption, QLabel#StatCaption { color: %(muted)s; font-size: 11px; }
QLabel#EmptyState { background: %(surface)s; color: %(muted)s; border: 1px solid %(border)s; border-radius: 8px; font-size: 13px; }
QLabel#Notice { background: %(surface_alt)s; color: %(text)s; border: 1px solid %(border)s; border-radius: 7px; padding: 10px 12px; }
QFrame#StatCard { background: %(surface)s; border: 1px solid %(border)s; border-radius: 10px; }
QLabel#StatLabel { color: %(muted)s; font-size: 12px; }
QLabel#StatValue { color: %(text)s; font-size: 26px; font-weight: 600; }
QFrame#Toolbar { background: %(surface)s; border: 1px solid %(border)s; border-radius: 9px; }
QFrame#PreviewPhone { background: %(surface)s; border: 1px solid %(border)s; border-radius: 14px; }
QLabel#PreviewPlatform { font-size: 15px; font-weight: 600; }
QLabel#PreviewTitle { font-size: 16px; font-weight: 600; }
QLabel#PreviewTags { color: %(primary)s; }
QLabel#PreviewInfoValue { font-weight: 400; }
QLabel#PreviewMedia, QVideoWidget#PreviewVideo { background: #0B0D12; color: #A6ADBD; border: none; border-radius: 8px; }
QTextEdit#PreviewBody { background: transparent; border: none; padding: 0; }
QSlider::groove:horizontal { height: 4px; background: %(border)s; border-radius: 2px; }
QSlider::sub-page:horizontal { background: %(primary)s; border-radius: 2px; }
QSlider::handle:horizontal { background: %(primary)s; width: 12px; margin: -5px 0; border-radius: 6px; }
QGroupBox { background: %(surface)s; border: 1px solid %(border)s; border-radius: 10px; margin-top: 16px; padding: 14px 12px 12px 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; top: 2px; padding: 0 5px; background: %(window)s; color: %(text)s; font-size: 13px; font-weight: 600; }
QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QTimeEdit, QSpinBox { background: %(input_bg)s; border: 1px solid %(border)s; border-radius: 6px; padding: 7px 9px; selection-background-color: %(primary)s; selection-color: %(on_primary)s; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus, QTimeEdit:focus, QSpinBox:focus { border: 1px solid %(primary)s; }
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QDateTimeEdit:disabled, QTimeEdit:disabled, QSpinBox:disabled { color: %(muted)s; background: %(surface_alt)s; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: %(surface)s; border: 1px solid %(border)s; selection-background-color: %(primary)s; selection-color: %(on_primary)s; }
QPushButton { background: %(surface_alt)s; color: %(text)s; border: 1px solid %(border)s; border-radius: 7px; padding: 7px 15px; min-height: 18px; }
QPushButton:hover { border: 1px solid %(primary)s; color: %(primary)s; background: %(surface)s; }
QPushButton:pressed { background: %(border)s; }
QPushButton:focus { border: 1px solid %(primary)s; }
QPushButton:disabled { color: %(muted)s; background: %(surface_alt)s; border-color: %(border)s; }
QPushButton#PrimaryButton { background: %(primary)s; color: %(on_primary)s; border: none; font-weight: 600; }
QPushButton#PrimaryButton:hover { background: %(primary_hover)s; color: %(on_primary)s; }
QPushButton#DangerButton { color: %(primary)s; }
QTableWidget, QListWidget { background: %(surface)s; border: 1px solid %(border)s; border-radius: 8px; gridline-color: transparent; selection-background-color: %(surface_alt)s; selection-color: %(text)s; alternate-background-color: %(surface)s; outline: none; }
QTableWidget::item { padding: 8px; border-bottom: 1px solid %(border)s; }
QTableWidget::item:selected { background: %(surface_alt)s; color: %(primary)s; }
QHeaderView::section { background: %(surface)s; color: %(muted)s; border: none; border-bottom: 1px solid %(border)s; padding: 9px 8px; font-size: 12px; font-weight: 500; }
QListWidget::item { border-radius: 7px; padding: 6px; }
QListWidget::item:selected { background: %(surface_alt)s; color: %(primary)s; border: 1px solid %(primary)s; }
QCheckBox { spacing: 6px; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid %(border)s; border-radius: 4px; background: %(input_bg)s; }
QCheckBox::indicator:hover { border-color: %(primary)s; }
QCheckBox::indicator:checked { background: %(primary)s; border-color: %(primary)s; }
QCheckBox::indicator:disabled { background: %(surface_alt)s; }
QToolButton#PlatformButton { background: %(input_bg)s; border: 1px solid %(border)s; border-radius: 8px; color: %(muted)s; font-size: 13px; padding: 8px; }
QToolButton#PlatformButton:hover { border: 1px solid %(primary)s; color: %(primary)s; }
QToolButton#PlatformButton:checked { background: %(surface_alt)s; color: %(primary)s; border: 1px solid %(primary)s; font-weight: 600; }
QToolButton#PlatformButton:disabled { color: %(border)s; background: %(surface_alt)s; }
QCalendarWidget QWidget { alternate-background-color: %(surface_alt)s; }
QCalendarWidget QAbstractItemView:enabled { background: %(surface)s; color: %(text)s; selection-background-color: %(primary)s; selection-color: %(on_primary)s; }
QCalendarWidget QToolButton { background: transparent; color: %(text)s; }
QCalendarWidget QMenu { background: %(surface)s; color: %(text)s; }
QCalendarWidget QSpinBox { background: %(input_bg)s; color: %(text)s; }
QCalendarWidget QWidget#qt_calendar_navigationbar { background: %(primary)s; }
QCalendarWidget QWidget#qt_calendar_navigationbar QToolButton { color: %(on_primary)s; font-weight: 600; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: %(border)s; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: %(muted)s; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 2px; }
QScrollBar::handle:horizontal { background: %(border)s; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QSplitter::handle { background: %(window)s; width: 8px; height: 8px; }
QDialog { background: %(window)s; }
QDialogButtonBox QPushButton { min-width: 72px; }
QMenu { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s; padding: 4px; }
QMenu::item { padding: 7px 24px; border-radius: 4px; }
QMenu::item:selected { background: %(surface_alt)s; color: %(primary)s; }
QToolTip { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s; }
"""


def build_qss(key):
    return QSS_TEMPLATE % THEMES[key]


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")


def get_config_value(key, default=None):
    return load_config().get(key, default)


def set_config_value(key, value):
    config = load_config()
    config[key] = value
    save_config(config)


def load_theme_key():
    theme = get_config_value("theme")
    return theme if theme in THEMES else "coral_cloud"


def save_theme_key(key):
    set_config_value("theme", key)
