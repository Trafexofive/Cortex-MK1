"""
==============================================================================
AGENT ORCHESTRATOR - MAIN APPLICATION
==============================================================================
FastAPI service for agent session coordination and message routing.
Port: 8085
==============================================================================
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from managers import SessionManager
from api import (
    sessions_router,
    messages_router
)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8085"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Service URLs
STORAGE_URL = os.getenv("STORAGE_URL", "http://localhost:8084")
LLM_URL = os.getenv("LLM_URL", "http://localhost:8081")
MANIFEST_URL = os.getenv("MANIFEST_URL", "http://localhost:8082")
CONTAINER_URL = os.getenv("CONTAINER_URL", "http://localhost:8086")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the agent orchestrator."""
    
    # Startup
    logger.info("🚀 Starting Agent Orchestrator...")
    
    # Initialize session manager
    session_manager = SessionManager(
        storage_url=STORAGE_URL,
        llm_url=LLM_URL,
        manifest_url=MANIFEST_URL,
        container_url=CONTAINER_URL
    )
    
    app.state.session_manager = session_manager
    
    logger.info(f"✅ Agent Orchestrator ready on port {PORT}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Agent Orchestrator...")
    await session_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Cortex-Prime Agent Orchestrator",
    description="Agent session coordination and message routing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions_router)
app.include_router(messages_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agent_orchestrator",
        "version": "1.0.0",
        "dependencies": {
            "storage": STORAGE_URL,
            "llm": LLM_URL,
            "manifest": MANIFEST_URL,
            "container": CONTAINER_URL
        }
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Cortex-Prime Agent Orchestrator",
        "version": "1.0.0",
        "description": "Agent session coordination",
        "endpoints": {
            "sessions": "/agent/{agent_name}/session",
            "messages": "/agent/session/{id}/message"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level=LOG_LEVEL.lower()
    )
