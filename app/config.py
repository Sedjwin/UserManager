from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8005

    secret_key: str = "change-me-in-production"
    token_expire_hours: int = 12

    database_url: str = "sqlite+aiosqlite:///./data/usermanager.db"

    # Seeded on first run if no admin exists
    admin_username: str = "admin"
    admin_password: str = "changeme"

    # Used by other services (AgentManager etc.) to create/delete agent principals
    service_key: str = "change-me-service-key"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
