"""
src/models/message.py
----------------------
Data model cho một tin nhắn trong Chat.

MessageRole : enum USER | ASSISTANT
Message     : dataclass lưu một tin nhắn
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime    import datetime
from enum        import Enum
from typing      import Optional


# ---------------------------------------------------------------------------
# MessageRole
# ---------------------------------------------------------------------------

class MessageRole(str, Enum):
    """
    Kế thừa str để dễ serialize/compare với string.
      msg.role == "user"          → True
      msg.role.value              → "user"
      {"role": msg.role, ...}     → JSON-serializable
    """
    USER      = "user"
    ASSISTANT = "assistant"


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """
    Một tin nhắn trong hội thoại.

    Attributes:
        role       : USER hoặc ASSISTANT
        content    : Nội dung văn bản
        timestamp  : Thời điểm tạo (mặc định = now)
        session_id : ID session chat chứa tin nhắn này
        id         : UUID tự sinh nếu không truyền
    """

    role:       MessageRole
    content:    str
    timestamp:  datetime         = field(default_factory=datetime.now)
    session_id: str              = field(default="")
    id:         Optional[str]    = field(default=None)

    def __post_init__(self):
        # Tự sinh UUID nếu chưa có
        if self.id is None:
            self.id = str(uuid.uuid4())

        # Chấp nhận string thô ("user" / "assistant") → tự convert sang enum
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)

    # ── Helpers ──────────────────────────────────────────────────────

    def display_time(self) -> str:
        """Trả về giờ:phút để hiển thị trên bubble."""
        return self.timestamp.strftime("%H:%M")

    def display_datetime(self) -> str:
        """Trả về ngày giờ đầy đủ."""
        return self.timestamp.strftime("%d/%m/%Y %H:%M")

    @property
    def is_user(self) -> bool:
        return self.role == MessageRole.USER

    @property
    def is_assistant(self) -> bool:
        return self.role == MessageRole.ASSISTANT

    # ── Serialize ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Chuyển sang dict để lưu DB hoặc JSON."""
        return {
            "id":         self.id,
            "role":       self.role.value,
            "content":    self.content,
            "timestamp":  self.timestamp.isoformat(),
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        """Tạo Message từ dict (đọc từ DB hoặc JSON)."""
        return cls(
            id         = data.get("id"),
            role       = MessageRole(data["role"]),
            content    = data["content"],
            timestamp  = datetime.fromisoformat(data["timestamp"])
                         if isinstance(data.get("timestamp"), str)
                         else data.get("timestamp", datetime.now()),
            session_id = data.get("session_id", ""),
        )

    # ── Format cho API ───────────────────────────────────────────────

    def to_api_dict(self) -> dict:
        """
        Format để truyền vào Gemini/Claude API history.
        {"role": "user"|"model", "content": "..."}
        """
        # Gemini dùng "model" thay vì "assistant"
        api_role = "user" if self.is_user else "model"
        return {"role": api_role, "content": self.content}

    def __repr__(self) -> str:
        preview = self.content[:40].replace("\n", " ")
        return f"<Message {self.role.value} '{preview}...' @ {self.display_time()}>"