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
    # Google Calendar connection (backend.md §8a; what to create in Google Cloud: the comment block in api/routes/connect.py).
    # All three unset (or empty) = "not configured": POST /connect/google/start answers 503 google_not_configured.
    google_client_id: str | None = None      # GOOGLE_CLIENT_ID
    google_client_secret: str | None = None  # GOOGLE_CLIENT_SECRET (server only)
    google_redirect_uri: str | None = None   # GOOGLE_REDIRECT_URI: https://<railway-host>/api/connect/google/callback
    connect_state_secret: str | None = None  # CONNECT_STATE_SECRET: signs the OAuth `state`; falls back to the service-role key
    demo_gcal_email: str = 'sam@example.com'  # DEMO_GCAL_EMAIL: the account shown when DEMO_GCAL_FIXTURE=1 connects the fixture
    demo_key: str | None = None  # X-Demo-Key for POST /dev/reset
    demo_workspace_id: str | None = None
    demo_record_workspace_id: str | None = None
    demo_open: bool = False  # DEMO_OPEN=1: POST /demo/enter signs anyone in as the demo user (open-room demo)
    demo_open_email: str = 'sam@quilt.demo'
    version: str = '0.1.0'


@lru_cache
def settings() -> Settings:
    return Settings()
