"""
src/views/roadmap/roadmap_view.py
-----------------------------------
View trang Lộ Trình Học – hoàn chỉnh
ĐÃ SỬA: generate_learning_roadmap nhận topics từ AI.
"""

from __future__ import annotations

from datetime import date
from typing   import Optional, List

from PyQt6.QtCore    import pyqtSignal, Qt, QDate
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QSizePolicy, QSpacerItem,
    QDialog, QDialogButtonBox, QWidget, QGridLayout,
    QLineEdit, QComboBox, QDateEdit, QFormLayout, QSpinBox,
    QPlainTextEdit,
)

from src.controllers.base_controller import BaseController
from src.models.app_state            import AppState
from src.models.roadmap_node         import SubjectRoadmap, Topic, TopicStatus
from src.models.settings             import AppSettings
from src.utils.study_subjects        import strip_icon, subject_combo_items
from src.utils.date_helpers          import deadline_label

# DB optional
try:
    from src.database.db_manager import DBManager
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# GoalCard – hiển thị một mục tiêu học tập đang theo dõi
# ---------------------------------------------------------------------------

class GoalCard(QFrame):
    def __init__(self, goal: dict, parent=None):
        super().__init__(parent)
        self._goal = goal
        self.setStyleSheet(
            "QFrame{background:#fff;border-radius:12px;"
            "border:1px solid #e2e8f0;}"
        )
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        g = self._goal
        subject  = g.get('subject', '')
        topic    = g.get('topic', '')
        deadline = g.get('deadline')
        cur_pct  = g.get('current_pct', 0)
        tgt_pct  = g.get('target_pct', 100)

        hdr = QHBoxLayout()
        title_lbl = QLabel(f"🎯 {subject}")
        title_lbl.setStyleSheet(
            "color:#1a1f2e;font-size:13px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        dl_lbl = QLabel(deadline_label(deadline) if deadline else "")
        dl_lbl.setStyleSheet(
            "color:#718096;font-size:11px;background:transparent;border:none;"
        )
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(dl_lbl)
        lay.addLayout(hdr)

        topic_lbl = QLabel(topic)
        topic_lbl.setWordWrap(True)
        topic_lbl.setStyleSheet(
            "color:#4a5568;font-size:12px;background:transparent;border:none;"
        )
        lay.addWidget(topic_lbl)

        pb_row = QHBoxLayout()
        pb = QProgressBar()
        pb.setRange(0, tgt_pct)
        pb.setValue(cur_pct)
        pb.setTextVisible(False)
        pb.setFixedHeight(6)
        color = "#38a169" if cur_pct >= tgt_pct * 0.8 else \
                "#d69e2e" if cur_pct >= tgt_pct * 0.4 else "#e53e3e"
        pb.setStyleSheet(
            f"QProgressBar{{background:#e2e8f0;border-radius:3px;border:none;}}"
            f"QProgressBar::chunk{{background:{color};border-radius:3px;}}"
        )
        pct_lbl = QLabel(f"{cur_pct}/{tgt_pct}%")
        pct_lbl.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        pct_lbl.setFixedWidth(55)
        pb_row.addWidget(pb)
        pb_row.addWidget(pct_lbl)
        lay.addLayout(pb_row)


# ---------------------------------------------------------------------------
# SubjectCard – hiển thị một môn học và các topic của nó
# ---------------------------------------------------------------------------

class SubjectCard(QFrame):
    topic_changed = pyqtSignal()

    def __init__(self, rm: SubjectRoadmap, on_topic_callback, parent=None):
        super().__init__(parent)
        self._rm = rm
        self._on_topic_callback = on_topic_callback
        self._subject_name = rm.name
        self.setStyleSheet(
            "QFrame{background:#ffffff;border-radius:14px;"
            "border:1px solid #e2e8f0;}"
        )
        self._build()

    def _build(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(18, 16, 18, 16)
        self._outer.setSpacing(10)

        hdr = QHBoxLayout()
        name_lbl = QLabel(f"{self._rm.icon}  {self._rm.name}")
        name_lbl.setStyleSheet(
            "color:#1a1f2e;font-size:15px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        pct_lbl = QLabel(f"{self._rm.progress}%")
        pct_lbl.setStyleSheet(
            f"color:{self._rm.color};font-size:14px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        self._expand_btn = QPushButton("▼" if self._rm.expanded else "▶")
        self._expand_btn.setFixedSize(26, 26)
        self._expand_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;"
            "color:#718096;font-size:12px;}"
            "QPushButton:hover{color:#2d3748;}"
        )
        self._expand_btn.clicked.connect(self._toggle)
        hdr.addWidget(name_lbl)
        hdr.addStretch()
        hdr.addWidget(pct_lbl)
        hdr.addWidget(self._expand_btn)
        self._outer.addLayout(hdr)

        pb = QProgressBar()
        pb.setValue(self._rm.progress)
        pb.setTextVisible(False)
        pb.setFixedHeight(6)
        pb.setStyleSheet(
            f"QProgressBar{{background:#e2e8f0;border-radius:3px;border:none;}}"
            f"QProgressBar::chunk{{background:{self._rm.color};border-radius:3px;}}"
        )
        self._outer.addWidget(pb)

        stats = QLabel(
            f"{self._rm.done_topics}/{self._rm.total_topics} chủ đề hoàn thành  ·  "
            f"~{self._rm.estimated_remaining_hours:.0f}h còn lại"
        )
        stats.setStyleSheet(
            "color:#718096;font-size:11px;background:transparent;border:none;"
        )
        self._outer.addWidget(stats)

        self._topics_widget = QWidget()
        self._topics_widget.setStyleSheet("background:transparent;")
        grid = QGridLayout(self._topics_widget)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setSpacing(8)
        cols = 2
        for i, topic in enumerate(self._rm.topics):
            btn = self._make_topic_btn(topic)
            grid.addWidget(btn, i // cols, i % cols)
        self._outer.addWidget(self._topics_widget)
        self._topics_widget.setVisible(self._rm.expanded)

    def _make_topic_btn(self, topic: Topic) -> QPushButton:
        STYLES = {
            TopicStatus.DONE: (
                f"background:#f0fff4;border:1.5px solid {self._rm.color};"
                "border-radius:10px;color:#276749;",
                f"background:#c6f6d5;border:1.5px solid {self._rm.color};"
                "border-radius:10px;color:#276749;"
            ),
            TopicStatus.IN_PROGRESS: (
                "background:#fffbeb;border:1.5px solid #f6ad55;"
                "border-radius:10px;color:#744210;",
                "background:#fefcbf;border:1.5px solid #f6ad55;"
                "border-radius:10px;color:#744210;"
            ),
            TopicStatus.LOCKED: (
                "background:#f7f8fc;border:1.5px solid #e2e8f0;"
                "border-radius:10px;color:#a0aec0;",
                None
            ),
        }
        normal, hover = STYLES.get(topic.status, STYLES[TopicStatus.LOCKED])
        btn = QPushButton(topic.display_name)
        btn.setMinimumHeight(36)
        hover_css = f"QPushButton:hover{{{hover}}}" if hover else ""
        btn.setStyleSheet(
            f"QPushButton{{font-size:12px;font-weight:500;"
            f"text-align:left;padding:0 10px;{normal}}}"
            + hover_css
        )
        if topic.status != TopicStatus.LOCKED:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, t=topic: self._on_topic_callback(t, self._subject_name))
        else:
            btn.setEnabled(False)
        return btn

    def _toggle(self):
        self._rm.expanded = not self._rm.expanded
        self._topics_widget.setVisible(self._rm.expanded)
        self._expand_btn.setText("▼" if self._rm.expanded else "▶")

    def rebuild(self):
        self._build()


# ---------------------------------------------------------------------------
# TopicDialog – hiển thị chi tiết topic, cho phép học ngay hoặc đánh dấu hoàn thành
# ---------------------------------------------------------------------------

class TopicDialog(QDialog):
    topic_completed = pyqtSignal(object)
    topic_study = pyqtSignal(str, str)

    def __init__(self, topic: Topic, subject_name: str = "", parent=None):
        super().__init__(parent)
        self._topic = topic
        self._subject_name = subject_name
        self.setWindowTitle(topic.name)
        self.setMinimumWidth(420)
        self.setStyleSheet(
            "QDialog{background:#fff;font-family:'Segoe UI',Arial,sans-serif;}"
        )
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel(f"📚 {self._topic.name}")
        title.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#1a1f2e;"
            "background:transparent;border:none;"
        )
        lay.addWidget(title)

        badge_info = {
            TopicStatus.DONE:        ("✅ Đã hoàn thành", "#f0fff4", "#276749"),
            TopicStatus.IN_PROGRESS: ("⏳ Đang học",       "#fffbeb", "#744210"),
            TopicStatus.LOCKED:      ("🔒 Chưa mở khóa",  "#f7f8fc", "#718096"),
        }
        txt, bg, fg = badge_info.get(self._topic.status, ("❓ Không rõ", "#f7f8fc", "#718096"))
        badge = QLabel(txt)
        badge.setStyleSheet(
            f"background:{bg};color:{fg};border-radius:8px;"
            f"padding:6px 14px;font-size:13px;font-weight:600;"
            "border:none;"
        )
        badge.setFixedHeight(34)
        lay.addWidget(badge)

        time_lbl = QLabel(f"⏱ Thời gian dự kiến: {self._topic.estimated_h:.1f} giờ")
        time_lbl.setStyleSheet(
            "color:#718096;font-size:12px;background:transparent;border:none;"
        )
        lay.addWidget(time_lbl)

        if self._topic.detail:
            desc = QLabel(self._topic.detail)
            desc.setWordWrap(True)
            desc.setStyleSheet(
                "color:#4a5568;font-size:13px;line-height:1.5;"
                "background:transparent;border:none;"
            )
            lay.addWidget(desc)

        if self._topic.resource_urls:
            res_lbl = QLabel("📎 Tài liệu tham khảo:")
            res_lbl.setStyleSheet(
                "color:#2d3748;font-size:12px;font-weight:600;"
                "background:transparent;border:none;"
            )
            lay.addWidget(res_lbl)
            for url in self._topic.resource_urls[:3]:
                link = QLabel(f'<a href="{url}">{url}</a>')
                link.setOpenExternalLinks(True)
                link.setStyleSheet(
                    "color:#4a6cf7;font-size:12px;"
                    "background:transparent;border:none;"
                )
                lay.addWidget(link)

        btn_row = QHBoxLayout()
        if self._topic.status != TopicStatus.DONE:
            mark_btn = QPushButton("✅ Đánh dấu hoàn thành")
            mark_btn.setMinimumHeight(38)
            mark_btn.setStyleSheet(
                "QPushButton{background:#38a169;color:white;border:none;"
                "border-radius:8px;padding:8px 16px;font-size:13px;}"
                "QPushButton:hover{background:#2f855a;}"
            )
            mark_btn.clicked.connect(self._mark_done)
            btn_row.addWidget(mark_btn)

        if self._topic.status != TopicStatus.LOCKED:
            study_btn = QPushButton("📖 Học ngay")
            study_btn.setMinimumHeight(38)
            study_btn.setStyleSheet(
                "QPushButton{background:#4a6cf7;color:white;border:none;"
                "border-radius:8px;padding:8px 16px;font-size:13px;}"
                "QPushButton:hover{background:#3b5bdb;}"
            )
            study_btn.clicked.connect(self._study_now)
            btn_row.addWidget(study_btn)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.setStyleSheet(
            "QPushButton{background:#f7f8fc;color:#4a5568;border:1px solid #e2e8f0;"
            "border-radius:8px;padding:8px 20px;font-size:13px;}"
            "QPushButton:hover{background:#e2e8f0;}"
        )
        btns.rejected.connect(self.reject)
        btn_row.addWidget(btns)
        lay.addLayout(btn_row)

    def _mark_done(self):
        self._topic.mark_done()
        self.topic_completed.emit(self._topic)
        self.accept()

    def _study_now(self):
        self.topic_study.emit(self._subject_name, self._topic.name)
        self.accept()


# ---------------------------------------------------------------------------
# AddGoalDialog
# ---------------------------------------------------------------------------

class AddGoalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: Optional[dict] = None
        self.setWindowTitle("🎯 Thêm Mục Tiêu Học Tập")
        self.setMinimumWidth(440)
        self.setStyleSheet(
            "QDialog{background:#fff;font-family:'Segoe UI',Arial,sans-serif;}"
        )
        self._build()

    def _build(self):
        _FIELD = (
            "QLineEdit,QComboBox,QDateEdit,QSpinBox,QPlainTextEdit{"
            "background:#f7f8fc;border:1px solid #e2e8f0;"
            "border-radius:8px;padding:6px 12px;font-size:13px;color:#2d3748;}"
            "QLineEdit:focus,QComboBox:focus,QDateEdit:focus,QSpinBox:focus{"
            "border-color:#4a6cf7;background:#fff;}"
        )

        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(14)

        title = QLabel("🎯 Thêm Mục Tiêu Học Tập")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#1a1f2e;")
        main.addWidget(title)

        sub = QLabel("Đặt mục tiêu rõ ràng để AI hỗ trợ cá nhân hóa tốt hơn")
        sub.setStyleSheet("color:#718096;font-size:12px;")
        main.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet("color:#4a5568;font-size:12px;font-weight:600;")
            return l

        self._subj_combo = QComboBox()
        self._subj_combo.addItems(subject_combo_items(include_all=False))
        self._subj_combo.setMinimumHeight(38)
        self._subj_combo.setStyleSheet(_FIELD)
        form.addRow(lbl("Môn học *"), self._subj_combo)

        self._topic_edit = QLineEdit()
        self._topic_edit.setPlaceholderText("VD: Ôn tập chương 3 – Tích phân bất định")
        self._topic_edit.setMinimumHeight(38)
        self._topic_edit.setStyleSheet(_FIELD)
        form.addRow(lbl("Chủ đề / Mục tiêu *"), self._topic_edit)

        self._target_spin = QSpinBox()
        self._target_spin.setRange(10, 100)
        self._target_spin.setValue(100)
        self._target_spin.setSuffix("%")
        self._target_spin.setSingleStep(10)
        self._target_spin.setMinimumHeight(38)
        self._target_spin.setStyleSheet(_FIELD)
        form.addRow(lbl("Mục tiêu đạt"), self._target_spin)

        self._deadline_edit = QDateEdit(QDate.currentDate().addDays(30))
        self._deadline_edit.setCalendarPopup(True)
        self._deadline_edit.setMinimumDate(QDate.currentDate())
        self._deadline_edit.setMinimumHeight(38)
        self._deadline_edit.setStyleSheet(_FIELD)
        form.addRow(lbl("Deadline *"), self._deadline_edit)

        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("Ghi chú thêm (tuỳ chọn)...")
        self._notes_edit.setFixedHeight(64)
        self._notes_edit.setStyleSheet(_FIELD)
        form.addRow(lbl("Ghi chú"), self._notes_edit)

        main.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:white;border:none;"
            "border-radius:8px;padding:9px 22px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
        )
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        main.addWidget(btns)

    def _on_save(self):
        from PyQt6.QtWidgets import QMessageBox

        topic = self._topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập chủ đề / mục tiêu!")
            return

        qd = self._deadline_edit.date()
        deadline = date(qd.year(), qd.month(), qd.day())
        subject = strip_icon(self._subj_combo.currentText())

        self._result = {
            "subject": subject,
            "topic": topic,
            "target_pct": self._target_spin.value(),
            "deadline": deadline,
            "notes": self._notes_edit.toPlainText().strip(),
        }
        self.accept()

    def get_goal(self) -> Optional[dict]:
        return self._result


# ---------------------------------------------------------------------------
# RoadmapView (ĐÃ SỬA: tham số topics trong generate_learning_roadmap)
# ---------------------------------------------------------------------------

class RoadmapView(BaseController):
    UI_FILE = "roadmap_page.ui"

    goal_added = pyqtSignal(str)
    roadmap_updated = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None):
        self._settings = settings
        self._main_window = None
        super().__init__(parent)

    # ── Setup ─────────────────────────────────────────────────────────

    def setup_ui(self):
        self._state = AppState.instance()
        self._filter = "Tất cả môn học"
        self._populate_filters()
        self._build_goal_cards()
        self._build_cards()
        self._update_overall()
        self._sync_progress_from_db()

    def connect_signals(self):
        try:
            self.roadmapSubjectFilter.currentTextChanged.connect(self._on_filter)
        except AttributeError:
            pass
        try:
            self.btnAddGoal.clicked.connect(self._add_goal_dialog)
        except AttributeError:
            pass
        try:
            self.btnSaveGoal.clicked.connect(self._save_inline_goal)
        except AttributeError:
            pass

    def refresh(self):
        self._sync_progress_from_db()
        self._populate_filters()
        self._update_overall()
        self._rebuild_cards()
        self._build_goal_cards()

    def set_main_window(self, mw):
        self._main_window = mw

    # ── DB sync ───────────────────────────────────────────────────────

    def _sync_progress_from_db(self):
        if not _DB_AVAILABLE:
            return
        try:
            db = DBManager.instance()
            progress = db.get_subject_progress()
            for rm in self._state.roadmap:
                pct = progress.get(rm.name)
                if pct is not None and pct > rm.progress:
                    done_count = round(len(rm.topics) * pct / 100)
                    for i, topic in enumerate(rm.topics):
                        if i < done_count:
                            topic.status = TopicStatus.DONE
                        elif i == done_count:
                            topic.status = TopicStatus.IN_PROGRESS
                        else:
                            topic.status = TopicStatus.LOCKED
        except Exception as e:
            print(f"[Roadmap] _sync_progress_from_db lỗi: {e}")

    # ── Goal cards ────────────────────────────────────────────────────

    def _build_goal_cards(self):
        try:
            frame = self.goalsFrame
        except AttributeError:
            return

        lay = frame.layout()
        if lay is None:
            lay = QVBoxLayout(frame)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(8)
        else:
            while lay.count():
                item = lay.takeAt(0)
                if item and item.widget():
                    item.widget().setParent(None)

        if not _DB_AVAILABLE:
            return

        try:
            goals = DBManager.instance().get_goals_with_progress()
            if not goals:
                no_goal = QLabel("Chưa có mục tiêu nào. Bấm '+ Thêm Mục Tiêu' để bắt đầu.")
                no_goal.setStyleSheet(
                    "color:#718096;font-size:12px;padding:8px;"
                    "background:transparent;border:none;"
                )
                no_goal.setWordWrap(True)
                lay.addWidget(no_goal)
                return

            for g in goals[:5]:
                card = GoalCard(g)
                lay.addWidget(card)
        except Exception as e:
            print(f"[Roadmap] _build_goal_cards lỗi: {e}")

    # ── Filter ────────────────────────────────────────────────────────

    def _populate_filters(self):
        try:
            self.roadmapSubjectFilter.blockSignals(True)
            self.roadmapSubjectFilter.clear()
            subjects = ["Tất cả môn học"] + [r.name for r in self._state.roadmap]
            self.roadmapSubjectFilter.addItems(subjects)
            self.roadmapSubjectFilter.blockSignals(False)
        except AttributeError:
            pass

        try:
            self.goalSubjectCombo.clear()
            self.goalSubjectCombo.addItems([r.name for r in self._state.roadmap])
        except AttributeError:
            pass

    def _on_filter(self, text: str):
        self._filter = text
        self._build_cards()

    # ── Subject cards ─────────────────────────────────────────────────

    def _build_cards(self):
        try:
            layout = self.roadmapItemsLayout
        except AttributeError:
            return

        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for rm in self._state.roadmap:
            if self._filter != "Tất cả môn học" and self._filter != rm.name:
                continue
            card = SubjectCard(rm, self._show_topic, self)
            layout.addWidget(card)

        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

    def _rebuild_cards(self):
        self._build_cards()

    # ── Overall progress ──────────────────────────────────────────────

    def _update_overall(self):
        try:
            pct = self._state.overall_progress
            self.overallProgress.setValue(pct)

            total = sum(len(r.topics) for r in self._state.roadmap)
            done = sum(
                sum(1 for t in r.topics if t.status == TopicStatus.DONE)
                for r in self._state.roadmap
            )
            remaining = total - done

            for lbl in self.findChildren(QLabel):
                txt = lbl.text()
                if "hoàn thành" in txt and "chủ đề" in txt:
                    lbl.setText(f"{pct}% hoàn thành  ·  {remaining} chủ đề còn lại")
                    break
        except AttributeError:
            pass

    # ── Topic handlers ────────────────────────────────────────────────

    def _show_topic(self, topic: Topic, subject_name: str):
        dlg = TopicDialog(topic, subject_name, self)
        dlg.topic_completed.connect(self._on_topic_completed)
        dlg.topic_study.connect(self._on_topic_study)
        dlg.exec()

    def _on_topic_completed(self, topic: Topic):
        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_study_session(
                    subject=topic.name,
                    topic=topic.name,
                    duration_min=int(topic.estimated_h * 60),
                    progress_pct=100,
                    note="Hoàn thành qua Roadmap",
                )
            except Exception as e:
                print(f"[Roadmap] save_study_session lỗi: {e}")

        for rm in self._state.roadmap:
            if any(t.id == topic.id for t in rm.topics):
                rm.unlock_next()
                break

        self._update_overall()
        self._rebuild_cards()
        self.roadmap_updated.emit()

    def _on_topic_study(self, subject_name: str, topic_name: str):
        from src.views.components.study_dialog import StudySessionDialog
        dlg = StudySessionDialog(subject_name, topic_name, self)
        dlg.session_completed.connect(self._on_study_completed)
        dlg.exec()

    def _on_study_completed(self, subject: str, topic: str, elapsed_min: int):
        for rm in self._state.roadmap:
            if rm.name == subject:
                for t in rm.topics:
                    if t.name == topic:
                        t.mark_done()
                        self._update_overall()
                        self._rebuild_cards()
                        if _DB_AVAILABLE:
                            try:
                                DBManager.instance().save_study_session(
                                    subject=subject,
                                    topic=topic,
                                    duration_min=elapsed_min,
                                    progress_pct=100,
                                    note="Hoàn thành qua StudySessionDialog"
                                )
                            except Exception:
                                pass
                        break
                break

    # ── Goal ─────────────────────────────────────────────────────────

    def _add_goal_dialog(self):
        dlg = AddGoalDialog(parent=self)
        if dlg.exec() == AddGoalDialog.DialogCode.Accepted:
            goal = dlg.get_goal()
            if not goal:
                return

            if _DB_AVAILABLE:
                try:
                    DBManager.instance().save_goal(
                        subject=goal["subject"],
                        topic=goal["topic"],
                        target_pct=goal["target_pct"],
                        deadline=goal["deadline"],
                    )
                except Exception as e:
                    print(f"[Roadmap] save_goal lỗi: {e}")

            self.goal_added.emit(goal["subject"])
            self._build_goal_cards()
            self.show_info(
                self, "Thành công",
                f"✅ Đã thêm mục tiêu:\n«{goal['topic']}»\n"
                f"Môn: {goal['subject']} – Deadline: {goal['deadline'].strftime('%d/%m/%Y')}"
            )

    def _save_inline_goal(self):
        try:
            title = self.goalTitleInput.text().strip()
        except AttributeError:
            return

        if not title:
            self.show_warning(self, "Thiếu thông tin", "Vui lòng nhập tiêu đề mục tiêu!")
            return

        try:
            sd = self.goalStartDate.date()
            ed = self.goalEndDate.date()
            if ed < sd:
                self.show_warning(self, "Ngày không hợp lệ",
                                  "Ngày kết thúc phải sau ngày bắt đầu!")
                return
            subject = strip_icon(self.goalSubjectCombo.currentText())
            ed_py = date(ed.year(), ed.month(), ed.day())
        except AttributeError:
            subject = ""
            ed_py = date.today()

        if _DB_AVAILABLE and subject:
            try:
                DBManager.instance().save_goal(
                    subject=subject,
                    topic=title,
                    target_pct=100,
                    deadline=ed_py,
                )
            except Exception as e:
                print(f"[Roadmap] save_inline_goal lỗi: {e}")

        self.goal_added.emit(subject)
        self._build_goal_cards()

        try:
            self.goalTitleInput.clear()
            self.goalDescInput.clear()
        except AttributeError:
            pass

        self.show_info(self, "Thành công", f"✅ Đã thêm mục tiêu:\n«{title}»")

    # ── AI Tool (ĐÃ SỬA: nhận topics từ AI) ─────────────────────────────

    def generate_learning_roadmap(
        self,
        subject: str,
        level: str = "beginner",
        topics: List[str] = None,          # <-- Tham số mới: danh sách topics từ AI
        current_pct: int = 0,
        target_pct: int = 100,
        weeks_remaining: int = 4,
    ) -> dict:
        """
        Tạo lộ trình học tập cho một môn học.
        Nếu có topics từ AI thì dùng, nếu không thì fallback về _generate_topics.
        """
        # Nếu AI cung cấp danh sách topics, dùng nó
        if topics and isinstance(topics, list) and len(topics) > 0:
            topics_data = []
            for i, topic_name in enumerate(topics):
                # Cắt ngắn nếu quá dài
                if len(topic_name) > 60:
                    topic_name = topic_name[:57] + "..."
                topics_data.append(Topic(
                    name=topic_name,
                    status=TopicStatus.IN_PROGRESS if i == 0 else TopicStatus.LOCKED,
                    detail=f"Nội dung: {topic_name} – {subject} (trình độ {level})",
                    estimated_h=round((weeks_remaining * 5) / len(topics), 1)
                ))
        else:
            # Fallback: dùng template cũ (hoặc generic)
            pct_needed = target_pct - current_pct
            topics_data = self._generate_topics(subject, pct_needed, weeks_remaining)

        existing = self._state.get_roadmap_by_subject(subject)
        if existing:
            # Nếu roadmap đã tồn tại, cập nhật status dựa trên current_pct
            self._update_existing_roadmap(existing, current_pct)
            rm = existing
        else:
            from src.utils.study_subjects import get_subject_icon, get_subject_color
            rm = SubjectRoadmap(
                name=subject,
                icon=get_subject_icon(subject),
                color=get_subject_color(subject),
                topics=topics_data,
            )
            self._state.roadmap.append(rm)

        # Tự động tạo goal trong DB
        if _DB_AVAILABLE:
            try:
                from datetime import timedelta
                DBManager.instance().save_goal(
                    subject=subject,
                    topic=f"Đạt {target_pct}% môn {subject}",
                    target_pct=target_pct,
                    deadline=date.today() + timedelta(weeks=weeks_remaining),
                )
            except Exception:
                pass

        self._populate_filters()
        self._rebuild_cards()
        self._update_overall()
        self._build_goal_cards()

        return {
            "subject": subject,
            "level": level,
            "current_pct": current_pct,
            "target_pct": target_pct,
            "weeks_remaining": weeks_remaining,
            "topics_count": len(rm.topics),
            "done_topics": rm.done_topics,
            "remaining_topics": rm.total_topics - rm.done_topics,
            "estimated_hours": rm.estimated_remaining_hours,
            "hours_per_week": round(rm.estimated_remaining_hours / max(1, weeks_remaining), 1),
        }

    def _generate_topics(self, subject: str, pct_needed: int, weeks_remaining: int) -> list[Topic]:
        """Fallback: sinh topics dùng template hoặc generic (giữ nguyên code cũ)."""
        n_topics = max(3, min(12, pct_needed // 10))
        topic_templates = {
            "Toán học": ["Lý thuyết cơ bản", "Công thức trọng tâm", "Bài tập mức 1",
                         "Bài tập mức 2", "Bài tập nâng cao", "Ôn tập tổng hợp"],
            "Vật lý": ["Khái niệm & Định luật", "Công thức cần nhớ", "Bài tập cơ bản",
                       "Bài tập vận dụng", "Bài tập nâng cao", "Ôn tập tổng hợp"],
            "Hóa học": ["Lý thuyết phản ứng", "Cân bằng phương trình", "Bài tập cơ bản",
                        "Bài tập vận dụng", "Bài tập nâng cao", "Ôn tập"],
            "Tiếng Anh": ["Từ vựng trọng tâm", "Ngữ pháp cần ôn", "Đọc hiểu",
                          "Viết luận", "Luyện đề", "Ôn tập tổng hợp"],
        }
        templates = topic_templates.get(subject, [f"Chủ đề {i+1}" for i in range(n_topics)])
        topics = []
        for i in range(n_topics):
            topics.append(Topic(
                name=templates[i % len(templates)],
                status=TopicStatus.IN_PROGRESS if i == 0 else TopicStatus.LOCKED,
                detail=f"Nội dung ôn tập: {templates[i % len(templates)]} môn {subject}",
                estimated_h=round((weeks_remaining * 5) / n_topics, 1),
            ))
        return topics

    def _update_existing_roadmap(self, rm: SubjectRoadmap, current_pct: int):
        if not rm.topics:
            return
        done_count = round(len(rm.topics) * current_pct / 100)
        for i, topic in enumerate(rm.topics):
            if i < done_count:
                topic.status = TopicStatus.DONE
            elif i == done_count:
                topic.status = TopicStatus.IN_PROGRESS
            else:
                topic.status = TopicStatus.LOCKED