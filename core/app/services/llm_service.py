from typing import AsyncGenerator

class LLMService:
    async def generate_response_streaming(self, user_id: str, message: str) -> AsyncGenerator[str, None]:
        """
        Placeholder for a streaming LLM response.
        This will be replaced with a real LLM implementation.
        """
        response_message = f"LLM response to: {message}"
        for char in response_message:
            yield char
