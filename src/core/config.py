from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Raíz del paquete
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    ROOT_DIR: Path = Field(default_factory=lambda: ROOT_DIR)

    # Supabase
    SUPABASE_URL: str = Field(default="https://khoikdwablpqiapxkgqx.supabase.co")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")

    # OpenAI (Motor Principal de Inteligencia y Conversación)
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o")
    OPENAI_FALLBACK_MODEL: str = Field(default="gpt-4o-mini")

    # Gemini (Únicamente utilidades secundarias: Google Search Grounding y Embeddings)
    GEMINI_API_KEY: str = Field(default="")
    ORCHESTRATOR_MODEL: str = Field(default="gpt-4o")
    WRITER_MODEL: str = Field(default="gpt-4o")
    EMBEDDING_MODEL: str = Field(default="text-embedding-004")

    # WhatsApp Cloud API
    WHATSAPP_TOKEN: str = Field(default="")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="rick_secret_verify_token_2026")
    WHATSAPP_API_VERSION: str = Field(default="v20.0")
    META_APP_SECRET: str = Field(default="")
    ALLOWED_ORIGINS: list[str] = Field(default=["*"])

    # Apify
    APIFY_API_TOKEN: str = Field(default="")

    # RapidAPI (Fallback Instagram Scraper)
    RAPIDAPI_KEY: str = Field(default="")
    RAPIDAPI_HOST: str = Field(default="instagram-scraper-stable-api.p.rapidapi.com")

    # Telegram Bot API
    TELEGRAM_BOT_TOKEN: str = Field(default="")

    # App
    APP_ENV: str = Field(default="development")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)

    # Rutas base del conocimiento
    BRAIN_DIR: Path = Field(default_factory=lambda: ROOT_DIR / "brain")
    SKILLS_DIR: Path = Field(default_factory=lambda: ROOT_DIR / "skills")
    AGENTS_FILE: Path = Field(default_factory=lambda: ROOT_DIR / "AGENTS.md")

config = Settings()
