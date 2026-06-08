from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"

    CLAUDE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_MODEL: str = "gpt-4o"

    SQLCIPHER_DB_PATH: str = "data/personality_vault.db"
    SQLCIPHER_KEY: str = "change-me-in-production"

    GRPC_HOST: str = "[::]:50051"
    GRPC_MAX_WORKERS: int = 10

    COMPATIBILITY_THRESHOLD: float = 0.90
    VECTOR_WEIGHT: float = 0.60
    DIALOGUE_WEIGHT: float = 0.40

    FOLDER3_API_URL: str = "http://localhost:8001"
    FOLDER5_API_URL: str = "http://localhost:8002"
    INGESTION_TIMEOUT: int = 30

    DRIFT_ALERT_THRESHOLD: float = 0.15
    UPDATE_SCHEDULE_HOUR: int = 2
    UPDATE_SCHEDULE_MINUTE: int = 0

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def db_path_absolute(self) -> Path:
        p = Path(self.SQLCIPHER_DB_PATH)
        if not p.is_absolute():
            return self.PROJECT_ROOT / p
        return p


settings = Settings()
