# test_gemini.py
from src.api.ai_service import AIService

ai = AIService()
response = ai.chat("Hãy chào tôi bằng một câu đơn giản")
print(response)