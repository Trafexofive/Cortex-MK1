import yaml
from pathlib import Path
from .models import ToolDefinition, AgentDefinition, RelicConnectorDefinition

class ResourceLoader:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def scan_and_load(self):
        agents = self.load_resources("agents", AgentDefinition)
        tools = self.load_resources("tools", ToolDefinition)
        connectors = self.load_resources("connectors", RelicConnectorDefinition)
        return agents, tools, connectors

    def load_resources(self, resource_type: str, model_class):
        resources = {}
        resource_path = self.base_path / resource_type
        if not resource_path.is_dir():
            return resources

        for file_path in resource_path.glob("*.yml"):
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    resources[file_path.stem] = model_class(**data)
            except Exception as e:
                print(f"Error loading {resource_type} from {file_path}: {e}")
        return resources
