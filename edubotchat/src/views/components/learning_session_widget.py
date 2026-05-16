"""
learning_session_widget.py - Form học trực tiếp trên app.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSlider, QPlainTextEdit, QSpinBox
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

from src.database.db_manager import DBManager
from src.utils.study_subjects import subject_combo_items


class LearningSessionWidget(QFrame):
    """
    Người dùng:
    1. Chọn môn + chủ đề
    2. Bấm Bắt đầu → timer chạy
    3. Bấm Kết thúc → kéo slider đánh giá % → lưu DB
    """

    session_saved = pyqtSignal(str, int, int)  # subject, duration_min, progress_pct

    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed_sec = 0
        self._running     = False
        self._timer       = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._build()

    def _build(self):
        self.setStyleSheet(
            "QFrame{background:#1a1f2e;border-radius:16px;}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        # Title
        title = QLabel("📖 Buổi Học Mới")
        title.setStyleSheet(
            "color:#fff;font-size:15px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        lay.addWidget(title)

        # Subject + topic
        self._subj_combo = QComboBox()
        self._subj_combo.addItems(subject_combo_items())
        self._subj_combo.setStyleSheet(
            "QComboBox{background:#2d3748;color:#e2e8f0;"
            "border:none;border-radius:8px;padding:6px 12px;"
            "font-size:13px;}"
        )
        lay.addWidget(self._subj_combo)

        self._topic_input = QPlainTextEdit()
        self._topic_input.setPlaceholderText("Chủ đề hôm nay (VD: Đạo hàm – quy tắc dây chuyền)...")
        self._topic_input.setFixedHeight(56)
        self._topic_input.setStyleSheet(
            "QPlainTextEdit{background:#2d3748;color:#e2e8f0;"
            "border:none;border-radius:8px;padding:8px;font-size:13px;}"
        )
        lay.addWidget(self._topic_input)

        # Timer display
        self._timer_lbl = QLabel("00:00:00")
        self._timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._timer_lbl.setStyleSheet(
            "color:#ffffff;font-size:36px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        lay.addWidget(self._timer_lbl)

        # Start / Stop buttons
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶ Bắt đầu học")
        self._start_btn.setMinimumHeight(40)
        self._start_btn.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:#fff;border:none;"
            "border-radius:10px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
        )
        self._start_btn.clicked.connect(self._toggle)
        btn_row.addWidget(self._start_btn)

        self._end_btn = QPushButton("⏹ Kết thúc & Lưu")
        self._end_btn.setMinimumHeight(40)
        self._end_btn.setEnabled(False)
        self._end_btn.setStyleSheet(
            "QPushButton{background:#38a169;color:#fff;border:none;"
            "border-radius:10px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#2f855a;}"
            "QPushButton:disabled{background:#2d3748;color:#4a5568;}"
        )
        self._end_btn.clicked.connect(self._finish)
        btn_row.addWidget(self._end_btn)
        lay.addLayout(btn_row)

        # Progress slider (ẩn, chỉ hiện khi kết thúc)
        self._eval_frame = QFrame()
        self._eval_frame.setStyleSheet("background:transparent;")
        eval_lay = QVBoxLayout(self._eval_frame)
        eval_lay.setSpacing(6)

        eval_lbl = QLabel("Bạn hiểu được bao nhiêu % chủ đề này?")
        eval_lbl.setStyleSheet(
            "color:#a0aec0;font-size:12px;background:transparent;border:none;"
        )
        eval_lay.addWidget(eval_lbl)

        slider_row = QHBoxLayout()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setValue(70)
        self._slider.setStyleSheet(
            "QSlider::groove:horizontal{height:6px;background:#4a5568;"
            "border-radius:3px;}"
            "QSlider::handle:horizontal{width:18px;height:18px;"
            "background:#4a6cf7;border-radius:9px;margin:-6px 0;}"
            "QSlider::sub-page:horizontal{background:#4a6cf7;border-radius:3px;}"
        )
        self._pct_lbl = QLabel("70%")
        self._pct_lbl.setFixedWidth(36)
        self._pct_lbl.setStyleSheet(
            "color:#4a6cf7;font-size:13px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        self._slider.valueChanged.connect(
            lambda v: self._pct_lbl.setText(f"{v}%")
        )
        slider_row.addWidget(self._slider)
        slider_row.addWidget(self._pct_lbl)
        eval_lay.addLayout(slider_row)

        self._note_input = QPlainTextEdit()
        self._note_input.setPlaceholderText("Ghi chú nhanh (khó chỗ nào, cần ôn lại gì)...")
        self._note_input.setFixedHeight(52)
        self._note_input.setStyleSheet(
            "QPlainTextEdit{background:#2d3748;color:#e2e8f0;"
            "border:none;border-radius:8px;padding:8px;font-size:12px;}"
        )
        eval_lay.addWidget(self._note_input)

        self._save_btn = QPushButton("💾 Lưu buổi học")
        self._save_btn.setMinimumHeight(38)
        self._save_btn.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:#fff;border:none;"
            "border-radius:10px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
        )
        self._save_btn.clicked.connect(self._save)
        eval_lay.addWidget(self._save_btn)

        self._eval_frame.setVisible(False)
        lay.addWidget(self._eval_frame)

    # ── Logic ────────────────────────────────────────────────────────

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
        from src.utils.study_subjects import strip_icon
        subject      = strip_icon(self._subj_combo.currentText())
        topic        = self._topic_input.toPlainText().strip() or "Chưa ghi chủ đề"
        duration_min = self._elapsed_sec // 60
        progress_pct = self._slider.value()
        note         = self._note_input.toPlainText().strip()

        db = DBManager.instance()
        db.save_study_session(subject, topic, duration_min, progress_pct, note)

        self.session_saved.emit(subject, duration_min, progress_pct)

        # Reset
        self._elapsed_sec = 0
        self._timer_lbl.setText("00:00:00")
        self._topic_input.clear()
        self._note_input.clear()
        self._slider.setValue(70)
        self._eval_frame.setVisible(False)
        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶ Bắt đầu học")