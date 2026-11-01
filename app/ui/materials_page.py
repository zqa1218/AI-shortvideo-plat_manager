import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from app import database
from app.thumbs import detect_kind, file_md5, make_thumbnail
from app.ui.components import add_page_header
from app.ui.material_detail import MaterialDetailDialog


def populate_grid(grid, materials):
    grid.clear()
    for material in materials:
        name = material["path"].replace("\\", "/").rsplit("/", 1)[-1]
        label = f"{name}\n[{material['tags'] or '未打标'}]"
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, material)
        if material["thumb_path"]:
            item.setIcon(QIcon(material["thumb_path"]))
        grid.addItem(item)


class EditMaterialDialog(QDialog):
    def __init__(self, material, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑素材")
        form = QFormLayout(self)
        self.tags = QLineEdit(material["tags"])
        self.tags.setPlaceholderText("标签，用逗号分隔")
        form.addRow("标签", self.tags)
        self.note = QTextEdit(material["note"])
        self.note.setMaximumHeight(100)
        form.addRow("备注", self.note)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class MaterialsPage(QWidget):
    def __init__(self, on_use=None):
        super().__init__()
        self.on_use = on_use
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        import_btn = QPushButton("导入素材")
        import_btn.setObjectName("PrimaryButton")
        import_btn.clicked.connect(self._import)
        add_page_header(
            layout, "素材库", "集中管理图片与视频，让优质内容可以被反复使用。",
            [import_btn],
        )
        toolbar = QFrame()
        toolbar.setObjectName("Toolbar")
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(10, 8, 10, 8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索文件名、备注或标签")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.reload)
        self.kind_filter = QComboBox()
        self.kind_filter.addItems(["全部类型", "图片", "视频"])
        self.kind_filter.currentIndexChanged.connect(self.reload)
        self.tag_filter = QComboBox()
        self.tag_filter.currentIndexChanged.connect(self.reload)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.kind_filter)
        bar.addWidget(self.tag_filter)
        layout.addWidget(toolbar)

        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(150, 150))
        self.grid.setGridSize(QSize(180, 200))
        self.grid.setMovement(QListWidget.Static)
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setSelectionMode(QListWidget.ExtendedSelection)
        self.grid.setSpacing(6)
        self.grid_stack = QStackedWidget()
        self.grid_stack.addWidget(self.grid)
        self.empty_label = QLabel("素材库还是空的\n\n点击右上角导入素材，或将图片、视频拖到这里")
        self.empty_label.setObjectName("EmptyState")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.grid_stack.addWidget(self.empty_label)
        layout.addWidget(self.grid_stack, 1)

        actions = QHBoxLayout()
        edit_btn = QPushButton("编辑标签/备注")
        edit_btn.clicked.connect(self._edit)
        remove_btn = QPushButton("移出库（保留文件）")
        remove_btn.setObjectName("DangerButton")
        remove_btn.clicked.connect(self._remove)
        use_btn = QPushButton("用于发布")
        use_btn.clicked.connect(self._use)
        detail_btn = QPushButton("发布与表现")
        detail_btn.clicked.connect(self._detail)
        self.count_label = QLabel()
        self.count_label.setObjectName("Caption")
        actions.addWidget(edit_btn)
        actions.addWidget(remove_btn)
        actions.addWidget(use_btn)
        actions.addWidget(detail_btn)
        actions.addStretch(1)
        actions.addWidget(self.count_label)
        layout.addLayout(actions)
        self.reload()

    def _detail(self):
        selected = self._selected()
        if selected:
            MaterialDetailDialog(selected[0], self).exec()

    def _filters(self):
        clauses, params = [], []
        keyword = self.search.text().strip()
        if keyword:
            clauses.append("(path LIKE ? OR note LIKE ? OR tags LIKE ?)")
            params += [f"%{keyword}%"] * 3
        kind = self.kind_filter.currentText()
        if kind == "图片":
            clauses.append("kind='image'")
        elif kind == "视频":
            clauses.append("kind='video'")
        tag = self.tag_filter.currentText()
        if tag and tag != "全部标签":
            clauses.append("tags LIKE ?")
            params.append(f"%{tag}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    def reload(self):
        current_tag = self.tag_filter.currentText()
        tags = set()
        for row in database.query("SELECT tags FROM materials"):
            tags.update(t.strip() for t in row["tags"].split(",") if t.strip())
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("全部标签")
        self.tag_filter.addItems(sorted(tags))
        if current_tag:
            self.tag_filter.setCurrentText(current_tag)
        self.tag_filter.blockSignals(False)
        where, params = self._filters()
        materials = database.query(f"SELECT * FROM materials {where} ORDER BY id DESC", params)
        populate_grid(self.grid, materials)
        self.grid_stack.setCurrentWidget(self.grid if materials else self.empty_label)
        self.count_label.setText(f"共 {len(materials)} 项")

    def _import(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "导入素材", "", "素材文件 (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.mp4 *.mov *.mkv *.flv *.avi)")
        self._import_paths(paths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self._import_paths(paths)
        event.acceptProposedAction()

    def _import_paths(self, paths):
        added, duplicated = 0, 0
        for path in paths:
            if not path or not os.path.isfile(path):
                continue
            digest = file_md5(path)
            if database.query("SELECT id FROM materials WHERE md5=?", (digest,)):
                duplicated += 1
                continue
            kind = detect_kind(path)
            thumb = make_thumbnail(path, kind)
            database.execute(
                "INSERT INTO materials (path, kind, md5, thumb_path) VALUES (?, ?, ?, ?)",
                (path, kind, digest, thumb))
            added += 1
        self.reload()
        QMessageBox.information(self, "导入完成", f"新增 {added} 项，重复跳过 {duplicated} 项")

    def _selected(self):
        return [item.data(Qt.UserRole) for item in self.grid.selectedItems()]

    def _edit(self):
        selected = self._selected()
        if not selected:
            return
        dialog = EditMaterialDialog(selected[0], self)
        if not dialog.exec():
            return
        for material in selected:
            database.execute("UPDATE materials SET tags=?, note=? WHERE id=?",
                             (dialog.tags.text().strip(), dialog.note.toPlainText().strip(), material["id"]))
        self.reload()

    def _remove(self):
        selected = self._selected()
        for material in selected:
            database.execute("DELETE FROM materials WHERE id=?", (material["id"],))
        self.reload()

    def _use(self):
        selected = self._selected()
        if selected and self.on_use:
            self.on_use([m["path"] for m in selected])


class MaterialPickerDialog(QDialog):
    def __init__(self, multi=False, kind="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("从素材库选择")
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(140, 140))
        self.grid.setGridSize(QSize(170, 190))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setSelectionMode(QListWidget.ExtendedSelection if multi else QListWidget.SingleSelection)
        layout.addWidget(self.grid)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.grid.itemDoubleClicked.connect(lambda _: self.accept())
        query = "SELECT * FROM materials"
        if kind:
            query += f" WHERE kind='{kind}'"
        populate_grid(self.grid, database.query(query + " ORDER BY id DESC"))

    def selected_paths(self):
        return [item.data(Qt.UserRole)["path"] for item in self.grid.selectedItems()]
