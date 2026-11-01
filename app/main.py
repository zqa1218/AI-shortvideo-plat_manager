import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.paths import asset_path
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("猫后台助手")
    app.setWindowIcon(QIcon(asset_path("cat.ico")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
