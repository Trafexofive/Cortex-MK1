"""
==============================================================================
MANIFEST PYDANTIC MODELS v1.0
==============================================================================
Strongly-typed Pydantic models for all Cortex-Prime manifest types.
Based on the Sovereign Core Standard seen in the journaler agent manifest.
==============================================================================
"""

from typing import Dict, List, Optional, Union, Any, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ManifestKind(str, Enum):
    AGENT = "Agent"
    TOOL = "Tool"
    RELIC = "Relic"
    WORKFLOW = "Workflow"
    MONUMENT = "Monument"
    AMULET = "Amulet"


class AgencyLevel(str, Enum):
    STRICT = "strict"
    DEFAULT = "default"
    AUTONOMOUS = "autonomous"


class Grade(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"


class State(str, Enum):
    STABLE = "stable"
    NIGHTLY = "nightly"
    UNSTABLE = "unstable"


# LLM provider types - referenced but managed by llm_gateway
class ProviderType(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GROQ = "groq"


# ============================================================================
# BASE MODELS
# ============================================================================

class BaseManifest(BaseModel):
    """Base class for all manifest types"""
    kind: ManifestKind
    version: str = Field(default="1.0", description="Manifest schema version")
    name: str = Field(..., description="Unique identifier for this entity")
    summary: str = Field(..., description="Brief description of purpose")
    author: str = Field(default="PRAETORIAN_CHIMERA", description="Creator/maintainer")
    state: State = Field(default=State.UNSTABLE, description="Stability level")
    
    class Config:
        use_enum_values = True


class CognitiveEngine(BaseModel):
    """Configuration for LLM cognitive processing - managed by llm_gateway"""
    
    class ModelConfig(BaseModel):
        provider: ProviderType
        model: str
    
    class ModelParameters(BaseModel):
        temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
        top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
        max_tokens: Optional[int] = Field(default=4096, ge=1)
        stream: Optional[bool] = Field(default=True)
        # Allow additional parameters for different providers
        extra_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    primary: ModelConfig
    fallback: Optional[ModelConfig] = None
    parameters: Optional[ModelParameters] = Field(default_factory=ModelParameters)


class ContextFeed(BaseModel):
    """Defines an environmental input to the agent"""
    
    class SourceConfig(BaseModel):
        type: Literal["internal", "tool", "relic", "external"]
        action: Optional[str] = None
        name: Optional[str] = None
        params: Dict[str, Any] = Field(default_factory=dict)
    
    id: str
    type: Literal["on_demand", "periodic", "streaming"]
    interval: Optional[int] = Field(None, description="Seconds for periodic feeds")
    source: SourceConfig


class ImportConfig(BaseModel):
    """Defines external dependencies and capabilities"""
    amulets: List[str] = Field(default_factory=list)
    monuments: List[str] = Field(default_factory=list)
    agents: List[str] = Field(default_factory=list)
    relics: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    workflows: List[str] = Field(default_factory=list)


class EnvironmentConfig(BaseModel):
    """Runtime environment configuration"""
    env_file: List[str] = Field(default_factory=lambda: [".env"])
    variables: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# AGENT MANIFEST MODEL
# ============================================================================

class PersonaConfig(BaseModel):
    """Agent personality and instruction configuration"""
    agent: str = Field(..., description="Path to agent persona markdown")
    user: Optional[str] = Field(None, description="Path to user-facing instructions")
    system: Optional[str] = Field(None, description="Path to system instructions")
    knowledge: Optional[str] = Field(None, description="Path to knowledge base")


class AgentManifest(BaseManifest):
    """Complete specification for an autonomous agent"""
    kind: Literal[ManifestKind.AGENT] = ManifestKind.AGENT
    
    # Behavioral Profile
    persona: PersonaConfig
    agency_level: AgencyLevel = Field(default=AgencyLevel.STRICT)
    grade: Grade = Field(default=Grade.COMMON)
    iteration_cap: int = Field(default=5, ge=0, description="Max thought-action cycles")
    
    # Cognitive Engine - Optional since it's managed by llm_gateway
    cognitive_engine: Optional[CognitiveEngine] = None
    
    # Capabilities and Dependencies
    import_: ImportConfig = Field(default_factory=ImportConfig, alias="import")
    
    # Sensory Inputs
    context_feeds: List[ContextFeed] = Field(default_factory=list)
    
    # Environment
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    
    class Config:
        populate_by_name = True


# ============================================================================
# TOOL MANIFEST MODEL
# ============================================================================

class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = Field(default=True)
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolManifest(BaseManifest):
    """Complete specification for a stateless function/tool"""
    kind: Literal[ManifestKind.TOOL] = ManifestKind.TOOL
    
    # Tool Specification
    description: str = Field(..., description="Detailed tool description")
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: str = Field(..., description="Description of return value")
    
    # Implementation
    implementation: Dict[str, Any] = Field(..., description="Implementation details")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)
    
    # Environment
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)


