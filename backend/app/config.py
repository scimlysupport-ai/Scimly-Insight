"""
Central place for all app configuration.
Reads values from the .env file so we never hardcode secrets in code.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://scimly_user:scimly_pass@localhost:5432/scimly_db"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Phase 12 — Authentication
    # Used to sign/verify login sessions (JWTs). Change this to a long
    # random value in production — anyone with it can mint valid tokens.
    JWT_SECRET_KEY: str = "dev-only-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14 days

    # Where the frontend runs — OAuth callbacks redirect here once the
    # backend has finished the provider exchange.
    FRONTEND_URL: str = "http://localhost:5173"
    # Where this API is reachable from the browser — used to build the
    # redirect_uri OAuth providers send the user back to.
    BACKEND_URL: str = "http://localhost:8000"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Phase 13 — Large Dataset Support
    # Files at or above this size skip the synchronous "analyze on first
    # request" path (Phase 3) and are instead queued as a Celery task, so
    # a 300MB upload doesn't block a request thread / time out the client.
    LARGE_FILE_THRESHOLD_BYTES: int = 100 * 1024 * 1024  # 100 MB
    # Phase 2 capped uploads at 50MB outright. Phase 13 raises the ceiling
    # a large background-capable file can reach — anything between the two
    # thresholds still uploads synchronously, anything above queues.
    MAX_FILE_SIZE_BYTES: int = 1024 * 1024 * 1024  # 1 GB

    REDIS_URL: str = "redis://localhost:6379/0"
    # Separate DB index from REDIS_URL's broker so Celery's own bookkeeping
    # keys never collide with the progress hashes progress_service writes.
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
