"""
planner_controller.py
---------------------
Controller cho trang Lịch Học (Planner).

Chức năng:
  - Hiển thị lịch theo tuần (QTableWidget)
  - Danh sách nhiệm vụ hôm nay với checkbox hoàn thành
  - Form thêm / sửa nhiệm vụ
  - Điều hướng tuần: Prev / Next
  - Validate form trước khi lưu
  - Thống kê tiến độ ngày trong status bar
"""

from dataclasses import dataclass, field
from datetime    import date, datetime, timedelta
from typing      import List

from PyQt6.QtCore    import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui     import QColor, QBrush
from PyQt6.QtWidgets import QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout

from controllers.base_controller import BaseController


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title:    str
    subject:  str
    date:     date
    start:    QTime
    duration: int          # phút
    priority: str          # "high" | "medium" | "low"
    notes:    str = ""
    done:     bool = False
    id:       int  = 0


PRIORITY_COLORS = {
    "high":   ("#fff5f5", "#e53e3e"),
    "medium": ("#fffbeb", "#d69e2e"),
    "low":    ("#f0fff4", "#38a169"),
}

SUBJECT_ICONS = {
    "Toán học":    "📐",
    "Vật lý":      "⚛️",
    "Hóa học":     "🧪",
    "Sinh học":    "🌿",
    "Ngữ văn":     "📖",
    "Tiếng Anh":   "🇬🇧",
    "Lịch sử":     "🌍",
}

# ID counter đơn giản
_next_id = 0

def _new_id() -> int:
    global _next_id
    _next_id += 1
    return _next_id


