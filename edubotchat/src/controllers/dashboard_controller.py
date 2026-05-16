"""
dashboard_controller.py
------------------------
Controller cho trang Tổng Quan (Dashboard).

Chức năng:
  - Hiển thị thống kê: số phiên chat, câu hỏi, nhiệm vụ, streak
  - Hiển thị ngày hôm nay
  - Cập nhật thanh tiến độ môn học
  - Xử lý các nút truy cập nhanh (Quick Actions)
  - Danh sách lịch sử chat gần đây
"""

from datetime import datetime
from PyQt6.QtCore import pyqtSignal

from controllers.base_controller import BaseController


# ---------------------------------------------------------------------------
# Dữ liệu giả lập (thay thế bằng DB / API thật sau)
# ---------------------------------------------------------------------------

SAMPLE_STATS = {
    "chat_count":     24,
    "question_count": 187,
    "task_done":      12,
    "task_total":     15,
    "streak_days":    7,
}

SAMPLE_PROGRESS = {
    "Toán":       78,
    "Vật Lý":     65,
    "Hóa Học":    82,
    "Tiếng Anh":  91,
}

SAMPLE_RECENT_CHATS = [
    ("💬", "Giải phương trình bậc 2",         "30 phút trước"),
    ("💬", "Định luật Newton và bài tập",      "2 giờ trước"),
    ("💬", "Phản ứng hóa học oxi hóa khử",    "Hôm qua"),
    ("💬", "Giải tích tích phân cơ bản",       "2 ngày trước"),
    ("💬", "Ngữ pháp tiếng Anh nâng cao",      "3 ngày trước"),
]


class DashboardController(BaseController):
    """Controller trang Tổng Quan."""

    UI_FILE = "dashboard_page.ui"

    # Signal phát ra khi người dùng bấm các nút quick-action
    # Giá trị: index trang cần chuyển tới (0=dash,1=chat,2=planner,3=roadmap)
    navigate_to = pyqtSignal(int)

    # ------------------------------------------------------------------ #
    #  Khởi tạo                                                           #
    # ------------------------------------------------------------------ #

    def setup_ui(self):
        self._update_date_label()
        self._load_stats()
        self._load_progress()
        self._load_recent_chats()

    def connect_signals(self):
        # Quick-action buttons
        self.btnNewChatQuick.clicked.connect(lambda: self.navigate_to.emit(1))
        self.btnPlannerQuick.clicked.connect(lambda: self.navigate_to.emit(2))
        self.btnRoadmapQuick.clicked.connect(lambda: self.navigate_to.emit(3))
        self.btnSeeAllChats.clicked.connect(lambda: self.navigate_to.emit(1))

        # Double-click lịch sử chat → mở chat
        self.recentChatsList.itemDoubleClicked.connect(
            lambda: self.navigate_to.emit(1)
        )

    def refresh(self):
        """Gọi lại khi trang được hiển thị lại."""
        self._update_date_label()
        self._load_stats()

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _update_date_label(self):
        now = datetime.now()
        weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5",
                    "Thứ 6", "Thứ 7", "Chủ Nhật"]
        day_name = weekdays[now.weekday()]
        self.dateLabel.setText(
            f"{day_name}, {now.strftime('%d/%m/%Y')}"
        )

    def _load_stats(self):
        s = SAMPLE_STATS
        self.chatCountLabel.setText(str(s["chat_count"]))
        self.questionCountLabel.setText(str(s["question_count"]))
        self.taskCountLabel.setText(
            f"{s['task_done']}/{s['task_total']}"
        )
        self.streakCountLabel.setText(f"{s['streak_days']} ngày")

    def _load_progress(self):
        bars = {
            "Toán":      self.progressToan,
            "Vật Lý":    self.progressLy,
            "Hóa Học":   self.progressHoa,
            "Tiếng Anh": self.progressAnh,
        }
        for subject, bar in bars.items():
            bar.setValue(SAMPLE_PROGRESS.get(subject, 0))

    def _load_recent_chats(self):
        self.recentChatsList.clear()
        for icon, title, time_str in SAMPLE_RECENT_CHATS:
            self.recentChatsList.addItem(f"{icon}  {title}  ·  {time_str}")

    # ------------------------------------------------------------------ #
    #  Public API – MainWindow có thể gọi                                 #
    # ------------------------------------------------------------------ #

    def update_stats(self, stats: dict):
        """Cập nhật số liệu thống kê từ ngoài (sau khi có DB thật)."""
        SAMPLE_STATS.update(stats)
        self._load_stats()

    def add_recent_chat(self, title: str):
        """Thêm một phiên chat mới vào đầu danh sách."""
        SAMPLE_RECENT_CHATS.insert(0, ("💬", title, "Vừa xong"))
        self._load_recent_chats()