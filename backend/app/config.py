from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Campus Lost & Found API"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://lostfound:lostfound@localhost:5432/lostfound"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
