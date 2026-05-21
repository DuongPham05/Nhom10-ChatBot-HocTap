"""
main.py
-------
Entry-point của ứng dụng EduBot – Chatbot Hỗ Trợ Học Tập.

Kiến trúc:
  MainWindow  (mainwindow.ui)
  ├── Sidebar navigation (btnDashboard / btnChat / btnPlanner / btnRoadmap)
  └── QStackedWidget
      ├── [0] DashboardView   (dashboard_page.ui)
      ├── [1] ChatView        (chat_page.ui)
      ├── [2] PlannerView     (planner_page.ui)
      └── [3] RoadmapView     (roadmap_page.ui)

Chạy:
  python main.py
"""

import sys
import os

# ── Path setup ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QButtonGroup, QMessageBox
from PyQt6.QtCore    import Qt, QSize
from PyQt6.QtGui     import QIcon, QFont
from PyQt6           import uic
from PyQt6           import uic

from src.models.settings          import AppSettings
from src.models.app_state         import AppState
from src.models.roadmap_node      import default_roadmap

# Views mới
from views.dashboard.dashboard_view import DashboardView
from src.views.chat.chat_view          import ChatView
from src.views.planner.planner_view    import PlannerView
from src.views.roadmap.roadmap_view    import RoadmapView
from src.controllers.base_controller   import BaseController

# DB (optional)
try:
    from src.database.db_manager import DBManager
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# DB Initialization
# ---------------------------------------------------------------------------

