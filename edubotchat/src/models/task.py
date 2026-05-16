"""
src/models/task.py
-------------------
Data model cho một nhiệm vụ học tập (Task).

Priority : enum HIGH | MEDIUM | LOW
Task     : dataclass lưu một nhiệm vụ
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime    import date, time
from enum        import Enum
from typing      import Optional


# ---------------------------------------------------------------------------
# Priority enum
# ---------------------------------------------------------------------------

class Priority(str, Enum):
    """
    Kế thừa str để dễ compare và serialize.
      task.priority == "high"   → True
      task.priority.value       → "high"
    """
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

    # ── Helpers ──────────────────────────────────────────────────────

    @property
    def label_vi(self) -> str:
        """Nhãn tiếng Việt."""
        return {"high": "Cao", "medium": "Vừa", "low": "Thấp"}[self.value]

    @property
    def colors(self) -> tuple[str, str]:
        """Trả về (background_hex, accent_hex) cho UI."""
        return {
            Priority.HIGH:   ("#fff5f5", "#e53e3e"),
            Priority.MEDIUM: ("#fffbeb", "#d69e2e"),
            Priority.LOW:    ("#f0fff4", "#38a169"),
        }[self]

    @property
    def bg(self) -> str:
        return self.colors[0]

    @property
    def accent(self) -> str:
        return self.colors[1]


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

# ID counter đơn giản (dùng khi không có DB)
_next_id: int = 0

def _gen_id() -> int:
    global _next_id
    _next_id += 1
    return _next_id


@dataclass
class Task:
    """
    Một nhiệm vụ học tập trong Planner.

    Attributes:
        title      : Tên nhiệm vụ
        subject    : Môn học
        date       : Ngày thực hiện
        start      : Giờ bắt đầu (QTime hoặc datetime.time)
        duration   : Thời lượng (phút)
        priority   : Priority enum
        notes      : Ghi chú tuỳ chọn
        done       : Đã hoàn thành chưa
        id         : ID duy nhất (tự sinh nếu không truyền)
    """

    title:    str
    subject:  str
    date:     date
    start:    time                   = field(default_factory=lambda: time(8, 0))
    duration: int                    = 60
    priority: Priority               = Priority.MEDIUM
    notes:    str                    = ""
    done:     bool                   = False
    id:       int                    = field(default_factory=_gen_id)

    def __post_init__(self):
        # Chấp nhận string thô → tự convert sang enum
        if isinstance(self.priority, str):
            self.priority = Priority(self.priority)

    # ── Icon môn học ─────────────────────────────────────────────────

    SUBJECT_ICONS: dict[str, str] = field(default=None, init=False, repr=False)

    _ICONS = {
        "Toán học":            "📐",
        "Vật lý":              "⚛️",
        "Hóa học":             "🧪",
        "Sinh học":            "🧬",
        "Ngữ văn":             "📚",
        "Tiếng Anh":           "🇬🇧",
        "Lịch sử":             "🏛️",
        "Địa lý":              "🌍",
        "Giáo dục công dân":   "⚖️",
        "Tin học":             "💻",
        "Công nghệ":           "🔧",
        "Thể dục":             "⚽",
        "Âm nhạc":             "🎵",
        "Mỹ thuật":            "🎨",
    }

    @classmethod
    def get_icon(cls, subject: str) -> str:
        """Trả về emoji icon cho môn học."""
        return cls._ICONS.get(subject, "📌")

    # ── Helpers ──────────────────────────────────────────────────────

    def time_range_str(self) -> str:
        """VD: '08:00 – 09:30'"""
        from datetime import timedelta, datetime
        try:
            start_dt = datetime.combine(self.date, self.start)
            end_dt   = start_dt + timedelta(minutes=self.duration)
            return f"{start_dt.strftime('%H:%M')} – {end_dt.strftime('%H:%M')}"
        except Exception:
            return str(self.start)

    def duration_str(self) -> str:
        """VD: '1 giờ 30 phút' hoặc '45 phút'"""
        h, m = divmod(self.duration, 60)
        if h and m:
            return f"{h} giờ {m} phút"
        if h:
            return f"{h} giờ"
        return f"{m} phút"

    @property
    def icon(self) -> str:
        return self.get_icon(self.subject)

    @property
    def priority_label(self) -> str:
        return self.priority.label_vi

    @property
    def bg_color(self) -> str:
        return self.priority.bg

    @property
    def accent_color(self) -> str:
        return self.priority.accent

    # ── Serialize ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Chuyển sang dict để lưu JSON hoặc DB."""
        return {
            "id":       self.id,
            "title":    self.title,
            "subject":  self.subject,
            "date":     self.date.isoformat(),
            "start":    self.start.strftime("%H:%M")
                        if isinstance(self.start, time)
                        else str(self.start),
            "duration": self.duration,
            "priority": self.priority.value,
            "notes":    self.notes,
            "done":     self.done,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Tạo Task từ dict (đọc từ JSON hoặc DB)."""
        # Parse start time
        raw_start = data.get("start", data.get("start_time", "08:00"))
        if isinstance(raw_start, str):
            h, m   = map(int, raw_start.split(":")[:2])
            start  = time(h, m)
        else:
            start  = raw_start

        return cls(
            id       = data.get("id", _gen_id()),
            title    = data["title"],
            subject  = data["subject"],
            date     = date.fromisoformat(data["date"])
                       if isinstance(data["date"], str)
                       else data["date"],
            start    = start,
            duration = data.get("duration", 60),
            priority = Priority(data.get("priority", "medium")),
            notes    = data.get("notes", ""),
            done     = data.get("done", False),
        )

    def __repr__(self) -> str:
        status = "✅" if self.done else "⬜"
        return (
            f"<Task {status} [{self.priority.value}] "
            f"'{self.title}' {self.date} {self.time_range_str()}>"
        )