from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class ScheduleWidget(QFrame):
    def __init__(self, schedule_data: dict):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        title = QLabel(f"<h2>📅 {schedule_data['topic']}</h2>")
        layout.addWidget(title)
        info = QLabel(f"<b>Cấp độ:</b> {schedule_data['level']}<br>"
                     f"<b>Thời lượng:</b> {schedule_data['duration_weeks']} tuần<br>"
                     f"<b>Giờ mỗi tuần:</b> {schedule_data['hours_per_week']} giờ")
        layout.addWidget(info)
        for week in schedule_data['weeks']:
            week_frame = QFrame()
            week_layout = QVBoxLayout(week_frame)
            week_title = QLabel(f"<b>Tuần {week['week']}:</b> {week['focus']}")
            week_layout.addWidget(week_title)
            tasks = QLabel("• " + "<br>• ".join(week['tasks']))
            week_layout.addWidget(tasks)
            layout.addWidget(week_frame)