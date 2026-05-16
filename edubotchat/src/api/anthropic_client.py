"""
anthropic_client.py - Client gọi Anthropic Claude API.
"""

import os
from typing import Optional, Generator
from src.api.exceptions import (
    APIError, APIAuthenticationError, APIRateLimitError,
    APITimeoutError, APIInvalidRequestError
)

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class AnthropicClient:
    """Client để tương tác với Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """
        Args:
            api_key: Anthropic API key. Nếu None, đọc từ biến môi trường ANTHROPIC_API_KEY
            model: Model ID (mặc định: claude-3-haiku-20240307)
        """
        if not HAS_ANTHROPIC:
            raise ImportError(
                "Thư viện 'anthropic' chưa được cài đặt. "
                "Hãy chạy: pip install anthropic"
            )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise APIAuthenticationError(
                "Chưa có API key. Vui lòng đặt biến môi trường ANTHROPIC_API_KEY "
                "hoặc truyền api_key vào constructor."
            )

        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def send_message(
        self,
        user_message: str,
        system: Optional[str] = None,
        history: Optional[list[dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Gửi tin nhắn và nhận phản hồi từ Claude.

        Args:
            user_message: Tin nhắn của người dùng
            system: System prompt (nếu None, dùng mặc định)
            history: Lịch sử chat (list các dict với key 'role' và 'content')
            max_tokens: Số token tối đa cho phản hồi
            temperature: Độ sáng tạo (0-1)

        Returns:
            Phản hồi text từ AI

        Raises:
            APIError: Khi có lỗi từ API
        """
        try:
            messages = history or []
            messages.append({"role": "user", "content": user_message})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "",
                messages=messages,
            )

            return response.content[0].text

        except anthropic.AuthenticationError as e:
            raise APIAuthenticationError(str(e)) from e
        except anthropic.RateLimitError as e:
            raise APIRateLimitError(str(e)) from e
        except anthropic.APIStatusError as e:
            if e.status_code == 400:
                raise APIInvalidRequestError(str(e)) from e
            raise APIError(str(e), status_code=e.status_code) from e
        except Exception as e:
            raise APIError(f"Lỗi không xác định: {str(e)}") from e

    def send_message_stream(
        self,
        user_message: str,
        system: Optional[str] = None,
        history: Optional[list[dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Gửi tin nhắn và nhận phản hồi dạng streaming.

        Yields:
            Từng phần (chunk) của phản hồi
        """
        try:
            messages = history or []
            messages.append({"role": "user", "content": user_message})

            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "",
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except anthropic.AuthenticationError as e:
            raise APIAuthenticationError(str(e)) from e
        except anthropic.RateLimitError as e:
            raise APIRateLimitError(str(e)) from e
        except anthropic.APIStatusError as e:
            if e.status_code == 400:
                raise APIInvalidRequestError(str(e)) from e
            raise APIError(str(e), status_code=e.status_code) from e
        except Exception as e:
            raise APIError(f"Lỗi không xác định: {str(e)}") from e