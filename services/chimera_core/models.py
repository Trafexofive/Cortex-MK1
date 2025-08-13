from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ToolDefinition(BaseModel):
    name: str
    description: str
    type: str
    runtime: str
    path: str
    parameters_schema: Dict[str, Any]

class AgentDefinition(BaseModel):
    name: str
    description: str
    system_prompt: str = Field(alias='system_prompt')
    model: str
    iteration_cap: int
    # For now, we will assume tools are loaded based on a directory, not an explicit list