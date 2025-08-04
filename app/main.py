from fastapi import FastAPI
from .api.routes import agent, voice, knowledge, health, voice_cloning

app = FastAPI(
    title="GraphRAG-Agent-MK1",
    description="A blazing-fast, low-latency Graph RAG implementation for live voice agents.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(agent.router)
app.include_router(voice.router)
app.include_router(knowledge.router)
app.include_router(voice_cloning.router)
