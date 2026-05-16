"""
src/views/planner/planner_view.py
-----------------------------------
View trang Lịch Học + Pomodoro Timer + Learning Session.
Hỗ trợ học trực tiếp từ Lộ Trình.
"""

from __future__ import annotations

from datetime import date, timedelta, time
from typing   import Optional

from PyQt6.QtCore    import Qt, QDate, QTime, pyqtSignal, QTimer
from PyQt6.QtGui     import QColor, QBrush
from PyQt6.QtWidgets import (
    QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QScrollArea,
    QWidget, QSizePolicy, QSlider, QPlainTextEdit,
    QComboBox, QSpinBox, QCheckBox, QDialog, QDialogButtonBox,
)

from src.controllers.base_controller     import BaseController
from src.models.app_state                import AppState
from src.models.task                     import Task, Priority
from src.models.settings                 import AppSettings
from src.utils.date_helpers              import format_month_vi, week_start
from src.utils.study_subjects            import subject_combo_items, strip_icon
from src.views.components.pomodoro_timer import PomodoroTimer
from src.views.dialogs.task_dialog       import TaskDialog

# DB optional
try:
    from src.database.db_manager import DBManager
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# LearningSessionWidget – học trực tiếp trên app
# ---------------------------------------------------------------------------

class LearningSessionWidget(QFrame):
    """
    Widget ghi nhận một buổi học:
      1. Chọn môn + chủ đề
      2. Bấm Bắt đầu → timer chạy
      3. Bấm Kết thúc → kéo slider đánh giá % → lưu DB
    """

    session_saved = pyqtSignal(str, int, int)   # subject, duration_min, progress_pct

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed_sec = 0
        self._running     = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._build()

    def _build(self):
        self.setStyleSheet(
            "LearningSessionWidget{"
            "background:#1a1f2e;border-radius:16px;"
            "border:1px solid #2d3748;}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # Title
        title = QLabel("📖 Buổi Học Mới")
        title.setStyleSheet(
            "color:#fff;font-size:14px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        lay.addWidget(title)

        # Subject combo
        self._subj_combo = QComboBox()
        self._subj_combo.addItems(subject_combo_items(include_all=False))
        self._subj_combo.setStyleSheet(
            "QComboBox{background:#2d3748;color:#e2e8f0;border:none;"
            "border-radius:8px;padding:6px 10px;font-size:12px;}"
            "QComboBox::drop-down{border:none;}"
        )
        lay.addWidget(self._subj_combo)

        # Topic input
        self._topic_input = QPlainTextEdit()
        self._topic_input.setPlaceholderText(
            "Chủ đề hôm nay (VD: Đạo hàm – quy tắc dây chuyền)..."
        )
        self._topic_input.setFixedHeight(52)
        self._topic_input.setStyleSheet(
            "QPlainTextEdit{background:#2d3748;color:#e2e8f0;"
            "border:none;border-radius:8px;padding:6px;font-size:12px;}"
        )
        lay.addWidget(self._topic_input)

        # Timer display
        self._timer_lbl = QLabel("00:00:00")
        self._timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._timer_lbl.setStyleSheet(
            "color:#ffffff;font-size:32px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        lay.addWidget(self._timer_lbl)

        # Start / End buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._start_btn = QPushButton("▶ Bắt đầu học")
        self._start_btn.setMinimumHeight(36)
        self._start_btn.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:#fff;border:none;"
            "border-radius:8px;font-size:12px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
        )
        self._start_btn.clicked.connect(self._toggle)
        btn_row.addWidget(self._start_btn)

        self._end_btn = QPushButton("⏹ Kết thúc")
        self._end_btn.setMinimumHeight(36)
        self._end_btn.setEnabled(False)
        self._end_btn.setStyleSheet(
            "QPushButton{background:#38a169;color:#fff;border:none;"
            "border-radius:8px;font-size:12px;font-weight:600;}"
            "QPushButton:hover{background:#2f855a;}"
            "QPushButton:disabled{background:#2d3748;color:#4a5568;}"
        )
        self._end_btn.clicked.connect(self._finish)
        btn_row.addWidget(self._end_btn)
        lay.addLayout(btn_row)

        # Evaluation frame (ẩn đến khi kết thúc)
        self._eval_frame = QFrame()
        self._eval_frame.setStyleSheet("background:transparent;border:none;")
        eval_lay = QVBoxLayout(self._eval_frame)
        eval_lay.setContentsMargins(0, 4, 0, 0)
        eval_lay.setSpacing(6)

        eval_lbl = QLabel("Bạn nắm được bao nhiêu % chủ đề này?")
        eval_lbl.setStyleSheet(
            "color:#a0aec0;font-size:11px;background:transparent;border:none;"
        )
        eval_lay.addWidget(eval_lbl)

        slider_row = QHBoxLayout()
        self._slider = QSlider(Qt.Orientation.Horizontal) 
        self._slider.setValue(70)
        self._slider.setStyleSheet(
            "QSlider::groove:horizontal{height:6px;background:#4a5568;"
            "border-radius:3px;}"
            "QSlider::handle:horizontal{width:16px;height:16px;"
            "background:#4a6cf7;border-radius:8px;margin:-5px 0;}"
            "QSlider::sub-page:horizontal{background:#4a6cf7;border-radius:3px;}"
        )
        self._pct_lbl = QLabel("70%")
        self._pct_lbl.setFixedWidth(32)
        self._pct_lbl.setStyleSheet(
            "color:#4a6cf7;font-size:12px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        self._slider.valueChanged.connect(
            lambda v: self._pct_lbl.setText(f"{v}%")
        )
        slider_row.addWidget(self._slider)
        slider_row.addWidget(self._pct_lbl)
        eval_lay.addLayout(slider_row)

        self._note_input = QPlainTextEdit()
        self._note_input.setPlaceholderText("Ghi chú: khó chỗ nào, cần ôn lại gì...")
        self._note_input.setFixedHeight(46)
        self._note_input.setStyleSheet(
            "QPlainTextEdit{background:#2d3748;color:#e2e8f0;"
            "border:none;border-radius:8px;padding:6px;font-size:11px;}"
        )
        eval_lay.addWidget(self._note_input)

        save_btn = QPushButton("💾 Lưu buổi học")
        save_btn.setMinimumHeight(34)
        save_btn.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:#fff;border:none;"
            "border-radius:8px;font-size:12px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
        )
        save_btn.clicked.connect(self._save)
        eval_lay.addWidget(save_btn)

        self._eval_frame.setVisible(False)
        lay.addWidget(self._eval_frame)

    # ── Logic ─────────────────────────────────────────────────────────

    def _tick(self):
        self._elapsed_sec += 1
        h = self._elapsed_sec // 3600
        m = (self._elapsed_sec % 3600) // 60
        s = self._elapsed_sec % 60
        self._timer_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _toggle(self):
        if not self._running:
            self._running = True
            self._timer.start()
            self._start_btn.setText("⏸ Tạm dừng")
            self._end_btn.setEnabled(True)
        else:
            self._running = False
            self._timer.stop()
            self._start_btn.setText("▶ Tiếp tục")

    def _finish(self):
        self._timer.stop()
        self._running = False
        self._start_btn.setEnabled(False)
        self._end_btn.setEnabled(False)
        self._eval_frame.setVisible(True)

    def _save(self):
        subject      = strip_icon(self._subj_combo.currentText())
        topic        = self._topic_input.toPlainText().strip() or "Chưa ghi chủ đề"
        duration_min = max(1, self._elapsed_sec // 60)
        progress_pct = self._slider.value()
        note         = self._note_input.toPlainText().strip()

        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_study_session(
                    subject=subject,
                    topic=topic,
                    duration_min=duration_min,
                    progress_pct=progress_pct,
                    note=note,
                )
            except Exception as e:
                print(f"[DB] save_study_session lỗi: {e}")

        self.session_saved.emit(subject, duration_min, progress_pct)
        self._reset()

    def _reset(self):
        self._elapsed_sec = 0
        self._timer_lbl.setText("00:00:00")
        self._topic_input.clear()
        self._note_input.clear()
        self._slider.setValue(70)
        self._eval_frame.setVisible(False)
        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶ Bắt đầu học")
        self._end_btn.setEnabled(False)
        self._running = False
        self._timer.stop()

    # ── Public API để gọi từ ngoài (Roadmap) ─────────────────────────
    def start_study(self, subject: str, topic: str):
        """Tự động điền subject và topic, sau đó bắt đầu học."""
        # Chọn subject trong combo
        idx = self._subj_combo.findText(subject, Qt.MatchFlag.MatchContains)
        if idx >= 0:
            self._subj_combo.setCurrentIndex(idx)
        self._topic_input.setPlainText(topic)
        # Tự động bắt đầu nếu chưa chạy
        if not self._running:
            self._toggle()


# ---------------------------------------------------------------------------
# PlannerView
# ---------------------------------------------------------------------------

class PlannerView(BaseController):
    """Controller + View trang Lịch Học."""

    UI_FILE = "planner_page.ui"

    tasks_changed = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None):
        self._settings  = settings
        self._today_container: Optional[QVBoxLayout] = None
        self._pomodoro: Optional[PomodoroTimer] = None
        self._learn_widget: Optional[LearningSessionWidget] = None
        self.main_window = None  # sẽ được set từ MainWindow
        super().__init__(parent)

    # ── Setup ─────────────────────────────────────────────────────────

    def setup_ui(self):
        self._state   = AppState.instance()
        self._week_dt = week_start(date.today())

        self._setup_table()
        self._setup_subject_combo()
        self._setup_form_defaults()
        self._setup_today_panel()
        self._inject_widgets()   # chèn Pomodoro và LearningSession vào placeholder
        self._render_week()
        self._render_today()
        self._update_week_label()

    def connect_signals(self):
        self.btnPrevWeek.clicked.connect(self._prev_week)
        self.btnNextWeek.clicked.connect(self._next_week)
        self.btnWeekView.clicked.connect(lambda: self.btnWeekView.setChecked(True))
        self.btnDayView.clicked.connect(lambda: self.btnDayView.setChecked(True))
        self.btnAddTask.clicked.connect(self._open_task_dialog)
        self.btnSaveTask.clicked.connect(self._save_inline_task)
        self.btnCancelTask.clicked.connect(self._reset_form)
        self.priorityHigh.clicked.connect(lambda: self._select_priority("high"))
        self.priorityMed.clicked.connect(lambda: self._select_priority("medium"))
        self.priorityLow.clicked.connect(lambda: self._select_priority("low"))

    def refresh(self):
        self._render_week()
        self._render_today()

    # ── Setup helpers ─────────────────────────────────────────────────

    def _setup_table(self):
        tbl = self.weekCalendar
        tbl.setRowCount(1)
        tbl.setColumnCount(7)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setSelectionMode(tbl.SelectionMode.SingleSelection)
        tbl.horizontalHeader().setSectionResizeMode(
            tbl.horizontalHeader().ResizeMode.Stretch
        )
        tbl.setFixedHeight(80)

    def _setup_subject_combo(self):
        try:
            self.taskSubjectCombo.clear()
            self.taskSubjectCombo.addItems(subject_combo_items(include_all=False))
        except AttributeError:
            pass

    def _setup_form_defaults(self):
        try:
            self.taskDateEdit.setDate(QDate.currentDate())
            self.taskTimeEdit.setTime(QTime(8, 0))
            self.taskDurationSpin.setValue(60)
            self._select_priority("medium")
        except AttributeError:
            pass

    def _setup_today_panel(self):
        """Tạo QVBoxLayout riêng trong todayTasksFrame để hiển thị task."""
        frame = self._find_today_frame()
        if frame is None:
            return

        old_layout = frame.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._today_container = old_layout
        else:
            self._today_container = QVBoxLayout(frame)
            self._today_container.setContentsMargins(8, 8, 8, 8)
            self._today_container.setSpacing(8)

        # Header
        today_str = date.today().strftime("%d/%m/%Y")
        header = QLabel(f"📋 Nhiệm vụ hôm nay – {today_str}")
        header.setStyleSheet(
            "color:#2d3748;font-size:13px;font-weight:bold;"
            "background:transparent;border:none;padding:4px 0;"
        )
        self._today_container.addWidget(header)
        self._today_header_count = 1

    def _find_today_frame(self) -> Optional[QFrame]:
        frame = getattr(self, "todayTasksFrame", None)
        if frame:
            return frame
        frame = self.findChild(QFrame, "todayTasksFrame")
        if frame:
            return frame
        # Fallback: tìm frame có tên chứa "today"
        for child in self.findChildren(QFrame):
            if "today" in child.objectName().lower():
                return child
        return None

    def _inject_widgets(self):
        """Chèn PomodoroTimer và LearningSessionWidget vào placeholder trong UI."""
        # Tìm placeholder cho Pomodoro
        pomo_placeholder = self.findChild(QFrame, "pomodoroPlaceholder")
        if pomo_placeholder is None:
            # Nếu không tìm thấy placeholder, tạo frame mới và chèn vào rightColumn
            # (fallback cho UI cũ)
            right_layout = self.findChild(QVBoxLayout, "rightColumn")
            if right_layout is None:
                # Tìm layout bất kỳ chứa quickAddFrame
                quick_frame = self.findChild(QFrame, "quickAddFrame")
                if quick_frame and quick_frame.parentWidget() and quick_frame.parentWidget().layout():
                    parent_layout = quick_frame.parentWidget().layout()
                    # Chèn trước quickAddFrame
                    idx = parent_layout.indexOf(quick_frame)
                    if idx >= 0:
                        pomo_placeholder = QFrame()
                        pomo_placeholder.setObjectName("pomodoroPlaceholder")
                        parent_layout.insertWidget(idx, pomo_placeholder)
        if pomo_placeholder:
            self._pomodoro = PomodoroTimer()
            self._pomodoro.session_completed.connect(self._on_pomodoro_done)
            # Xóa widget con cũ, tái dùng layout có sẵn (tránh QLayout warning)
            old = pomo_placeholder.layout()
            if old:
                while old.count():
                    item = old.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                old.setContentsMargins(0, 0, 0, 0)
                old.addWidget(self._pomodoro)
            else:
                lay = QVBoxLayout(pomo_placeholder)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(self._pomodoro)
        else:
            # Fallback: tạo mới và thêm vào rightColumn
            self._pomodoro = PomodoroTimer()
            self._pomodoro.session_completed.connect(self._on_pomodoro_done)

        # Tìm placeholder cho LearningSession
        learn_placeholder = self.findChild(QFrame, "learningSessionPlaceholder")
        if learn_placeholder is None:
            quick_frame = self.findChild(QFrame, "quickAddFrame")
            if quick_frame and quick_frame.parentWidget() and quick_frame.parentWidget().layout():
                parent_layout = quick_frame.parentWidget().layout()
                idx = parent_layout.indexOf(quick_frame)
                if idx >= 0:
                    learn_placeholder = QFrame()
                    learn_placeholder.setObjectName("learningSessionPlaceholder")
                    parent_layout.insertWidget(idx, learn_placeholder)
        if learn_placeholder:
            self._learn_widget = LearningSessionWidget()
            self._learn_widget.session_saved.connect(self._on_session_saved)
            old = learn_placeholder.layout()
            if old:
                while old.count():
                    item = old.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                old.setContentsMargins(0, 0, 0, 0)
                old.addWidget(self._learn_widget)
            else:
                lay = QVBoxLayout(learn_placeholder)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(self._learn_widget)
        else:
            self._learn_widget = LearningSessionWidget()
            self._learn_widget.session_saved.connect(self._on_session_saved)

    # ── Week calendar ─────────────────────────────────────────────────

    def _render_week(self):
        tbl = self.weekCalendar
        today = date.today()
        tbl.setHorizontalHeaderLabels(["T2","T3","T4","T5","T6","T7","CN"])
        for col in range(7):
            d = self._week_dt + timedelta(days=col)
            tasks_n = len(self._state.tasks_for_date(d))
            badge = f" [{tasks_n}]" if tasks_n else ""
            item = QTableWidgetItem(f"{d.day}{badge}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if d == today:
                item.setBackground(QBrush(QColor("#4a6cf7")))
                item.setForeground(QBrush(QColor("#ffffff")))
            elif tasks_n:
                item.setBackground(QBrush(QColor("#ebf4ff")))
                item.setForeground(QBrush(QColor("#2b6cb0")))
            tbl.setItem(0, col, item)

    def _update_week_label(self):
        try:
            self.weekLabel.setText(format_month_vi(self._week_dt))
        except AttributeError:
            pass

    def _prev_week(self):
        self._week_dt -= timedelta(weeks=1)
        self._render_week()
        self._update_week_label()

    def _next_week(self):
        self._week_dt += timedelta(weeks=1)
        self._render_week()
        self._update_week_label()

    # ── Today tasks ───────────────────────────────────────────────────

    def _render_today(self):
        if self._today_container is None:
            return

        header_count = getattr(self, "_today_header_count", 1)
        while self._today_container.count() > header_count:
            item = self._today_container.takeAt(header_count)
            if item and item.widget():
                item.widget().deleteLater()

        today_tasks = self._state.tasks_for_date(date.today())
        if not today_tasks:
            empty = QLabel("🎉 Không có nhiệm vụ nào hôm nay!")
            empty.setStyleSheet(
                "color:#718096;font-size:13px;padding:12px;"
                "background:transparent;border:none;"
            )
            self._today_container.addWidget(empty)
        else:
            for task in today_tasks:
                item_w = self._make_task_row(task)
                self._today_container.addWidget(item_w)

        self._today_container.addStretch()
        self.tasks_changed.emit()

    def _make_task_row(self, task: Task) -> QFrame:
        accent = task.accent_color
        row = QFrame()
        row.setStyleSheet(
            f"QFrame{{background:{task.bg_color};"
            f"border-left:4px solid {accent};"
            f"border-radius:8px;}}"
        )
        h = QHBoxLayout(row)
        h.setContentsMargins(10, 8, 10, 8)
        h.setSpacing(10)

        cb = QCheckBox()
        cb.setChecked(task.done)
        cb.setStyleSheet(
            f"QCheckBox::indicator{{width:18px;height:18px;"
            f"border-radius:4px;border:2px solid {accent};}}"
            f"QCheckBox::indicator:checked{{background:{accent};}}"
        )
        cb.stateChanged.connect(
            lambda s, t=task: self._on_task_done_changed(
                t, s == Qt.CheckState.Checked.value
            )
        )
        h.addWidget(cb)

        info = QVBoxLayout()
        info.setSpacing(2)
        title_lbl = QLabel(f"{task.icon} {task.title}")
        title_lbl.setStyleSheet(
            f"color:{'#a0aec0' if task.done else '#1a1f2e'};"
            f"font-size:13px;font-weight:bold;"
            f"{'text-decoration:line-through;' if task.done else ''}"
            "background:transparent;border:none;"
        )
        time_lbl = QLabel(f"{task.time_range_str()}  ·  {task.duration_str()}")
        time_lbl.setStyleSheet(
            f"color:{accent};font-size:11px;background:transparent;border:none;"
        )
        info.addWidget(title_lbl)
        info.addWidget(time_lbl)
        h.addLayout(info)
        h.addStretch()

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;"
            "color:#a0aec0;font-size:12px;border-radius:4px;}"
            "QPushButton:hover{background:#fed7d7;color:#c53030;}"
        )
        del_btn.clicked.connect(lambda _, t=task: self._on_task_deleted(t))
        h.addWidget(del_btn)

        return row

    def _on_task_done_changed(self, task: Task, done: bool):
        task.done = done
        self.tasks_changed.emit()
        self._state.save_tasks()
        self._render_today()

    def _on_task_deleted(self, task: Task):
        if self.confirm(self, "Xoá nhiệm vụ", f"Xoá nhiệm vụ «{task.title}»?"):
            self._state.remove_task(task.id)
            self._state.save_tasks()
            self._render_today()
            self._render_week()

    # ── Priority ──────────────────────────────────────────────────────

    def _select_priority(self, level: str):
        try:
            self.priorityHigh.setChecked(level == "high")
            self.priorityMed.setChecked(level == "medium")
            self.priorityLow.setChecked(level == "low")
        except AttributeError:
            pass

    def _get_priority(self) -> Priority:
        try:
            if self.priorityHigh.isChecked():
                return Priority.HIGH
            if self.priorityLow.isChecked():
                return Priority.LOW
        except AttributeError:
            pass
        return Priority.MEDIUM

    # ── Form ──────────────────────────────────────────────────────────

    def _open_task_dialog(self):
        dlg = TaskDialog(parent=self)
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            task = dlg.get_task()
            if task:
                self._state.add_task(task)
                self._state.save_tasks()
                self._render_today()
                self._render_week()
                self.show_info(self, "Thành công", f"✅ Đã thêm: {task.title}")

    def _save_inline_task(self):
        try:
            title = self.taskNameInput.text().strip()
        except AttributeError:
            return
        if not title:
            self.show_warning(self, "Thiếu thông tin", "Vui lòng nhập tên nhiệm vụ!")
            return

        try:
            qd = self.taskDateEdit.date()
            task = Task(
                title=title,
                subject=strip_icon(self.taskSubjectCombo.currentText()),
                date=date(qd.year(), qd.month(), qd.day()),
                start=self.taskTimeEdit.time(),
                duration=self.taskDurationSpin.value(),
                priority=self._get_priority(),
                notes=self.taskNotesInput.toPlainText().strip(),
            )
        except Exception as e:
            self.show_error(self, "Lỗi", str(e))
            return

        self._state.add_task(task)
        self._state.save_tasks()
        self._reset_form()
        self._render_today()
        self._render_week()
        self.show_info(self, "Thành công", f"✅ Đã lưu: {title}")

    def _reset_form(self):
        try:
            self.taskNameInput.clear()
            self.taskSubjectCombo.setCurrentIndex(0)
            self.taskDateEdit.setDate(QDate.currentDate())
            self.taskTimeEdit.setTime(QTime(8, 0))
            self.taskDurationSpin.setValue(60)
            self._select_priority("medium")
            self.taskNotesInput.clear()
        except AttributeError:
            pass

    # ── Pomodoro & Learning Session ───────────────────────────────────

    def _on_pomodoro_done(self, mode: str):
        if mode == "focus":
            self.show_info(
                self, "🍅 Pomodoro xong!",
                "Nghỉ ngơi 5 phút rồi tiếp tục học nhé! 💪"
            )

    def _on_session_saved(self, subject: str, duration_min: int, progress_pct: int):
        self.show_info(
            self, "✅ Đã lưu buổi học",
            f"Môn: {subject}\n"
            f"Thời gian: {duration_min} phút\n"
            f"Tiến độ: {progress_pct}%"
        )
        self.tasks_changed.emit()
        if _DB_AVAILABLE:
            try:
                db = DBManager.instance()
                db.save_study_session(subject, "Buổi học tự do", duration_min, progress_pct, "")
            except Exception:
                pass

    # ── AI Agent tools (gọi từ ChatView) ─────────────────────────────

    def create_learning_schedule(
        self,
        topic: str,
        level: str,
        duration_type: str = "week",      # 'day' hoặc 'week'
        target_date: str = None,          # 'today' hoặc 'YYYY-MM-DD'
        duration_weeks: int = 4,
        hours_per_day: float = 2.0,
        hours_per_week: int = 5,
    ) -> dict:
        """
        Tool AI: tạo lịch trình học tập và tự động thêm task vào Planner.
        Hỗ trợ lịch theo ngày (duration_type='day') hoặc theo tuần (duration_type='week').
        """
        schedule = {
            "topic": topic,
            "level": level,
            "duration_type": duration_type,
            "tasks_created": [],
        }

        if duration_type == "day":
            # Xử lý ngày cụ thể
            if not target_date or target_date == "today":
                study_date = date.today()
            else:
                try:
                    study_date = date.fromisoformat(target_date)
                except ValueError:
                    study_date = date.today()

            # Tạo các task trong ngày
            tasks = [
                f"📖 Đọc tài liệu {topic} – lý thuyết cơ bản",
                f"✍️ Làm bài tập thực hành {topic}",
                f"🔄 Ôn tập lại kiến thức {topic}"
            ]
            for i, task_title in enumerate(tasks):
                t = Task(
                    title=task_title,
                    subject=topic,
                    date=study_date,
                    start=time(8 + i*2, 0),  # 8h, 10h, 12h
                    duration=int(hours_per_day * 60 // len(tasks)),
                    priority=Priority.HIGH if level == "beginner" else Priority.MEDIUM,
                )
                self._state.add_task(t)
                self._state.save_tasks()
                schedule["tasks_created"].append(task_title)

            schedule["date"] = study_date.isoformat()
            schedule["hours"] = hours_per_day
            schedule["message"] = f"Đã tạo {len(tasks)} nhiệm vụ cho ngày {study_date.strftime('%d/%m/%Y')}"

        else:  # week
            today = date.today()
            for i in range(1, duration_weeks + 1):
                tasks_for_week = [
                    f"Đọc tài liệu {topic} – phần {i}",
                    f"Làm bài tập thực hành tuần {i}",
                    f"Ôn lại kiến thức tuần {max(1, i-1)}" if i > 1
                    else f"Làm quen với {topic}",
                ]
                week_date = today + timedelta(weeks=i - 1)
                for j, task_title in enumerate(tasks_for_week):
                    t = Task(
                        title=task_title,
                        subject=topic,
                        date=week_date + timedelta(days=j * 2),
                        duration=(hours_per_week * 60) // len(tasks_for_week),
                        priority=Priority.HIGH if i == 1 else Priority.MEDIUM,
                    )
                    self._state.add_task(t)
                    self._state.save_tasks()
                    schedule["tasks_created"].append(task_title)

            schedule["duration_weeks"] = duration_weeks
            schedule["hours_per_week"] = hours_per_week
            schedule["message"] = f"Đã tạo lịch {duration_weeks} tuần cho môn {topic}"

        if level == "beginner":
            schedule["notes"] = "Hãy dành nhiều thời gian thực hành."
        elif level == "advanced":
            schedule["notes"] = "Tập trung vào các bài tập khó và project thực tế."

        self._render_week()
        self._render_today()
        return schedule

    # ── Public API ────────────────────────────────────────────────────

    def get_stats(self) -> tuple[int, int]:
        return self._state.tasks_done, self._state.tasks_total

    def add_task_from_external(self, title: str, subject: str = "Toán học"):
        """Thêm task từ controller khác (Chat, Roadmap)."""
        task = Task(
            title=title,
            subject=subject,
            date=date.today(),
            duration=60,
            priority=Priority.MEDIUM,
        )
        self._state.add_task(task)
        self._state.save_tasks()
        self._render_today()
        self._render_week()

    def set_main_window(self, mw):
        self.main_window = mw

    def start_study_from_roadmap(self, subject: str, topic: str):
        """Gọi từ RoadmapView để bắt đầu học ngay một topic."""
        if self.main_window:
            self.main_window.stackedWidget.setCurrentIndex(2)
        if self._learn_widget:
            self._learn_widget.start_study(subject, topic)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Học ngay", f"Hãy vào tab Lịch Học để học topic: {topic}")