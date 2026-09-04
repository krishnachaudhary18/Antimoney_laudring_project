"""
LaundraLens X — Central configuration using Pydantic BaseSettings.
All configuration is loaded from environment variables / .env file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root of the project
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Demo Mode ---
    demo_mode: bool = True
    demo_case_id: str = "CASE-DEMO-001"
    demo_seed: int = 42

    # --- Database ---
    database_url: str = f"sqlite:///{ROOT_DIR}/data/laundralens.db"

    # --- LLM ---
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    # --- Logging ---
    log_level: str = "INFO"

    # --- Derived paths ---
    @property
    def data_dir(self) -> Path:
        return ROOT_DIR / "data"

    @property
    def synthetic_dir(self) -> Path:
        return ROOT_DIR / "data" / "synthetic"

    @property
    def model_artifacts_dir(self) -> Path:
        return ROOT_DIR / "model_artifacts"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


# Singleton instance
settings = Settings()


class RuntimeConfig:
    """Unified runtime configuration consumed across dashboard and backend services."""
    def __init__(self):
        self.api_base: str = f"http://{settings.api_host if settings.api_host != '0.0.0.0' else 'localhost'}:{settings.api_port}/api/v1"
        self.default_hops: int = 1
        self.default_graph_mode: str = "investigation"
        self.demo_mode: bool = settings.demo_mode
        self.demo_case_id: str = settings.demo_case_id
        self.model_version: str = "1.0.0"
        self.feature_version: str = "1.0.0"


runtime_config = RuntimeConfig()
