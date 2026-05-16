"""
src/api/api_worker.py
----------------------
QThread worker gọi Gemini API trong thread riêng.
Tránh block UI khi chờ phản hồi AI.

Signals:
    response_ready(str)       – AI trả về text thường
    tool_call_request(str, dict) – AI yêu cầu gọi tool
    error_occurred(str)       – lỗi kết nối / API
    finished_work()           – luôn emit khi xong (dù thành công hay lỗi)
"""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from src.api.ai_service import AIService


class ApiWorker(QThread):
    """
    Worker chạy Gemini API trong QThread riêng.

    Dùng:
        worker = ApiWorker(
            user_text = "Giải phương trình ...",
            history   = [...],          # list[dict] {"role","content"}
            system    = "Bạn là ...",   # system prompt
            subject   = "Toán học",
            api_key   = "",             # bỏ trống → dùng GEMINI_API_KEY env
        )
        worker.response_ready.connect(my_slot)
        worker.error_occurred.connect(my_error_slot)
        worker.finished_work.connect(my_done_slot)
        worker.start()
    """

    response_ready    = pyqtSignal(str)          # text response từ AI
    tool_call_request = pyqtSignal(str, dict)    # (tool_name, arguments)
    error_occurred    = pyqtSignal(str)          # thông báo lỗi
    finished_work     = pyqtSignal()             # luôn emit khi thread kết thúc

    def __init__(
        self,
        user_text:  str,
        history:    List[dict]   = None,
        system:     str          = "",
        subject:    str          = "",
        api_key:    str          = "",
        tools_def:  list         = None,
        parent=None,
    ):
        super().__init__(parent)
        self.user_text = user_text
        self.history   = history or []
        self.system    = system
        self.subject   = subject
        self.api_key   = api_key
        self.tools_def = tools_def   # None = không dùng tool calling

    # ── Thread entry point ────────────────────────────────────────────

    def run(self):
        try:
            ai = AIService()

            if self.tools_def:
                # Chế độ tool calling
                self._run_with_tools(ai)
            else:
                # Chế độ chat thường
                self._run_chat(ai)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished_work.emit()

    # ── Chat thường ───────────────────────────────────────────────────

    def _run_chat(self, ai: AIService):
        """Gọi AI không có tool, emit response_ready khi xong."""
        # Xây history dạng list[dict] từ Message objects nếu cần
        history_dicts = self._normalize_history()

        reply = ai.chat(
            user_message=self.user_text,
            subject=self.subject,
            history=history_dicts,
            system_prompt=self.system,
        )

        if reply:
            self.response_ready.emit(reply.strip())
        else:
            self.error_occurred.emit("AI không trả về phản hồi. Vui lòng thử lại.")

    # ── Tool calling ──────────────────────────────────────────────────

    def _run_with_tools(self, ai: AIService):
        """Gọi AI có tool, emit tool_call_request hoặc response_ready."""
        history_dicts = self._normalize_history()

        response = ai.chat_with_tools(
            user_message=self.user_text,
            tools_def=self.tools_def,
            subject=self.subject,
            history=history_dicts,
        )

        if response is None:
            self.error_occurred.emit("Không thể kết nối AI. Vui lòng thử lại.")
            return

        # Kiểm tra có tool call không
        try:
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    part = candidate.content.parts[0]
                    if hasattr(part, "function_call") and part.function_call:
                        func      = part.function_call
                        tool_name = func.name
                        tool_args = dict(func.args) if func.args else {}
                        self.tool_call_request.emit(tool_name, tool_args)
                        return
        except Exception:
            pass

        # Không có tool call → lấy text thường
        try:
            reply = response.text
            self.response_ready.emit(reply.strip() if reply else "")
        except Exception:
            self.error_occurred.emit(
                "Rất tiếc, tôi không thể xử lý yêu cầu này. Vui lòng thử lại."
            )

    # ── Helper ───────────────────────────────────────────────────────

    def _normalize_history(self) -> List[dict]:
        """
        Chuẩn hóa history về dạng list[{"role": str, "content": str}].
        Chấp nhận cả Message objects lẫn dict sẵn.
        """
        result = []
        for item in self.history:
            if isinstance(item, dict):
                result.append({
                    "role":    item.get("role", "user"),
                    "content": item.get("content", ""),
                })
            elif hasattr(item, "role") and hasattr(item, "content"):
                # Message object
                role = item.role.value if hasattr(item.role, "value") else str(item.role)
                result.append({"role": role, "content": item.content})
        return result