"""
src/utils/date_helpers.py
--------------------------
Các hàm tiện ích xử lý ngày tháng cho EduBot.

Hàm chính:
  week_start(d)          → date  : Thứ Hai của tuần chứa d
  week_end(d)            → date  : Chủ Nhật của tuần chứa d
  format_date_vi(d)      → str   : "Thứ 2, 14/05/2025"
  format_month_vi(d)     → str   : "Tháng 5, 2025"
  relative_time(d)       → str   : "Hôm nay" / "Hôm qua" / "3 ngày trước" / ...
  days_until(d)          → int   : số ngày còn lại đến deadline
  is_today / is_overdue  → bool
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing   import Optional, Union


# ---------------------------------------------------------------------------
# Hằng số tiếng Việt
# ---------------------------------------------------------------------------

_WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

_MONTHS = [
    "Tháng 1", "Tháng 2", "Tháng 3",  "Tháng 4",
    "Tháng 5", "Tháng 6", "Tháng 7",  "Tháng 8",
    "Tháng 9", "Tháng 10","Tháng 11", "Tháng 12",
]

_MONTHS_SHORT = [
    "T1", "T2", "T3",  "T4",
    "T5", "T6", "T7",  "T8",
    "T9", "T10","T11", "T12",
]


# ---------------------------------------------------------------------------
# Tuần
# ---------------------------------------------------------------------------

def week_start(d: Optional[date] = None) -> date:
    """
    Trả về ngày Thứ Hai của tuần chứa d.
    Mặc định dùng hôm nay nếu d=None.
    """
    if d is None:
        d = date.today()
    return d - timedelta(days=d.weekday())


def week_end(d: Optional[date] = None) -> date:
    """Trả về ngày Chủ Nhật của tuần chứa d."""
    return week_start(d) + timedelta(days=6)


def week_range(d: Optional[date] = None) -> tuple[date, date]:
    """Trả về (monday, sunday) của tuần chứa d."""
    start = week_start(d)
    return start, start + timedelta(days=6)


# ---------------------------------------------------------------------------
# Định dạng ngày tháng
# ---------------------------------------------------------------------------

def format_date_vi(d: date) -> str:
    """
    Định dạng ngày tháng đầy đủ tiếng Việt.

    VD: date(2025, 5, 14) → "Thứ 4, 14/05/2025"
    """
    weekday = _WEEKDAYS[d.weekday()]
    return f"{weekday}, {d.strftime('%d/%m/%Y')}"


def format_month_vi(d: date) -> str:
    """
    Định dạng tháng/năm tiếng Việt.

    VD: date(2025, 5, 14) → "Tháng 5, 2025"
    """
    return f"{_MONTHS[d.month - 1]}, {d.year}"


def format_month_short_vi(d: date) -> str:
    """
    Định dạng tháng ngắn gọn.

    VD: date(2025, 5, 14) → "T5/2025"
    """
    return f"{_MONTHS_SHORT[d.month - 1]}/{d.year}"


def format_week_range_vi(d: Optional[date] = None) -> str:
    """
    Định dạng khoảng tuần.

    VD: "12/05 – 18/05/2025"
    """
    start, end = week_range(d)
    if start.month == end.month:
        return f"{start.strftime('%d')} – {end.strftime('%d/%m/%Y')}"
    return f"{start.strftime('%d/%m')} – {end.strftime('%d/%m/%Y')}"


def format_time(h: int, m: int) -> str:
    """VD: (8, 5) → '08:05'"""
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------------------
# Thời gian tương đối
# ---------------------------------------------------------------------------

def relative_time(d: Union[date, datetime, None]) -> str:
    """
    Trả về chuỗi thời gian tương đối so với hôm nay.

    VD:
        hôm nay           → "Hôm nay"
        hôm qua           → "Hôm qua"
        3 ngày trước      → "3 ngày trước"
        2 tuần trước      → "2 tuần trước"
        1 tháng trước     → "1 tháng trước"
        ngày mai          → "Ngày mai"
        3 ngày nữa        → "3 ngày nữa"
    """
    if d is None:
        return "Chưa rõ"

    # Chuẩn hóa về date
    if isinstance(d, datetime):
        d = d.date()

    today = date.today()
    delta = (today - d).days   # dương = trong quá khứ

    if delta == 0:
        return "Hôm nay"
    if delta == 1:
        return "Hôm qua"
    if delta == 2:
        return "2 ngày trước"
    if delta < 7:
        return f"{delta} ngày trước"
    if delta < 14:
        return "1 tuần trước"
    if delta < 30:
        weeks = delta // 7
        return f"{weeks} tuần trước"
    if delta < 60:
        return "1 tháng trước"
    if delta < 365:
        months = delta // 30
        return f"{months} tháng trước"

    # Tương lai
    future = -delta
    if future == 1:
        return "Ngày mai"
    if future < 7:
        return f"{future} ngày nữa"
    if future < 30:
        weeks = future // 7
        return f"{weeks} tuần nữa"
    months = future // 30
    return f"{months} tháng nữa"


# ---------------------------------------------------------------------------
# Kiểm tra
# ---------------------------------------------------------------------------

def is_today(d: date) -> bool:
    return d == date.today()


def is_tomorrow(d: date) -> bool:
    return d == date.today() + timedelta(days=1)


def is_yesterday(d: date) -> bool:
    return d == date.today() - timedelta(days=1)


def is_overdue(d: date) -> bool:
    """Trả về True nếu ngày d đã qua (không tính hôm nay)."""
    return d < date.today()


def days_until(d: date) -> int:
    """
    Số ngày còn lại đến ngày d.
    Âm nếu đã qua deadline.
    """
    return (d - date.today()).days


def deadline_label(d: date) -> str:
    """
    Nhãn deadline thân thiện, có màu ẩn ý.

    VD:
        quá hạn      → "⚠️ Quá hạn 3 ngày"
        hôm nay      → "🔴 Hôm nay!"
        ngày mai     → "🟡 Còn 1 ngày"
        7 ngày nữa   → "🟢 Còn 7 ngày"
        xa hơn       → "📅 Còn 14 ngày"
    """
    delta = days_until(d)
    if delta < 0:
        return f"⚠️ Quá hạn {-delta} ngày"
    if delta == 0:
        return "🔴 Hôm nay!"
    if delta == 1:
        return "🟡 Còn 1 ngày"
    if delta <= 3:
        return f"🟡 Còn {delta} ngày"
    if delta <= 7:
        return f"🟢 Còn {delta} ngày"
    return f"📅 Còn {delta} ngày"


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------

def calc_streak(study_dates: list[date]) -> int:
    """
    Tính số ngày học liên tiếp tính đến hôm nay.

    Args:
        study_dates: danh sách date đã học (có thể trùng, không cần sort)

    Returns:
        Số ngày liên tiếp (0 nếu hôm nay chưa học)
    """
    if not study_dates:
        return 0

    unique_sorted = sorted(set(study_dates), reverse=True)
    streak = 0
    check  = date.today()

    for d in unique_sorted:
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        elif d < check:
            break

    return streak


# ---------------------------------------------------------------------------
# Tiện ích khác
# ---------------------------------------------------------------------------

def get_week_dates(week_start_date: date) -> list[date]:
    """Trả về list 7 ngày trong tuần bắt đầu từ week_start_date."""
    return [week_start_date + timedelta(days=i) for i in range(7)]


def dates_in_month(year: int, month: int) -> list[date]:
    """Trả về tất cả các ngày trong tháng."""
    import calendar
    _, days = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, days + 1)]