"""
src/views/components/pomodoro_timer.py
----------------------------------------
Widget Pomodoro Timer tích hợp – dùng trên PlannerPage.

Chế độ:
  🍅 Focus  : 25 phút học
  ☕ Break  : 5 phút nghỉ
  🌿 Long   : 15 phút nghỉ dài (sau 4 pomodoro)
"""
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton)
from PyQt6.QtCore    import QTimer, pyqtSignal, Qt


class PomodoroTimer(QFrame):
    """
    Signals:
        session_completed(mode: str)  – mỗi khi hết 1 chu kỳ
    """

    session_completed = pyqtSignal(str)

    MODES = {
        "focus": ("🍅 Focus",  25 * 60, "#4a6cf7"),
        "break": ("☕ Break",   5 * 60,  "#38a169"),
        "long":  ("🌿 Nghỉ dài",15 * 60, "#d69e2e"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode        = "focus"
        self._seconds     = self.MODES["focus"][1]
        self._running     = False
        self._pomodoros   = 0

        self.setStyleSheet(
            "QFrame{background:#1a1f2e;border-radius:16px;}"
        )

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._build()
        self._refresh_display()

    # ── Build UI ────────────────────────────────────────────────────────

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)

        # Mode label
        self._mode_lbl = QLabel()
        self._mode_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_lbl.setStyleSheet(
            "color:#a0aec0;font-size:13px;background:transparent;border:none;"
        )
        lay.addWidget(self._mode_lbl)

        # Time display
        self._time_lbl = QLabel()
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_lbl.setStyleSheet(
            "color:#ffffff;font-size:40px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        lay.addWidget(self._time_lbl)

        # Pomodoro count
        self._count_lbl = QLabel()
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet(
            "color:#718096;font-size:12px;background:transparent;border:none;"
        )
        lay.addWidget(self._count_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._start_btn = QPushButton("▶ Bắt đầu")
        self._start_btn.setMinimumHeight(36)
        self._start_btn.setStyleSheet(
            "QPushButton{background:#4a6cf7;color:#fff;border:none;"
            "border-radius:8px;font-size:13px;font-weight:600;}"
            "QPushButton:hover{background:#3b5bdb;}"
        )
        self._start_btn.clicked.connect(self._toggle)
        btn_row.addWidget(self._start_btn)

        reset_btn = QPushButton("↺")
        reset_btn.setFixedWidth(40)
        reset_btn.setMinimumHeight(36)
        reset_btn.setStyleSheet(
            "QPushButton{background:#2d3748;color:#a0aec0;border:none;"
            "border-radius:8px;font-size:16px;}"
            "QPushButton:hover{background:#4a5568;color:#fff;}"
        )
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)

        lay.addLayout(btn_row)

        # Mode switch row
        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        for key, (label, _, _c) in self.MODES.items():
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setStyleSheet(
                "QPushButton{background:#2d3748;color:#718096;border:none;"
                "border-radius:6px;font-size:11px;padding:0 8px;}"
                "QPushButton:hover{color:#fff;background:#4a5568;}"
            )
            btn.clicked.connect(lambda _, k=key: self._switch_mode(k))
            mode_row.addWidget(btn)
        lay.addLayout(mode_row)

    # ── Logic ────────────────────────────────────────────────────────────

    def _tick(self):
        if self._seconds > 0:
            self._seconds -= 1
            self._refresh_display()
        else:
            self._timer.stop()
            self._running = False
            self._on_complete()

    def _toggle(self):
        if self._running:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("▶ Tiếp tục")
        else:
            self._timer.start()
            self._running = True
            self._start_btn.setText("⏸ Tạm dừng")

    def _reset(self):
        self._timer.stop()
        self._running = False
        self._seconds = self.MODES[self._mode][1]
        self._start_btn.setText("▶ Bắt đầu")
        self._refresh_display()

    def _switch_mode(self, mode: str):
        self._timer.stop()
        self._running = False
        self._mode    = mode
        self._seconds = self.MODES[mode][1]
        self._start_btn.setText("▶ Bắt đầu")
        self._refresh_display()

    def _on_complete(self):
        mode = self._mode
        if mode == "focus":
            self._pomodoros += 1
            self.session_completed.emit("focus")
            # Auto-switch to break
            next_mode = "long" if self._pomodoros % 4 == 0 else "break"
            self._switch_mode(next_mode)
        else:
            self.session_completed.emit(mode)
            self._switch_mode("focus")
        self._start_btn.setText("▶ Bắt đầu")

    def _refresh_display(self):
        label, _, color = self.MODES[self._mode]
        m, s = divmod(self._seconds, 60)
        self._time_lbl.setText(f"{m:02d}:{s:02d}")
        self._mode_lbl.setText(label)
        self._count_lbl.setText(
            "🍅" * self._pomodoros + f"  ({self._pomodoros} pomodoro)"
            if self._pomodoros else "Chưa có pomodoro nào"
        )
        # Đổi màu accent theo mode
        self._start_btn.setStyleSheet(
            f"QPushButton{{background:{color};color:#fff;border:none;"
            f"border-radius:8px;font-size:13px;font-weight:600;}}"
            f"QPushButton:hover{{opacity:0.85;}}"
        )