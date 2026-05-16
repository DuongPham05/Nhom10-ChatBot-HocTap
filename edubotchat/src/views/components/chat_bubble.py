"""
src/views/components/chat_bubble.py
-------------------------------------
Widget bong bóng tin nhắn cho giao diện Chat.
"""
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout,
                              QLabel, QSizePolicy)
from PyQt6.QtCore    import Qt

from src.models.message import Message, MessageRole


class ChatBubble(QFrame):
    """
    Một hàng hiển thị 1 tin nhắn.

    User  → bong bóng xanh, bên phải
    Bot   → bong bóng trắng, bên trái
    """

    _USER_BUBBLE = (
        "QFrame{background:#4a6cf7;"
        "border-radius:14px 0px 14px 14px;}"
    )
    _BOT_BUBBLE = (
        "QFrame{background:#ffffff;"
        "border-radius:0px 14px 14px 14px;"
        "border:1px solid #e2e8f0;}"
    )
    _USER_TEXT = "color:#fff;font-size:14px;background:transparent;border:none;"
    _BOT_TEXT  = "color:#2d3748;font-size:14px;line-height:1.6;background:transparent;border:none;"

    def __init__(self, message: Message, parent=None):
        super().__init__(parent)
        is_user = (message.role == MessageRole.USER)
        self._build(message.content, is_user, message.display_time())

    def _build(self, text: str, is_user: bool, time_str: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(8)

        avatar = QLabel("👤" if is_user else "🤖")
        avatar.setStyleSheet("font-size:20px;")
        avatar.setAlignment(Qt.AlignmentFlag.AlignTop)
        avatar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bubble = QFrame()
        b_lay  = QVBoxLayout(bubble)
        b_lay.setContentsMargins(14, 10, 14, 10)
        b_lay.setSpacing(4)

        content_lbl = QLabel(text)
        content_lbl.setWordWrap(True)
        content_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        content_lbl.setStyleSheet(
            self._USER_TEXT if is_user else self._BOT_TEXT
        )
        b_lay.addWidget(content_lbl)

        # Timestamp
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.6);font-size:10px;"
            "background:transparent;border:none;"
            if is_user else
            "color:#a0aec0;font-size:10px;"
            "background:transparent;border:none;"
        )
        time_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft
        )
        b_lay.addWidget(time_lbl)

        bubble.setStyleSheet(self._USER_BUBBLE if is_user else self._BOT_BUBBLE)
        bubble.setMaximumWidth(600)

        spacer = QLabel()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if is_user:
            outer.addWidget(spacer)
            outer.addWidget(bubble)
            outer.addWidget(avatar)
        else:
            outer.addWidget(avatar)
            outer.addWidget(bubble)
            outer.addWidget(spacer)


class TypingIndicator(QFrame):
    """Bubble 'đang gõ...' hiển thị khi chờ bot."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)

        avatar = QLabel("🤖")
        avatar.setStyleSheet("font-size:20px;")
        avatar.setAlignment(Qt.AlignmentFlag.AlignTop)
        avatar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        bubble = QFrame()
        bubble.setStyleSheet(
            "QFrame{background:#ffffff;border-radius:0px 14px 14px 14px;"
            "border:1px solid #e2e8f0;}"
        )
        b_lay = QHBoxLayout(bubble)
        b_lay.setContentsMargins(14, 12, 14, 12)

        dots = QLabel("● ● ●")
        dots.setStyleSheet(
            "color:#a0aec0;font-size:16px;letter-spacing:4px;"
            "background:transparent;border:none;"
        )
        b_lay.addWidget(dots)

        spacer = QLabel()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay.addWidget(avatar)
        lay.addWidget(bubble)
        lay.addWidget(spacer)