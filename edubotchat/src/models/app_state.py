"""
src/models/app_state.py
------------------------
Singleton quản lý toàn bộ trạng thái runtime của EduBot.

Cung cấp:
  - Quản lý session chat (tạo, chuyển, đặt tên, lấy tin nhắn)
  - Quản lý task (thêm, xóa, lọc theo ngày)
  - Quản lý roadmap
  - Thống kê tổng hợp cho Dashboard
  - Tích hợp DBManager (lưu/load từ MySQL nếu có)

Dùng:
  state = AppState.instance()
  state.new_session("Chat mới")
  state.add_message(sid, MessageRole.USER, "Xin chào")
"""

from __future__ import annotations

import uuid
from collections import OrderedDict
from datetime    import date, datetime
from typing      import Dict, List, Optional

from src.models.message      import Message, MessageRole
from src.models.task         import Task
from src.models.roadmap_node import RoadmapNode
from src.models.settings     import AppSettings

# DB optional – app vẫn chạy khi chưa có MySQL
try:
    from src.database.db_manager import DBManager
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# AppState
# ---------------------------------------------------------------------------

class AppState:
    """
    Singleton – chỉ một instance tồn tại trong toàn bộ vòng đời app.

    Truy cập:  AppState.instance()
    """

    _instance: Optional[AppState] = None

    @classmethod
    def instance(cls) -> AppState:
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._init()
        return cls._instance

    # ── Khởi tạo nội bộ ──────────────────────────────────────────────

    def _init(self):
        """Chỉ gọi một lần duy nhất bởi instance()."""

        # ── Settings ─────────────────────────────────────────────────
        self.settings = AppSettings()

        # ── Sessions (chat) ───────────────────────────────────────────
        # OrderedDict giữ thứ tự tạo:  sid → List[Message]
        self._sessions: OrderedDict[str, List[Message]] = OrderedDict()
        # Tên hiển thị của mỗi session
        self._session_titles: Dict[str, str] = {}
        # Session đang mở
        self.current_session: str = ""

        # Tạo session mặc định ngay khi khởi động
        default_sid = self.new_session("Chat mới")
        self.current_session = default_sid

        # ── Tasks (Planner) ───────────────────────────────────────────
        self._tasks: List[Task] = []

        # ── Roadmap ───────────────────────────────────────────────────
        # List các SubjectRoadmap (mỗi môn là 1 phần tử)
        self.roadmap: List = []

        # ── Thống kê ─────────────────────────────────────────────────
        self._total_questions: int = 0   # tổng câu hỏi đã hỏi AI
        self._streak_days:     int = 0   # số ngày học liên tiếp

        # Load từ DB nếu có
        if _DB_AVAILABLE:
            self._load_from_db()

    # ==================================================================
    #  Session management
    # ==================================================================

    def new_session(self, title: str = "") -> str:
        """
        Tạo session mới, trả về session_id (sid).

        Args:
            title: Tên hiển thị. Nếu để trống, tự tạo theo timestamp.
        """
        sid = str(uuid.uuid4())
        if not title:
            title = f"Chat {datetime.now().strftime('%d/%m %H:%M')}"
        self._sessions[sid]       = []
        self._session_titles[sid] = title
        self.current_session      = sid
        return sid

    def session_title(self, sid: str) -> str:
        """Trả về tên hiển thị của session."""
        return self._session_titles.get(sid, "Chat")

    def rename_session(self, sid: str, title: str):
        """Đổi tên session."""
        if sid in self._session_titles:
            self._session_titles[sid] = title

    def delete_session(self, sid: str):
        """Xóa session và toàn bộ tin nhắn của nó."""
        self._sessions.pop(sid, None)
        self._session_titles.pop(sid, None)
        # Nếu đang mở session này thì chuyển sang session đầu tiên còn lại
        if self.current_session == sid:
            if self._sessions:
                self.current_session = next(iter(self._sessions))
            else:
                self.current_session = self.new_session("Chat mới")

    @property
    def session_order(self) -> List[str]:
        """Danh sách sid theo thứ tự tạo mới nhất trước."""
        return list(reversed(list(self._sessions.keys())))

    # ==================================================================
    #  Message management
    # ==================================================================

    def add_message(
        self,
        sid: str,
        role: MessageRole,
        content: str,
    ) -> Message:
        """
        Tạo và lưu Message vào session, trả về object Message.

        Args:
            sid:     Session ID
            role:    MessageRole.USER hoặc MessageRole.ASSISTANT
            content: Nội dung tin nhắn
        """
        if sid not in self._sessions:
            # Session không tồn tại → tạo mới để tránh crash
            self._sessions[sid]       = []
            self._session_titles[sid] = "Chat"

        msg = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            session_id=sid,
        )
        self._sessions[sid].append(msg)

        # Đếm câu hỏi người dùng
        if role == MessageRole.USER:
            self._total_questions += 1

        return msg

    def get_messages(self, sid: str) -> List[Message]:
        """Trả về danh sách tin nhắn của session theo thứ tự thời gian."""
        return list(self._sessions.get(sid, []))

    def clear_messages(self, sid: str):
        """Xóa toàn bộ tin nhắn của session."""
        if sid in self._sessions:
            self._sessions[sid] = []

    def get_history_for_api(self, sid: str) -> List[Dict]:
        """
        Trả về lịch sử dạng list[dict] để truyền vào APIWorker.
        Format: [{"role": "user"|"assistant", "content": "..."}]
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self._sessions.get(sid, [])
        ]

    # ==================================================================
    #  Task management (Planner)
    # ==================================================================

    def add_task(self, task: Task):
        """Thêm task mới."""
        self._tasks.append(task)

        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_study_session(
                    subject=task.subject,
                    topic=task.title,
                    duration_min=task.duration,
                    progress_pct=0,
                )
            except Exception:
                pass

    def remove_task(self, task_id: int):
        """Xóa task theo id."""
        self._tasks = [t for t in self._tasks if t.id != task_id]

    def update_task(self, task: Task):
        """Cập nhật task đã tồn tại (thay thế theo id)."""
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                return

    def tasks_for_date(self, d: date) -> List[Task]:
        """Trả về danh sách task của một ngày cụ thể."""
        return [t for t in self._tasks if t.date == d]

    def tasks_for_week(self, week_start: date) -> Dict[date, List[Task]]:
        """
        Trả về dict {ngày: [tasks]} cho 7 ngày bắt đầu từ week_start.
        """
        from datetime import timedelta
        result: Dict[date, List[Task]] = {}
        for i in range(7):
            d = week_start + timedelta(days=i)
            result[d] = self.tasks_for_date(d)
        return result

    @property
    def tasks_done(self) -> int:
        return sum(1 for t in self._tasks if t.done)

    @property
    def tasks_total(self) -> int:
        return len(self._tasks)

    def get_task_stats(self) -> tuple[int, int]:
        """Trả về (done, total)."""
        return self.tasks_done, self.tasks_total

    # ==================================================================
    #  Roadmap management
    # ==================================================================

    def set_roadmap(self, roadmap: list):
        """Gán danh sách SubjectRoadmap."""
        self.roadmap = roadmap

    def get_roadmap_by_subject(self, subject: str):
        """Tìm SubjectRoadmap theo tên môn."""
        for rm in self.roadmap:
            if rm.name == subject:
                return rm
        return None

    @property
    def overall_progress(self) -> int:
        """
        Tính % hoàn thành tổng thể của tất cả môn trong roadmap.
        Trả về 0 nếu chưa có roadmap.
        """
        if not self.roadmap:
            return 0
        try:
            total = sum(rm.progress for rm in self.roadmap)
            return total // len(self.roadmap)
        except Exception:
            return 0

    # ==================================================================
    #  Thống kê cho Dashboard
    # ==================================================================

    @property
    def total_questions(self) -> int:
        """Tổng số câu hỏi đã hỏi AI trong toàn bộ phiên."""
        return self._total_questions

    @property
    def streak_days(self) -> int:
        """Số ngày học liên tiếp (lấy từ DB nếu có)."""
        return self._streak_days

    def get_dashboard_stats(self) -> dict:
        """
        Trả về dict thống kê đầy đủ cho DashboardView.

        Keys: chat_count, question_count, task_done,
              task_total, streak_days, overall_progress
        """
        return {
            "chat_count":       len(self._sessions),
            "question_count":   self._total_questions,
            "task_done":        self.tasks_done,
            "task_total":       self.tasks_total,
            "streak_days":      self._streak_days,
            "overall_progress": self.overall_progress,
        }

    # ==================================================================
    #  DB sync
    # ==================================================================

    def _load_from_db(self):
        """Load dữ liệu ban đầu từ MySQL vào memory."""
        try:
            db  = DBManager.instance()
            ctx = db.get_user_context()

            # Streak (tính từ study_sessions)
            sessions = ctx.get("sessions", [])
            self._streak_days = self._calc_streak(sessions)

        except Exception:
            pass   # DB chưa kết nối → bỏ qua, dùng giá trị mặc định

    @staticmethod
    def _calc_streak(sessions: list) -> int:
        """
        Tính số ngày học liên tiếp tính đến hôm nay
        dựa trên danh sách study_sessions từ DB.
        """
        if not sessions:
            return 0

        studied_dates = sorted(
            {s['studied_at'].date() for s in sessions if s.get('studied_at')},
            reverse=True,
        )
        if not studied_dates:
            return 0

        streak = 0
        check  = date.today()
        for d in studied_dates:
            if d == check:
                streak += 1
                from datetime import timedelta
                check -= timedelta(days=1)
            elif d < check:
                break   # có ngày bị bỏ qua → streak kết thúc

        return streak

    def sync_task_to_db(self, task: Task):
        """Lưu một task cụ thể vào DB (gọi từ PlannerView sau khi lưu)."""
        if not _DB_AVAILABLE:
            return
        try:
            DBManager.instance().save_study_session(
                subject=task.subject,
                topic=task.title,
                duration_min=task.duration,
                progress_pct=100 if task.done else 0,
            )
        except Exception:
            pass

    # ==================================================================
    #  Tiện ích
    # ==================================================================

    def reset(self):
        """
        Reset toàn bộ state về mặc định.
        Dùng khi đăng xuất hoặc test.
        """
        self._sessions.clear()
        self._session_titles.clear()
        self._tasks.clear()
        self.roadmap           = []
        self._total_questions  = 0
        self._streak_days      = 0
        default_sid            = self.new_session("Chat mới")
        self.current_session   = default_sid

    def __repr__(self) -> str:
        return (
            f"<AppState sessions={len(self._sessions)} "
            f"tasks={len(self._tasks)} "
            f"questions={self._total_questions}>"
        )