"""
db_manager.py - Kết nối và thao tác MySQL qua pymysql.
Cải tiến v2.1:
  ✅ Thêm get_study_stats() – tổng hợp thống kê học tập
  ✅ Thêm get_goals_with_progress() – mục tiêu kèm tiến độ thực tế
  ✅ Thêm get_streak() – tính streak ngay trong DB
  ✅ Thêm update_progress() – cập nhật tiến độ môn học
  ✅ Thêm get_recent_sessions() – buổi học gần đây cho Dashboard
  ✅ Fix: get_recent_chat() trả về created_at để Dashboard sort đúng
"""
import pymysql
import json
from datetime import date, datetime, timedelta
from collections import Counter
from typing import Optional


class DBManager:
    _instance = None

    @classmethod
    def instance(cls) -> 'DBManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._conn = None
        self._user_id: Optional[int] = None

    # ── Kết nối ──────────────────────────────────────────────────────

    def connect(self, host="localhost", user="root",
                password="", db="edubot", port=3306):
        self._conn = pymysql.connect(
            host=host, user=user, password=password,
            database=db, port=port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def disconnect(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass

    def is_connected(self) -> bool:
        try:
            if self._conn:
                self._conn.ping(reconnect=True)
                return True
        except Exception:
            pass
        return False

    # ── User ─────────────────────────────────────────────────────────

    def get_or_create_user(self, name: str, grade: str = "") -> int:
        """Trả về user_id, tạo mới nếu chưa có."""
        with self._conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE name=%s", (name,))
            row = cur.fetchone()
            if row:
                self._user_id = row['id']
                return self._user_id
            cur.execute(
                "INSERT INTO users (name, grade) VALUES (%s, %s)",
                (name, grade)
            )
            self._user_id = self._conn.insert_id()
            return self._user_id

    def get_user_id(self) -> Optional[int]:
        return self._user_id

    # ── Goals ────────────────────────────────────────────────────────

    def save_goal(self, subject: str, topic: str,
                  target_pct: int, deadline: date) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO goals
                   (user_id, subject, topic, target_pct, deadline)
                   VALUES (%s,%s,%s,%s,%s)""",
                (self._user_id, subject, topic, target_pct, deadline)
            )
            return self._conn.insert_id()

    def get_goals(self) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM goals WHERE user_id=%s ORDER BY deadline",
                (self._user_id,)
            )
            return cur.fetchall()

    def get_goals_with_progress(self) -> list[dict]:
        """
        Trả về goals kèm tiến độ thực tế (progress_pct mới nhất của môn đó).
        """
        goals = self.get_goals()
        for g in goals:
            sessions = self.get_sessions_for_subject(g['subject'])
            if sessions:
                g['current_pct'] = sessions[-1].get('progress_pct', 0)
                g['total_hours'] = sum(s.get('duration_min', 0) for s in sessions) / 60
            else:
                g['current_pct'] = 0
                g['total_hours'] = 0.0
            # Tính % hoàn thành so với mục tiêu
            target = g.get('target_pct', 100)
            g['completion_ratio'] = min(100, round(
                g['current_pct'] / max(1, target) * 100
            ))
        return goals

    def update_goal_progress(self, goal_id: int, current_pct: int):
        """Cập nhật tiến độ thực tế vào bảng goals (nếu có cột current_pct)."""
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE goals SET current_pct=%s WHERE id=%s AND user_id=%s",
                    (current_pct, goal_id, self._user_id)
                )
        except Exception:
            pass   # Cột chưa tồn tại → bỏ qua

    # ── Study sessions ───────────────────────────────────────────────

    def save_study_session(self, subject: str, topic: str,
                           duration_min: int, progress_pct: int,
                           note: str = "", goal_id: int = None):
        with self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO study_sessions
                   (user_id, goal_id, subject, topic,
                    duration_min, progress_pct, note)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (self._user_id, goal_id, subject, topic,
                 duration_min, progress_pct, note)
            )

    def get_sessions_for_subject(self, subject: str) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM study_sessions
                   WHERE user_id=%s AND subject=%s
                   ORDER BY studied_at""",
                (self._user_id, subject)
            )
            return cur.fetchall()

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        """Lấy các buổi học gần đây nhất (tất cả môn)."""
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM study_sessions
                   WHERE user_id=%s
                   ORDER BY studied_at DESC LIMIT %s""",
                (self._user_id, limit)
            )
            return cur.fetchall()

    def get_total_study_time(self) -> int:
        """Tổng số phút đã học (tất cả môn)."""
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT COALESCE(SUM(duration_min), 0) as total
                   FROM study_sessions WHERE user_id=%s""",
                (self._user_id,)
            )
            row = cur.fetchone()
            return int(row['total']) if row else 0

    def get_subject_progress(self) -> dict[str, int]:
        """
        Trả về dict {subject: latest_progress_pct} cho tất cả môn.
        Lấy progress_pct của buổi học MỚI NHẤT mỗi môn.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT subject, progress_pct
                   FROM study_sessions
                   WHERE user_id=%s
                   ORDER BY studied_at DESC""",
                (self._user_id,)
            )
            rows = cur.fetchall()

        result: dict[str, int] = {}
        for r in rows:
            subj = r['subject']
            if subj not in result:   # chỉ lấy mới nhất mỗi môn
                result[subj] = r['progress_pct']
        return result

    # ── Streak ───────────────────────────────────────────────────────

    def get_streak(self) -> int:
        """
        Tính số ngày học liên tiếp tính đến hôm nay trực tiếp từ DB.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    """SELECT DATE(studied_at) as d
                       FROM study_sessions
                       WHERE user_id=%s
                       GROUP BY DATE(studied_at)
                       ORDER BY d DESC""",
                    (self._user_id,)
                )
                rows = cur.fetchall()
            if not rows:
                return 0

            streak = 0
            check  = date.today()
            for r in rows:
                d = r['d']
                if isinstance(d, str):
                    d = date.fromisoformat(d)
                if d == check:
                    streak += 1
                    check -= timedelta(days=1)
                elif d < check:
                    break
            return streak
        except Exception:
            return 0

    # ── Quiz results ─────────────────────────────────────────────────

    def save_quiz_result(self, subject: str, topic: str,
                         score: float, total_q: int,
                         correct_q: int, weak_areas: list[str]):
        with self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO quiz_results
                   (user_id, subject, topic, score,
                    total_q, correct_q, weak_areas)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (self._user_id, subject, topic, score,
                 total_q, correct_q,
                 json.dumps(weak_areas, ensure_ascii=False))
            )

    def get_quiz_results(self, subject: str = None) -> list[dict]:
        with self._conn.cursor() as cur:
            if subject:
                cur.execute(
                    """SELECT * FROM quiz_results
                       WHERE user_id=%s AND subject=%s
                       ORDER BY taken_at""",
                    (self._user_id, subject)
                )
            else:
                cur.execute(
                    "SELECT * FROM quiz_results WHERE user_id=%s ORDER BY taken_at",
                    (self._user_id,)
                )
            rows = cur.fetchall()
            for r in rows:
                if isinstance(r.get('weak_areas'), str):
                    try:
                        r['weak_areas'] = json.loads(r['weak_areas'])
                    except Exception:
                        r['weak_areas'] = []
            return rows

    def get_avg_quiz_score(self, subject: str = None) -> float:
        """Điểm trung bình quiz của môn (hoặc tất cả môn)."""
        results = self.get_quiz_results(subject)
        if not results:
            return 0.0
        scores = [r.get('score', 0) for r in results]
        return round(sum(scores) / len(scores), 1)

    # ── Chat history ─────────────────────────────────────────────────

    def save_chat_message(self, role: str, content: str,
                          session_name: str = ""):
        with self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_history
                   (user_id, session_name, role, content)
                   VALUES (%s,%s,%s,%s)""",
                (self._user_id, session_name, role, content)
            )

    def get_recent_chat(self, limit: int = 20) -> list[dict]:
        """Trả về tin nhắn gần đây kèm created_at để sort."""
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT role, content, session_name, created_at
                   FROM chat_history
                   WHERE user_id=%s
                   ORDER BY created_at DESC LIMIT %s""",
                (self._user_id, limit)
            )
            rows = cur.fetchall()
            return list(reversed(rows))   # chronological

    def get_chat_session_count(self) -> int:
        """Đếm số phiên chat duy nhất."""
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(DISTINCT session_name) as cnt
                   FROM chat_history WHERE user_id=%s""",
                (self._user_id,)
            )
            row = cur.fetchone()
            return int(row['cnt']) if row else 0

    def get_question_count(self) -> int:
        """Đếm số tin nhắn user đã gửi."""
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(*) as cnt FROM chat_history
                   WHERE user_id=%s AND role='user'""",
                (self._user_id,)
            )
            row = cur.fetchone()
            return int(row['cnt']) if row else 0

    # ── Context tổng hợp cho AI ──────────────────────────────────────

    def get_user_context(self, subject: str = None) -> dict:
        """
        Trả về dict tổng hợp toàn bộ dữ liệu người dùng
        để đưa vào system prompt của AI.
        """
        goals    = self.get_goals()
        sessions = (self.get_sessions_for_subject(subject)
                    if subject else self.get_recent_sessions(50))
        quizzes  = self.get_quiz_results(subject)

        total_min  = sum(s.get('duration_min', 0) for s in sessions)
        current_pct = sessions[-1].get('progress_pct', 0) if sessions else 0

        related_goal = next(
            (g for g in goals
             if subject and g['subject'] == subject), None
        )

        all_weak = []
        for q in quizzes:
            all_weak.extend(q.get('weak_areas') or [])
        weak_freq = Counter(all_weak).most_common(5)

        return {
            "goals":           goals,
            "sessions":        sessions,
            "quiz_results":    quizzes,
            "total_study_min": total_min,
            "current_pct":     current_pct,
            "related_goal":    related_goal,
            "top_weak_areas":  weak_freq,
        }

    # ── Study stats tổng hợp cho Dashboard ───────────────────────────

    def get_study_stats(self) -> dict:
        """
        Trả về dict thống kê học tập đầy đủ cho Dashboard.
        Gọi 1 lần thay vì nhiều query riêng lẻ.
        """
        try:
            return {
                "streak":           self.get_streak(),
                "total_min":        self.get_total_study_time(),
                "chat_sessions":    self.get_chat_session_count(),
                "question_count":   self.get_question_count(),
                "subject_progress": self.get_subject_progress(),
                "avg_quiz_score":   self.get_avg_quiz_score(),
                "goals":            self.get_goals_with_progress(),
            }
        except Exception as e:
            print(f"[DB] get_study_stats lỗi: {e}")
            return {
                "streak": 0, "total_min": 0,
                "chat_sessions": 0, "question_count": 0,
                "subject_progress": {}, "avg_quiz_score": 0.0,
                "goals": [],
            }