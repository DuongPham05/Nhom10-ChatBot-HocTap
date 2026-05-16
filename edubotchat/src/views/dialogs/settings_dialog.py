"""src/views/dialogs/settings_dialog.py – Dialog Cài Đặt."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QDialogButtonBox,
    QTabWidget, QWidget, QCheckBox, QSpinBox,
)
from PyQt6.QtCore import Qt
from src.models.settings import AppSettings

_FIELD = (
    "QLineEdit,QComboBox,QSpinBox{"
    "background:#f7f8fc;border:1px solid #e2e8f0;"
    "border-radius:8px;padding:6px 12px;font-size:13px;color:#2d3748;}"
    "QLineEdit:focus,QComboBox:focus,QSpinBox:focus{"
    "border-color:#4a6cf7;background:#fff;}"
)

def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet("color:#4a5568;font-size:12px;font-weight:600;")
    return l


class SettingsDialog(QDialog):

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._s = settings
        self.setWindowTitle("⚙️ Cài Đặt")
        self.setMinimumWidth(460)
        self.setMinimumHeight(380)
        self.setStyleSheet(
            "QDialog{background:#fff;font-family:'Segoe UI',Arial,sans-serif;}"
            "QTabWidget::pane{border:1px solid #e2e8f0;border-radius:8px;}"
            "QTabBar::tab{padding:8px 18px;font-size:13px;color:#718096;}"
            "QTabBar::tab:selected{color:#4a6cf7;font-weight:bold;"
            "border-bottom:2px solid #4a6cf7;}"
        )
        self._build()

    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 16)
        main.setSpacing(0)

        # Title
        title = QLabel("⚙️  Cài Đặt Ứng Dụng")
        title.setStyleSheet(
            "font-size:18px;font-weight:bold;color:#1a1f2e;"
            "padding:20px 24px 12px 24px;"
        )
        main.addWidget(title)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._tab_profile(), "👤 Hồ Sơ")
        tabs.addTab(self._tab_api(),     "🔑 API Key")
        tabs.addTab(self._tab_ui(),      "🎨 Giao Diện")
        main.addWidget(tabs)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.setContentsMargins(24, 8, 24, 0)
        btns.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:white;border:none;"
            "border-radius:8px;padding:9px 22px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
            "QPushButton[text='Cancel']{background:#f7f8fc;color:#4a5568;"
            "border:1px solid #e2e8f0;}"
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

    def _tab_profile(self) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        f.setContentsMargins(24, 16, 24, 16)
        f.setSpacing(12)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit(self._s.user_name)
        self._name_edit.setMinimumHeight(38)
        self._name_edit.setStyleSheet(_FIELD)

        self._grade_combo = QComboBox()
        self._grade_combo.addItems([
            "Lớp 10","Lớp 11","Lớp 12",
            "Đại học năm 1","Đại học năm 2","Đại học năm 3","Khác"
        ])
        idx = self._grade_combo.findText(self._s.grade)
        if idx >= 0: self._grade_combo.setCurrentIndex(idx)
        self._grade_combo.setMinimumHeight(38)
        self._grade_combo.setStyleSheet(_FIELD)

        f.addRow(_lbl("Họ tên *"),    self._name_edit)
        f.addRow(_lbl("Lớp / Cấp"),   self._grade_combo)
        return w

    def _tab_api(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(10)

        info = QLabel(
            "🔑 <b>Anthropic API Key</b><br>"
            "<span style='color:#718096;font-size:12px;'>"
            "Lấy key tại: console.anthropic.com → API Keys<br>"
            "Để trống để dùng chế độ offline (bot giả lập)</span>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setStyleSheet("background:#f0f4ff;border-radius:8px;padding:10px;"
                           "border:1px solid #c3d0ff;")
        lay.addWidget(info)

        self._api_edit = QLineEdit(self._s.api_key)
        self._api_edit.setPlaceholderText("sk-ant-api03-...")
        self._api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_edit.setMinimumHeight(38)
        self._api_edit.setStyleSheet(_FIELD)
        lay.addWidget(_lbl("API Key"))
        lay.addWidget(self._api_edit)

        show_cb = QCheckBox("Hiện key")
        show_cb.setStyleSheet("color:#718096;font-size:12px;")
        show_cb.toggled.connect(
            lambda v: self._api_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if v
                else QLineEdit.EchoMode.Password
            )
        )
        lay.addWidget(show_cb)
        lay.addStretch()
        return w

    def _tab_ui(self) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        f.setContentsMargins(24, 16, 24, 16)
        f.setSpacing(12)
        f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["🌙 Sidebar tối", "☀️ Sáng toàn bộ"])
        self._theme_combo.setMinimumHeight(38)
        self._theme_combo.setStyleSheet(_FIELD)

        self._font_spin = QSpinBox()
        self._font_spin.setRange(9, 16)
        self._font_spin.setValue(self._s.font_size)
        self._font_spin.setSuffix(" pt")
        self._font_spin.setMinimumHeight(38)
        self._font_spin.setStyleSheet(_FIELD)

        f.addRow(_lbl("Giao diện"), self._theme_combo)
        f.addRow(_lbl("Cỡ chữ"),   self._font_spin)
        return w

    def _save(self):
        name = self._name_edit.text().strip()
        if not name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập họ tên!")
            return
        self._s.user_name  = name
        self._s.grade      = self._grade_combo.currentText()
        self._s.api_key    = self._api_edit.text().strip()
        self._s.font_size  = self._font_spin.value()
        self._s.sync()
        self.accept()