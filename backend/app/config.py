import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AION Materials Discovery Platform"
    debug: bool = True
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://aion:aion_pass@db:5432/aion"
        if os.getenv("DOCKER_ENV") == "true"
        else "sqlite:///./aion.db",
    )
    docker_env: bool = os.getenv("DOCKER_ENV") == "true"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    mp_api_key: str = ""
    secret_key: str = "aion-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    model_config = {"env_file": ".env"}


settings = Settings()
