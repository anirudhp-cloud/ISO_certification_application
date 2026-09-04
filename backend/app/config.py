# App settings — database URL, storage root, Azure/OpenAI keys, CORS origins.
# Storage root/CORS still get added as those pieces get wired up.

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the project root (one level above backend/), not inside backend/,
# so it has to be located relative to this file rather than to the process cwd.
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    llm_endpoint: str
    llm_api_key: str
    llm_deployment: str
    llm_api_version: str
    # Fixed so repeated assessments of the same evidence are reproducible. Paired
    # with temperature=0 in app/ai/openai_client.py.
    llm_seed: int = 42

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Celery broker — only dereferenced when a task is actually sent via .delay()/
    # .apply_async(); calling a task function directly (as extraction does for now,
    # see tasks/extract_document.py) never touches this, so it's safe to leave
    # pointing at a Redis that isn't running yet.
    redis_url: str = "redis://localhost:6379/0"

    # Azure AI Document Intelligence — OCR fallback for scanned/image-only PDFs
    # and embedded images. Optional: native extraction (the common case) never
    # needs it, so its absence shouldn't block startup.
    doc_intelligence_endpoint: str | None = None
    doc_intelligence_key: str | None = None

    # Coverage thresholds behind the *proposed* grade (app/ai/grading.py). These pick
    # a suggestion an auditor then confirms or overrides — they are not a conformity
    # determination, and they have no basis in ISO/IEC 42001, which grades
    # conformity / OFI / minor NC / major NC rather than percentages. Configurable
    # precisely because they're a judgement call.
    grade_full_coverage_threshold: float = 90.0
    grade_partial_coverage_threshold: float = 50.0


settings = Settings()
