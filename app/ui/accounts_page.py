from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app import database
from app.models import PLATFORMS
from app.publishers import sau
from app.ui.components import add_page_header


class AccountsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        add_page_header(
            layout, "账号管理", "维护各平台账号与登录状态，为自动发布和数据采集提供连接。",
        )
        quick_box = QGroupBox("快速扫码登录")
        quick_layout = QHBoxLayout(quick_box)
        for key, info in PLATFORMS.items():
            quick_btn = QPushButton(f"{info['name']}扫码")
            quick_btn.clicked.connect(lambda checked=False, platform=key: self._quick_login(platform))
            quick_layout.addWidget(quick_btn)
        layout.addWidget(quick_box)
        add_box = QGroupBox("添加账号")
        form = QHBoxLayout()
        add_box.setLayout(form)
        self.platform = QComboBox()
        for key, info in PLATFORMS.items():
            self.platform.addItem(info["name"], key)
        self.nickname = QLineEdit()
        self.nickname.setPlaceholderText("账号昵称")
        add_btn = QPushButton("添加账号")
        add_btn.clicked.connect(self._add)
        form.addWidget(QLabel("平台"))
        form.addWidget(self.platform)
        form.addWidget(self.nickname)
        form.addWidget(add_btn)
        layout.addWidget(add_box)
        accounts_box = QGroupBox("已连接账号")
        accounts_layout = QVBoxLayout(accounts_box)
        accounts_layout.setContentsMargins(0, 10, 0, 0)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "平台", "昵称", "添加时间"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        accounts_layout.addWidget(self.table)
        layout.addWidget(accounts_box, 1)
        btn_row = QHBoxLayout()
        login_btn = QPushButton("扫码登录选中账号")
        login_btn.setObjectName("PrimaryButton")
        login_btn.clicked.connect(self._login)
        check_btn = QPushButton("检查登录态")
        check_btn.clicked.connect(self._check)
        remove_btn = QPushButton("删除选中账号")
        remove_btn.setObjectName("DangerButton")
        remove_btn.clicked.connect(self._remove)
        btn_row.addWidget(login_btn)
        btn_row.addWidget(check_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        hint = QLabel("快速扫码会自动使用该平台最近账号，首次使用自动创建 default；扫码完成后关闭登录窗口即可。")
        hint.setObjectName("Caption")
        layout.addWidget(hint)
        self.reload()

    def _selected_account(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        account_id = int(self.table.item(row, 0).text())
        rows = database.query("SELECT * FROM accounts WHERE id=?", (account_id,))
        return rows[0] if rows else None

    def _login(self):
        account = self._selected_account()
        if account is None:
            QMessageBox.information(self, "提示", "请先选中一个账号")
            return
        if not sau.available():
            QMessageBox.warning(self, "提示", "未检测到 social-auto-upload 安装")
            return
        sau.open_login(account["platform"], account["nickname"])

    def _quick_login(self, platform):
        if not sau.available():
            QMessageBox.warning(self, "提示", "未检测到 social-auto-upload 安装")
            return
        nickname = sau.find_account(platform)
        if not nickname:
            nickname = "default"
            database.execute("INSERT INTO accounts (platform, nickname) VALUES (?, ?)",
                             (platform, nickname))
            self.reload()
        sau.open_login(platform, nickname)

    def _check(self):
        account = self._selected_account()
        if account is None:
            QMessageBox.information(self, "提示", "请先选中一个账号")
            return
        if not sau.available():
            QMessageBox.warning(self, "提示", "未检测到 social-auto-upload 安装")
            return
        sau.open_console([account["platform"], "check", "--account", account["nickname"]])

    def reload(self):
        accounts = database.query("SELECT * FROM accounts ORDER BY id DESC")
        self.table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            values = [str(account["id"]), PLATFORMS[account["platform"]]["name"],
                      account["nickname"], account["created_at"]]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _add(self):
        nickname = self.nickname.text().strip()
        if not nickname:
            return
        database.execute("INSERT INTO accounts (platform, nickname) VALUES (?, ?)",
                         (self.platform.currentData(), nickname))
        self.nickname.clear()
        self.reload()

    def _remove(self):
        row = self.table.currentRow()
        if row < 0:
            return
        account_id = int(self.table.item(row, 0).text())
        database.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        self.reload()
