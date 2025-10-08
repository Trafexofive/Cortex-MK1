"""
==============================================================================
STREAMING EXECUTION PROTOCOL v1.1 - Examples
==============================================================================
Examples demonstrating the new features from June 2024 draft:
1. Actions inside thoughts
2. Non-terminating responses
3. Context feeds
4. Internal actions
==============================================================================
"""

import asyncio
from typing import AsyncGenerator


# ============================================================================
# Example 1: Actions Inside Thoughts
# ============================================================================

EXAMPLE_1_ACTIONS_IN_THOUGHTS = """
<thought>
I need to research this topic thoroughly. Let me start by fetching data 
from multiple sources in parallel.

<action type="tool" mode="async" id="fetch_wiki">
{
  "name": "web_scraper",
  "parameters": {"url": "https://en.wikipedia.org/wiki/AI"}
}
</action>

While Wikipedia is loading, I'll also fetch recent research papers.

<action type="tool" mode="async" id="fetch_arxiv">
{
  "name": "arxiv_search",
  "parameters": {"query": "artificial intelligence", "max_results": 10}
}
</action>

Both of these are now running in the background while I continue thinking.
Next, I'll need to analyze the combined results once they're ready.
</thought>

<action type="agent" mode="sync" id="analyze">
{
  "name": "data_analyzer",
  "parameters": {
    "wiki": "$fetch_wiki",
    "papers": "$fetch_arxiv"
  },
  "depends_on": ["fetch_wiki", "fetch_arxiv"],
  "output_key": "analysis"
}
</action>

<response final="true">
Based on my comprehensive analysis:

$analysis

## Key Findings
- Modern AI focuses on transformer architectures
- Ethical considerations are increasingly important
- Multi-modal models are the new frontier
</response>
"""


# ============================================================================
# Example 2: Non-Terminating Responses
# ============================================================================

EXAMPLE_2_NON_TERMINATING_RESPONSES = """
<thought>
This is a complex research task. I'll provide updates as I progress
through multiple phases.
</thought>

<action type="tool" mode="async" id="phase1_data">
{
  "name": "data_collector",
  "parameters": {"sources": ["wiki", "arxiv", "news"], "topic": "AI"}
}
</action>

<response final="false">
## Phase 1: Data Collection

I've started collecting data from 3 sources. Initial results show:
- 15 Wikipedia articles found
- 47 research papers from arXiv
- 23 recent news articles

**Status:** Data collection in progress...
</response>

<thought>
Now I'll analyze the patterns across all sources.
</thought>

<action type="agent" mode="sync" id="phase2_analysis">
{
  "name": "pattern_analyzer",
  "parameters": {"data": "$phase1_data"},
  "depends_on": ["phase1_data"]
}
</action>

<response final="false">
## Phase 2: Pattern Analysis

Analysis complete. I've identified several key themes:
1. Rapid advancement in model efficiency
2. Growing focus on AI safety
3. Democratization of AI tools

**Status:** Moving to detailed insights...
</response>

<thought>
Finally, I'll generate comprehensive recommendations based on all findings.
</thought>

<action type="llm" mode="sync" id="phase3_recommendations">
{
  "name": "generate_recommendations",
  "parameters": {
    "analysis": "$phase2_analysis",
    "context": "enterprise AI adoption"
  },
  "depends_on": ["phase2_analysis"]
}
</action>

<response final="true">
## Final Report: AI Landscape Analysis

### Executive Summary
Based on comprehensive analysis of 85 sources across academic, 
encyclopedic, and news domains:

$phase3_recommendations

### Conclusion
The AI field is evolving rapidly with a strong emphasis on practical
applications, safety, and accessibility.

**Report Status:** COMPLETE
</response>
"""


# ============================================================================
# Example 3: Context Feeds
# ============================================================================

