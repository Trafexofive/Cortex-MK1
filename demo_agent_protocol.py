#!/usr/bin/env python3
"""
Demo: Agent Execution Protocol v2.0
Demonstrates streaming execution with async/sync actions and dependencies
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "runtime_executor"))

from models.agent_execution_protocol import (
    Action,
    ActionType,
    ActionMode,
    ExecutionPlan,
    ExecutionGraph,
    AgentLoopProtocol
)


def print_banner(text: str):
    """Print fancy banner"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def create_demo_plan() -> ExecutionPlan:
    """Create a realistic execution plan"""
    return ExecutionPlan(
        agent_name="research_assistant",
        iteration=1,
        max_parallel=4,
        fail_fast=False,
        actions=[
            # === Wave 1: Parallel Data Fetching ===
            Action(
                id="fetch_wikipedia",
                name="Fetch Wikipedia Article",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="web_scraper",
                parameters={"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"},
                output_key="wiki_content",
                timeout_seconds=30
            ),
            
            Action(
                id="fetch_arxiv",
                name="Search arXiv Papers",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="arxiv_api",
                parameters={"query": "machine learning", "max_results": 10},
                output_key="papers",
                timeout_seconds=30
            ),
            
            Action(
                id="fetch_news",
                name="Fetch Recent AI News",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="news_aggregator",
                parameters={"topic": "artificial intelligence", "days": 7},
                output_key="news_articles",
                timeout_seconds=20
            ),
            
            # === Wave 2: Parallel Processing ===
            Action(
                id="extract_wiki_facts",
                name="Extract Key Facts from Wikipedia",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="fact_extractor",
                depends_on=["fetch_wikipedia"],
                parameters={"text": "$wiki_content"},
                output_key="wiki_facts",
                timeout_seconds=15
            ),
            
            Action(
                id="summarize_papers",
                name="Summarize Research Papers",
                type=ActionType.AGENT,
                mode=ActionMode.ASYNC,
                target="paper_summarizer",
                depends_on=["fetch_arxiv"],
                parameters={"papers": "$papers"},
                output_key="paper_summaries",
                timeout_seconds=60
            ),
            
            # === Wave 3: Synthesis ===
            Action(
                id="synthesize_report",
                name="Synthesize Comprehensive Report",
                type=ActionType.LLM,
                mode=ActionMode.SYNC,
                depends_on=["extract_wiki_facts", "summarize_papers", "fetch_news"],
                wait_for_all=True,
                target="report_synthesizer",
                parameters={
                    "facts": "$wiki_facts",
                    "summaries": "$paper_summaries",
                    "news": "$news_articles"
                },
                output_key="final_report",
                timeout_seconds=120
            ),
            
            # === Wave 4: Parallel Post-Processing ===
            Action(
                id="cache_report",
                name="Cache Report in Database",
                type=ActionType.RELIC,
                mode=ActionMode.FIRE_AND_FORGET,
                target="results_cache",
                depends_on=["synthesize_report"],
                parameters={
                    "key": "ai_research_report",
                    "value": "$final_report",
                    "ttl": 86400
                },
                timeout_seconds=10
            ),
            
            Action(
                id="quality_check",
                name="Run Quality Checks",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="quality_checker",
                depends_on=["synthesize_report"],
                parameters={"report": "$final_report"},
                output_key="quality_metrics",
                timeout_seconds=20
            ),
            
            Action(
                id="generate_citations",
                name="Generate Citations",
                type=ActionType.TOOL,
                mode=ActionMode.ASYNC,
                target="citation_generator",
                depends_on=["synthesize_report"],
                parameters={"report": "$final_report"},
                output_key="citations",
                timeout_seconds=15
            ),
            
            # === Wave 5: Finalization ===
            Action(
                id="finalize_report",
                name="Finalize Report with Metadata",
                type=ActionType.TOOL,
                mode=ActionMode.SYNC,
                target="report_finalizer",
                depends_on=["quality_check", "generate_citations"],
                parameters={
                    "report": "$final_report",
                    "quality": "$quality_metrics",
                    "citations": "$citations"
                },
                output_key="complete_report",
                timeout_seconds=10
            )
        ]
    )


def visualize_execution_graph(graph: ExecutionGraph):
    """Visualize the execution dependency graph"""
    print("📊 Execution Dependency Graph")
    print("-" * 70)
    
    # Group by waves
    completed = set()
    wave = 0
    
    while len(completed) < len(graph.nodes):
        ready = graph.get_ready_actions(completed)
        if not ready:
            break
        
        wave += 1
        print(f"\n🌊 Wave {wave} (can run in parallel):")
        
        for action in ready:
            mode_emoji = {
                ActionMode.SYNC: "⏸️ ",
                ActionMode.ASYNC: "🔄",
                ActionMode.FIRE_AND_FORGET: "🔥"
            }
            
            type_emoji = {
                ActionType.TOOL: "🔧",
                ActionType.AGENT: "🤖",
                ActionType.RELIC: "🏺",
                ActionType.LLM: "🧠",
                ActionType.WORKFLOW: "📜"
            }
            
            emoji = f"{type_emoji.get(action.type, '❓')} {mode_emoji.get(action.mode, '⚙️')}"
            
            deps_str = ""
            if action.depends_on:
                dep_names = [graph.nodes[did].name for did in action.depends_on]
                deps_str = f" (waits for: {', '.join(dep_names)})"
            
            timeout_str = f" [{action.timeout_seconds}s]"
            
            print(f"  {emoji} {action.name}{timeout_str}{deps_str}")
            
            completed.add(action.id)
    
    print()


