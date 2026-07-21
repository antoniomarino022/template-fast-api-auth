from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(default=...)
    SECRET_KEY_JWT: str = Field(default=...)
    SECRET_KEY_SESSION: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def session_secret(self) -> str:
        return self.SECRET_KEY_SESSION or self.SECRET_KEY_JWT


settings = Settings()
