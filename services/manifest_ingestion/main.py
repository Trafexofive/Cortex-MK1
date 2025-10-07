"""
==============================================================================
MANIFEST INGESTION SERVICE v1.0
==============================================================================
FastAPI + Pydantic microservice for ingesting, parsing, and validating
custom markdown manifests in the Cortex-Prime ecosystem.

Philosophy:
- Sovereignty: Each manifest defines a complete, autonomous entity
- Declarative: Manifests are the single source of truth
- Typed: Strong validation using Pydantic models
- Extensible: Plugin-based architecture for different manifest types
- Hot-Reload: FAAFO-friendly iteration without service restarts
==============================================================================
"""

import os
import yaml
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
from loguru import logger

# Import our Pydantic models
from models.manifest_models import (
    AgentManifest, 
    ToolManifest, 
    RelicManifest, 
    WorkflowManifest,
    ManifestRegistry,
    ManifestValidationResponse
)
from parsers.manifest_parser import ManifestParser
from registry.manifest_registry import ManifestRegistryService
from hotreload import HotReloadWatcher
from config import settings


# Application Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    logger.info("🚀 Starting Manifest Ingestion Service...")
    
    # Initialize registry service
    app.state.registry = ManifestRegistryService()
    
    # Load existing manifests on startup
    await app.state.registry.load_manifests_from_filesystem()
    
    # Start hot-reload watcher if enabled
    hot_reload_enabled = settings.get("hot_reload.enabled", True)
    if hot_reload_enabled:
        manifest_root = Path(settings.get("manifests.root_path", settings.manifests_root))
        
        async def handle_manifest_change(event_type: str, file_path: str):
            """Handle manifest file changes"""
            try:
                logger.info(f"🔄 Manifest {event_type}: {file_path}")
                
                if event_type in ("created", "modified"):
                    # Reload the specific manifest
                    await app.state.registry.reload_manifest_file(Path(file_path))
                elif event_type == "deleted":
                    # Remove the manifest from registry
                    await app.state.registry.remove_manifest_by_path(Path(file_path))
                    
            except Exception as e:
                logger.error(f"Failed to handle manifest change for {file_path}: {e}")
        
        # Create and start the watcher
        app.state.watcher = HotReloadWatcher(
            manifest_root=manifest_root,
            reload_callback=handle_manifest_change,
            loop=asyncio.get_event_loop()
        )
        app.state.watcher.start()
        logger.info("🔥 Hot-reload enabled for manifest changes")
    else:
        app.state.watcher = None
        logger.info("❄️  Hot-reload disabled")
    
    logger.info("✅ Manifest Ingestion Service ready")
    yield
    
    # Cleanup on shutdown
    if app.state.watcher:
        app.state.watcher.stop()
    
    logger.info("🛑 Shutting down Manifest Ingestion Service...")


# FastAPI App
app = FastAPI(
    title="Cortex-Prime Manifest Ingestion Service",
    description="Sovereign manifest parsing, validation, and registry service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "manifest-ingestion", "version": "1.0.0"}


@app.get("/registry/status")
async def get_registry_status():
    """Get overall registry status and statistics"""
    return await app.state.registry.get_status()


# ============================================================================
# MANIFEST INGESTION ENDPOINTS
# ============================================================================

@app.post("/manifests/upload")
async def upload_manifest(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and parse a manifest file (YAML or Markdown)
    """
    try:
        content = await file.read()
        
        # Parse the manifest
        parser = ManifestParser()
        manifest_data = await parser.parse_manifest_content(
            content.decode('utf-8'),
            filename=file.filename
        )
        
        # Validate and register
        validation_result = await app.state.registry.register_manifest(manifest_data)
        
        return {
            "status": "success",
            "filename": file.filename,
            "manifest_type": manifest_data.get("kind"),
            "manifest_name": manifest_data.get("name"),
            "validation": validation_result
        }
        
    except Exception as e:
        logger.error(f"Failed to upload manifest {file.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/manifests/parse")
async def parse_manifest_content(
    content: str,
    manifest_type: Optional[str] = None
):
    """
    Parse manifest content directly (for testing/validation)
    """
    try:
        parser = ManifestParser()
        manifest_data = await parser.parse_manifest_content(content)
        
        return {
            "status": "success",
            "parsed_data": manifest_data,
            "manifest_type": manifest_data.get("kind"),
            "validation": await app.state.registry.validate_manifest(manifest_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to parse manifest content: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# REGISTRY QUERY ENDPOINTS  
# ============================================================================

@app.get("/registry/agents")
async def list_agents():
    """List all registered agent manifests"""
    return await app.state.registry.list_manifests("Agent")


@app.get("/registry/tools")
async def list_tools():
    """List all registered tool manifests"""
    return await app.state.registry.list_manifests("Tool")


@app.get("/registry/relics")
async def list_relics():
    """List all registered relic manifests"""
    return await app.state.registry.list_manifests("Relic")


@app.get("/registry/workflows")
async def list_workflows():
    """List all registered workflow manifests"""
    return await app.state.registry.list_manifests("Workflow")


@app.get("/registry/manifest/{manifest_type}/{name}")
async def get_manifest(manifest_type: str, name: str):
    """Get a specific manifest by type and name"""
    manifest = await app.state.registry.get_manifest(manifest_type, name)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Manifest {manifest_type}/{name} not found")
    return manifest


# ============================================================================
# DEPENDENCY RESOLUTION ENDPOINTS
# ============================================================================

@app.get("/registry/dependencies/{manifest_type}/{name}")
async def get_manifest_dependencies(manifest_type: str, name: str):
    """Get all dependencies for a specific manifest"""
    dependencies = await app.state.registry.resolve_dependencies(manifest_type, name)
    return {"dependencies": dependencies}


@app.get("/registry/validate-dependencies/{manifest_type}/{name}")
async def validate_dependencies(manifest_type: str, name: str):
    """Validate that all dependencies for a manifest are satisfied"""
    validation = await app.state.registry.validate_dependencies(manifest_type, name)
    return validation


# ============================================================================
# FILESYSTEM SYNC ENDPOINTS
# ============================================================================

@app.post("/registry/sync")
async def sync_with_filesystem():
    """Sync registry with filesystem manifests"""
    try:
        result = await app.state.registry.load_manifests_from_filesystem()
        return {"status": "success", "synced": result}
    except Exception as e:
        logger.error(f"Failed to sync with filesystem: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/registry/export")
async def export_registry():
    """Export the entire registry as JSON"""
    try:
        export_data = await app.state.registry.export_registry()
        return {"status": "success", "registry": export_data}
    except Exception as e:
        logger.error(f"Failed to export registry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Configuration from settings
    host = settings.get("service.host", settings.host)
    port = settings.get("service.port", settings.port)
    log_level = settings.get("service.log_level", settings.log_level).lower()
    
    logger.info(f"Starting {settings.get('service.name', 'ManifestIngestion')} v{settings.get('service.version', '1.0.0')}")
    logger.info(f"Service listening on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=settings.get("service.reload", settings.reload)
    )