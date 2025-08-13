import yaml
import os
from pathlib import Path
from typing import Dict, Any
from models import AgentDefinition, ToolDefinition

class ResourceLoader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def load_agents(self) -> Dict[str, AgentDefinition]:
        agents = {}
        agents_root = self.base_path / 'agents'
        for agent_dir in agents_root.iterdir():
            if agent_dir.is_dir():
                # Find the primary YAML file for the agent module
                # e.g., in 'demurge/' find 'demurge.yml'
                agent_file = agent_dir / f"{agent_dir.name}.yml"
                if agent_file.exists():
                    try:
                        with open(agent_file, 'r') as f:
                            data = yaml.safe_load(f)
                            agent_def = AgentDefinition(**data)
                            agents[agent_def.name] = agent_def
                    except Exception as e:
                        print(f"Error loading agent from {agent_file}: {e}")
        return agents