# Agent manifest configuration
EXAMPLE_3_CONTEXT_FEEDS_MANIFEST = """
# agent.yml
name: research_agent
version: 1.1.0

context_feeds:
  # On-demand feeds
  - id: "current_datetime"
    type: "on_demand"
    source:
      type: "internal"
      action: "system_clock"
      params:
        format: "ISO8601"
        timezone: "UTC"
  
  - id: "repo_structure"
    type: "on_demand"
    cache_ttl: 3600
    max_tokens: 2000
    source:
      type: "tool"
      name: "git_tree"
      params:
        path: "${REPO_ROOT}"
        max_depth: 3
  
  # Periodic feeds
  - id: "system_metrics"
    type: "periodic"
    interval: 30
    source:
      type: "tool"
      name: "system_monitor"
      params:
        metrics: ["cpu", "memory", "disk"]
  
  - id: "service_health"
    type: "periodic"
    interval: 60
    source:
      type: "relic"
      name: "health_check_service"
      params:
        services: ["api", "database", "cache"]

  # LLM-generated feeds
  - id: "codebase_summary"
    type: "on_demand"
    cache_ttl: 1800
    source:
      type: "llm"
      name: "summarize"
      params:
        prompt: "Summarize the main purpose and architecture"
        context: "$repo_structure"
        model: "gemini-1.5-flash"
"""

# Context feed injection at runtime
EXAMPLE_3_CONTEXT_FEEDS_RUNTIME = """
<context_feed id="current_datetime">
2024-06-15T14:32:18Z
</context_feed>

<context_feed id="system_metrics">
{
  "cpu": 45.2,
  "memory": 62.8,
  "disk": 78.3,
  "timestamp": "2024-06-15T14:32:18Z"
}
</context_feed>

<thought>
I can see the system is at moderate load (CPU: 45%, Memory: 63%). 
I'll proceed with the analysis, but I'll use lighter-weight tools
to avoid overwhelming the system.
</thought>

<action type="tool" mode="async" id="lightweight_analysis">
{
  "name": "quick_analyzer",
  "parameters": {
    "data": "$input_data",
    "mode": "fast",
    "timestamp": "$current_datetime"
  }
}
</action>
"""


# ============================================================================
# Example 4: Internal Actions (Dynamic Feed Management)
# ============================================================================

EXAMPLE_4_INTERNAL_ACTIONS = """
<thought>
I'm encountering errors in the workflow. Let me add a context feed
to monitor recent error logs so I can debug more effectively.
</thought>

<action type="internal" mode="sync" id="add_error_feed">
{
  "name": "add_context_feed",
  "parameters": {
    "id": "recent_errors",
    "type": "on_demand",
    "source": {
      "type": "relic",
      "name": "log_service",
      "params": {
        "filter": "ERROR",
        "since": "1h",
        "max_entries": 50
      }
    },
    "max_tokens": 1000
  }
}
</action>

<thought>
Now I can access the error logs via $recent_errors. Let me analyze them.
</thought>

<action type="agent" mode="sync" id="analyze_errors">
{
  "name": "error_analyzer",
  "parameters": {
    "logs": "$recent_errors",
    "context": "$system_metrics"
  },
  "depends_on": ["add_error_feed"]
}
</action>

<response final="false">
## Error Analysis

I've identified the root cause:
$analyze_errors

I'll now increase monitoring frequency and add debug context.
</response>

<action type="internal" mode="sync" id="update_metrics_feed">
{
  "name": "update_context_feed",
  "parameters": {
    "id": "system_metrics",
    "interval": 10
  }
}
</action>

<action type="internal" mode="sync" id="add_debug_feed">
{
  "name": "add_context_feed",
  "parameters": {
    "id": "debug_trace",
    "type": "periodic",
    "interval": 5,
    "source": {
      "type": "tool",
      "name": "debug_tracer",
      "params": {"level": "verbose"}
    }
  }
}
</action>

<thought>
With enhanced monitoring in place, I'll attempt the operation again.
</thought>

<action type="workflow" mode="sync" id="retry_operation">
{
  "name": "main_workflow",
  "parameters": {"retry": true}
}
</action>

<response final="true">
## Resolution

The operation completed successfully after:
1. Identifying the error pattern
2. Increasing monitoring frequency
3. Adding debug traces
4. Retrying with enhanced observability

**Cleaning up temporary feeds...**
</response>

<action type="internal" mode="fire_and_forget" id="cleanup">
{
  "name": "remove_context_feed",
  "parameters": {"id": "debug_trace"}
}
</action>
"""


