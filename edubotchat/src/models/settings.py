"""
src/models/settings.py
-----------------------
Model lưu trữ cài đặt người dùng của EduBot.

AppSettings : dataclass toàn bộ cài đặt
            - Tự load/lưu JSON qua sync() và load()
            - Tích hợp DBManager để lưu thông tin người dùng
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib     import Path
from typing      import Optional


# Đường dẫn file lưu settings
_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "settings.json"


# ---------------------------------------------------------------------------
# AppSettings
# ---------------------------------------------------------------------------

@dataclass
class AppSettings:
    """
    Toàn bộ cài đặt ứng dụng.

    Tự động load từ data/settings.json khi khởi tạo.
    Gọi settings.sync() để lưu lại.
    """

    # ── Hồ sơ người dùng ─────────────────────────────────────────────
    user_name:  str  = "Học Sinh"
    grade:      str  = "Lớp 12"

    # ── API ──────────────────────────────────────────────────────────
    api_key:    str  = ""
    api_model:  str  = "gemini-2.5-flash"
    max_tokens: int  = 1024
    temperature: float = 0.7

    # ── Giao diện ────────────────────────────────────────────────────
    theme:      str  = "dark_sidebar"   # "dark_sidebar" | "light"
    font_size:  int  = 10               # pt (phải > 0, không được để -1)
    language:   str  = "vi"

    # ── Học tập ──────────────────────────────────────────────────────
    default_subject:      str  = "Toán học"
    daily_goal_minutes:   int  = 120
    reminder_enabled:     bool = False
    reminder_time:        str  = "20:00"

    # ── DB connection ─────────────────────────────────────────────────
    db_host:     str  = "localhost"
    db_user:     str  = "root"
    db_password: str  = ""
    db_name:     str  = "edubot"
    db_port:     int  = 3306

    # ── Internal (không serialize ra JSON) ───────────────────────────
    _loaded: bool = field(default=False, init=False, repr=False, compare=False)

    def __post_init__(self):
        """Tự load từ file khi khởi tạo."""
        self.load()

    # ── Load / Save ───────────────────────────────────────────────────

    def load(self):
        """Đọc cài đặt từ data/settings.json nếu tồn tại."""
        if not _SETTINGS_PATH.exists():
            return
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply(data)
            self._loaded = True
        except Exception:
            pass   # File lỗi → dùng giá trị mặc định

    def sync(self):
        """Lưu cài đặt hiện tại vào data/settings.json."""
        try:
            _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Settings] Không thể lưu settings: {e}")

    def _apply(self, data: dict):
        """Áp dụng dict vào các field hiện tại (chỉ ghi đè field đã biết)."""
        known = {f for f in self.to_dict()}
        for key, val in data.items():
            if key in known and hasattr(self, key):
                setattr(self, key, val)

    # ── Serialize ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            # Hồ sơ
            "user_name":            self.user_name,
            "grade":                self.grade,
            # API
            "api_key":              self.api_key,
            "api_model":            self.api_model,
            "max_tokens":           self.max_tokens,
            "temperature":          self.temperature,
            # Giao diện
            "theme":                self.theme,
            "font_size":            self.font_size,
            "language":             self.language,
            # Học tập
            "default_subject":      self.default_subject,
            "daily_goal_minutes":   self.daily_goal_minutes,
            "reminder_enabled":     self.reminder_enabled,
            "reminder_time":        self.reminder_time,
            # DB
            "db_host":              self.db_host,
            "db_user":              self.db_user,
            "db_password":          self.db_password,
            "db_name":              self.db_name,
            "db_port":              self.db_port,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppSettings:
        """Tạo AppSettings từ dict (không trigger load từ file)."""
        obj = cls.__new__(cls)
        # Gán giá trị mặc định trước
        obj.__init__.__func__(obj) if False else None

        # Dùng dataclass defaults
        import dataclasses
        defaults = {f.name: f.default for f in dataclasses.fields(cls)
                    if f.default is not dataclasses.MISSING}
        defaults.update({f.name: f.default_factory()
                         for f in dataclasses.fields(cls)
                         if f.default_factory is not dataclasses.MISSING})  # type: ignore
        for k, v in defaults.items():
            setattr(obj, k, v)

        # Ghi đè bằng data truyền vào
        for k, v in data.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj

    # ── DB connection helper ──────────────────────────────────────────

    def get_db_config(self) -> dict:
        """Trả về dict cấu hình kết nối MySQL."""
        return {
            "host":     self.db_host,
            "user":     self.db_user,
            "password": self.db_password,
            "db":       self.db_name,
            "port":     self.db_port,
        }

    def has_api_key(self) -> bool:
        """Kiểm tra đã cấu hình API key chưa."""
        return bool(self.api_key and self.api_key.strip())

    def has_db_config(self) -> bool:
        """Kiểm tra đã cấu hình DB chưa (host và db name)."""
        return bool(self.db_host and self.db_name)

    def __repr__(self) -> str:
        key_preview = f"{self.api_key[:8]}..." if self.api_key else "(trống)"
        return (
            f"<AppSettings user='{self.user_name}' "
            f"grade='{self.grade}' "
            f"model='{self.api_model}' "
            f"api_key={key_preview}>"
        )