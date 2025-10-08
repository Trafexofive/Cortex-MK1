"""
==============================================================================
STREAMING EXECUTION PROTOCOL - LLM Response Parser
==============================================================================
Parse and execute actions in real-time as the LLM streams its response.

The LLM responds with a structured format that includes:
- Thoughts/reasoning (streamed as text)
- Action blocks (parsed and executed immediately when complete)
- Dependencies between actions
- Final response

Format supports:
- XML-style tags for structure
- JSON for action parameters
- Markdown for human-readable content
==============================================================================
"""

import re
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid


# ============================================================================
# PROTOCOL FORMAT DEFINITION
# ============================================================================

PROTOCOL_SPEC = """
# Cortex Agent Response Protocol v1.0

The LLM should respond in the following format:

<thought>
Your reasoning and planning here. This streams to the user in real-time.
Can be multiple paragraphs explaining your approach.
</thought>

<action type="tool" mode="async">
{
  "name": "web_scraper",
  "parameters": {
    "url": "https://example.com",
    "extract": ["title", "content"]
  },
  "output_key": "webpage_data",
  "depends_on": []
}
</action>

<action type="tool" mode="async">
{
  "name": "database_query",
  "parameters": {
    "query": "SELECT * FROM users LIMIT 10"
  },
  "output_key": "user_data",
  "depends_on": []
}
</action>

<action type="agent" mode="sync">
{
  "name": "data_analyzer",
  "parameters": {
    "webpage": "$webpage_data",
    "users": "$user_data"
  },
  "output_key": "analysis",
  "depends_on": ["web_scraper", "database_query"]
}
</action>

<response>
Based on my analysis, here are the findings:

The data shows...

**Key Insights:**
- Insight 1
- Insight 2

**Recommendations:**
1. Recommendation 1
2. Recommendation 2
</response>

## Rules:
1. <thought> blocks stream as they're generated (user sees thinking in real-time)
2. <action> blocks are parsed and executed as soon as closing tag is detected
3. Actions with no depends_on execute immediately (in parallel if mode=async)
4. Actions with depends_on wait for dependencies to complete
5. <response> is the final answer to the user (can reference action outputs)
6. Use $variable_name to reference outputs from previous actions
7. mode can be: sync, async, fire_and_forget
8. type can be: tool, agent, relic, workflow, llm

## Example with Dependencies:

<action type="tool" mode="async" id="fetch1">
{"name": "fetch_wiki", "output_key": "wiki"}
</action>

<action type="tool" mode="async" id="fetch2">
{"name": "fetch_news", "output_key": "news"}
</action>

<action type="tool" mode="sync" id="analyze">
{"name": "analyze_data", "parameters": {"data": ["$wiki", "$news"]}, "depends_on": ["fetch1", "fetch2"]}
</action>
"""


# ============================================================================
# PARSER STATE
# ============================================================================

class ParserState(str, Enum):
    """State of the streaming parser"""
    INITIAL = "initial"
    IN_THOUGHT = "in_thought"
    IN_ACTION = "in_action"
    IN_ACTION_IN_THOUGHT = "in_action_in_thought"  # Action embedded in thought
    IN_RESPONSE = "in_response"
    IN_CONTEXT_FEED = "in_context_feed"  # Context feed injection
    COMPLETE = "complete"


@dataclass
class ParsedToken:
    """A parsed token with its type and content"""
    token_type: str  # 'thought', 'action', 'response', 'text'
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class ParsedAction:
    """A complete parsed action ready for execution"""
    id: str
    type: str
    mode: str
    name: str
    parameters: Dict[str, Any]
    output_key: Optional[str] = None
    depends_on: List[str] = None
    raw_json: str = ""
    embedded_in_thought: bool = False  # Whether action was in <thought> block
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class ParsedResponse:
    """A complete parsed response"""
    content: str
    final: bool = True  # Whether this terminates execution
    variable_references: List[str] = None
    
    def __post_init__(self):
        if self.variable_references is None:
            self.variable_references = []


