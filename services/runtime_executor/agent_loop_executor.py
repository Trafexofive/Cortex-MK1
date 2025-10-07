"""
==============================================================================
AGENT LOOP EXECUTOR v2.0 - Stream-As-We-Execute Implementation
==============================================================================
Core execution engine for the agent loop with:
- Streaming results as actions complete
- Async/Sync action orchestration
- Dependency resolution and parallel execution
- Real-time progress updates
==============================================================================
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator, Set, Tuple
from datetime import datetime, timedelta
from loguru import logger
import json

from models.agent_execution_protocol import (
    Action,
    ActionResult,
    ActionStatus,
    ActionMode,
    ActionType,
    ExecutionPlan,
    ExecutionGraph,
    StreamEvent,
    AgentExecutionState,
    AgentLoopProtocol
)


class AgentLoopExecutor:
    """
    Orchestrates agent execution loop with streaming and async/sync actions
    """
    
    def __init__(
        self,
        agent_name: str,
        protocol: AgentLoopProtocol,
        tool_executor: Any,
        llm_client: Any
    ):
        self.agent_name = agent_name
        self.protocol = protocol
        self.tool_executor = tool_executor
        self.llm_client = llm_client
        
        # Execution state
        self.state = AgentExecutionState(
            agent_name=agent_name,
            max_iterations=protocol.max_iterations
        )
        
        # Active async tasks
        self.async_tasks: Dict[str, asyncio.Task] = {}
        
        # Event queue for streaming
        self.event_queue: asyncio.Queue = asyncio.Queue()
    
    
    async def execute_agent_loop(self) -> AsyncGenerator[StreamEvent, None]:
        """
        Main agent loop with streaming execution
        Yields StreamEvent objects as execution progresses
        """
        self.state.status = ActionStatus.RUNNING
        self.state.started_at = datetime.utcnow()
        
        try:
            yield StreamEvent(
                event_type="agent_started",
                data={
                    "agent_name": self.agent_name,
                    "execution_id": self.state.execution_id,
                    "max_iterations": self.state.max_iterations
                }
            )
            
            # Main iteration loop
            while self.state.current_iteration < self.state.max_iterations:
                self.state.current_iteration += 1
                
                yield StreamEvent(
                    event_type="iteration_started",
                    data={
                        "iteration": self.state.current_iteration,
                        "max_iterations": self.state.max_iterations
                    }
                )
                
                # 1. Generate execution plan for this iteration
                plan = await self._generate_execution_plan()
                self.state.iteration_plans.append(plan)
                
                yield StreamEvent(
                    event_type="plan_generated",
                    data={
                        "iteration": self.state.current_iteration,
                        "actions_count": len(plan.actions),
                        "actions": [
                            {
                                "id": a.id,
                                "name": a.name,
                                "type": a.type.value,
                                "mode": a.mode.value,
                                "depends_on": a.depends_on
                            }
                            for a in plan.actions
                        ]
                    }
                )
                
                # 2. Execute the plan with streaming
                async for event in self._execute_plan_streaming(plan):
                    yield event
                
                # 3. Check termination conditions
                should_continue, reason = await self._should_continue()
                
                if not should_continue:
                    yield StreamEvent(
                        event_type="termination",
                        data={
                            "reason": reason,
                            "iteration": self.state.current_iteration
                        }
                    )
                    break
                
                yield StreamEvent(
                    event_type="iteration_completed",
                    data={
                        "iteration": self.state.current_iteration,
                        "actions_completed": len([
                            r for r in self.state.action_results.values()
                            if r.status == ActionStatus.COMPLETED
                        ])
                    }
                )
            
            self.state.status = ActionStatus.COMPLETED
            self.state.completed_at = datetime.utcnow()
            
            yield StreamEvent(
                event_type="agent_completed",
                data={
                    "execution_id": self.state.execution_id,
                    "total_iterations": self.state.current_iteration,
                    "total_actions": len(self.state.action_results),
                    "total_llm_calls": self.state.total_llm_calls,
                    "total_tool_calls": self.state.total_tool_calls,
                    "duration_seconds": (
                        self.state.completed_at - self.state.started_at
                    ).total_seconds() if self.state.completed_at and self.state.started_at else None
                }
            )
            
        except Exception as e:
            logger.error(f"Agent loop failed: {str(e)}")
            self.state.status = ActionStatus.FAILED
            self.state.completed_at = datetime.utcnow()
            
            yield StreamEvent(
                event_type="agent_failed",
                data={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    
    async def _execute_plan_streaming(
        self,
        plan: ExecutionPlan
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Execute plan with dependency resolution and streaming results
        """
        # Build execution graph
        graph = ExecutionGraph()
        for action in plan.actions:
            graph.add_action(action)
        
        # Check for cycles
        if graph.has_cycles():
            yield StreamEvent(
                event_type="error",
                data={"error": "Circular dependencies detected in execution plan"}
            )
            return
        
        # Track completion
        completed: Set[str] = set()
        failed: Set[str] = set()
        running: Dict[str, asyncio.Task] = {}
        
        # Execute in waves based on dependencies
        while len(completed) + len(failed) < len(plan.actions):
            # Get ready actions (dependencies satisfied)
            ready_actions = [
                action for action in graph.get_ready_actions(completed)
                if action.id not in running and action.id not in failed
            ]
            
            if not ready_actions and not running:
                # No more actions can be executed
                yield StreamEvent(
                    event_type="warning",
                    data={
                        "message": "No more actions can execute (blocked by dependencies)",
                        "completed": len(completed),
                        "failed": len(failed),
                        "total": len(plan.actions)
                    }
                )
                break
            
            # Start ready actions (respecting max_parallel)
            for action in ready_actions:
                if len(running) >= plan.max_parallel:
                    break
                
                # Start action execution
                task = asyncio.create_task(self._execute_action(action))
                running[action.id] = task
                
                yield StreamEvent(
                    event_type="action_started",
                    action_id=action.id,
                    action_name=action.name,
                    data={
                        "type": action.type.value,
                        "mode": action.mode.value,
                        "target": action.target,
                        "parameters": action.parameters
                    }
                )
            
            # Wait for at least one action to complete
            if running:
                done, pending = await asyncio.wait(
                    running.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed actions
                for task in done:
                    # Find action ID for this task
                    action_id = next(
                        aid for aid, t in running.items() if t == task
                    )
                    action = graph.nodes[action_id]
                    
                    try:
                        result = await task
                        self.state.action_results[action_id] = result
                        
                        if result.status == ActionStatus.COMPLETED:
                            completed.add(action_id)
                            
                            # Store output in context if specified
                            if action.output_key and result.output is not None:
                                self.state.context[action.output_key] = result.output
                            
                            yield StreamEvent(
                                event_type="action_completed",
                                action_id=action.id,
                                action_name=action.name,
                                data={
                                    "status": result.status.value,
                                    "duration_seconds": result.duration_seconds,
                                    "output": result.output,
                                    "has_output": result.output is not None
                                }
                            )
                        else:
                            failed.add(action_id)
                            
                            yield StreamEvent(
                                event_type="action_failed",
                                action_id=action.id,
                                action_name=action.name,
                                data={
                                    "status": result.status.value,
                                    "error": result.error,
                                    "error_type": result.error_type
                                }
                            )
                            
                            # Check fail_fast
                            if plan.fail_fast:
                                yield StreamEvent(
                                    event_type="execution_stopped",
                                    data={"reason": "fail_fast enabled, action failed"}
                                )
                                return
                        
                    except Exception as e:
                        logger.error(f"Action {action_id} raised exception: {str(e)}")
                        failed.add(action_id)
                        
                        yield StreamEvent(
                            event_type="action_failed",
                            action_id=action.id,
                            action_name=action.name,
                            data={
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                        )
                    
                    finally:
                        # Remove from running
                        del running[action_id]
    
    
    async def _execute_action(self, action: Action) -> ActionResult:
        """
        Execute a single action (tool, agent, relic, etc.)
        """
        result = ActionResult(
            action_id=action.id,
            action_name=action.name,
            status=ActionStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            # Resolve parameter variables from context
            resolved_params = self._resolve_parameters(action.parameters)
            
            # Execute based on action type
            if action.type == ActionType.TOOL:
                output = await self._execute_tool(action.target, resolved_params)
                self.state.total_tool_calls += 1
            
            elif action.type == ActionType.AGENT:
                output = await self._execute_agent(action.target, resolved_params)
            
            elif action.type == ActionType.RELIC:
                output = await self._execute_relic(action.target, resolved_params)
            
            elif action.type == ActionType.LLM:
                output = await self._execute_llm(action.target, resolved_params)
                self.state.total_llm_calls += 1
            
            elif action.type == ActionType.WORKFLOW:
                output = await self._execute_workflow(action.target, resolved_params)
            
            else:
                raise ValueError(f"Unsupported action type: {action.type}")
            
            result.status = ActionStatus.COMPLETED
            result.output = output
            
        except Exception as e:
            logger.error(f"Action {action.name} failed: {str(e)}")
            result.status = ActionStatus.FAILED
            result.error = str(e)
            result.error_type = type(e).__name__
            
            if not action.skip_on_error:
                raise
        
        finally:
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()
        
        return result
    
    
    def _resolve_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve parameter variables like $wiki_data from context
        """
        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('$'):
                # Variable reference
                var_name = value[1:]
                resolved[key] = self.state.context.get(var_name)
            else:
                resolved[key] = value
        return resolved
    
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool"""
        logger.info(f"Executing tool: {tool_name}")
        # Call tool executor
        result = await self.tool_executor.execute(tool_name, parameters)
        return result
    
    
    async def _execute_agent(self, agent_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a sub-agent"""
        logger.info(f"Executing agent: {agent_name}")
        # Recursively create and execute sub-agent
        # For now, placeholder
        return {"status": "delegated", "agent": agent_name}
    
    
    async def _execute_relic(self, relic_name: str, parameters: Dict[str, Any]) -> Any:
        """Call a relic service"""
        logger.info(f"Calling relic: {relic_name}")
        # Call relic HTTP endpoint
        # For now, placeholder
        return {"status": "called", "relic": relic_name}
    
    
    async def _execute_llm(self, prompt: str, parameters: Dict[str, Any]) -> Any:
        """Execute LLM call"""
        logger.info(f"LLM call with prompt: {prompt[:50]}...")
        # Call LLM client
        result = await self.llm_client.generate(prompt, **parameters)
        return result
    
    
    async def _execute_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a workflow"""
        logger.info(f"Executing workflow: {workflow_name}")
        # Execute workflow steps
        # For now, placeholder
        return {"status": "executed", "workflow": workflow_name}
    
    
    async def _generate_execution_plan(self) -> ExecutionPlan:
        """
        Generate execution plan for current iteration using LLM
        Returns ExecutionPlan with actions to execute
        """
        # This would call LLM to generate plan based on:
        # - Current context
        # - Previous iteration results
        # - Agent goals
        # - Available tools/agents/relics
        
        # For now, return empty plan (placeholder)
        return ExecutionPlan(
            agent_name=self.agent_name,
            iteration=self.state.current_iteration,
            actions=[]
        )
    
    
    async def _should_continue(self) -> Tuple[bool, str]:
        """
        Check if agent loop should continue
        Returns (should_continue, reason)
        """
        # Check max iterations
        if self.state.current_iteration >= self.state.max_iterations:
            return False, "max_iterations_reached"
        
        # Check if goal achieved (would analyze context and results)
        # For now, simple placeholder logic
        
        # Check if any actions were executed this iteration
        current_plan = self.state.iteration_plans[-1] if self.state.iteration_plans else None
        if current_plan and len(current_plan.actions) == 0:
            return False, "no_actions_to_execute"
        
        return True, ""


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_streaming_execution():
    """Example of using AgentLoopExecutor with streaming"""
    
    # Mock dependencies
    class MockToolExecutor:
        async def execute(self, tool_name: str, params: Dict[str, Any]):
            await asyncio.sleep(0.5)  # Simulate execution
            return {"result": f"Tool {tool_name} executed", "params": params}
    
    class MockLLMClient:
        async def generate(self, prompt: str, **kwargs):
            await asyncio.sleep(0.3)  # Simulate LLM call
            return {"text": f"LLM response to: {prompt[:30]}...", "tokens": 150}
    
    # Create protocol
    protocol = AgentLoopProtocol(
        mode="autonomous",
        max_iterations=2,
        stream_action_results=True,
        allow_parallel_actions=True,
        max_parallel_actions=3
    )
    
    # Create executor
    executor = AgentLoopExecutor(
        agent_name="test_agent",
        protocol=protocol,
        tool_executor=MockToolExecutor(),
        llm_client=MockLLMClient()
    )
    
    # Execute with streaming
    print("Starting agent loop execution with streaming...\n")
    
    async for event in executor.execute_agent_loop():
        print(f"[{event.timestamp.strftime('%H:%M:%S.%f')[:-3]}] {event.event_type}")
        if event.data:
            print(f"  Data: {json.dumps(event.data, indent=4, default=str)}")
        print()


if __name__ == "__main__":
    asyncio.run(example_streaming_execution())
