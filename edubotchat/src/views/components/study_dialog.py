"""
src/views/dialogs/study_session_dialog.py
------------------------------------------
Dialog học tập theo thiết kế draw.io:
  - Trái : Đồng hồ bấm giờ hình tròn (circular countdown / stopwatch)
  - Phải : Bảng ghi chú
  - Dưới : Chọn môn học | Bắt đầu học | Tạm dừng | Tiếp tục | Kết thúc | Hoàn thành môn

Mở từ RoadmapView khi bấm "Học ngay".
"""

from __future__ import annotations

import math
from datetime import datetime
from typing   import Optional

from PyQt6.QtCore    import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui     import (QPainter, QPen, QColor, QBrush,
                              QFont, QFontMetrics, QConicalGradient)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QPlainTextEdit,
    QFrame, QSizePolicy, QWidget, QMessageBox,
)

from src.utils.study_subjects import subject_combo_items, strip_icon


# ─────────────────────────────────────────────────────────────
#  CircularTimer  –  đồng hồ hình tròn vẽ bằng QPainter
# ─────────────────────────────────────────────────────────────

class CircularTimer(QWidget):
    """
    Widget đồng hồ hình tròn.
    Chạy như stopwatch (đếm lên từ 0).
    Vòng cung màu xanh quay theo thời gian (chu kỳ 60s).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed   = 0          # giây đã trôi qua
        self._running   = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # ── Public API ──────────────────────────────────────────

    def start(self):
        self._running = True
        self._timer.start()

    def pause(self):
        self._running = False
        self._timer.stop()
        self.update()

    def resume(self):
        self._running = True
        self._timer.start()

    def reset(self):
        self._running = False
        self._timer.stop()
        self._elapsed = 0
        self.update()

    @property
    def elapsed_seconds(self) -> int:
        return self._elapsed

    @property
    def elapsed_str(self) -> str:
        h, rem = divmod(self._elapsed, 3600)
        m, s   = divmod(rem, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    # ── Internal ────────────────────────────────────────────

    def _tick(self):
        self._elapsed += 1
        self.update()

    # ── Paint ───────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side   = min(self.width(), self.height())
        margin = 14
        rect   = QRectF(
            (self.width()  - side) / 2 + margin,
            (self.height() - side) / 2 + margin,
            side - 2 * margin,
            side - 2 * margin,
        )

        # ① Track (nền vòng tròn xám)
        track_pen = QPen(QColor("#e2e8f0"), 10)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawEllipse(rect)

        # ② Arc tiến độ (xanh, chu kỳ 60s)
        progress = (self._elapsed % 60) / 60.0
        span_deg = int(-progress * 360 * 16)   # Qt dùng 1/16 độ

        if self._running:
            arc_color = QColor("#4a6cf7")
        else:
            arc_color = QColor("#a0aec0")

        arc_pen = QPen(arc_color, 10)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(rect, 90 * 16, span_deg)

        # ③ Vòng tròn giữa (nền trắng)
        inner_margin = 18
        inner_rect = rect.adjusted(inner_margin, inner_margin, -inner_margin, -inner_margin)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(inner_rect)

        # ④ Thời gian (to, giữa)
        time_font = QFont("Segoe UI", int(side * 0.13), QFont.Weight.Bold)
        painter.setFont(time_font)
        painter.setPen(QColor("#1a1f2e"))
        painter.drawText(inner_rect, Qt.AlignmentFlag.AlignCenter, self.elapsed_str)

        # ⑤ Trạng thái nhỏ bên dưới số
        status_rect = QRectF(inner_rect.left(), inner_rect.center().y() + inner_rect.height() * 0.18,
                             inner_rect.width(), inner_rect.height() * 0.25)
        status_font = QFont("Segoe UI", int(side * 0.055))
        painter.setFont(status_font)
        painter.setPen(QColor("#718096"))
        status = "Đang học..." if self._running else ("Tạm dừng" if self._elapsed > 0 else "Sẵn sàng")
        painter.drawText(status_rect, Qt.AlignmentFlag.AlignCenter, status)

        painter.end()


# ─────────────────────────────────────────────────────────────
#  StudySessionDialog
# ─────────────────────────────────────────────────────────────

class StudySessionDialog(QDialog):
    """
    Dialog học tập mở khi bấm "Học ngay" từ Lộ Trình.

    Signals:
        session_completed(subject, topic, elapsed_min)
            – emit khi bấm "Hoàn thành môn" hoặc "Kết thúc học"
    """

    session_completed = pyqtSignal(str, str, int)   # subject, topic, minutes

    def __init__(
        self,
        subject_name: str = "",
        topic_name:   str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._subject_name = subject_name
        self._topic_name   = topic_name
        self._finished     = False

        self.setWindowTitle(f"📖 Học: {topic_name}" if topic_name else "📖 Buổi Học")
        self.setMinimumSize(860, 560)
        self.resize(960, 620)
        self.setModal(True)

        self._build_ui()
        self._apply_style()
        self._connect_signals()

        # Điền sẵn môn học từ roadmap
        if subject_name:
            self._pre_select_subject(subject_name)

    # ── Build UI ─────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ═══ Header ═══
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)

        title_lbl = QLabel("📖 Buổi Học Tập")
        title_lbl.setObjectName("headerTitle")

        topic_lbl = QLabel(self._topic_name)
        topic_lbl.setObjectName("headerTopic")

        h_lay.addWidget(title_lbl)
        h_lay.addStretch()
        h_lay.addWidget(topic_lbl)
        root.addWidget(header)

        # ═══ Body (timer + notes) ═══
        body = QFrame()
        body.setObjectName("body")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 20, 24, 16)
        body_lay.setSpacing(24)

        # ── Trái: Timer ──
        timer_frame = QFrame()
        timer_frame.setObjectName("timerFrame")
        timer_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        t_lay = QVBoxLayout(timer_frame)
        t_lay.setContentsMargins(16, 16, 16, 16)
        t_lay.setSpacing(8)

        timer_label = QLabel("⏱ Thời Gian Học")
        timer_label.setObjectName("sectionLabel")
        t_lay.addWidget(timer_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._clock = CircularTimer()
        t_lay.addWidget(self._clock)

        # Thống kê nhỏ bên dưới đồng hồ
        stats_row = QHBoxLayout()
        self._lbl_minutes = QLabel("0 phút")
        self._lbl_minutes.setObjectName("statChip")
        self._lbl_sessions = QLabel("Chủ đề: —")
        self._lbl_sessions.setObjectName("statChip")
        stats_row.addStretch()
        stats_row.addWidget(self._lbl_minutes)
        stats_row.addSpacing(12)
        stats_row.addWidget(self._lbl_sessions)
        stats_row.addStretch()
        t_lay.addLayout(stats_row)

        body_lay.addWidget(timer_frame, stretch=4)

        # ── Phải: Ghi chú ──
        notes_frame = QFrame()
        notes_frame.setObjectName("notesFrame")
        notes_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        n_lay = QVBoxLayout(notes_frame)
        n_lay.setContentsMargins(16, 16, 16, 16)
        n_lay.setSpacing(8)

        notes_label = QLabel("📝 Bảng Ghi Chú")
        notes_label.setObjectName("sectionLabel")
        n_lay.addWidget(notes_label)

        self._notes = QPlainTextEdit()
        self._notes.setPlaceholderText(
            f"Ghi chú khi học '{self._topic_name}'...\n\n"
            "• Điểm quan trọng cần nhớ\n"
            "• Câu hỏi cần hỏi thầy/cô\n"
            "• Công thức cần ôn lại"
        )
        self._notes.setObjectName("notesArea")
        n_lay.addWidget(self._notes)

        # Timestamp cuối
        self._notes_footer = QLabel("💡 Ghi chú sẽ được lưu khi kết thúc buổi học")
        self._notes_footer.setObjectName("notesFooter")
        n_lay.addWidget(self._notes_footer)

        body_lay.addWidget(notes_frame, stretch=5)
        root.addWidget(body, stretch=1)

        # ═══ Footer (controls) ═══
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(80)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(24, 0, 24, 0)
        f_lay.setSpacing(10)

        # Chọn môn học
        self._subject_combo = QComboBox()
        self._subject_combo.addItems(subject_combo_items(include_all=False))
        self._subject_combo.setObjectName("subjectCombo")
        self._subject_combo.setFixedWidth(160)

        # Buttons
        self._btn_start    = self._make_btn("▶  Bắt đầu học",   "btnStart")
        self._btn_pause    = self._make_btn("⏸  Tạm dừng",       "btnPause")
        self._btn_resume   = self._make_btn("▶  Tiếp tục",        "btnResume")
        self._btn_end      = self._make_btn("⏹  Kết thúc học",   "btnEnd")
        self._btn_complete = self._make_btn("🏆  Hoàn thành môn", "btnComplete")

        # Trạng thái ban đầu
        self._btn_pause.setEnabled(False)
        self._btn_resume.setEnabled(False)
        self._btn_end.setEnabled(False)

        f_lay.addWidget(self._subject_combo)
        f_lay.addStretch()
        f_lay.addWidget(self._btn_start)
        f_lay.addWidget(self._btn_pause)
        f_lay.addWidget(self._btn_resume)
        f_lay.addWidget(self._btn_end)
        f_lay.addStretch()
        f_lay.addWidget(self._btn_complete)

        root.addWidget(footer)

    def _make_btn(self, text: str, obj_name: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName(obj_name)
        btn.setMinimumHeight(40)
        btn.setMinimumWidth(130)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    # ── Style ─────────────────────────────────────────────────

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background: #f7f8fc;
            }

            /* Header */
            QFrame#header {
                background: #1a1f2e;
                border: none;
            }
            QLabel#headerTitle {
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
                background: transparent;
            }
            QLabel#headerTopic {
                color: #4a6cf7;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }

            /* Body */
            QFrame#body {
                background: #f7f8fc;
            }

            /* Timer frame */
            QFrame#timerFrame {
                background: #ffffff;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
            QLabel#sectionLabel {
                color: #4a5568;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }
            QLabel#statChip {
                color: #4a6cf7;
                font-size: 12px;
                font-weight: 600;
                background: #eef2ff;
                border-radius: 10px;
                padding: 3px 10px;
            }

            /* Notes frame */
            QFrame#notesFrame {
                background: #ffffff;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }
            QPlainTextEdit#notesArea {
                background: #f7f8fc;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
            }
            QPlainTextEdit#notesArea:focus {
                border-color: #4a6cf7;
                background: #ffffff;
            }
            QLabel#notesFooter {
                color: #a0aec0;
                font-size: 11px;
                background: transparent;
            }

            /* Footer */
            QFrame#footer {
                background: #ffffff;
                border-top: 1px solid #e2e8f0;
            }

            /* Subject combo */
            QComboBox#subjectCombo {
                background: #f7f8fc;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox#subjectCombo:hover {
                border-color: #4a6cf7;
            }

            /* Buttons */
            QPushButton#btnStart {
                background: #4a6cf7;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#btnStart:hover { background: #3b5bdb; }

            QPushButton#btnPause {
                background: #f6ad55;
                color: #744210;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#btnPause:hover   { background: #ed8936; color: white; }
            QPushButton#btnPause:disabled {
                background: #e2e8f0; color: #a0aec0;
            }

            QPushButton#btnResume {
                background: #68d391;
                color: #276749;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#btnResume:hover   { background: #38a169; color: white; }
            QPushButton#btnResume:disabled {
                background: #e2e8f0; color: #a0aec0;
            }

            QPushButton#btnEnd {
                background: #fc8181;
                color: #742a2a;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#btnEnd:hover   { background: #e53e3e; color: white; }
            QPushButton#btnEnd:disabled {
                background: #e2e8f0; color: #a0aec0;
            }

            QPushButton#btnComplete {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                min-width: 150px;
            }
            QPushButton#btnComplete:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #5a67d8, stop:1 #6b46c1);
            }
        """)

    # ── Signals ───────────────────────────────────────────────

    def _connect_signals(self):
        self._btn_start.clicked.connect(self._on_start)
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_resume.clicked.connect(self._on_resume)
        self._btn_end.clicked.connect(self._on_end)
        self._btn_complete.clicked.connect(self._on_complete)

        # Cập nhật stat chip mỗi giây
        self._stat_timer = QTimer(self)
        self._stat_timer.setInterval(1000)
        self._stat_timer.timeout.connect(self._update_stats)
        self._stat_timer.start()

    # ── Actions ───────────────────────────────────────────────

    def _on_start(self):
        self._clock.reset()
        self._clock.start()
        self._btn_start.setEnabled(False)
        self._btn_pause.setEnabled(True)
        self._btn_resume.setEnabled(False)
        self._btn_end.setEnabled(True)
        self._subject_combo.setEnabled(False)
        topic = self._topic_name or "Chủ đề"
        self._lbl_sessions.setText(f"Chủ đề: {topic[:20]}")

    def _on_pause(self):
        self._clock.pause()
        self._btn_pause.setEnabled(False)
        self._btn_resume.setEnabled(True)

    def _on_resume(self):
        self._clock.resume()
        self._btn_pause.setEnabled(True)
        self._btn_resume.setEnabled(False)

    def _on_end(self):
        self._clock.pause()
        minutes = self._clock.elapsed_seconds // 60
        self._save_and_close(complete=False, minutes=minutes)

    def _on_complete(self):
        self._clock.pause()
        minutes = self._clock.elapsed_seconds // 60
        # Xác nhận
        reply = QMessageBox.question(
            self,
            "Hoàn thành môn",
            f"🏆 Bạn đã hoàn thành chủ đề\n「{self._topic_name}」?\n\n"
            f"Thời gian học: {self._clock.elapsed_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._save_and_close(complete=True, minutes=minutes)

    def _save_and_close(self, complete: bool, minutes: int):
        subject = strip_icon(self._subject_combo.currentText())
        notes   = self._notes.toPlainText().strip()

        # Lưu DB nếu có
        try:
            from src.database.db_manager import DBManager
            DBManager.instance().save_study_session(
                subject      = subject,
                topic        = self._topic_name or "Tự học",
                duration_min = minutes,
                progress_pct = 100 if complete else 50,
                note         = notes,
            )
        except Exception:
            pass

        self.session_completed.emit(subject, self._topic_name, minutes)
        self._finished = True
        self.accept()

    def _update_stats(self):
        secs = self._clock.elapsed_seconds
        mins = secs // 60
        self._lbl_minutes.setText(f"{mins} phút")

    def _pre_select_subject(self, subject_name: str):
        """Chọn sẵn môn học trong combo từ tên truyền vào."""
        for i in range(self._subject_combo.count()):
            item = self._subject_combo.itemText(i)
            if subject_name in item:
                self._subject_combo.setCurrentIndex(i)
                break

    # ── Close guard ────────────────────────────────────────────

    def closeEvent(self, event):
        if not self._finished and self._clock.elapsed_seconds > 0:
            reply = QMessageBox.question(
                self, "Thoát buổi học",
                "Bạn đang có buổi học chưa kết thúc.\nBạn có chắc muốn thoát không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        self._clock.pause()
        event.accept()