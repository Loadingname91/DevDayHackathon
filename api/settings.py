"""Server settings, read from the environment (Railway service variables) or api/.env locally."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent / '.env', extra='ignore')

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    web_origin: str = 'http://localhost:5173'
    demo_tz: str = 'America/Denver'
    demo_now: str | None = None  # ISO datetime; when set, "now" is pinned to it (DEMO_NOW, backend.md §2.2)
    demo_gcal_fixture: bool = False  # DEMO_GCAL_FIXTURE=1: resets include the four seeded Google events (backend.md §8a fallback)
    demo_key: str | None = None  # X-Demo-Key for POST /dev/reset
    demo_workspace_id: str | None = None
    demo_record_workspace_id: str | None = None
    version: str = '0.1.0'


@lru_cache
def settings() -> Settings:
    return Settings()