def _init_db(settings: AppSettings) -> bool:
    """
    Kết nối MySQL và đăng ký người dùng.
    Trả về True nếu thành công, False nếu không có DB.
    """
    if not _DB_AVAILABLE:
        return False
    if not settings.has_db_config():
        return False

    try:
        db = DBManager.instance()
        db.connect(**settings.get_db_config())
        # Đăng ký / lấy user_id
        db.get_or_create_user(settings.user_name, settings.grade)
        print(f"[DB] Kết nối thành công – user: {settings.user_name}")
        return True
    except Exception as e:
        print(f"[DB] Không thể kết nối MySQL: {e}")
        print("[DB] App chạy ở chế độ offline (in-memory).")
        return False


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Cửa sổ chính – quản lý navigation và kết nối các controller."""

    PAGE_DASHBOARD = 0
    PAGE_CHAT      = 1
    PAGE_PLANNER   = 2
    PAGE_ROADMAP   = 3

    def __init__(self, settings: AppSettings):
        super().__init__()
        self._settings = settings
        self._load_ui()
        self._init_state()
        self._init_pages()
        self._init_nav()
        self._connect_cross_page_signals()
        self._apply_global_style()
        self._navigate(self.PAGE_DASHBOARD)

    # ── UI Load ───────────────────────────────────────────────────────

    def _load_ui(self):
        # __file__ = d:/TestChucNang/forms/main.py
        # UI files nằm cùng thư mục với main.py (forms/)
        ui_dir  = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(ui_dir, "mainwindow.ui")
        uic.loadUi(ui_path, self)
        self.setWindowTitle("EduBot – Chatbot Hỗ Trợ Học Tập")
        self.resize(1280, 800)
        self.setMinimumSize(QSize(1100, 700))

    # ── State init ────────────────────────────────────────────────────

    def _init_state(self):
        """Khởi tạo AppState và load roadmap mặc định."""
        state = AppState.instance()
        # Load roadmap mẫu nếu chưa có dữ liệu từ DB
        if not state.roadmap:
            state.set_roadmap(default_roadmap())

    # ── Pages ─────────────────────────────────────────────────────────

    def _init_pages(self):
        self.dashboard = DashboardView(parent=self)
        self.chat      = ChatView(settings=self._settings, parent=self)
        self.planner   = PlannerView(settings=self._settings, parent=self)
        self.roadmap   = RoadmapView(settings=self._settings, parent=self)

        self.stackedWidget.addWidget(self.dashboard)   # index 0
        self.stackedWidget.addWidget(self.chat)        # index 1
        self.stackedWidget.addWidget(self.planner)     # index 2
        self.stackedWidget.addWidget(self.roadmap)     # index 3

        # Truyền tham chiếu MainWindow để các view có thể chuyển tab
        self.roadmap.set_main_window(self)
        self.planner.set_main_window(self)
        self.chat.set_main_window(self)

        # Hiển thị tên người dùng trên sidebar
        self.userNameLabel.setText(self._settings.user_name)

    # ── Navigation ────────────────────────────────────────────────────

    def _init_nav(self):
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        nav_buttons = [
            self.btnDashboard,
            self.btnChat,
            self.btnPlanner,
            self.btnRoadmap,
        ]
        for i, btn in enumerate(nav_buttons):
            btn.setCheckable(True)
            self._nav_group.addButton(btn, i)
            btn.clicked.connect(lambda _, idx=i: self._navigate(idx))

        self.actionNewChat.triggered.connect(lambda: self._navigate(self.PAGE_CHAT))
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self._show_about)
        self.actionExport.triggered.connect(self._export_history)
        self.btnSettings.clicked.connect(self._open_settings)

    def _navigate(self, index: int):
        index = max(0, min(index, 3))
        self.stackedWidget.setCurrentIndex(index)

        btn = self._nav_group.button(index)
        if btn:
            btn.setChecked(True)

        pages = [self.dashboard, self.chat, self.planner, self.roadmap]
        pages[index].refresh()

        page_names = ["Tổng Quan", "Chat với AI", "Lịch Học", "Lộ Trình"]
        self.statusBar().showMessage(f"📍 {page_names[index]}", 2000)

    # ── Cross-page signals ────────────────────────────────────────────

    def _connect_cross_page_signals(self):
        # Dashboard → navigate
        self.dashboard.navigate_to.connect(self._navigate)

        # Chat → Dashboard recent list
        self.chat.new_session_created.connect(self.dashboard.on_new_chat)

        # Chat → Dashboard stats (đếm câu hỏi)
        self.chat.message_sent.connect(self.dashboard.on_tasks_changed)

        # Planner → Dashboard stats
        self.planner.tasks_changed.connect(self.dashboard.on_tasks_changed)

        # Roadmap → status bar
        self.roadmap.goal_added.connect(
            lambda subject: self.statusBar().showMessage(
                f"🎯 Đã thêm mục tiêu môn {subject}", 3000
            )
        )

    # ── Style ─────────────────────────────────────────────────────────

    def _apply_global_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f8fc; }
            QMenuBar {
                background-color: #1a1f2e;
                color: #a0aec0;
                font-size: 13px;
                padding: 2px;
            }
            QMenuBar::item:selected {
                background-color: #2d3748;
                color: #ffffff;
                border-radius: 4px;
            }
            QMenu {
                background-color: #2d3748;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #4a6cf7;
                color: white;
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #1a1f2e;
                color: #718096;
                font-size: 12px;
            }
        """)

    # ── Menu actions ──────────────────────────────────────────────────

    def _show_about(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Giới Thiệu EduBot")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText("""
            <div style='font-family:Segoe UI,Arial;'>
            <h2 style='color:#4a6cf7;'>🎓 EduBot</h2>
            <p><b>Chatbot Hỗ Trợ Học Tập</b></p>
            <p style='color:#718096;'>
                Phiên bản: 2.0.0<br>
                Nền tảng: Python 3.12 + PyQt6<br>
                AI: Google Gemini 2.5 Flash<br>
                DB: MySQL (XAMPP)
            </p>
            <p>EduBot giúp học sinh:</p>
            <ul>
                <li>Chat với AI cá nhân hóa theo tiến độ học</li>
                <li>Lên lịch học và ghi nhận buổi học</li>
                <li>Theo dõi lộ trình học tập theo từng môn</li>
                <li>Phân tích điểm yếu và phân bổ thời gian</li>
            </ul>
            </div>
        """)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def _export_history(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Xuất Lịch Sử Chat", "chat_history.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            state = AppState.instance()
            with open(path, "w", encoding="utf-8") as f:
                f.write("=== Lịch Sử Chat EduBot ===\n\n")
                for sid in state.session_order:
                    title = state.session_title(sid)
                    msgs  = state.get_messages(sid)
                    if not msgs:
                        continue
                    f.write(f"── {title} ──\n")
                    for msg in msgs:
                        prefix = "Bạn" if msg.is_user else "AI "
                        f.write(f"[{msg.display_datetime()}] {prefix}: {msg.content}\n")
                    f.write("\n")
            QMessageBox.information(self, "Thành công", f"✅ Đã xuất ra:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu file:\n{e}")

    def _open_settings(self):
        from src.views.dialogs.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._settings, parent=self)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            # Cập nhật tên hiển thị trên sidebar
            self.userNameLabel.setText(self._settings.user_name)
            self.dashboard.refresh()
            # Thử kết nối lại DB nếu settings DB thay đổi
            if _DB_AVAILABLE:
                _init_db(self._settings)
            self.statusBar().showMessage("✅ Đã lưu cài đặt", 2000)

    # ── Close event ───────────────────────────────────────────────────

    def closeEvent(self, event):
        """Lưu settings và đóng kết nối DB khi thoát."""
        try:
            self._settings.sync()
            state = AppState.instance()
            state.save_roadmap()
            state.save_tasks()
        except Exception:
            pass
        try:
            if _DB_AVAILABLE:
                DBManager.instance().disconnect()
        except Exception:
            pass
        event.accept()


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------

def main():
    # Hi-DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("EduBot")
    app.setApplicationVersion("2.0.0")

    # ── Load settings ─────────────────────────────────────────────────
    settings = AppSettings()

    # Font theo settings
    font = QFont("Segoe UI", settings.font_size)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)
    app.setStyleSheet("""
        QLabel, QTextEdit, QPushButton, QPlainTextEdit {
            font-family: 'Segoe UI';
        }
    """)

    # ── Kết nối DB ────────────────────────────────────────────────────
    db_ok = _init_db(settings)

    # ── Khởi động MainWindow ──────────────────────────────────────────
    window = MainWindow(settings)
    window.show()

    if db_ok:
        window.statusBar().showMessage(
            f"🎓 EduBot sẵn sàng – Đã kết nối DB ✅", 4000
        )
    else:
        window.statusBar().showMessage(
            "🎓 EduBot sẵn sàng – Chế độ offline (chưa kết nối DB)", 4000
        )

    sys.exit(app.exec())


if __name__ == "__main__":

    main()
