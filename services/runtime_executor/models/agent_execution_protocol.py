"""
==============================================================================
AGENT EXECUTION PROTOCOL v2.0 - Stream-As-We-Execute Model
==============================================================================
New execution model with:
- Async/Sync action execution
- Dependency resolution (depends_on)
- Streaming results as they complete
- Parallel execution where possible
- Tool/Agent/Relic/Workflow orchestration
==============================================================================
"""

from typing import Dict, List, Optional, Any, AsyncGenerator, Union, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
import uuid


# ============================================================================
# ACTION MODELS
# ============================================================================

class ActionType(str, Enum):
    """Type of action to execute"""
    TOOL = "tool"
    AGENT = "agent"
    RELIC = "relic"
    WORKFLOW = "workflow"
    LLM = "llm"
    DECISION = "decision"
    PARALLEL = "parallel"


class ActionMode(str, Enum):
    """Execution mode for action"""
    SYNC = "sync"    # Wait for completion before continuing
    ASYNC = "async"  # Execute and continue, collect result later
    FIRE_AND_FORGET = "fire_and_forget"  # Execute and don't wait for result


class ActionStatus(str, Enum):
    """Status of action execution"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    WAITING_FOR_DEPENDENCIES = "waiting_for_dependencies"


class Action(BaseModel):
    """Single action in agent execution plan"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Action name/identifier")
    type: ActionType = Field(..., description="Type of action")
    mode: ActionMode = Field(default=ActionMode.SYNC, description="Execution mode")
    
    # Target and parameters
    target: str = Field(..., description="Tool/Agent/Relic name to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="Action IDs this depends on")
    wait_for_all: bool = Field(default=True, description="Wait for all dependencies or just one")
    
    # Configuration
    timeout_seconds: Optional[int] = Field(default=300)
    retry_count: int = Field(default=0, ge=0, le=5)
    retry_delay_seconds: int = Field(default=1)
    
    # Conditional execution
    condition: Optional[str] = Field(default=None, description="Python expression to evaluate")
    skip_on_error: bool = Field(default=False, description="Skip instead of fail on error")
    
    # Output handling
    output_key: Optional[str] = Field(default=None, description="Key to store output in context")
    transform: Optional[str] = Field(default=None, description="Transform function for output")


class ActionResult(BaseModel):
    """Result of action execution"""
    action_id: str
    action_name: str
    status: ActionStatus
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Result
    output: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    retries: int = 0
    dependencies_met: bool = True
    skipped_reason: Optional[str] = None


# ============================================================================
# EXECUTION PLAN
# ============================================================================

class ExecutionPlan(BaseModel):
    """Complete execution plan for an agent iteration"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    iteration: int = 0
    
    # Actions to execute
    actions: List[Action] = Field(default_factory=list)
    
    # Execution strategy
    max_parallel: int = Field(default=5, description="Max concurrent actions")
    fail_fast: bool = Field(default=False, description="Stop on first failure")
    
    # Context
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared execution context")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionGraph(BaseModel):
    """DAG representation of execution plan for dependency resolution"""
    nodes: Dict[str, Action] = Field(default_factory=dict)
    edges: Dict[str, List[str]] = Field(default_factory=dict)  # action_id -> [dependent_action_ids]
    
    def add_action(self, action: Action):
        """Add action to graph"""
        self.nodes[action.id] = action
        
        # Add reverse edges for dependents
        for dep_id in action.depends_on:
            if dep_id not in self.edges:
                self.edges[dep_id] = []
            self.edges[dep_id].append(action.id)
    
    def get_ready_actions(self, completed: Set[str]) -> List[Action]:
        """Get actions whose dependencies are satisfied"""
        ready = []
        for action_id, action in self.nodes.items():
            if action_id in completed:
                continue
            
            # Check if all dependencies are met
            if not action.depends_on:
                ready.append(action)
            elif action.wait_for_all:
                if all(dep_id in completed for dep_id in action.depends_on):
                    ready.append(action)
            else:
                if any(dep_id in completed for dep_id in action.depends_on):
                    ready.append(action)
        
        return ready
    
    def has_cycles(self) -> bool:
        """Check for circular dependencies"""
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle_util(node_id):
                    return True
        
        return False


# ============================================================================
# STREAMING EXECUTION EVENT
# ============================================================================

class StreamEvent(BaseModel):
    """Event streamed during execution"""
    event_type: str  # action_started, action_completed, action_failed, llm_token, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    action_id: Optional[str] = None
    action_name: Optional[str] = None


# ============================================================================
# AGENT EXECUTION STATE
# ============================================================================

class AgentExecutionState(BaseModel):
    """State of agent execution across iterations"""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    
    # Iteration state
    current_iteration: int = 0
    max_iterations: int = 10
    
    # Execution context (shared across iterations)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # History
    action_results: Dict[str, ActionResult] = Field(default_factory=dict)
    iteration_plans: List[ExecutionPlan] = Field(default_factory=list)
    
    # Status
    status: ActionStatus = ActionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # LLM conversation
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metrics
    total_llm_calls: int = 0
    total_tool_calls: int = 0
    total_tokens: int = 0


# ============================================================================
# AGENT LOOP PROTOCOL
# ============================================================================

class AgentLoopProtocol(BaseModel):
    """Protocol configuration for agent loop execution"""
    
    # Loop control
    mode: str = Field(default="autonomous", description="strict, default, autonomous")
    max_iterations: int = Field(default=10)
    max_execution_time_seconds: int = Field(default=3600)
    
    # Streaming
    stream_llm_tokens: bool = Field(default=True, description="Stream LLM tokens as they arrive")
    stream_action_results: bool = Field(default=True, description="Stream action results immediately")
    stream_thoughts: bool = Field(default=True, description="Stream agent reasoning/thoughts")
    
    # Execution strategy
    allow_parallel_actions: bool = Field(default=True)
    max_parallel_actions: int = Field(default=5)
    auto_retry_on_failure: bool = Field(default=True)
    
    # Decision making
    require_user_approval: bool = Field(default=False, description="Require approval for actions")
    auto_plan_next_iteration: bool = Field(default=True)
    
    # Termination conditions
    terminate_on_goal_achieved: bool = Field(default=True)
    terminate_on_no_progress: bool = Field(default=True)
    terminate_on_error: bool = Field(default=False)
    
    # Context management
    max_context_size: int = Field(default=100000, description="Max context window size")
    context_compression: bool = Field(default=True)
    persist_context: bool = Field(default=True)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def create_example_plan() -> ExecutionPlan:
    """Create example execution plan with dependencies"""
    
    plan = ExecutionPlan(
        agent_name="research_agent",
        iteration=1,
        max_parallel=3,
        actions=[
            # First, fetch data from two sources in parallel (async)
            Action(
                id="fetch_wiki",
                name="Fetch Wikipedia data",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="web_scraper",
                parameters={"url": "https://en.wikipedia.org/wiki/AI"},
                output_key="wiki_data"
            ),
            Action(
                id="fetch_arxiv",
                name="Fetch arXiv papers",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="arxiv_search",
                parameters={"query": "artificial intelligence", "max_results": 5},
                output_key="arxiv_data"
            ),
            
            # Then analyze both results (depends on both fetches)
            Action(
                id="analyze_combined",
                name="Analyze combined data",
                type=ActionType.AGENT,
                mode=ActionMode.SYNC,
                target="data_analyzer",
                depends_on=["fetch_wiki", "fetch_arxiv"],
                parameters={
                    "wiki_data": "$wiki_data",  # Reference from context
                    "arxiv_data": "$arxiv_data"
                },
                output_key="analysis_result"
            ),
            
            # Store result in cache (depends on analysis)
            Action(
                id="cache_result",
                name="Cache analysis result",
                type=ActionType.RELIC,
                mode=ActionMode.FIRE_AND_FORGET,
                target="results_cache",
                depends_on=["analyze_combined"],
                parameters={
                    "key": "ai_research_analysis",
                    "value": "$analysis_result",
                    "ttl": 3600
                }
            ),
            
            # Simultaneously, run quality check (depends on analysis)
            Action(
                id="quality_check",
                name="Quality check analysis",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="quality_checker",
                depends_on=["analyze_combined"],
                parameters={"data": "$analysis_result"},
                output_key="quality_score"
            )
        ]
    )
    
    return plan


if __name__ == "__main__":
    # Example: Create and display execution plan
    plan = create_example_plan()
    
    # Build execution graph
    graph = ExecutionGraph()
    for action in plan.actions:
        graph.add_action(action)
    
    print("Execution Plan:")
    print(f"  Agent: {plan.agent_name}")
    print(f"  Actions: {len(plan.actions)}")
    print(f"  Max Parallel: {plan.max_parallel}")
    print(f"\nAction Dependency Graph:")
    
    for action in plan.actions:
        deps = ", ".join(action.depends_on) if action.depends_on else "None"
        print(f"  {action.name} ({action.mode.value}) -> depends on: {deps}")
    
    # Check for cycles
    if graph.has_cycles():
        print("\n⚠️  WARNING: Circular dependencies detected!")
    else:
        print("\n✅ No circular dependencies")
    
    # Show execution order
    print(f"\nExecution Order (wave-based):")
    completed = set()
    wave = 0
    
    while len(completed) < len(plan.actions):
        ready = graph.get_ready_actions(completed)
        if not ready:
            break
        
        wave += 1
        print(f"\n  Wave {wave}:")
        for action in ready:
            print(f"    - {action.name} ({action.mode.value})")
            completed.add(action.id)
