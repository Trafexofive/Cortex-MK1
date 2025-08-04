from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from .neo4j_client import Neo4jClient
from .redis_client import RedisClient
import asyncio

class GraphRAGEngine:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.neo4j = Neo4jClient()
        self.redis = RedisClient()
        self.prediction_cache = {}
    
    async def retrieve_with_prediction(self, query: str, user_context: Dict, 
                                     max_depth: int = 3) -> Dict[str, Any]:
        """Retrieve context and predict next queries"""
        
        # Parallel execution for speed
        retrieve_task = self.retrieve(query, max_depth)
        predict_task = self.predict_next_queries(query, user_context)
        
        context, predictions = await asyncio.gather(retrieve_task, predict_task)
        
        # Pre-load predicted contexts in background
        asyncio.create_task(self.preload_predictions(predictions))
        
        return {
            "context": context,
            "predictions": predictions,
            "retrieval_time_ms": context.get("retrieval_time_ms", 0)
        }
    
    async def retrieve(self, query: str, max_depth: int = 3) -> Dict[str, Any]:
        """Core retrieval with sub-100ms target"""
        start_time = asyncio.get_event_loop().time()
        
        # Check cache first
        cache_key = f"query:{hash(query)}:{max_depth}"
        cached = await self.redis.get(cache_key)
        if cached:
            return {"cached": True, "data": cached, "retrieval_time_ms": 5}
        
        # Generate embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Parallel graph operations
        similar_task = self.neo4j.find_similar_nodes(query_embedding, limit=10)
        expand_task = self.neo4j.expand_graph_context([], max_depth)  # Will be updated
        
        similar_nodes = await similar_task
        expanded_context = await self.neo4j.expand_graph_context(similar_nodes, max_depth)
        
        result = {
            "query": query,
            "similar_nodes": similar_nodes,
            "expanded_context": expanded_context,
            "retrieval_depth": max_depth,
            "retrieval_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000
        }
        
        # Cache result
        await self.redis.setex(cache_key, 3600, result)
        
        return result
    
    async def predict_next_queries(self, current_query: str, context: Dict) -> List[str]:
        """Predict likely follow-up queries"""
        # Simple prediction based on conversation context
        conversation_history = context.get("history", [])
        
        # This would use a lightweight model or rule-based system
        # For now, simple heuristics
        predictions = []
        
        if "what" in current_query.lower():
            predictions.append(current_query.replace("what", "how"))
            predictions.append(current_query.replace("what", "why"))
        
        return predictions[:3]
    
    async def preload_predictions(self, predictions: List[str]):
        """Pre-compute contexts for predicted queries"""
        for prediction in predictions:
            if prediction not in self.prediction_cache:
                asyncio.create_task(self.retrieve(prediction))