# Dữ liệu mẫu
def _sample_tasks() -> List[Task]:
    today = date.today()
    return [
        Task("Ôn tập Toán - Giải tích",        "Toán học",  today,
             QTime(7, 0),  90, "high",   "", False, _new_id()),
        Task("Học Hóa - Phản ứng điện phân",   "Hóa học",   today,
             QTime(9, 0),  90, "medium", "", False, _new_id()),
        Task("Luyện Vật Lý - Điện học",        "Vật lý",    today,
             QTime(14, 0), 90, "high",   "", False, _new_id()),
        Task("Đọc Ngữ văn chương 5",           "Ngữ văn",
             today - timedelta(days=1), QTime(16, 0), 60, "low", "", True, _new_id()),
        Task("Từ vựng Tiếng Anh Unit 7",       "Tiếng Anh",
             today + timedelta(days=1), QTime(8, 0),  45, "medium", "", False, _new_id()),
    ]


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class PlannerController(BaseController):
    """Controller trang Lịch Học."""

    UI_FILE = "planner_page.ui"

    # Phát ra khi số nhiệm vụ hoàn thành thay đổi
    tasks_updated = pyqtSignal(int, int)   # (done, total)

    # ------------------------------------------------------------------ #
    #  Khởi tạo                                                           #
    # ------------------------------------------------------------------ #

    def setup_ui(self):
        self._tasks: List[Task] = _sample_tasks()
        self._current_week_start: date = self._get_week_start(date.today())
        self._editing_task: Task | None = None

        # Cài đặt calendar table
        self._setup_week_table()

        # Cài mặc định form
        self.taskDateEdit.setDate(QDate.currentDate())
        self.taskTimeEdit.setTime(QTime(8, 0))
        self.taskDurationSpin.setValue(60)

        # Render dữ liệu
        self._render_week()
        self._render_today_tasks()
        self._update_week_label()

    def connect_signals(self):
        # Điều hướng tuần
        self.btnPrevWeek.clicked.connect(self._prev_week)
        self.btnNextWeek.clicked.connect(self._next_week)

        # View mode (UI only, không thay đổi logic)
        self.btnWeekView.clicked.connect(lambda: self.btnWeekView.setChecked(True))
        self.btnDayView.clicked.connect(lambda: self.btnDayView.setChecked(True))

        # Form lưu / hủy
        self.btnSaveTask.clicked.connect(self._save_task)
        self.btnCancelTask.clicked.connect(self._reset_form)
        self.btnAddTask.clicked.connect(self._reset_form)

        # Priority buttons – chỉ cho phép chọn 1
        self.priorityHigh.clicked.connect(
            lambda: self._select_priority("high")
        )
        self.priorityMed.clicked.connect(
            lambda: self._select_priority("medium")
        )
        self.priorityLow.clicked.connect(
            lambda: self._select_priority("low")
        )

    def refresh(self):
        self._render_week()
        self._render_today_tasks()

    # ------------------------------------------------------------------ #
    #  Week calendar                                                       #
    # ------------------------------------------------------------------ #

    def _setup_week_table(self):
        tbl = self.weekCalendar
        tbl.setRowCount(1)
        tbl.setColumnCount(7)
        tbl.horizontalHeader().setVisible(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setSelectionMode(tbl.SelectionMode.SingleSelection)
        tbl.horizontalHeader().setStretchLastSection(False)

    def _render_week(self):
        tbl = self.weekCalendar
        tbl.clear()

        # Header labels
        day_headers = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        tbl.setHorizontalHeaderLabels(day_headers)

        today = date.today()
        tbl.setRowCount(1)

        # Thư mục task theo ngày trong tuần
        week_tasks: dict[date, List[Task]] = {}
        for i in range(7):
            d = self._current_week_start + timedelta(days=i)
            week_tasks[d] = [t for t in self._tasks if t.date == d]

        for col in range(7):
            day = self._current_week_start + timedelta(days=col)
            task_list = week_tasks.get(day, [])

            # Nội dung ô: ngày + số task
            badge = f" [{len(task_list)}]" if task_list else ""
            text  = f"{day.day}{badge}"
            item  = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Highlight hôm nay
            if day == today:
                item.setBackground(QBrush(QColor("#4a6cf7")))
                item.setForeground(QBrush(QColor("#ffffff")))
            elif task_list:
                item.setBackground(QBrush(QColor("#ebf4ff")))
                item.setForeground(QBrush(QColor("#2b6cb0")))
            else:
                item.setForeground(QBrush(QColor("#4a5568")))

            tbl.setItem(0, col, item)

        # Cột đồng đều
        tbl.horizontalHeader().setSectionResizeMode(
            tbl.horizontalHeader().ResizeMode.Stretch
        )
        tbl.setFixedHeight(80)

    def _update_week_label(self):
        months = ["Jan","Feb","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                  "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"]
        m = self._current_week_start.month
        y = self._current_week_start.year
        self.weekLabel.setText(f"{months[m-1]}, {y}")

    def _prev_week(self):
        self._current_week_start -= timedelta(weeks=1)
        self._render_week()
        self._update_week_label()

    def _next_week(self):
        self._current_week_start += timedelta(weeks=1)
        self._render_week()
        self._update_week_label()

    @staticmethod
    def _get_week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())

    # ------------------------------------------------------------------ #
    #  Today task list                                                     #
    # ------------------------------------------------------------------ #

    def _render_today_tasks(self):
        today = date.today()
        today_tasks = [t for t in self._tasks if t.date == today]

        # Cập nhật checkbox 3 nhiệm vụ mẫu cứng trong UI
        cb_map = {
            0: self.task1Done,
            1: self.task2Done,
            2: self.task3Done,
        }
        for i, cb in cb_map.items():
            if i < len(today_tasks):
                task = today_tasks[i]
                cb.setChecked(task.done)
                cb.stateChanged.connect(
                    lambda state, t=task: self._toggle_task_done(t, state)
                )

        # Phát tín hiệu thống kê
        done  = sum(1 for t in self._tasks if t.done)
        total = len(self._tasks)
        self.tasks_updated.emit(done, total)

    def _toggle_task_done(self, task: Task, state: int):
        task.done = (state == Qt.CheckState.Checked.value)
        done  = sum(1 for t in self._tasks if t.done)
        total = len(self._tasks)
        self.tasks_updated.emit(done, total)

    # ------------------------------------------------------------------ #
    #  Form                                                                #
    # ------------------------------------------------------------------ #

    def _select_priority(self, level: str):
        self.priorityHigh.setChecked(level == "high")
        self.priorityMed.setChecked(level  == "medium")
        self.priorityLow.setChecked(level  == "low")

    def _get_selected_priority(self) -> str:
        if self.priorityHigh.isChecked():
            return "high"
        if self.priorityLow.isChecked():
            return "low"
        return "medium"

    def _get_selected_subject(self) -> str:
        raw = self.taskSubjectCombo.currentText()
        # Bỏ icon phía trước
        for name in SUBJECT_ICONS:
            if name in raw:
                return name
        return raw.strip()

    def _save_task(self):
        # --- Validate ---
        title = self.taskNameInput.text().strip()
        if not title:
            self.show_warning(self, "Thiếu thông tin",
                              "Vui lòng nhập tên nhiệm vụ!")
            self.taskNameInput.setFocus()
            return

        qdate    = self.taskDateEdit.date()
        task_date = date(qdate.year(), qdate.month(), qdate.day())
        task_time = self.taskTimeEdit.time()
        duration  = self.taskDurationSpin.value()
        subject   = self._get_selected_subject()
        priority  = self._get_selected_priority()
        notes     = self.taskNotesInput.toPlainText().strip()

        if self._editing_task:
            # Sửa task hiện tại
            t = self._editing_task
            t.title    = title
            t.subject  = subject
            t.date     = task_date
            t.start    = task_time
            t.duration = duration
            t.priority = priority
            t.notes    = notes
            self._editing_task = None
        else:
            # Thêm mới
            new_task = Task(
                title=title, subject=subject, date=task_date,
                start=task_time, duration=duration,
                priority=priority, notes=notes,
                done=False, id=_new_id(),
            )
            self._tasks.append(new_task)

        self._reset_form()
        self._render_week()
        self._render_today_tasks()
        self.show_info(self, "Thành công", f"✅ Đã lưu nhiệm vụ: {title}")

    def _reset_form(self):
        self._editing_task = None
        self.taskNameInput.clear()
        self.taskSubjectCombo.setCurrentIndex(0)
        self.taskDateEdit.setDate(QDate.currentDate())
        self.taskTimeEdit.setTime(QTime(8, 0))
        self.taskDurationSpin.setValue(60)
        self._select_priority("medium")
        self.taskNotesInput.clear()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def get_tasks_stats(self) -> tuple[int, int]:
        done  = sum(1 for t in self._tasks if t.done)
        return done, len(self._tasks)

    def add_task_from_chat(self, title: str, subject: str = "Toán học"):
        """Chat controller có thể tạo task từ hội thoại."""
        task = Task(
            title=title, subject=subject,
            date=date.today(), start=QTime(8, 0),
            duration=60, priority="medium",
            id=_new_id(),
        )
        self._tasks.append(task)
        self._render_today_tasks()
        self._render_week()
        # ---------- THÊM HÀM MỚI NÀY ĐỂ PHỤC VỤ TOOL ----------
    
    def create_learning_schedule(self, topic: str, level: str, duration_weeks: int = 4, hours_per_week: int = 5) -> dict:
        """Hàm tạo lịch trình học tập dựa trên tham số. Dùng làm tool cho Gemini."""
        schedule = {
            "topic": topic,
            "level": level,
            "duration_weeks": duration_weeks,
            "hours_per_week": hours_per_week,
            "weeks": []
        }
        for i in range(1, duration_weeks + 1):
            schedule["weeks"].append({
                "week": i,
                "focus": f"Tuần {i}: Các khái niệm cốt lõi của {topic} cho người {level}",
                "tasks": [
                    f"Đọc tài liệu cơ bản về {topic}",
                    f"Làm bài tập thực hành số {i}",
                    f"Ôn tập lại kiến thức tuần {max(1, i-1)}" if i > 1 else "Làm quen với môi trường học tập"
                ]
            })
        if level == "beginner":
            schedule["notes"] = "Hãy dành nhiều thời gian cho thực hành."
        return schedule