from pydantic import BaseSettings

class Settings(BaseSettings):
    # Neo4j Configuration
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # Redis Configuration
    redis_url: str

    # Embedding Configuration
    embedding_model: str
    embedding_dimension: int

    # Voice Configuration
    whisper_model: str
    piper_voice: str
    audio_sample_rate: int
    vad_threshold: float

    # API Configuration
    api_host: str
    api_port: int
    ws_port: int
    debug: bool

    # Performance Configuration
    max_retrieval_depth: int
    cache_ttl: int
    prediction_window: float
    parallel_workers: int

    class Config:
        env_file = ".env"

settings = Settings()