@dataclass  
class ParsedContextFeed:
    """A parsed context feed injection"""
    id: str
    content: str
    timestamp: datetime


# ============================================================================
# STREAMING PROTOCOL PARSER
# ============================================================================

class StreamingProtocolParser:
    """
    Parses LLM streaming responses and emits structured events
    Executes actions as soon as they're complete (don't wait for full response)
    """
    
    def __init__(self, action_executor: Optional[Callable] = None):
        self.state = ParserState.INITIAL
        self.buffer = ""
        self.action_executor = action_executor
        
        # Track parsed elements
        self.thoughts: List[str] = []
        self.actions: List[ParsedAction] = []
        self.response_parts: List[str] = []
        
        # Regex patterns
        self.tag_pattern = re.compile(r'<(/?)(\w+)([^>]*)>')
        
        # Active action being parsed
        self.current_action_buffer = ""
        self.current_action_attrs = {}
        
        # Active response attributes (for final="true/false")
        self.current_response_attrs = {}
        
        # Active context feed being parsed
        self.current_feed_buffer = ""
        self.current_feed_attrs = {}
    
    
    async def parse_stream(
        self,
        token_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[ParsedToken, None]:
        """
        Parse streaming tokens and yield structured events
        Execute actions as soon as they're complete
        """
        
        async for token in token_stream:
            self.buffer += token
            
            # Try to parse tags from buffer
            async for parsed in self._process_buffer():
                yield parsed
        
        # Process any remaining buffer
        async for parsed in self._flush_buffer():
            yield parsed
        
        self.state = ParserState.COMPLETE
    
    
    async def _process_buffer(self) -> AsyncGenerator[ParsedToken, None]:
        """Process buffer and emit parsed tokens"""
        
        while True:
            # Look for tags in buffer
            match = self.tag_pattern.search(self.buffer)
            
            if not match:
                # No complete tag found
                # If we're in thought or response, emit accumulated text
                if self.state == ParserState.IN_THOUGHT:
                    if len(self.buffer) > 50:  # Emit in chunks
                        text = self.buffer[:50]
                        self.buffer = self.buffer[50:]
                        self.thoughts.append(text)
                        yield ParsedToken(
                            token_type="thought",
                            content=text,
                            metadata={"streaming": True},
                            timestamp=datetime.now()
                        )
                    else:
                        break
                elif self.state == ParserState.IN_RESPONSE:
                    if len(self.buffer) > 50:  # Emit in chunks
                        text = self.buffer[:50]
                        self.buffer = self.buffer[50:]
                        self.response_parts.append(text)
                        yield ParsedToken(
                            token_type="response",
                            content=text,
                            metadata={"streaming": True},
                            timestamp=datetime.now()
                        )
                    else:
                        break
                else:
                    break
                continue  # Skip to next iteration
            
            # Found a tag
            is_closing = bool(match.group(1))
            tag_name = match.group(2)
            attributes = match.group(3).strip()
            
            # Text before the tag
            text_before = self.buffer[:match.start()]
            
            # Handle text before tag based on current state
            if text_before and self.state == ParserState.IN_THOUGHT:
                self.thoughts.append(text_before)
                yield ParsedToken(
                    token_type="thought",
                    content=text_before,
                    metadata={"streaming": True},
                    timestamp=datetime.now()
                )
            elif text_before and self.state == ParserState.IN_RESPONSE:
                self.response_parts.append(text_before)
                yield ParsedToken(
                    token_type="response",
                    content=text_before,
                    metadata={"streaming": True},
                    timestamp=datetime.now()
                )
            elif text_before and (self.state == ParserState.IN_ACTION or self.state == ParserState.IN_ACTION_IN_THOUGHT):
                self.current_action_buffer += text_before
            elif text_before and self.state == ParserState.IN_CONTEXT_FEED:
                self.current_feed_buffer += text_before
            
            # Update buffer (remove processed part)
            self.buffer = self.buffer[match.end():]
            
            # Handle tag
            if tag_name == "thought":
                if not is_closing:
                    self.state = ParserState.IN_THOUGHT
                else:
                    self.state = ParserState.INITIAL
            
            elif tag_name == "action":
                if not is_closing:
                    # Check if we're inside a thought
                    if self.state == ParserState.IN_THOUGHT:
                        self.state = ParserState.IN_ACTION_IN_THOUGHT
                    else:
                        self.state = ParserState.IN_ACTION
                    self.current_action_buffer = ""
                    self.current_action_attrs = self._parse_attributes(attributes)
                else:
                    # Action complete - parse and execute
                    was_in_thought = self.state == ParserState.IN_ACTION_IN_THOUGHT
                    
                    action = self._parse_action(
                        self.current_action_buffer,
                        self.current_action_attrs,
                        embedded_in_thought=was_in_thought
                    )
                    
                    if action:
                        self.actions.append(action)
                        
                        yield ParsedToken(
                            token_type="action",
                            content=action.name,
                            metadata={
                                "action": action,
                                "execute": True,
                                "embedded_in_thought": was_in_thought
                            },
                            timestamp=datetime.now()
                        )
                        
                        # Execute action immediately if no dependencies
                        if not action.depends_on and self.action_executor:
                            asyncio.create_task(self._execute_action(action))
                    
                    # Return to previous state
                    if was_in_thought:
                        self.state = ParserState.IN_THOUGHT
                    else:
                        self.state = ParserState.INITIAL
            
            elif tag_name == "response":
                if not is_closing:
                    self.state = ParserState.IN_RESPONSE
                    # Parse response attributes (final="true/false")
                    self.current_response_attrs = self._parse_attributes(attributes)
                else:
                    # Check if response is final
                    is_final = self.current_response_attrs.get('final', 'true').lower() == 'true'
                    
                    yield ParsedToken(
                        token_type="response_complete",
                        content="",
                        metadata={
                            "final": is_final,
                            "content": "".join(self.response_parts)
                        },
                        timestamp=datetime.now()
                    )
                    
                    self.state = ParserState.INITIAL if is_final else ParserState.INITIAL
            
            elif tag_name == "context_feed":
                # Parse context feed injection
                if not is_closing:
                    self.state = ParserState.IN_CONTEXT_FEED
                    self.current_feed_attrs = self._parse_attributes(attributes)
                    self.current_feed_buffer = ""
                else:
                    feed_id = self.current_feed_attrs.get('id', 'unknown')
                    yield ParsedToken(
                        token_type="context_feed",
                        content=self.current_feed_buffer,
                        metadata={
                            "feed_id": feed_id,
                            "timestamp": datetime.now()
                        },
                        timestamp=datetime.now()
                    )
                    self.state = ParserState.INITIAL
    
    
    async def _flush_buffer(self) -> AsyncGenerator[ParsedToken, None]:
        """Flush remaining buffer at end of stream"""
        if self.buffer:
            if self.state == ParserState.IN_THOUGHT:
                self.thoughts.append(self.buffer)
                yield ParsedToken(
                    token_type="thought",
                    content=self.buffer,
                    metadata={"streaming": False, "final": True},
                    timestamp=datetime.now()
                )
            elif self.state == ParserState.IN_RESPONSE:
                self.response_parts.append(self.buffer)
                yield ParsedToken(
                    token_type="response",
                    content=self.buffer,
                    metadata={"streaming": False, "final": True},
                    timestamp=datetime.now()
                )
            
            self.buffer = ""
    
    
    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse XML-style attributes"""
        attrs = {}
        # Simple attribute parsing: key="value" or key='value'
        pattern = r'(\w+)=["\']([^"\']*)["\']'
        for match in re.finditer(pattern, attr_string):
            attrs[match.group(1)] = match.group(2)
        return attrs
    
    
    def _parse_action(self, json_str: str, attrs: Dict[str, str], embedded_in_thought: bool = False) -> Optional[ParsedAction]:
        """Parse action JSON"""
        try:
            data = json.loads(json_str.strip())
            
            return ParsedAction(
                id=attrs.get('id', str(uuid.uuid4())),
                type=attrs.get('type', 'tool'),
                mode=attrs.get('mode', 'sync'),
                name=data.get('name', ''),
                parameters=data.get('parameters', {}),
                output_key=data.get('output_key'),
                depends_on=data.get('depends_on', []),
                raw_json=json_str,
                embedded_in_thought=embedded_in_thought
            )
        except json.JSONDecodeError as e:
            print(f"Failed to parse action JSON: {e}")
            return None
    
    
    async def _execute_action(self, action: ParsedAction):
        """Execute an action (if executor is provided)"""
        if self.action_executor:
            try:
                result = await self.action_executor(action)
                print(f"✅ Action '{action.name}' completed: {result}")
            except Exception as e:
                print(f"❌ Action '{action.name}' failed: {e}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def simulate_llm_stream() -> AsyncGenerator[str, None]:
    """Simulate LLM streaming response"""
    
    response = """<thought>
Let me gather information from multiple sources to answer this question. 
I'll fetch data from Wikipedia and arXiv in parallel, then analyze the combined results.
</thought>

<action type="tool" mode="async" id="fetch_wiki">
{
  "name": "web_scraper",
  "parameters": {
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
  },
  "output_key": "wiki_data"
}
</action>

<action type="tool" mode="async" id="fetch_arxiv">
{
  "name": "arxiv_search",
  "parameters": {
    "query": "machine learning",
    "max_results": 5
  },
  "output_key": "papers"
}
</action>

<action type="agent" mode="sync" id="analyze">
{
  "name": "data_analyzer",
  "parameters": {
    "wiki": "$wiki_data",
    "papers": "$papers"
  },
  "depends_on": ["fetch_wiki", "fetch_arxiv"],
  "output_key": "analysis"
}
</action>

<response>
Based on the data I gathered and analyzed, here are the key findings:

**Overview:**
Artificial intelligence is a rapidly evolving field...

**Recent Research:**
The latest papers show significant progress in...

**Recommendations:**
1. Focus on transformer architectures
2. Consider ethical implications
</response>"""
    
    # Simulate streaming character by character
    for char in response:
        yield char
        await asyncio.sleep(0.001)  # Simulate network delay


async def mock_action_executor(action: ParsedAction) -> Dict[str, Any]:
    """Mock action executor"""
    await asyncio.sleep(0.5)  # Simulate execution
    return {
        "status": "success",
        "output": f"Result from {action.name}",
        "execution_time": 0.5
    }


async def demo_streaming_parser():
    """Demonstrate streaming parser"""
    
    print("=" * 70)
    print("STREAMING PROTOCOL PARSER DEMO")
    print("=" * 70)
    print()
    
    parser = StreamingProtocolParser(action_executor=mock_action_executor)
    
    print("Parsing LLM stream...\n")
    
    async for token in parser.parse_stream(simulate_llm_stream()):
        if token.token_type == "thought":
            print(f"💭 {token.content}", end='', flush=True)
        
        elif token.token_type == "action":
            action = token.metadata['action']
            mode_emoji = {
                'sync': '⏸️',
                'async': '🔄',
                'fire_and_forget': '🔥'
            }
            print(f"\n\n🎬 ACTION: {mode_emoji.get(action.mode, '⚙️')} {action.name}")
            print(f"   Type: {action.type}")
            print(f"   Mode: {action.mode}")
            if action.depends_on:
                print(f"   Depends on: {', '.join(action.depends_on)}")
            if action.output_key:
                print(f"   Output key: ${action.output_key}")
            print(f"   Status: Executing...")
        
        elif token.token_type == "response":
            print(f"\n\n📝 RESPONSE:\n{token.content}", end='', flush=True)
    
    print("\n\n" + "=" * 70)
    print("Summary:")
    print(f"  Thoughts: {len(parser.thoughts)} chunks")
    print(f"  Actions: {len(parser.actions)} total")
    print(f"  Response: {''.join(parser.response_parts)[:50]}...")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_streaming_parser())
