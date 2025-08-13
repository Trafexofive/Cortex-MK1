import asyncio
import time
import statistics
from app.core.voice_pipeline import VoicePipeline
from app.core.graph_rag import GraphRAGEngine

async def benchmark_voice_pipeline():
    pipeline = VoicePipeline()
    times = []
    
    for i in range(100):
        start = time.time()
        
        # Simulate voice input -> transcription -> response -> TTS
        test_audio = generate_test_audio("Hello, how are you?")
        transcript = await pipeline.transcribe_streaming([test_audio]).__anext__()
        
        # Mock response generation
        response_audio = pipeline.synthesize_streaming("I'm doing well, thank you!")
        async for chunk in response_audio:
            pass  # Consume stream
            
        end = time.time()
        times.append((end - start) * 1000)  # Convert to ms
    
    print(f"Voice Pipeline Latency:")
    print(f"  Mean: {statistics.mean(times):.1f}ms")
    print(f"  P95: {sorted(times)[95]:.1f}ms")
    print(f"  P99: {sorted(times)[99]:.1f}ms")

async def benchmark_graph_rag():
    rag = GraphRAGEngine()
    times = []
    
    test_queries = [
        "What is machine learning?",
        "How does neural network training work?",
        "Explain gradient descent algorithm"
    ]
    
    for query in test_queries * 33:  # 100 total
        start = time.time()
        result = await rag.retrieve(query)
        end = time.time()
        times.append((end - start) * 1000)
    
    print(f"Graph RAG Retrieval:")
    print(f"  Mean: {statistics.mean(times):.1f}ms")
    print(f"  P95: {sorted(times)[95]:.1f}ms")
    print(f"  P99: {sorted(times)[99]:.1f}ms")

if __name__ == "__main__":
    asyncio.run(benchmark_voice_pipeline())
    asyncio.run(benchmark_graph_rag())