"""
src/database/__init__.py
-------------------------
Package quản lý kết nối và thao tác MySQL cho EduBot.

Export chính:
  DBManager        - singleton kết nối MySQL
  build_system_prompt - tạo system prompt cá nhân hóa từ dữ liệu DB
"""

from src.database.db_manager      import DBManager
from src.database.context_builder import build_system_prompt

__all__ = ["DBManager", "build_system_prompt"]