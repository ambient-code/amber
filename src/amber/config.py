"""Configuration management for Amber"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Configuration
    github_token: str
    postgres_url: str

    # Vertex AI Configuration (Anthropic via Model Garden)
    gcp_project_id: str
    gcp_region: str = "us-east5"

    # LLM Configuration
    llm_model: str = "claude-sonnet-4-5-20250929"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 8000

    # Service Configuration
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    log_level: str = "INFO"

    # Kubernetes Configuration
    k8s_namespace: str = "ambient-code"
    k8s_in_cluster: bool = True

    # Repository Configuration
    repo_base_path: str = "/tmp/amber-repos"

    # Autonomy Configuration
    auto_merge_enabled: bool = False
    auto_merge_min_confidence: float = 0.95
    auto_merge_learning_period: int = 10  # Number of supervised merges before enabling


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