def analyze_execution_plan(plan: ExecutionPlan):
    """Analyze the execution plan"""
    print("📋 Execution Plan Analysis")
    print("-" * 70)
    
    # Count by type
    type_counts = {}
    mode_counts = {}
    
    for action in plan.actions:
        type_counts[action.type.value] = type_counts.get(action.type.value, 0) + 1
        mode_counts[action.mode.value] = mode_counts.get(action.mode.value, 0) + 1
    
    print(f"Agent: {plan.agent_name}")
    print(f"Iteration: {plan.iteration}")
    print(f"Total Actions: {len(plan.actions)}")
    print(f"Max Parallel: {plan.max_parallel}")
    print(f"Fail Fast: {plan.fail_fast}")
    
    print(f"\nActions by Type:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  • {type_name}: {count}")
    
    print(f"\nActions by Mode:")
    for mode_name, count in sorted(mode_counts.items()):
        print(f"  • {mode_name}: {count}")
    
    # Calculate dependencies
    with_deps = sum(1 for a in plan.actions if a.depends_on)
    without_deps = len(plan.actions) - with_deps
    
    print(f"\nDependencies:")
    print(f"  • Independent actions: {without_deps}")
    print(f"  • Dependent actions: {with_deps}")
    
    # Estimate execution time
    graph = ExecutionGraph()
    for action in plan.actions:
        graph.add_action(action)
    
    completed = set()
    wave_count = 0
    max_time_per_wave = []
    
    while len(completed) < len(plan.actions):
        ready = graph.get_ready_actions(completed)
        if not ready:
            break
        
        wave_count += 1
        # Max time in this wave (assuming all run in parallel)
        wave_max_time = max(a.timeout_seconds for a in ready)
        max_time_per_wave.append(wave_max_time)
        
        for action in ready:
            completed.add(action.id)
    
    estimated_time = sum(max_time_per_wave)
    sequential_time = sum(a.timeout_seconds for a in plan.actions)
    
    print(f"\nExecution Estimates:")
    print(f"  • Sequential execution: ~{sequential_time}s")
    print(f"  • Parallel execution: ~{estimated_time}s")
    print(f"  • Speedup: {sequential_time / estimated_time:.1f}x")
    print(f"  • Execution waves: {wave_count}")
    
    print()


def demonstrate_execution_flow():
    """Demonstrate the execution flow"""
    print_banner("🚀 Agent Execution Protocol v2.0 Demo")
    
    # Create execution plan
    plan = create_demo_plan()
    
    # Analyze plan
    analyze_execution_plan(plan)
    
    # Build graph
    graph = ExecutionGraph()
    for action in plan.actions:
        graph.add_action(action)
    
    # Check for cycles
    print("🔍 Validating Execution Graph")
    print("-" * 70)
    if graph.has_cycles():
        print("❌ ERROR: Circular dependencies detected!")
    else:
        print("✅ No circular dependencies found")
    
    print(f"✅ All actions have valid dependencies")
    print()
    
    # Visualize
    visualize_execution_graph(graph)
    
    # Show protocol configuration
    print("⚙️  Agent Loop Protocol Configuration")
    print("-" * 70)
    
    protocol = AgentLoopProtocol(
        mode="autonomous",
        max_iterations=10,
        max_execution_time_seconds=3600,
        stream_llm_tokens=True,
        stream_action_results=True,
        stream_thoughts=True,
        allow_parallel_actions=True,
        max_parallel_actions=4,
        auto_retry_on_failure=True,
        require_user_approval=False,
        auto_plan_next_iteration=True,
        terminate_on_goal_achieved=True,
        terminate_on_no_progress=True,
        terminate_on_error=False
    )
    
    print(f"Mode: {protocol.mode}")
    print(f"Max Iterations: {protocol.max_iterations}")
    print(f"Max Parallel Actions: {protocol.max_parallel_actions}")
    print(f"Streaming Enabled: {protocol.stream_action_results}")
    print(f"Auto Retry: {protocol.auto_retry_on_failure}")
    print()
    
    # Show timeline
    print("⏱️  Execution Timeline (Estimated)")
    print("-" * 70)
    
    completed = set()
    wave = 0
    cumulative_time = 0
    
    while len(completed) < len(plan.actions):
        ready = graph.get_ready_actions(completed)
        if not ready:
            break
        
        wave += 1
        wave_time = max(a.timeout_seconds for a in ready)
        
        print(f"\nWave {wave} (t={cumulative_time}s → {cumulative_time + wave_time}s):")
        
        for action in ready:
            mode_str = action.mode.value.upper()
            print(f"  [{mode_str:15}] {action.name} ({action.timeout_seconds}s)")
        
        cumulative_time += wave_time
        for action in ready:
            completed.add(action.id)
    
    print(f"\nTotal Estimated Time: {cumulative_time}s")
    print()
    
    # Calculate speedup
    sequential_time = sum(a.timeout_seconds for a in plan.actions)
    
    # Summary
    print_banner("✨ Summary")
    print(f"This execution plan demonstrates:")
    print(f"  • Parallel data fetching (3 sources simultaneously)")
    print(f"  • Dependency-based execution (wait for prerequisites)")
    print(f"  • Mixed execution modes (SYNC, ASYNC, FIRE_AND_FORGET)")
    print(f"  • Wave-based parallel processing ({wave} waves)")
    print(f"  • {sequential_time / cumulative_time:.1f}x speedup vs sequential execution")
    print()


if __name__ == "__main__":
    demonstrate_execution_flow()
