"""
src/utils/study_subjects.py
-----------------------------
Danh sách môn học, icon, màu sắc và các hàm tiện ích liên quan.

Hàm chính:
  subject_combo_items()  → list[str] dùng cho QComboBox (có icon)
  strip_icon(text)       → tên môn thuần (bỏ icon phía trước)
  get_subject_icon(name) → emoji icon
  get_subject_color(name)→ hex color
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Dữ liệu môn học
# ---------------------------------------------------------------------------

# Thứ tự hiển thị trong combo box
SUBJECTS: list[str] = [
    "Toán học",
    "Vật lý",
    "Hóa học",
    "Sinh học",
    "Ngữ văn",
    "Tiếng Anh",
    "Lịch sử",
    "Địa lý",
    "Giáo dục công dân",
    "Tin học",
    "Công nghệ",
    "Thể dục",
    "Âm nhạc",
    "Mỹ thuật",
]

# Icon emoji cho từng môn
SUBJECT_ICONS: dict[str, str] = {
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

# Màu accent đại diện cho từng môn (hex)
SUBJECT_COLORS: dict[str, str] = {
    "Toán học":            "#e53e3e",
    "Vật lý":              "#dd6b20",
    "Hóa học":             "#38a169",
    "Sinh học":            "#319795",
    "Ngữ văn":             "#805ad5",
    "Tiếng Anh":           "#3182ce",
    "Lịch sử":             "#d69e2e",
    "Địa lý":              "#2b6cb0",
    "Giáo dục công dân":   "#718096",
    "Tin học":             "#e53e3e",
    "Công nghệ":           "#d69e2e",
    "Thể dục":             "#38a169",
    "Âm nhạc":             "#805ad5",
    "Mỹ thuật":            "#dd6b20",
}

# Màu gradient cho mỗi môn (dùng trong StatCard / SubjectCard)
SUBJECT_GRADIENTS: dict[str, str] = {
    "Toán học":   "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fc5c7d,stop:1 #6a3093)",
    "Vật lý":     "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f7971e,stop:1 #ffd200)",
    "Hóa học":    "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #43e97b,stop:1 #38f9d7)",
    "Sinh học":   "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0fd850,stop:1 #f9f047)",
    "Ngữ văn":    "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #a18cd1,stop:1 #fbc2eb)",
    "Tiếng Anh":  "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4facfe,stop:1 #00f2fe)",
    "Lịch sử":    "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f093fb,stop:1 #f5576c)",
    "Địa lý":     "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4481eb,stop:1 #04befe)",
    "Tin học":    "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #667eea,stop:1 #764ba2)",
}


# ---------------------------------------------------------------------------
# Hàm tiện ích
# ---------------------------------------------------------------------------

def get_subject_icon(subject: str) -> str:
    """Trả về emoji icon cho môn học. Mặc định 📌 nếu không tìm thấy."""
    return SUBJECT_ICONS.get(subject, "📌")


def get_subject_color(subject: str) -> str:
    """Trả về màu hex accent cho môn học. Mặc định #a0aec0."""
    return SUBJECT_COLORS.get(subject, "#a0aec0")


def get_subject_gradient(subject: str) -> str:
    """Trả về CSS gradient string cho môn học."""
    return SUBJECT_GRADIENTS.get(
        subject,
        "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #4a6cf7,stop:1 #7f9cf5)"
    )


def subject_combo_items(include_all: bool = True) -> list[str]:
    """
    Trả về danh sách chuỗi dùng cho QComboBox, có kèm icon.

    Args:
        include_all: Thêm lựa chọn "Tất cả môn học" ở đầu (mặc định True)

    Returns:
        VD: ["📚 Tất cả môn học", "📐 Toán học", "⚛️ Vật lý", ...]
    """
    items = []
    if include_all:
        items.append("📚 Tất cả môn học")
    for subj in SUBJECTS:
        icon = SUBJECT_ICONS.get(subj, "📌")
        items.append(f"{icon} {subj}")
    return items


def strip_icon(text: str) -> str:
    """
    Bỏ icon emoji ở đầu chuỗi combo box, trả về tên môn thuần.

    VD:
        "📐 Toán học"          → "Toán học"
        "📚 Tất cả môn học"   → "Tất cả môn học"
        "Toán học"             → "Toán học"   (không có icon → giữ nguyên)
    """
    text = text.strip()
    if not text:
        return text

    # Duyệt các icon đã biết
    for icon in SUBJECT_ICONS.values():
        if text.startswith(icon):
            return text[len(icon):].strip()

    # Icon "Tất cả môn học"
    if text.startswith("📚"):
        return text[1:].strip()

    # Fallback: bỏ ký tự đầu nếu nó là emoji (code point > 127)
    first_char = text[0]
    if ord(first_char) > 127:
        return text[1:].strip()

    return text


def find_subject(raw: str) -> str:
    """
    Tìm tên môn học chuẩn từ chuỗi bất kỳ (có thể có icon, viết tắt...).

    VD:
        "📐 Toán học" → "Toán học"
        "toan"        → "Toán học"   (fuzzy, lowercase không dấu)
        "Hóa"         → "Hóa học"
    """
    # Thử strip icon trước
    stripped = strip_icon(raw)
    if stripped in SUBJECTS:
        return stripped

    # Fuzzy match không dấu, không hoa
    raw_lower = _no_accent(stripped.lower())
    for subj in SUBJECTS:
        if raw_lower in _no_accent(subj.lower()):
            return subj

    return stripped   # không tìm thấy → trả nguyên


def _no_accent(text: str) -> str:
    """Bỏ dấu tiếng Việt để so sánh fuzzy."""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def format_subject_with_icon(subject: str) -> str:
    """Trả về chuỗi có icon: '📐 Toán học'."""
    icon = get_subject_icon(subject)
    return f"{icon} {subject}"