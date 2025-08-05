from .loader import ResourceLoader

class AgentRegistry:
    _instance = None
    _agents = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentRegistry, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def load(self, loader: ResourceLoader):
        _, self._agents, _ = loader.scan_and_load()

    def get(self, name: str):
        return self._agents.get(name)

class ToolRegistry:
    _instance = None
    _tools = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ToolRegistry, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def load(self, loader: ResourceLoader):
        _, _, self._tools = loader.scan_and_load()

    def get(self, name: str):
        return self._tools.get(name)

class ConnectorRegistry:
    _instance = None
    _connectors = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConnectorRegistry, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def load(self, loader: ResourceLoader):
        _, _, self._connectors = loader.scan_and_load()

    def get(self, name: str):
        return self._connectors.get(name)
