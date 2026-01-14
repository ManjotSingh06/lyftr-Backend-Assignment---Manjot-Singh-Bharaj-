from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    webhook_secret: Optional[str] = None
    database_url: str = "sqlite+aiosqlite:///./app.db"
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        v_up = v.upper()
        if v_up not in ("INFO", "DEBUG"):
            raise ValueError("log_level must be INFO or DEBUG")
        return v_up

    @property
    def ready(self) -> bool:
        return bool(self.webhook_secret and self.webhook_secret.strip())

settings = Settings()
