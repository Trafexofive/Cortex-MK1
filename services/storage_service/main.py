"""
==============================================================================
STORAGE SERVICE - MAIN APPLICATION
==============================================================================
FastAPI service for abstract persistence layer.
Port: 8084
==============================================================================
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backends import SQLiteBackend
from api import (
    sessions_router,
    history_router,
    state_router,
    artifacts_router,
    metrics_router,
    cache_router
)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8084"))
DB_PATH = os.getenv("DB_PATH", "/data/storage.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the storage service."""
    
    # Startup
    logger.info("🚀 Starting Storage Service...")
    
    # Initialize backend
    backend = SQLiteBackend(db_path=DB_PATH)
    await backend.initialize()
    app.state.backend = backend
    
    logger.info(f"✅ Storage Service ready on port {PORT}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Storage Service...")
    await backend.close()


# Create FastAPI app
app = FastAPI(
    title="Cortex-Prime Storage Service",
    description="Abstract persistence layer for sessions, history, state, artifacts, metrics, and cache",
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
app.include_router(history_router)
app.include_router(state_router)
app.include_router(artifacts_router)
app.include_router(metrics_router)
app.include_router(cache_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "storage_service",
        "version": "1.0.0",
        "backend": "sqlite",
        "db_path": DB_PATH
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Cortex-Prime Storage Service",
        "version": "1.0.0",
        "description": "Abstract persistence layer",
        "endpoints": {
            "sessions": "/storage/sessions",
            "history": "/storage/history",
            "state": "/storage/state",
            "artifacts": "/storage/artifacts",
            "metrics": "/storage/metrics",
            "cache": "/storage/cache"
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
