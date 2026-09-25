from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    postgres_dsn: str
    redis_url: str
    jwt_secret: str
    
    # Optional / phase 2 variables mapped with default values or Optional
    llm_provider: str = "groq"
    llm_api_key: str | None = None
    llm_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    auto_resolve_confidence_threshold: float = 0.85
    full_sweep_cron: str = "0 2 * * *"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
