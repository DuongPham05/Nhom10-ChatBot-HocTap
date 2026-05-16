"""
exceptions.py - Các exception tùy chỉnh cho tầng API.
"""

class APIError(Exception):
    """Lỗi chung khi gọi API."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

class APIAuthenticationError(APIError):
    """Lỗi xác thực (401, 403)."""
    def __init__(self, message: str = "API key không hợp lệ hoặc hết hạn."):
        super().__init__(message, status_code=401)

class APIRateLimitError(APIError):
    """Lỗi vượt quá giới hạn request (429)."""
    def __init__(self, message: str = "Đã vượt quá giới hạn request. Vui lòng thử lại sau."):
        super().__init__(message, status_code=429)

class APITimeoutError(APIError):
    """Lỗi timeout khi gọi API."""
    def __init__(self, message: str = "Kết nối tới API bị timeout."):
        super().__init__(message, status_code=504)

class APIInvalidRequestError(APIError):
    """Lỗi request không hợp lệ (400)."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)