"""
context_builder.py - Xây dựng system prompt từ dữ liệu người dùng.
Cải tiến v2.1:
  ✅ Dùng get_study_stats() thay vì get_user_context() – ít query hơn
  ✅ Thêm thông tin quiz score trung bình
  ✅ Thêm thông tin goals còn lại và deadline
  ✅ Fallback rõ ràng khi DB chưa có dữ liệu
"""
from datetime import date
from .db_manager import DBManager


def build_system_prompt(subject: str = None) -> str:
    """
    Tạo system prompt đầy đủ context người dùng.
    AI sẽ đọc prompt này trước khi trả lời.

    Args:
        subject: Môn học đang chat (None = tất cả môn)

    Returns:
        System prompt dạng string
    """
    db  = DBManager.instance()

    # Thử dùng get_study_stats() trước (ít query hơn)
    try:
        stats = db.get_study_stats()
    except Exception:
        return _fallback_prompt(subject)

    ctx = db.get_user_context(subject)

    lines = [
        "Bạn là trợ lý học tập AI của EduBot – cá nhân hóa cho từng học sinh.",
        "Dưới đây là hồ sơ học tập thực tế của người dùng (đọc kỹ trước khi trả lời):",
        "",
    ]

    # ── Thống kê học tập ───────────────────────────────────────────
    streak    = stats.get("streak", 0)
    total_min = stats.get("total_min", 0)
    total_h   = total_min // 60
    avg_score = stats.get("avg_quiz_score", 0.0)

    if total_min > 0 or streak > 0:
        lines += [
            f"📊 THỐNG KÊ TỔNG QUAN:",
            f"   • Streak học liên tiếp: {streak} ngày",
            f"   • Tổng thời gian đã học: {total_h}h {total_min % 60}p",
        ]
        if avg_score > 0:
            lines.append(f"   • Điểm quiz trung bình: {avg_score}/10")
        lines.append("")

    # ── Mục tiêu đang theo dõi ───────────────────────────────────
    goals_with_progress = stats.get("goals", [])
    active_goals = [g for g in goals_with_progress if not _is_past(g.get("deadline"))]
    if active_goals:
        lines.append("🎯 MỤC TIÊU ĐANG THEO DÕI:")
        for g in active_goals[:3]:   # tối đa 3 mục tiêu
            days_left = (g['deadline'] - date.today()).days if g.get('deadline') else 0
            lines.append(
                f"   • {g['subject']}: {g['topic']} "
                f"(đạt {g.get('current_pct', 0)}% / mục tiêu {g['target_pct']}%, "
                f"còn {days_left} ngày)"
            )
        lines.append("")

    # ── Tiến độ môn học hiện tại ─────────────────────────────────
    subj_progress = stats.get("subject_progress", {})
    if subj_progress:
        lines.append("📈 TIẾN ĐỘ HIỆN TẠI:")
        for subj, pct in sorted(subj_progress.items(), key=lambda x: -x[1])[:5]:
            bar = _mini_bar(pct)
            lines.append(f"   • {subj}: {bar} {pct}%")
        lines.append("")

    # ── Buổi học gần đây (môn cụ thể nếu có) ─────────────────────
    if ctx.get("sessions"):
        recent = ctx["sessions"][-5:]
        lines.append(f"📅 BUỔI HỌC GẦN ĐÂY{f' ({subject})' if subject else ''}:")
        for s in recent:
            dt = s.get('studied_at')
            dt_str = dt.strftime('%d/%m') if hasattr(dt, 'strftime') else str(dt)
            lines.append(
                f"   • {dt_str}: {s.get('topic', '?')} – "
                f"{s.get('duration_min', 0)} phút – đạt {s.get('progress_pct', 0)}%"
            )
            if s.get('note'):
                lines.append(f"     Ghi chú: {s['note']}")
        lines.append("")

    # ── Điểm yếu từ quiz ─────────────────────────────────────────
    if ctx.get("top_weak_areas"):
        weak_str = ", ".join(f"{w[0]} ({w[1]} lần)" for w in ctx["top_weak_areas"][:3])
        lines += [
            f"⚠️  ĐIỂM YẾU CẦN CHÚ Ý: {weak_str}",
            "",
        ]

    # ── Kết quả quiz gần nhất ─────────────────────────────────────
    if ctx.get("quiz_results"):
        quizzes = ctx["quiz_results"][-3:]
        lines.append("📝 KẾT QUẢ QUIZ GẦN ĐÂY:")
        for q in quizzes:
            dt = q.get('taken_at')
            dt_str = dt.strftime('%d/%m') if hasattr(dt, 'strftime') else str(dt)
            lines.append(
                f"   • {dt_str} {q.get('subject','')}: "
                f"{q.get('score',0)}/10 "
                f"({q.get('correct_q',0)}/{q.get('total_q',0)} câu đúng)"
            )
        lines.append("")

    # ── Hướng dẫn cho AI ─────────────────────────────────────────
    lines += [
        "═══════════════════════════════════",
        "HƯỚNG DẪN TRẢ LỜI:",
        "1. Cá nhân hóa câu trả lời dựa trên dữ liệu trên",
        "2. Đề cập cụ thể đến điểm yếu nếu liên quan",
        "3. Đưa ra mốc thời gian thực tế dựa trên streak và goal deadline",
        "4. Nếu người dùng hỏi về môn đang học – ưu tiên topic họ đang"
           " IN_PROGRESS",
        "5. Tránh trả lời chung chung – dùng số liệu thực tế từ hồ sơ",
    ]

    return "\n".join(lines)


def _fallback_prompt(subject: str = None) -> str:
    """System prompt mặc định khi không có dữ liệu DB."""
    base = (
        "Bạn là EduBot – trợ lý học tập thông minh dành cho học sinh Việt Nam.\n"
        "Nhiệm vụ: giải đáp bài tập, giải thích khái niệm, hỗ trợ học tập hiệu quả.\n"
        "Luôn trả lời bằng tiếng Việt, thân thiện, rõ ràng và khuyến khích học sinh.\n"
        "Khi giải bài toán: trình bày từng bước cụ thể.\n"
        "Khi giải thích lý thuyết: dùng ví dụ thực tế dễ hiểu."
    )
    if subject and "Tất cả" not in subject:
        base += f"\n\nMôn học hiện tại: {subject}. Tập trung vào kiến thức môn này."
    return base


def _mini_bar(pct: int, width: int = 10) -> str:
    """Thanh tiến độ ASCII nhỏ: ████░░░░░░ 70%"""
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _is_past(d) -> bool:
    """Kiểm tra deadline đã qua chưa."""
    if d is None:
        return False
    if hasattr(d, 'date'):
        d = d.date()
    return d < date.today()