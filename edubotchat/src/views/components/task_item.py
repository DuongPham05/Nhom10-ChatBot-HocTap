"""
src/views/components/task_item.py
-----------------------------------
Widget hiển thị một nhiệm vụ trong danh sách hôm nay (Planner).
Có checkbox, tiêu đề, thời gian, nút xoá.
"""
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout,
                              QLabel, QCheckBox, QPushButton)
from PyQt6.QtCore    import pyqtSignal, Qt
from src.models.task import Task, Priority


_PRIORITY_CSS = {
    Priority.HIGH:   ("background:#fff5f5;border-left:4px solid #e53e3e;",  "#e53e3e"),
    Priority.MEDIUM: ("background:#fffbeb;border-left:4px solid #d69e2e;",  "#d69e2e"),
    Priority.LOW:    ("background:#f0fff4;border-left:4px solid #38a169;",  "#38a169"),
}

_SUBJECT_ICONS = {
    "Toán học":  "📐", "Vật lý": "⚛️", "Hóa học": "🧪",
    "Sinh học":  "🌿", "Ngữ văn": "📖","Tiếng Anh": "🇬🇧", "Lịch sử": "🌍",
}


class TaskItem(QFrame):
    """
    Signals:
        done_changed(task, bool)  – khi checkbox thay đổi
        delete_requested(task)    – khi bấm nút xoá
    """

    done_changed     = pyqtSignal(object, bool)
    delete_requested = pyqtSignal(object)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task
        self._build()

    def _build(self):
        bg_css, accent = _PRIORITY_CSS.get(
            self._task.priority,
            ("background:#f7f8fc;border-left:4px solid #e2e8f0;", "#718096")
        )
        self.setStyleSheet(
            f"QFrame{{border-radius:10px;{bg_css}}}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        # Left info
        info = QVBoxLayout()
        info.setSpacing(3)

        icon   = _SUBJECT_ICONS.get(self._task.subject, "📚")
        title  = QLabel(f"{icon} {self._task.title}")
        title.setStyleSheet(
            "color:#1a1f2e;font-size:13px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        if self._task.done:
            title.setStyleSheet(
                "color:#a0aec0;font-size:13px;font-weight:bold;"
                "text-decoration:line-through;background:transparent;border:none;"
            )
        info.addWidget(title)

        time_lbl = QLabel(
            f"{self._task.time_range_str()}  ·  {self._task.duration} phút"
        )
        time_lbl.setStyleSheet(
            f"color:{accent};font-size:12px;background:transparent;border:none;"
        )
        info.addWidget(time_lbl)

        row.addLayout(info)
        row.addStretch()

        # Checkbox
        cb = QCheckBox()
        cb.setChecked(self._task.done)
        cb.setStyleSheet(
            f"QCheckBox::indicator{{width:20px;height:20px;"
            f"border-radius:5px;border:2px solid {accent};}}"
            f"QCheckBox::indicator:checked{{background:{accent};}}"
        )
        cb.stateChanged.connect(
            lambda s: self.done_changed.emit(
                self._task, s == Qt.CheckState.Checked.value
            )
        )
        row.addWidget(cb)

        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;"
            "color:#a0aec0;font-size:14px;border-radius:4px;}"
            "QPushButton:hover{background:#fed7d7;color:#c53030;}"
        )
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._task))
        row.addWidget(del_btn)

    def mark_done(self, done: bool):
        self._task.done = done
        # Re-render
        for child in self.children():
            if isinstance(child, QHBoxLayout):
                break
        # Đơn giản: trigger rebuild
        self._build()