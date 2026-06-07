"""
config.py — Configurație centralizată cu pydantic-settings.

Variabilele sunt citite din fișierul .env (sau din mediu).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="svc-api/.env" if os.path.exists("svc-api/.env") else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- GraphDB ---
    graphdb_url: str = Field(default="http://localhost:7200", description="URL de bază GraphDB")
    graphdb_repository: str = Field(default="smarthome", description="Numele repository-ului GraphDB")

    # --- spaCy ---
    spacy_model: str = Field(default="en_core_web_sm", description="Modelul spaCy utilizat")

    # --- LLM ---
    llm_enabled: bool = Field(default=True, description="Activează/dezactivează apelurile LLM")
    llm_provider: str = Field(default="gemini", description="Provider LLM: ollama | gemini | openai")
    llm_model: str = Field(default="gemini-3.1-flash-lite", description="Modelul LLM utilizat")
    ollama_base_url: str = Field(default="http://localhost:11434", description="URL Ollama")
    openai_api_key: str = Field(default="", description="API Key OpenAI (opțional)")
    gemini_api_key: str = Field(default="", description="API Key Gemini (opțional)")
    gemini_model: str = Field(default="gemini-3.1-flash-lite", description="Modelul Gemini utilizat")

    # --- Paths ---
    data_input_dir: str = Field(default="data/input", description="Director fișiere text input")
    data_output_dir: str = Field(default="data/output", description="Director fișiere .ttl output")
    data_external_dir: str = Field(default="data/external", description="Director date externe")
    ontology_dir: str = Field(default="data/ontology", description="Director ontologie de bază")

    # --- App ---
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    debug: bool = Field(default=False)


settings = Settings()
