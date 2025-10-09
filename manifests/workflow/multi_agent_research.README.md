# Multi-Agent Research Workflow

**Research workflow with hierarchical agent coordination**

## Overview

A research workflow that delegates to the research_orchestrator agent, analyzes findings, and caches results. Demonstrates hierarchical agent coordination with actual implementations.

## Trigger

**Type:** Manual  
**Event:** `research.query`

### Parameters

- `query` (string, required) - Research query
- `max_sources` (integer, optional) - Maximum sources to search (default: 5)

## Steps

1. **research_task** - Delegate to research_orchestrator agent
2. **analyze_findings** - Analyze sentiment of research findings
3. **cache_results** - Store results in research cache with TTL

## Outputs

- `findings` - Research findings from orchestrator
- `cache_key` - Cached results key (optional)
- `sentiment` - Overall sentiment of findings (optional)

## Dependencies

### Agents
- `research_orchestrator` - Master research coordination agent
  - Automatically delegates to sub-agents (web_researcher, etc.)
  - Uses local tools (pdf_extractor)
  - Uses local relics (research_cache)

### Tools
- `sentiment_analyzer` - Sentiment analysis of findings

### Relics
- `research_cache` - Result caching (from research_orchestrator agent)

## Usage

Trigger research on a topic:

```json
{
  "query": "artificial intelligence applications in healthcare",
  "max_sources": 10
}
```

Expected output:
```json
{
  "findings": "Research findings...",
  "cache_key": "research:artificial intelligence...:1234567890",
  "sentiment": "neutral"
}
```

## Workflow Behavior

The research_orchestrator agent:
1. Analyzes the query
2. Delegates to specialized sub-agents:
   - web_researcher: Searches web sources
   - Additional sub-agents as configured
3. Uses local tools:
   - pdf_extractor: Extracts content from PDFs
4. Aggregates and synthesizes results
5. Returns comprehensive findings

The workflow then:
1. Analyzes sentiment of findings
2. Caches results for 1 hour (3600 seconds)

## Configuration

- **Timeout:** 600 seconds (10 minutes)
- **Retry Policy:** Exponential backoff, max 2 attempts
- **Error Handling:** Continue on step failure
- **Cache TTL:** 3600 seconds (1 hour)
- **Observability:** INFO level logging, tracing enabled

## Hierarchical Delegation

This workflow demonstrates fractal composition:
```
multi_agent_research (workflow)
  └── research_orchestrator (agent)
      ├── web_researcher (sub-agent)
      ├── pdf_extractor (local tool)
      └── research_cache (local relic)
```

## Error Handling

- Research task failure: Abort (critical operation)
- Sentiment analysis failure: Continue (optional analysis)
- Cache storage failure: Continue (optional optimization)

## Manifest

- **Path:** `workflow/multi_agent_research.workflow.yml`
- **Version:** 1.0
- **State:** stable
- **Author:** PRAETORIAN_CHIMERA
