import httpx
from .base import BaseLLMProvider
from ...config import settings

class GeminiProvider(BaseLLMProvider):
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        # Simplified for B-Line: does not use full chat history yet
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts":[{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
