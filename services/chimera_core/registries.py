from loader import ResourceLoader

class AgentRegistry:
    _instance = None
    _agents = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
        return cls._instance

    def load_all(self, loader: ResourceLoader):
        self._agents = loader.load_agents()
        print(f"Loaded {len(self._agents)} agents into registry.")

    def get(self, name: str):
        return self._agents.get(name)