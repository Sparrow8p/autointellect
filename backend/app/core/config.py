from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    # Без значения по умолчанию: приложение не стартует без явно заданного секрета.
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # Ставка нормо-часа, ₽ (заглушка до получения реальных данных).
    labor_rate_per_hour: int = Field(default=2000, gt=0)
    # Расходы на владение авто в год — доля цены авто (заглушка: 0.08 = 8%).
    annual_running_costs_rate: float = Field(default=0.08, gt=0, le=1)
    # JSON-список в переменной окружения, например: ["http://localhost:3000"]
    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
