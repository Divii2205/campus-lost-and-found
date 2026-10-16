from pydantic_settings import BaseSettings, SettingsConfigDict


# all app settings live here
# each value can be changed with an environment variable or the env file
class Settings(BaseSettings):
    app_name: str = "Campus Lost & Found API"
    environment: str = "local"
    # where the database is and how to log in to it
    database_url: str = "postgresql+psycopg://lostfound:lostfound@localhost:5432/lostfound"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# one shared settings object for the whole app
settings = Settings()
