"""
src/models/roadmap_node.py
---------------------------
Data models cho trang Lộ Trình Học (Roadmap).

Classes:
  TopicStatus    : enum LOCKED | IN_PROGRESS | DONE
  Topic          : một chủ đề nhỏ trong môn học
  SubjectRoadmap : toàn bộ lộ trình của một môn học
  RoadmapNode    : node cây đệ quy (dùng cho parse_roadmap.py)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum        import Enum
from typing      import List, Optional


# ---------------------------------------------------------------------------
# TopicStatus
# ---------------------------------------------------------------------------

class TopicStatus(str, Enum):
    """
    Trạng thái học của một chủ đề.
    Kế thừa str để so sánh và serialize dễ dàng.
    """
    LOCKED      = "locked"       # Chưa mở khóa
    IN_PROGRESS = "in_progress"  # Đang học
    DONE        = "done"         # Đã hoàn thành

    @property
    def label_vi(self) -> str:
        return {
            "locked":      "🔒 Chưa mở",
            "in_progress": "⏳ Đang học",
            "done":        "✅ Hoàn thành",
        }[self.value]

    @property
    def colors(self) -> tuple[str, str, str]:
        """Trả về (background, border/text, hover_bg)."""
        return {
            TopicStatus.DONE: (
                "#f0fff4", "#276749", "#c6f6d5"
            ),
            TopicStatus.IN_PROGRESS: (
                "#fffbeb", "#744210", "#fefcbf"
            ),
            TopicStatus.LOCKED: (
                "#f7f8fc", "#a0aec0", None
            ),
        }[self]

    @property
    def bg(self) -> str:
        return self.colors[0]

    @property
    def fg(self) -> str:
        return self.colors[1]

    @property
    def hover_bg(self) -> Optional[str]:
        return self.colors[2]


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------

@dataclass
class Topic:
    """
    Một chủ đề nhỏ trong lộ trình của một môn học.

    Attributes:
        name         : Tên chủ đề (VD: "Đạo hàm cơ bản")
        status       : TopicStatus
        detail       : Mô tả chi tiết (hiển thị trong TopicDialog)
        estimated_h  : Số giờ dự kiến
        resource_urls: Danh sách link tài liệu
        id           : UUID tự sinh
    """
    name:          str
    status:        TopicStatus        = TopicStatus.LOCKED
    detail:        str                = ""
    estimated_h:   float              = 1.0
    resource_urls: List[str]          = field(default_factory=list)
    id:            str                = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = TopicStatus(self.status)

    @property
    def display_name(self) -> str:
        """Tên rút gọn dùng trong button (tối đa 28 ký tự)."""
        if len(self.name) > 28:
            return self.name[:26] + "…"
        return self.name

    @property
    def is_done(self) -> bool:
        return self.status == TopicStatus.DONE

    @property
    def is_available(self) -> bool:
        return self.status != TopicStatus.LOCKED

    def mark_done(self):
        self.status = TopicStatus.DONE

    def mark_in_progress(self):
        self.status = TopicStatus.IN_PROGRESS

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "name":         self.name,
            "status":       self.status.value,
            "detail":       self.detail,
            "estimated_h":  self.estimated_h,
            "resource_urls": self.resource_urls,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Topic:
        return cls(
            id            = data.get("id", str(uuid.uuid4())),
            name          = data["name"],
            status        = TopicStatus(data.get("status", "locked")),
            detail        = data.get("detail", ""),
            estimated_h   = data.get("estimated_h", 1.0),
            resource_urls = data.get("resource_urls", []),
        )

    def __repr__(self) -> str:
        return f"<Topic '{self.name}' [{self.status.value}]>"


# ---------------------------------------------------------------------------
# SubjectRoadmap
# ---------------------------------------------------------------------------

@dataclass
class SubjectRoadmap:
    """
    Lộ trình học tập của một môn học.

    Attributes:
        name     : Tên môn học (phải khớp với SUBJECTS trong study_subjects.py)
        icon     : Emoji icon
        color    : Hex màu accent
        topics   : Danh sách chủ đề
        expanded : Trạng thái expand/collapse trong UI
    """
    name:     str
    icon:     str                = "📚"
    color:    str                = "#4a6cf7"
    topics:   List[Topic]        = field(default_factory=list)
    expanded: bool               = False

    # ── Thống kê ─────────────────────────────────────────────────────

    @property
    def total_topics(self) -> int:
        return len(self.topics)

    @property
    def done_topics(self) -> int:
        return sum(1 for t in self.topics if t.is_done)

    @property
    def in_progress_topics(self) -> int:
        return sum(1 for t in self.topics if t.status == TopicStatus.IN_PROGRESS)

    @property
    def progress(self) -> int:
        """% hoàn thành (0–100), tính theo số topic DONE."""
        if not self.topics:
            return 0
        return round(self.done_topics / self.total_topics * 100)

    @property
    def estimated_total_hours(self) -> float:
        return sum(t.estimated_h for t in self.topics)

    @property
    def estimated_remaining_hours(self) -> float:
        return sum(t.estimated_h for t in self.topics if not t.is_done)

    # ── Thao tác topic ────────────────────────────────────────────────

    def add_topic(self, topic: Topic):
        self.topics.append(topic)

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        return next((t for t in self.topics if t.id == topic_id), None)

    def unlock_next(self):
        """Mở khóa topic LOCKED đầu tiên sau topic DONE cuối cùng."""
        for topic in self.topics:
            if topic.status == TopicStatus.LOCKED:
                topic.status = TopicStatus.IN_PROGRESS
                break

    def summary(self) -> str:
        """Chuỗi tóm tắt ngắn dùng cho AI context."""
        return (
            f"{self.name}: {self.progress}% hoàn thành "
            f"({self.done_topics}/{self.total_topics} chủ đề), "
            f"còn khoảng {self.estimated_remaining_hours:.1f} giờ"
        )

    # ── Serialize ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name":     self.name,
            "icon":     self.icon,
            "color":    self.color,
            "topics":   [t.to_dict() for t in self.topics],
            "expanded": self.expanded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SubjectRoadmap:
        return cls(
            name     = data["name"],
            icon     = data.get("icon", "📚"),
            color    = data.get("color", "#4a6cf7"),
            topics   = [Topic.from_dict(t) for t in data.get("topics", [])],
            expanded = data.get("expanded", False),
        )

    def __repr__(self) -> str:
        return (
            f"<SubjectRoadmap '{self.name}' "
            f"{self.progress}% "
            f"({self.done_topics}/{self.total_topics} topics)>"
        )


# ---------------------------------------------------------------------------
# RoadmapNode  (cây đệ quy – dùng bởi parse_roadmap.py)
# ---------------------------------------------------------------------------

@dataclass
class RoadmapNode:
    """
    Node trong cây roadmap đệ quy.
    Dùng để parse văn bản AI trả về thành cấu trúc cây.
    Khác với SubjectRoadmap (là flat list topics cho UI).
    """
    title:           str
    description:     str               = ""
    children:        List[RoadmapNode] = field(default_factory=list)
    completed:       bool              = False
    estimated_hours: float             = 0.0
    resource_links:  List[str]         = field(default_factory=list)

    def add_child(self, child: RoadmapNode):
        self.children.append(child)

    def progress_percent(self) -> float:
        """% hoàn thành đệ quy qua các con."""
        if not self.children:
            return 100.0 if self.completed else 0.0
        return sum(c.progress_percent() for c in self.children) / len(self.children)

    def to_subject_roadmap(self, icon: str = "📚", color: str = "#4a6cf7") -> SubjectRoadmap:
        """
        Chuyển cây RoadmapNode sang SubjectRoadmap (flat list topics)
        để hiển thị trên UI RoadmapView.
        """
        topics = []
        for child in self.children:
            status = (TopicStatus.DONE if child.completed
                      else TopicStatus.IN_PROGRESS if topics
                      else TopicStatus.IN_PROGRESS)
            topics.append(Topic(
                name        = child.title,
                status      = status,
                detail      = child.description,
                estimated_h = child.estimated_hours or 1.0,
            ))
        return SubjectRoadmap(
            name   = self.title,
            icon   = icon,
            color  = color,
            topics = topics,
        )

    def to_dict(self) -> dict:
        return {
            "title":           self.title,
            "description":     self.description,
            "children":        [c.to_dict() for c in self.children],
            "completed":       self.completed,
            "estimated_hours": self.estimated_hours,
            "resource_links":  self.resource_links,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RoadmapNode:
        node = cls(
            title           = data["title"],
            description     = data.get("description", ""),
            completed       = data.get("completed", False),
            estimated_hours = data.get("estimated_hours", 0.0),
            resource_links  = data.get("resource_links", []),
        )
        for child_data in data.get("children", []):
            node.add_child(cls.from_dict(child_data))
        return node

    def __repr__(self) -> str:
        pct = self.progress_percent()
        return f"<RoadmapNode '{self.title}' {pct:.0f}% ({len(self.children)} children)>"


# ---------------------------------------------------------------------------
# Factory – tạo dữ liệu mẫu khi chưa có DB
# ---------------------------------------------------------------------------

def default_roadmap() -> List[SubjectRoadmap]:
    """
    Trả về danh sách SubjectRoadmap mẫu cho 4 môn chính.
    Dùng khi chưa có dữ liệu từ DB hoặc AI.
    """
    from src.utils.study_subjects import get_subject_icon, get_subject_color

    data = {
        "Toán học": [
            ("Giới hạn và liên tục",    TopicStatus.DONE),
            ("Đạo hàm cơ bản",          TopicStatus.DONE),
            ("Đạo hàm hàm hợp",         TopicStatus.IN_PROGRESS),
            ("Tích phân bất định",       TopicStatus.LOCKED),
            ("Tích phân xác định",       TopicStatus.LOCKED),
            ("Ứng dụng tích phân",       TopicStatus.LOCKED),
        ],
        "Vật lý": [
            ("Động học chất điểm",       TopicStatus.DONE),
            ("Động lực học Newton",      TopicStatus.DONE),
            ("Năng lượng và công",       TopicStatus.IN_PROGRESS),
            ("Động lượng",               TopicStatus.LOCKED),
            ("Dao động cơ",              TopicStatus.LOCKED),
            ("Sóng cơ học",              TopicStatus.LOCKED),
        ],
        "Hóa học": [
            ("Nguyên tử và bảng tuần hoàn", TopicStatus.DONE),
            ("Liên kết hóa học",         TopicStatus.DONE),
            ("Phản ứng oxi hóa khử",     TopicStatus.DONE),
            ("Điện phân",                TopicStatus.IN_PROGRESS),
            ("Hóa hữu cơ cơ bản",        TopicStatus.LOCKED),
            ("Polymer và ứng dụng",      TopicStatus.LOCKED),
        ],
        "Tiếng Anh": [
            ("Ngữ pháp thì cơ bản",      TopicStatus.DONE),
            ("Thì hoàn thành",           TopicStatus.DONE),
            ("Câu điều kiện",            TopicStatus.IN_PROGRESS),
            ("Từ vựng B1 – chủ đề 1",   TopicStatus.IN_PROGRESS),
            ("Viết luận cơ bản",         TopicStatus.LOCKED),
            ("Kỹ năng đọc hiểu",         TopicStatus.LOCKED),
        ],
    }

    result = []
    for subject, topics_data in data.items():
        rm = SubjectRoadmap(
            name   = subject,
            icon   = get_subject_icon(subject),
            color  = get_subject_color(subject),
            topics = [
                Topic(name=name, status=status, estimated_h=1.5)
                for name, status in topics_data
            ],
        )
        result.append(rm)
    return result