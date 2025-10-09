"""
==============================================================================
CONTAINER ORCHESTRATOR - MAIN APPLICATION
==============================================================================
FastAPI service for Docker container lifecycle management.
Port: 8086
==============================================================================
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from managers import DockerManager, NetworkManager
from api import (
    tools_router,
    relics_router,
    stats_router,
    cleanup_router
)


# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8086"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the container orchestrator."""
    
    # Startup
    logger.info("🚀 Starting Container Orchestrator...")
    
    # Initialize managers
    docker_manager = DockerManager()
    network_manager = NetworkManager()
    
    app.state.docker_manager = docker_manager
    app.state.network_manager = network_manager
    
    logger.info(f"✅ Container Orchestrator ready on port {PORT}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Container Orchestrator...")
    
    # Cleanup any remaining networks (optional - could keep for debugging)
    # network_manager.cleanup_all_session_networks()


# Create FastAPI app
app = FastAPI(
    title="Cortex-Prime Container Orchestrator",
    description="Docker container lifecycle management for tools and relics",
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
app.include_router(tools_router)
app.include_router(relics_router)
app.include_router(stats_router)
app.include_router(cleanup_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "container_orchestrator",
        "version": "1.0.0",
        "docker": "connected"
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Cortex-Prime Container Orchestrator",
        "version": "1.0.0",
        "description": "Docker container lifecycle management",
        "endpoints": {
            "tools": "/containers/tool",
            "relics": "/containers/relic",
            "stats": "/containers/stats",
            "cleanup": "/containers/cleanup"
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
