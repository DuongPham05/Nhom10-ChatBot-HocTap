"""
src/controllers/base_controller.py
-----------------------------------
Lớp cơ sở cho tất cả các controller/view trang.

Tự động tìm thư mục chứa file .ui bằng cách:
  1. Thử tìm thư mục "forms" từ gốc project
  2. Nếu không thấy, dùng thư mục cùng chỗ với file main.py đang chạy
  3. Fallback về thư mục hiện tại

Vòng đời khởi tạo:
    __init__ → _load_ui() → setup_ui() → connect_signals()
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6           import uic


# ---------------------------------------------------------------------------
# Tìm thư mục chứa file .ui
# ---------------------------------------------------------------------------

def _find_ui_dir() -> str:
    """
    Tìm thư mục chứa file .ui theo thứ tự ưu tiên:
      1. Thư mục chứa script đang chạy (sys.argv[0]) → thường là forms/
      2. Thư mục gốc project / forms
      3. Thư mục gốc project (nếu .ui để thẳng ở gốc)
      4. Thư mục hiện tại
    """
    candidates = []

    # 1. Thư mục chứa file đang chạy (main.py trong forms/)
    if sys.argv and sys.argv[0]:
        script_dir = Path(sys.argv[0]).resolve().parent
        candidates.append(script_dir)

    # 2. Từ vị trí của base_controller.py lùi lên tìm "forms"
    this_dir = Path(__file__).resolve().parent      # src/controllers/
    for parent in [this_dir, *this_dir.parents]:
        forms_dir = parent / "forms"
        if forms_dir.exists():
            candidates.append(forms_dir)
        candidates.append(parent)

    # 3. Thư mục làm việc hiện tại
    candidates.append(Path.cwd())
    candidates.append(Path.cwd() / "forms")

    # Trả về thư mục đầu tiên thực sự tồn tại
    for c in candidates:
        if c.exists():
            return str(c)

    return str(Path.cwd())


UI_DIR = _find_ui_dir()


# ---------------------------------------------------------------------------
# BaseController
# ---------------------------------------------------------------------------

class BaseController(QWidget):
    """
    Lớp cha của mọi PageController / View.

    Subclass phải override:
        UI_FILE        : tên file .ui (ví dụ "chat_page.ui")
                         Để "" nếu tự tạo UI bằng code
        setup_ui()     : thiết lập dữ liệu ban đầu
        connect_signals(): kết nối signals → slots
        refresh()      : reload dữ liệu khi trang được hiển thị lại
    """

    UI_FILE: str = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_ui()
        self.setup_ui()
        self.connect_signals()

    # ── Load UI ───────────────────────────────────────────────────────

    def _load_ui(self):
        """Nạp file .ui vào widget này nếu UI_FILE được chỉ định."""
        if not self.UI_FILE:
            return

        # Thử tìm file .ui ở nhiều vị trí khác nhau
        candidates = [
            os.path.join(UI_DIR, self.UI_FILE),
        ]

        # Thêm thư mục từ sys.argv[0]
        if sys.argv and sys.argv[0]:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            candidates.append(os.path.join(script_dir, self.UI_FILE))

        # Tìm file tồn tại
        found = None
        for path in candidates:
            if os.path.exists(path):
                found = path
                break

        if not found:
            raise FileNotFoundError(
                f"Không tìm thấy UI file '{self.UI_FILE}'.\n"
                f"Đã tìm ở:\n" + "\n".join(f"  {p}" for p in candidates)
            )

        uic.loadUi(found, self)

    # ── Interface – override trong subclass ───────────────────────────

    def setup_ui(self):
        """Khởi tạo dữ liệu / trạng thái hiển thị ban đầu."""
        pass

    def connect_signals(self):
        """Kết nối tất cả signals → slots của trang này."""
        pass

    def refresh(self):
        """Được gọi mỗi khi trang được navigate to."""
        pass

    def set_widget(self, widget: QWidget):
        """Gán widget vào layout của controller."""
        if self.layout():
            self.layout().addWidget(widget)
        else:
            layout = QVBoxLayout(self)
            layout.addWidget(widget)

    # ── Static helpers ────────────────────────────────────────────────

    @staticmethod
    def show_info(parent, title: str, message: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_warning(parent, title: str, message: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_error(parent, title: str, message: str):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def confirm(parent, title: str, message: str) -> bool:
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes