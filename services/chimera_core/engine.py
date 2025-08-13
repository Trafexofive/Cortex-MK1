import json
from registries import AgentRegistry
from llm_providers import manager as llm_manager

class ChimeraCore:
    def __init__(self, agent_name: str, session_id: str):
        self.session_id = session_id
        self.agent_def = AgentRegistry().get(agent_name)
        if not self.agent_def:
            raise ValueError(f"Agent '{agent_name}' not found in registry.")
        
        self.llm_provider = llm_manager.get_provider(self.agent_def.model)
        self.history = []

    def _assemble_prompt(self) -> str:
        # For B-Line, prompt is simple. A real version would use history, tools, etc.
        # This is a critical simplification for the first test.
        base_prompt = self.agent_def.system_prompt
        user_input = self.history[-1]['content']
        return f"{base_prompt}\n\nUser request: {user_input}"

    async def execute_turn(self, text_input: str) -> dict:
        self.history.append({"role": "user", "content": text_input})
        
        prompt = self._assemble_prompt()
        
        # The entire "thought-action" loop is simplified to this single call for B-Line
        llm_response_text = await self.llm_provider.generate(prompt)
        
        self.history.append({"role": "assistant", "content": llm_response_text})
        
        # The B-Line's only job is to prove this loop works.
        # It returns the raw text for the gateway to handle.
        return {"response_text": llm_response_text}