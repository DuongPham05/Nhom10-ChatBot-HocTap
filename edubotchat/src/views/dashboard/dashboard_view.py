"""
src/views/dashboard/dasboard_view.py
---------------------------------------
View trang Tổng Quan – cải tiến v2.1
  ✅ Fix thanh tiến độ hiện đôi (xóa placeholder cũ trước khi build mới)
  ✅ Load dữ liệu thực từ DB (goals, study_sessions, quiz_results)
  ✅ StatCard cập nhật realtime từ AppState
  ✅ Lịch sử chat có timestamp thực
  ✅ UI gọn, thông tin hữu ích hơn
"""
from __future__ import annotations

from datetime import date, datetime
from typing   import List

from PyQt6.QtCore    import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QWidget, QSizePolicy,
)

from src.controllers.base_controller       import BaseController
from src.models.app_state                  import AppState
from src.utils.date_helpers                import format_date_vi, relative_time
from src.views.components.stat_card        import StatCard
from src.views.components.subject_progress import SubjectProgressBar
from src.utils.study_subjects              import SUBJECT_COLORS

# DB optional
try:
    from src.database.db_manager import DBManager
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


class DashboardView(BaseController):
    """Controller + View cho trang Dashboard."""

    UI_FILE = "dashboard_page.ui"

    navigate_to = pyqtSignal(int)

    # ------------------------------------------------------------------ #

    def setup_ui(self):
        self._state = AppState.instance()
        self._prog_bars: dict[str, SubjectProgressBar] = {}

        # ① Xóa TOÀN BỘ placeholder widget cũ từ .ui trước khi build
        self._remove_ui_placeholders()

        # ② Build widget động
        self._build_stat_cards()
        self._build_progress_bars()

        # ③ Render dữ liệu
        self._refresh_date()
        self._refresh_stats()
        self._refresh_recent_chats()
        self._refresh_progress_bars()

        # ④ Tự refresh mỗi 60s khi app đang chạy
        self._auto_refresh = QTimer(self)
        self._auto_refresh.setInterval(60_000)
        self._auto_refresh.timeout.connect(self.refresh)
        self._auto_refresh.start()

    def connect_signals(self):
        self.btnNewChatQuick.clicked.connect(lambda: self.navigate_to.emit(1))
        self.btnPlannerQuick.clicked.connect(lambda: self.navigate_to.emit(2))
        self.btnRoadmapQuick.clicked.connect(lambda: self.navigate_to.emit(3))
        self.btnSeeAllChats.clicked.connect(lambda: self.navigate_to.emit(1))
        self.recentChatsList.itemDoubleClicked.connect(
            lambda: self.navigate_to.emit(1)
        )

    def refresh(self):
        self._refresh_date()
        self._refresh_stats()
        self._refresh_recent_chats()
        self._refresh_progress_bars()

    # ── Xóa placeholder .ui ───────────────────────────────────────────

    def _remove_ui_placeholders(self):
        """
        Ẩn/xóa widget placeholder cứng trong file .ui
        để tránh bị hiện đôi khi build widget động.
        """
        # StatCard cũ
        for name in ["cardChat", "cardQuestions", "cardTasks", "cardStreak"]:
            w = self.findChild(QWidget, name)
            if w:
                w.hide()
                w.setParent(None)

        # ProgressBar cũ – XÓA hẳn khỏi layout (không chỉ hide)
        for name in ["progressToan", "progressLy", "progressHoa", "progressAnh",
                     "subjectProgressToan", "subjectProgressLy",
                     "subjectProgressHoa", "subjectProgressAnh"]:
            w = self.findChild(QWidget, name)
            if w:
                w.setParent(None)
                w.deleteLater()

        # Label % cứng bên cạnh progress bar
        for name in ["pctToan", "pctLy", "pctHoa", "pctAnh"]:
            w = self.findChild(QWidget, name)
            if w:
                w.setParent(None)
                w.deleteLater()

    # ── Build widgets ─────────────────────────────────────────────────

    def _build_stat_cards(self):
        """Tạo 4 StatCard và nhét vào statsRow."""
        gradients = [
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4facfe,stop:1 #00f2fe)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #43e97b,stop:1 #38f9d7)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fa709a,stop:1 #fee140)",
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #a18cd1,stop:1 #fbc2eb)",
        ]
        self._card_chat  = StatCard("💬", "Phiên Chat",    "0", "Tháng này",     gradients[0])
        self._card_quest = StatCard("❓", "Câu Hỏi",       "0", "Đã hỏi AI",     gradients[1])
        self._card_task  = StatCard("✅", "Nhiệm Vụ",      "0/0", "Hoàn thành",  gradients[2])
        self._card_stk   = StatCard("🔥", "Streak",        "0",   "Ngày liên tiếp", gradients[3])

        try:
            row = self.statsRow
            # Xóa widget cũ trong statsRow nếu có
            while row.count():
                item = row.takeAt(0)
                if item and item.widget():
                    item.widget().setParent(None)
            for w in [self._card_chat, self._card_quest, self._card_task, self._card_stk]:
                row.addWidget(w)
        except AttributeError:
            pass

    def _build_progress_bars(self):
        """Thêm SubjectProgressBar vào progressFrame – xóa sạch trước."""
        subjects = [
            ("Toán học",   SUBJECT_COLORS.get("Toán học",   "#e53e3e")),
            ("Vật lý",     SUBJECT_COLORS.get("Vật lý",     "#dd6b20")),
            ("Hóa học",    SUBJECT_COLORS.get("Hóa học",    "#38a169")),
            ("Tiếng Anh",  SUBJECT_COLORS.get("Tiếng Anh",  "#3182ce")),
        ]

        try:
            frame = self.progressFrame
        except AttributeError:
            return

        # Lấy hoặc tạo layout
        prog_lay = frame.layout()
        if prog_lay is None:
            prog_lay = QVBoxLayout(frame)
            prog_lay.setContentsMargins(0, 0, 0, 0)
            prog_lay.setSpacing(10)
        else:
            # Xóa sạch layout cũ (tránh duplicate)
            while prog_lay.count():
                item = prog_lay.takeAt(0)
                if item and item.widget():
                    item.widget().setParent(None)
                    item.widget().deleteLater()

        self._prog_bars.clear()
        for name, color in subjects:
            bar = SubjectProgressBar(name, 0, color)
            self._prog_bars[name] = bar
            prog_lay.addWidget(bar)

        prog_lay.addStretch()

    # ── Refresh methods ───────────────────────────────────────────────

    def _refresh_date(self):
        try:
            self.dateLabel.setText(format_date_vi(date.today()))
        except AttributeError:
            pass

    def _refresh_stats(self):
        st = AppState.instance()

        # Lấy thêm từ DB nếu có
        total_study_min = 0
        streak = st.streak_days

        if _DB_AVAILABLE:
            try:
                db  = DBManager.instance()
                ctx = db.get_user_context()
                total_study_min = ctx.get("total_study_min", 0)
                # Tính streak từ DB
                sessions = ctx.get("sessions", [])
                if sessions:
                    from src.utils.date_helpers import calc_streak
                    study_dates = [
                        s["studied_at"].date()
                        for s in sessions
                        if s.get("studied_at")
                    ]
                    streak = calc_streak(study_dates)
            except Exception:
                pass

        chat_count = len(st.session_order)

        # Số phiên chat (nếu DB có)
        if _DB_AVAILABLE:
            try:
                recent = DBManager.instance().get_recent_chat(limit=999)
                # Đếm phiên duy nhất theo session_name
                sessions_set = {m.get("session_name", "") for m in recent if m.get("session_name")}
                if sessions_set:
                    chat_count = max(chat_count, len(sessions_set))
            except Exception:
                pass

        try:
            self._card_chat.set_value(str(chat_count))
            self._card_quest.set_value(str(st.total_questions))
            self._card_task.set_value(f"{st.tasks_done}/{st.tasks_total}")
            self._card_stk.set_value(f"{streak} ngày")
        except AttributeError:
            pass

        # Cập nhật QLabel cũ nếu tồn tại
        _safe_set(self, "chatCountLabel",     str(chat_count))
        _safe_set(self, "questionCountLabel", str(st.total_questions))
        _safe_set(self, "taskCountLabel",     f"{st.tasks_done}/{st.tasks_total}")
        _safe_set(self, "streakCountLabel",   f"{streak} ngày")

    def _refresh_recent_chats(self):
        try:
            lw = self.recentChatsList
            lw.clear()
        except AttributeError:
            return

        st = AppState.instance()

        # Lấy từ DB nếu có (mới nhất trước)
        db_chats: list[dict] = []
        if _DB_AVAILABLE:
            try:
                db_chats = DBManager.instance().get_recent_chat(limit=20)
            except Exception:
                pass

        # Gom theo session_name từ DB
        if db_chats:
            seen: dict[str, datetime] = {}
            for m in db_chats:
                sname = m.get("session_name", "Chat")
                ts    = m.get("created_at")
                if not ts:
                    continue
                if sname not in seen or ts > seen[sname]:
                    seen[sname] = ts

            # Sắp xếp mới nhất trước
            sorted_sessions = sorted(seen.items(), key=lambda x: x[1], reverse=True)
            for sname, ts in sorted_sessions[:8]:
                time_str = relative_time(ts.date() if hasattr(ts, "date") else ts)
                lw.addItem(f"💬  {sname}  ·  {time_str}")
            return

        # Fallback: lấy từ AppState (in-memory)
        for sid in st.session_order[:8]:
            title    = st.session_title(sid)
            msgs     = st.get_messages(sid)
            last     = msgs[-1].timestamp if msgs else None
            time_str = relative_time(last.date()) if last else "Chưa có tin nhắn"
            lw.addItem(f"💬  {title}  ·  {time_str}")

    def _refresh_progress_bars(self):
        """Cập nhật % tiến độ từ DB study_sessions hoặc AppState.roadmap."""

        # Ưu tiên từ DB
        if _DB_AVAILABLE:
            self._refresh_progress_from_db()
            return

        # Fallback: từ roadmap in-memory
        roadmap = AppState.instance().roadmap
        if not roadmap:
            return

        for rm in roadmap:
            bar = self._prog_bars.get(rm.name)
            if bar:
                bar.set_value(rm.progress)

    def _refresh_progress_from_db(self):
        """Tính % tiến độ từ study_sessions trong DB."""
        try:
            db = DBManager.instance()
            for subject, bar in self._prog_bars.items():
                sessions = db.get_sessions_for_subject(subject)
                if not sessions:
                    # Fallback từ roadmap
                    rm = AppState.instance().get_roadmap_by_subject(subject)
                    bar.set_value(rm.progress if rm else 0)
                    continue

                # Lấy progress_pct của buổi học mới nhất
                latest_pct = sessions[-1].get("progress_pct", 0)

                # Kết hợp với tiến độ roadmap (nếu có)
                rm = AppState.instance().get_roadmap_by_subject(subject)
                rm_pct = rm.progress if rm else 0

                # Dùng max để không bị giảm
                bar.set_value(max(latest_pct, rm_pct))

                # Cập nhật lại roadmap nếu DB cao hơn
                if rm and latest_pct > rm_pct:
                    done_count = round(len(rm.topics) * latest_pct / 100)
                    for i, topic in enumerate(rm.topics):
                        from src.models.roadmap_node import TopicStatus
                        if i < done_count:
                            topic.status = TopicStatus.DONE
                        elif i == done_count:
                            topic.status = TopicStatus.IN_PROGRESS
                        else:
                            topic.status = TopicStatus.LOCKED

        except Exception as e:
            print(f"[Dashboard] _refresh_progress_from_db lỗi: {e}")

    # ── Public API ────────────────────────────────────────────────────

    def on_new_chat(self, title: str):
        """Gọi từ MainWindow khi ChatView tạo session mới."""
        self._refresh_recent_chats()
        self._refresh_stats()

    def on_tasks_changed(self):
        """Gọi từ MainWindow khi Planner thay đổi task."""
        self._refresh_stats()
        self._refresh_progress_bars()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _safe_set(widget, attr: str, text: str):
    lbl = getattr(widget, attr, None)
    if lbl and hasattr(lbl, "setText"):
        lbl.setText(text)