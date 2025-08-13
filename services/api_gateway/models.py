from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class InferenceMessage(BaseModel):
    role: str
    content: str

class InferenceInput(BaseModel):
    messages: List[InferenceMessage]

class InferenceRequest(BaseModel):
    user_id: str = Field(..., description="The user ID.")
    provider: str = Field(..., description="The name of the backend service provider (e.g., 'graphrag-app').")
    model: Optional[str] = Field(None, description="The specific model to use from the provider.")
    input: InferenceInput
    stream: bool = Field(default=False, description="Whether to stream the response.")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Provider-specific parameters.")

class InferenceChoice(BaseModel):
    message: InferenceMessage

class InferenceResponse(BaseModel):
    id: str
    provider: str
    model: str
    output: Dict[str, List[InferenceChoice]]
