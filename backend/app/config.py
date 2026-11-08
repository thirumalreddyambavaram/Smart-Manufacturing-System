
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate the .env file in the main project directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "yottaflex_manufacturing"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
