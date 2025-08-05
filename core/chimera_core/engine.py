from .registries import AgentRegistry, ToolRegistry
import subprocess
import httpx

class ChimeraCore:
    def __init__(self, agent_name: str, session_id: str):
        self.agent_definition = AgentRegistry().get(agent_name)
        self.session_id = session_id
        self.tool_registry = ToolRegistry()

    def _assemble_prompt(self, text_input: str) -> str:
        # This is a placeholder for a more sophisticated prompt assembly
        return f"{self.agent_definition.description}\n\n{text_input}"

    def _execute_action(self, action: dict) -> str:
        tool_name = action.get("tool")
        tool_params = action.get("parameters", {})
        tool = self.tool_registry.get(tool_name)

        if not tool:
            return f"Error: Tool '{tool_name}' not found."

        if tool.runtime == "subprocess":
            # Example for a script-based tool
            command = ["python", tool.path] + list(tool_params.values())
            result = subprocess.run(command, capture_output=True, text=True)
            return result.stdout
        elif tool.runtime == "httpx":
            # Example for a connector-based tool
            url = tool.url
            response = httpx.post(url, json=tool_params)
            return response.text
        else:
            return f"Error: Unknown runtime '{tool.runtime}' for tool '{tool_name}'."

    def execute_turn(self, text_input: str) -> str:
        # In a real implementation, this would involve an LLM call
        # to decide which tool to use based on the input.
        # For now, we'll simulate a direct action.
        prompt = self._assemble_prompt(text_input)

        # Placeholder for LLM interaction
        # llm_response = llm.generate(prompt)
        # action = parse_llm_response(llm_response)
        # For now, we'll just return the prompt
        return prompt
