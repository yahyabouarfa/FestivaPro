from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FestivaPro Event Management"
    environment: str = "development"
    database_url: str = Field(default="mysql+pymysql://festivapro:festivapro@mysql:3306/festivapro", alias="DATABASE_URL")
    jwt_secret: str = Field(default="change-this-secret-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:8080", alias="CORS_ORIGINS")
    default_admin_email: str = Field(default="admin@festivapro.ma", alias="DEFAULT_ADMIN_EMAIL")
    default_admin_password: str = Field(default="FestivaPro2026!", alias="DEFAULT_ADMIN_PASSWORD")
    testing: bool = Field(default=False, alias="TESTING")

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore", populate_by_name=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
