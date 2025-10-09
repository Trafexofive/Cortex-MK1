# Runtime Executor Integration - What's Needed

## ✅ Step 1: Runtime Executor is Running

```bash
curl http://localhost:8083/health
# {"status":"healthy","service":"runtime-executor","version":"1.0.0","executors":["python","shell","docker"]}
```

**Services Now Running:**
- ✅ Storage Service (8084)
- ✅ Manifest Ingestion (8082)  
- ✅ LLM Gateway (8081)
- ✅ Container Orchestrator (8086)
- ✅ **Runtime Executor (8083)** ← NEW!
- ✅ Agent Orchestrator (8085)

## ❌ Step 2: Make LLM Output Streaming Protocol

The LLM currently outputs simple JSON. It needs to output XML streaming protocol:

### Current LLM Output (Wrong):
```json
{
  "content": "I'll help you with that...",
  "tool_calls": [{"name": "pdf_extractor", "arguments": {...}}]
}
```

### Required LLM Output (Streaming Protocol v1.1):
```xml
<thought>
I need to extract text from the PDF file.
<action type="tool" mode="async" id="extract_pdf">
{
  "name": "pdf_extractor",
  "parameters": {"pdf_path": "document.pdf"},
  "output_key": "pdf_text"
}
</action>
While that runs, I'll plan the next steps.
</thought>

<response final="true">
I've extracted the PDF content: $pdf_text
</response>
```

### How to Fix:

**Option A: Train/Prompt LLM to Output XML** (Recommended)
- Update system prompts to include Streaming Protocol format
- Show examples in few-shot prompts
- LLM directly outputs `<thought>`, `<action>`, `<response>` blocks
- Runtime Executor's `StreamingProtocolParser` parses it

**Option B: Convert JSON to XML**
- Keep current LLM output
- Add converter layer that wraps tool_calls in XML
- Less elegant, but works

## ❌ Step 3: Wire Agent Orchestrator → Runtime Executor

Current flow (my implementation):
```
User → Agent Orchestrator → LLM Gateway → Gemini
                ↓
         Container Orchestrator (for tools)
```

Correct flow (your architecture):
```
User → Agent Orchestrator → Runtime Executor
                                   ↓
                     Parse Streaming Protocol XML
                                   ↓
                  ┌────────────────┴────────────────┐
                  ↓                ↓                ↓
            LLM Gateway    Container Orch    Python/Shell Executor
          (for <action     (for <action      (for direct scripts)
           type="llm">)     type="tool">)
```

### Required Changes:

1. **Update Agent Orchestrator `/message` endpoint**:
   ```python
   # OLD (my code):
   async def send_message(...):
       llm_response = await llm_gateway.completion(...)
       if llm_response.tool_calls:
           execute_tools(...)
   
   # NEW (correct):
   async def send_message(...):
       # Forward to Runtime Executor
       async for event in runtime_executor.execute_streaming(...):
           yield event  # Stream back to user
   ```

2. **Runtime Executor handles everything**:
   - Parses streaming protocol
   - Executes `<action>` blocks
   - Manages dependencies and parallelism
   - Handles context feeds
   - Calls LLM Gateway when needed

## ❌ Step 4: LLM Integration with Streaming Protocol

Runtime Executor needs to call LLM Gateway to get streaming protocol output:

```python
# In Runtime Executor
async def call_llm_for_next_action(context):
    # Build prompt with context feeds, previous actions, etc.
    prompt = build_prompt(context)
    
    # Call LLM Gateway
    response = await llm_gateway.completion(
        messages=[{"role": "system", "content": STREAMING_PROTOCOL_INSTRUCTIONS},
                  {"role": "user", "content": prompt}]
    )
    
    # Parse streaming protocol from response
    async for event in parse_streaming_protocol(response):
        if event.type == "thought":
            yield ThoughtEvent(...)
        elif event.type == "action":
            result = await execute_action(event.action)
            yield ActionResultEvent(...)
        elif event.type == "response":
            yield ResponseEvent(...)
```

## Implementation Plan

### Phase 1: Test Runtime Executor Directly (30 mins)

Test that Runtime Executor works with manual XML input:

```bash
curl -X POST http://localhost:8083/execute/direct \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_text": "<thought>Testing</thought><action type=\"tool\">...</action>",
    "context": {}
  }'
```

### Phase 2: Add Streaming Protocol to System Prompt (1 hour)

Update LLM Gateway or Agent Orchestrator to include streaming protocol in system message:

```python
SYSTEM_PROMPT = """
You are an AI agent that communicates using the Streaming Protocol v1.1.

Your responses MUST use this format:

<thought>
Your reasoning here. You can embed actions:
<action type="tool" mode="async" id="unique_id">
{"name": "tool_name", "parameters": {...}}
</action>
</thought>

<response final="true">
Your final answer.
</response>

[Include full protocol spec here]
"""
```

### Phase 3: Update Agent Orchestrator to Use Runtime Executor (2 hours)

Replace my simple implementation with Runtime Executor calls:

1. Remove tool loading code from Agent Orchestrator
2. Remove agentic loop from Agent Orchestrator  
3. Forward requests to Runtime Executor
4. Stream results back to user

### Phase 4: End-to-End Testing (1 hour)

Test complete flow:
```
User message → Agent Orchestrator → Runtime Executor
                                          ↓
                                   LLM outputs XML
                                          ↓
                                   Parse & execute
                                          ↓
                                   Stream results back
```

## What You Get After Integration

### Capabilities Unlocked:

1. **Embedded Actions in Thoughts** ✅
   ```xml
   <thought>
   I need data.
   <action type="tool" mode="async">...</action>
   While that runs, I'll plan next steps.
   </thought>
   ```

2. **Non-Terminating Responses** ✅
   ```xml
   <response final="false">Partial results...</response>
   <thought>Continuing...</thought>
   <response final="true">Final answer</response>
   ```

3. **Context Feeds** ✅
   ```xml
   <action type="internal" mode="sync">
   {"name": "add_context_feed", "parameters": {...}}
   </action>
   ```

4. **Parallel Execution** ✅
   ```xml
   <action mode="async" id="fetch1">...</action>
   <action mode="async" id="fetch2">...</action>
   <action mode="sync" depends_on=["fetch1","fetch2">...</action>
   ```

5. **Variable References** ✅
   ```xml
   <action output_key="data">...</action>
   Later: {"param": "$data"}
   ```

## Estimated Time

- Phase 1 (test): 30 mins
- Phase 2 (prompts): 1 hour
- Phase 3 (integration): 2 hours
- Phase 4 (testing): 1 hour

**Total: 4-5 hours to full Streaming Protocol v1.1 integration**

## Current Blocker

The main blocker is **getting the LLM to output Streaming Protocol XML** instead of JSON.

Two approaches:
1. **Prompt engineering** - Show examples, be explicit about format
2. **Fine-tuning** - Train model specifically on streaming protocol format (longer term)

Once LLM outputs correct format, Runtime Executor already has everything to parse and execute it.
