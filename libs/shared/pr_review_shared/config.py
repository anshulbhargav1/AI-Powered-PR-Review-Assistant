from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/pr_review"

    # Temporal
    temporal_address: str = "temporal:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "pr-review-task-queue"

    # Groq (OpenAI-compatible)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com"

    # VCS
    vcs_mode: str = "mock"  # "mock" | "live"
    github_token: str = ""
    github_webhook_secret: str = ""
    gitlab_token: str = ""
    gitlab_webhook_secret: str = ""
    gitlab_base_url: str = "https://gitlab.com"

    # Dashboard
    dashboard_base_url: str = "http://localhost:5173"

    # Misc
    log_level: str = "INFO"
    env: str = "development"


settings = Settings()