# ============================================================================
# RELIC MANIFEST MODEL  
# ============================================================================

class RelicManifest(BaseManifest):
    """Complete specification for a stateful, persistent service"""
    kind: Literal[ManifestKind.RELIC] = ManifestKind.RELIC
    
    # Service Specification
    description: str = Field(..., description="Detailed relic description")
    service_type: str = Field(..., description="Type of service (database, cache, etc.)")
    
    # Interface Definition
    interface: Dict[str, Any] = Field(..., description="API/interface specification")
    
    # Persistence Configuration
    persistence: Dict[str, Any] = Field(default_factory=dict)
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)
    
    # Environment  
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)


# ============================================================================
# WORKFLOW MANIFEST MODEL
# ============================================================================

class WorkflowStep(BaseModel):
    """A single step in a workflow"""
    name: str
    type: str  # "agent", "tool", "relic", "decision", "parallel"
    target: str  # What to execute
    parameters: Dict[str, Any] = Field(default_factory=dict)
    condition: Optional[str] = Field(None, description="Execution condition")
    retry_policy: Optional[Dict[str, Any]] = None


class WorkflowManifest(BaseManifest):
    """Complete specification for a multi-step pipeline"""
    kind: Literal[ManifestKind.WORKFLOW] = ManifestKind.WORKFLOW
    
    # Workflow Specification
    description: str = Field(..., description="Detailed workflow description")
    trigger: Dict[str, Any] = Field(..., description="What triggers this workflow")
    
    # Steps Definition
    steps: List[WorkflowStep] = Field(..., min_items=1)
    
    # Configuration
    timeout: Optional[int] = Field(None, description="Workflow timeout in seconds")
    retry_policy: Optional[Dict[str, Any]] = None
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)
    
    # Environment
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)


# ============================================================================
# REGISTRY AND VALIDATION MODELS
# ============================================================================

class ManifestValidationResponse(BaseModel):
    """Response from manifest validation"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    dependencies_satisfied: bool = Field(default=True)
    missing_dependencies: List[str] = Field(default_factory=list)


class ManifestRegistry(BaseModel):
    """Complete registry of all manifests"""
    agents: Dict[str, AgentManifest] = Field(default_factory=dict)
    tools: Dict[str, ToolManifest] = Field(default_factory=dict)
    relics: Dict[str, RelicManifest] = Field(default_factory=dict)
    workflows: Dict[str, WorkflowManifest] = Field(default_factory=dict)
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_manifests: int = Field(default=0)
    
    def update_stats(self):
        """Update registry statistics"""
        self.total_manifests = (
            len(self.agents) + 
            len(self.tools) + 
            len(self.relics) + 
            len(self.workflows)
        )
        self.last_updated = datetime.utcnow()


# ============================================================================
# UNION TYPE FOR DYNAMIC PARSING
# ============================================================================

ManifestUnion = Union[AgentManifest, ToolManifest, RelicManifest, WorkflowManifest]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_manifest_from_dict(data: Dict[str, Any]) -> ManifestUnion:
    """Factory function to create the correct manifest type from dictionary data"""
    kind = data.get("kind")
    
    if kind == ManifestKind.AGENT:
        return AgentManifest(**data)
    elif kind == ManifestKind.TOOL:
        return ToolManifest(**data)
    elif kind == ManifestKind.RELIC:
        return RelicManifest(**data)
    elif kind == ManifestKind.WORKFLOW:
        return WorkflowManifest(**data)
    else:
        raise ValueError(f"Unknown manifest kind: {kind}")
