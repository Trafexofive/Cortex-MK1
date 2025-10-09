"""Tool building API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/containers/build", tags=["build"])


class BuildToolRequest(BaseModel):
    """Request to build a tool image."""
    tool_name: str
    force_rebuild: bool = False


class BuildToolResponse(BaseModel):
    """Response from building a tool."""
    tool_name: str
    image_tag: str
    status: str
    message: Optional[str] = None


@router.post("/tool", response_model=BuildToolResponse)
async def build_tool(request_data: BuildToolRequest, req: Request):
    """Build a tool image from its manifest."""
    docker_manager = req.app.state.docker_manager
    
    try:
        # Use the tool builder to build the image
        image_tag = docker_manager.tool_builder.ensure_tool_image(
            request_data.tool_name,
            None  # manifest_registry placeholder
        )
        
        return BuildToolResponse(
            tool_name=request_data.tool_name,
            image_tag=image_tag,
            status="success",
            message=f"Successfully built image: {image_tag}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build tool {request_data.tool_name}: {str(e)}"
        )


@router.get("/tool/{tool_name}/exists")
async def check_tool_image(tool_name: str, req: Request):
    """Check if a tool image exists."""
    docker_manager = req.app.state.docker_manager
    
    image_tag = f"cortex/tool-{tool_name}:latest"
    
    try:
        docker_manager.client.images.get(image_tag)
        return {
            "tool_name": tool_name,
            "image_tag": image_tag,
            "exists": True
        }
    except Exception:
        return {
            "tool_name": tool_name,
            "image_tag": image_tag,
            "exists": False
        }
