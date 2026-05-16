"""src/views/dialogs/task_dialog.py – Dialog thêm/sửa Task."""
from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QDialogButtonBox,
    QDateEdit, QTimeEdit, QSpinBox, QPlainTextEdit, QPushButton,
)
from PyQt6.QtCore import Qt, QDate, QTime

from src.models.task         import Task, Priority
from src.utils.study_subjects import subject_combo_items, strip_icon

_FIELD = (
    "QLineEdit,QComboBox,QDateEdit,QTimeEdit,QSpinBox,QPlainTextEdit{"
    "background:#f7f8fc;border:1px solid #e2e8f0;"
    "border-radius:8px;padding:6px 12px;font-size:13px;color:#2d3748;}"
    "QLineEdit:focus,QComboBox:focus,QDateEdit:focus,"
    "QTimeEdit:focus,QSpinBox:focus,QPlainTextEdit:focus{"
    "border-color:#4a6cf7;background:#fff;}"
)

def _lbl(t): 
    l = QLabel(t)
    l.setStyleSheet("color:#4a5568;font-size:12px;font-weight:600;")
    return l


class TaskDialog(QDialog):
    """
    Dùng cho cả thêm mới lẫn chỉnh sửa.
    Truyền `task` để chỉnh sửa, bỏ trống để thêm mới.
    """

    def __init__(self, task: Task | None = None, parent=None):
        super().__init__(parent)
        self._task   = task
        self._result: Task | None = None
        title = "✏️ Sửa Nhiệm Vụ" if task else "➕ Thêm Nhiệm Vụ"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setStyleSheet(
            "QDialog{background:#fff;font-family:'Segoe UI',Arial,sans-serif;}"
        )
        self._build()

    def _build(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(14)

        title_lbl = QLabel(
            f"{'✏️ Sửa' if self._task else '➕ Thêm'} Nhiệm Vụ Học Tập"
        )
        title_lbl.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#1a1f2e;"
        )
        main.addWidget(title_lbl)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Title
        self._title_edit = QLineEdit(self._task.title if self._task else "")
        self._title_edit.setPlaceholderText("VD: Ôn tập Toán chương 3...")
        self._title_edit.setMinimumHeight(38)
        self._title_edit.setStyleSheet(_FIELD)
        form.addRow(_lbl("Tên nhiệm vụ *"), self._title_edit)

        # Subject
        self._subj_combo = QComboBox()
        self._subj_combo.addItems(subject_combo_items())
        self._subj_combo.setMinimumHeight(38)
        self._subj_combo.setStyleSheet(_FIELD)
        if self._task:
            for i in range(self._subj_combo.count()):
                if self._task.subject in self._subj_combo.itemText(i):
                    self._subj_combo.setCurrentIndex(i)
                    break
        form.addRow(_lbl("Môn học"), self._subj_combo)

        # Date + time row
        dt_row = QHBoxLayout()
        dt_row.setSpacing(10)

        self._date_edit = QDateEdit(
            QDate(self._task.date.year, self._task.date.month, self._task.date.day)
            if self._task else QDate.currentDate()
        )
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setMinimumHeight(38)
        self._date_edit.setStyleSheet(_FIELD)

        self._time_edit = QTimeEdit(
            self._task.start if self._task else QTime(8, 0)
        )
        self._time_edit.setMinimumHeight(38)
        self._time_edit.setStyleSheet(_FIELD)

        dt_row.addWidget(self._date_edit)
        dt_row.addWidget(self._time_edit)
        form.addRow(_lbl("Ngày / Giờ"), dt_row)

        # Duration
        self._dur_spin = QSpinBox()
        self._dur_spin.setRange(15, 480)
        self._dur_spin.setValue(self._task.duration if self._task else 60)
        self._dur_spin.setSingleStep(15)
        self._dur_spin.setSuffix(" phút")
        self._dur_spin.setMinimumHeight(38)
        self._dur_spin.setStyleSheet(_FIELD)
        form.addRow(_lbl("Thời lượng"), self._dur_spin)

        main.addLayout(form)

        # Priority
        main.addWidget(_lbl("Mức độ ưu tiên"))
        prio_row = QHBoxLayout()
        prio_row.setSpacing(8)
        self._prio_btns: dict[Priority, QPushButton] = {}
        prio_defs = [
            (Priority.HIGH,   "🔴 Cao",  "#fff5f5","#e53e3e","#fed7d7"),
            (Priority.MEDIUM, "🟡 Vừa",  "#fffbeb","#d69e2e","#fefcbf"),
            (Priority.LOW,    "🟢 Thấp", "#f0fff4","#38a169","#c6f6d5"),
        ]
        for prio, label, bg, fg, hov in prio_defs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setMinimumHeight(34)
            btn.setStyleSheet(
                f"QPushButton{{background:{bg};color:{fg};"
                f"border:1.5px solid {hov};border-radius:8px;"
                f"font-size:12px;padding:0 10px;}}"
                f"QPushButton:checked{{background:{hov};border-color:{fg};"
                f"font-weight:bold;}}"
            )
            btn.clicked.connect(lambda _, p=prio: self._select_prio(p))
            self._prio_btns[prio] = btn
            prio_row.addWidget(btn)
        self._select_prio(self._task.priority if self._task else Priority.MEDIUM)
        main.addLayout(prio_row)

        # Notes
        main.addWidget(_lbl("Ghi chú"))
        self._notes_edit = QPlainTextEdit(self._task.notes if self._task else "")
        self._notes_edit.setPlaceholderText("Ghi chú thêm (tuỳ chọn)...")
        self._notes_edit.setFixedHeight(70)
        self._notes_edit.setStyleSheet(_FIELD)
        main.addWidget(self._notes_edit)

        # Buttons
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

    def _select_prio(self, p: Priority):
        for prio, btn in self._prio_btns.items():
            btn.setChecked(prio == p)
        self._selected_prio = p

    def _on_save(self):
        from PyQt6.QtWidgets import QMessageBox
        title = self._title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng nhập tên nhiệm vụ!")
            return
        qd = self._date_edit.date()
        task_date = date(qd.year(), qd.month(), qd.day())
        subject   = strip_icon(self._subj_combo.currentText())
        prio      = getattr(self, "_selected_prio", Priority.MEDIUM)

        if self._task:
            self._task.title    = title
            self._task.subject  = subject
            self._task.date     = task_date
            self._task.start    = self._time_edit.time()
            self._task.duration = self._dur_spin.value()
            self._task.priority = prio
            self._task.notes    = self._notes_edit.toPlainText().strip()
            self._result = self._task
        else:
            self._result = Task(
                title=title, subject=subject, date=task_date,
                start=self._time_edit.time(),
                duration=self._dur_spin.value(),
                priority=prio,
                notes=self._notes_edit.toPlainText().strip(),
            )
        self.accept()

    def get_task(self) -> Task | None:
        return self._result