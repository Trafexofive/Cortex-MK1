from ..core.graph_rag import GraphRAGEngine
from .llm_service import LLMService

class LiveAgentService:
    def __init__(self):
        self.rag_engine = GraphRAGEngine()
        self.llm_service = LLMService()

    async def process_message(self, user_id: str, message: str) -> dict:
        # This is a placeholder for the actual implementation
        response_generator = self.llm_service.generate_response_streaming(user_id, message)
        full_response = "".join([chunk async for chunk in response_generator])
        return {"response": full_response}
