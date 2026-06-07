"""
config.py — Configurație centralizată cu pydantic-settings.

Variabilele sunt citite din fișierul .env (sau din mediu).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- GraphDB ---
    graphdb_url: str = Field(default="http://localhost:7200", description="URL de bază GraphDB")
    graphdb_repository: str = Field(default="smarthome", description="Numele repository-ului GraphDB")

    # --- spaCy ---
    spacy_model: str = Field(default="en_core_web_sm", description="Modelul spaCy utilizat")

    # --- LLM ---
    llm_enabled: bool = Field(default=False, description="Activează/dezactivează apelurile LLM")
    llm_provider: str = Field(default="ollama", description="Provider LLM: ollama | openai")
    llm_model: str = Field(default="llama3", description="Modelul LLM utilizat")
    ollama_base_url: str = Field(default="http://localhost:11434", description="URL Ollama")
    openai_api_key: str = Field(default="", description="API Key OpenAI (opțional)")

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
