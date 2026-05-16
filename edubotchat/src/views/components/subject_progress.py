"""src/views/components/subject_progress.py – Thanh tiến độ môn học."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore    import Qt


class SubjectProgressBar(QWidget):
    """Row: 'Toán học  ────────── 78%'"""

    def __init__(self, subject: str, value: int, color: str = "#4a6cf7", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        # Header
        hdr = QHBoxLayout()
        name = QLabel(subject)
        name.setStyleSheet("color:#4a5568;font-size:13px;background:transparent;border:none;")
        pct  = QLabel(f"{value}%")
        pct.setStyleSheet(f"color:{color};font-size:13px;font-weight:bold;background:transparent;border:none;")
        hdr.addWidget(name)
        hdr.addStretch()
        hdr.addWidget(pct)
        lay.addLayout(hdr)

        # Bar
        self._bar = QProgressBar()
        self._bar.setValue(value)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet(
            f"QProgressBar{{background:#e2e8f0;border-radius:4px;border:none;}}"
            f"QProgressBar::chunk{{background:{color};border-radius:4px;}}"
        )
        lay.addWidget(self._bar)

    def set_value(self, v: int):
        self._bar.setValue(v)