# ============================================================================
# Example 5: Combined Advanced Features
# ============================================================================

EXAMPLE_5_COMBINED = """
<context_feed id="current_datetime">
2024-06-15T16:45:00Z
</context_feed>

<context_feed id="system_metrics">
{"cpu": 28.5, "memory": 45.2}
</context_feed>

<thought>
Starting comprehensive system analysis. The system looks healthy
(low load at $system_metrics), so I can run intensive operations.

Let me start data collection immediately while I plan the analysis.

<action type="tool" mode="async" id="collect_logs">
{
  "name": "log_aggregator",
  "parameters": {"since": "24h", "levels": ["ERROR", "WARN"]}
}
</action>

<action type="tool" mode="async" id="collect_metrics">
{
  "name": "metrics_collector",
  "parameters": {"period": "24h", "resolution": "1h"}
}
</action>

While those are running, I'll add a context feed for database status
to ensure I have real-time visibility.
</thought>

<action type="internal" mode="sync" id="add_db_feed">
{
  "name": "add_context_feed",
  "parameters": {
    "id": "database_status",
    "type": "periodic",
    "interval": 30,
    "source": {
      "type": "relic",
      "name": "postgres_monitor",
      "params": {"metrics": ["connections", "query_time", "locks"]}
    }
  }
}
</action>

<response final="false">
## Preliminary Analysis - $current_datetime

**System Status:** Healthy (CPU: 28%, Memory: 45%)

**Data Collection:** In progress
- Log aggregation: Running
- Metrics collection: Running
- Database monitoring: Active (30s intervals)

I'll provide detailed findings once data collection completes.
</response>

<thought>
Now that I have real-time database visibility via $database_status,
I can correlate application performance with database health.
</thought>

<action type="agent" mode="sync" id="correlate_data">
{
  "name": "correlation_analyzer",
  "parameters": {
    "logs": "$collect_logs",
    "metrics": "$collect_metrics",
    "db_status": "$database_status"
  },
  "depends_on": ["collect_logs", "collect_metrics", "add_db_feed"]
}
</action>

<response final="false">
## Analysis Update

**Correlation Findings:**
$correlate_data

**Next Steps:** Generating recommendations...
</response>

<action type="llm" mode="sync" id="generate_report">
{
  "name": "report_generator",
  "parameters": {
    "analysis": "$correlate_data",
    "format": "executive_summary",
    "model": "gemini-1.5-pro"
  },
  "depends_on": ["correlate_data"]
}
</action>

<response final="true">
## Final System Health Report
**Generated:** $current_datetime

$generate_report

---

**Monitoring:** Database status feed will continue running.
Use `remove_context_feed` to disable when no longer needed.
</response>
"""


if __name__ == "__main__":
    print(__doc__)
    print("\n" + "=" * 80)
    print("STREAMING PROTOCOL v1.1 - FEATURE EXAMPLES")
    print("=" * 80)
    
    print("\n1. Actions Inside Thoughts")
    print("-" * 80)
    print("Allows starting actions while still reasoning")
    print("Benefits: Earlier execution, natural interleaving")
    
    print("\n2. Non-Terminating Responses")
    print("-" * 80)
    print("Agent continues after partial responses")
    print("Benefits: Progressive updates, compute-driven approach")
    
    print("\n3. Context Feeds")
    print("-" * 80)
    print("Dynamic context injection from various sources")
    print("Benefits: Up-to-date info without explicit tool calls")
    
    print("\n4. Internal Actions")
    print("-" * 80)
    print("LLM can modify its own execution environment")
    print("Benefits: Dynamic adaptation, self-management")
    
    print("\n" + "=" * 80)
    print("See the constants above for detailed examples")
    print("=" * 80)
