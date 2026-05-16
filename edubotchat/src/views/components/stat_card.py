"""
src/views/components/stat_card.py
----------------------------------
Widget thẻ thống kê tái sử dụng (dùng trên Dashboard).
Gradient background, icon emoji, số liệu lớn, sub-label.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore    import Qt


class StatCard(QFrame):
    """
    Thẻ thống kê gradient.

    Params:
        icon      : emoji string, vd "💬"
        label     : tiêu đề thẻ
        value     : giá trị chính (str)
        sublabel  : dòng phụ nhỏ
        gradient  : CSS gradient string
    """

    def __init__(self,
                 icon:     str,
                 label:    str,
                 value:    str,
                 sublabel: str = "",
                 gradient: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                                 "stop:0 #4facfe,stop:1 #00f2fe)",
                 parent=None):
        super().__init__(parent)
        self.setMinimumHeight(110)
        self.setStyleSheet(
            f"QFrame{{background:{gradient};border-radius:14px;}}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(4)

        # Label + icon
        hdr = QLabel(f"{icon}  {label}")
        hdr.setStyleSheet(
            "color:rgba(255,255,255,0.85);font-size:13px;"
            "background:transparent;border:none;"
        )
        lay.addWidget(hdr)

        # Main value
        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(
            "color:#ffffff;font-size:32px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        lay.addWidget(self._value_lbl)

        # Sub-label
        if sublabel:
            sub = QLabel(sublabel)
            sub.setStyleSheet(
                "color:rgba(255,255,255,0.75);font-size:11px;"
                "background:transparent;border:none;"
            )
            lay.addWidget(sub)

    def set_value(self, value: str):
        self._value_lbl.setText(value)