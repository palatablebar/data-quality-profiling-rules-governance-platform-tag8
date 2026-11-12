"""Runtime configuration. Every value can be overridden by an env var of the same name."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # --- database ---
    DB_NAME: str = "qualiscope_db"
    DB_USER: str = "qualiscope_user"
    DB_PASSWORD: str = "qualiscope_pwd"
    DB_ROOT_PASSWORD: str = "qualiscope_root_pwd"
    DB_HOST: str = "db"
    DB_PORT: int = 3306

    # --- auth ---
    JWT_SECRET: str = "change_me_to_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # --- infra ---
    REDIS_URL: str = "redis://redis:6379/0"
    ARTIFACT_DIR: str = "/data/datasets"
    QUARANTINE_DIR: str = "/data/quarantine"

    # --- limits ---
    MAX_UPLOAD_MB: int = 64
    MAX_ROWS: int = 200000
    SCAN_DAILY_QUOTA: int = 40
    RATE_WINDOW_SECONDS: int = 60
    RATE_WINDOW_MAX: int = 30

    # --- demo seed ---
    SEED_DEMO: bool = True
    SEED_ACCOUNT_ROWS: int = 5000
    SEED_ORG_ROWS: int = 300

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
