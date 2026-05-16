"""
src/api/ai_service.py
----------------------
Wrapper cho Google Gemini API.

AIService được dùng như singleton qua AIService.instance()
để tránh tạo nhiều genai.Client() mỗi lần gọi.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing  import List, Optional

from dotenv import load_dotenv

# Load .env từ thư mục gốc project
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BASE_DIR / ".env")


class AIService:
    """
    Wrapper Gemini API.

    Dùng:
        ai    = AIService()          # hoặc AIService.instance()
        reply = ai.chat("Câu hỏi")
    """

    _instance: Optional[AIService] = None

    @classmethod
    def instance(cls) -> AIService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        from google import genai
        self._client     = genai.Client()
        self.model_name  = "gemini-2.5-flash"

    # ── Chat thường ───────────────────────────────────────────────────

    def chat(
        self,
        user_message:  str,
        subject:       str          = "",
        history:       List[dict]   = None,
        system_prompt: str          = "",
    ) -> str:
        """
        Gọi Gemini không có tool calling.

        Args:
            user_message  : tin nhắn hiện tại của người dùng
            subject       : môn học (thêm vào system prompt)
            history       : list[{"role","content"}] lịch sử hội thoại
            system_prompt : system prompt đầy đủ (nếu truyền thì ưu tiên dùng)

        Returns:
            Chuỗi phản hồi từ AI
        """
        from google.genai import types

        # Xây system instruction
        if system_prompt:
            sys_instr = system_prompt
        elif subject:
            sys_instr = (
                f"Bạn là trợ lý học tập thông minh cho môn {subject}. "
                "Trả lời bằng tiếng Việt, rõ ràng và ngắn gọn."
            )
        else:
            sys_instr = (
                "Bạn là trợ lý học tập thông minh của EduBot. "
                "Trả lời bằng tiếng Việt, thân thiện và hữu ích."
            )

        config = types.GenerateContentConfig(
            system_instruction=sys_instr,
            temperature=0.7,
        )

        # Xây contents từ history + tin nhắn hiện tại
        contents = []
        for msg in (history or []):
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg.get("content", ""))],
                )
            )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)],
            )
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        return response.text or ""

    # ── Chat có tool calling ──────────────────────────────────────────

    def chat_with_tools(
        self,
        user_message:  str,
        tools_def:     list,
        subject:       str          = "",
        history:       List[dict]   = None,
        system_prompt: str          = "",
    ):
        """
        Gọi Gemini với tool calling.

        Returns:
            Response object từ Gemini (caller tự parse candidates)
        """
        from google.genai import types

        if system_prompt:
            sys_instr = system_prompt
        elif subject:
            sys_instr = (
                f"Bạn là trợ lý học tập thông minh cho môn {subject}. "
                "Trả lời bằng tiếng Việt."
            )
        else:
            sys_instr = "Bạn là trợ lý học tập thông minh của EduBot. Trả lời bằng tiếng Việt."

        config = types.GenerateContentConfig(
            system_instruction=sys_instr,
            temperature=0.7,
            tools=tools_def,
        )

        contents = []
        for msg in (history or []):
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg.get("content", ""))],
                )
            )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)],
            )
        )

        return self._client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )