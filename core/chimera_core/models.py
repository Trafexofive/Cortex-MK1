from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    runtime: str
    # ... other fields

class AgentDefinition(BaseModel):
    name: str
    description: str
    tools: List[str]
    # ... other fields

class RelicConnectorDefinition(BaseModel):
    name: str
    description: str
    # ... other fields
