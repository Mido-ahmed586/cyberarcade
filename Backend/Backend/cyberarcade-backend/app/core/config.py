from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "CyberArcade"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:5173"
    # Where this backend is reachable from the user's browser. Used to build
    # the sandbox-payment URL the frontend redirects to. In prod set this to
    # your public HTTPS URL; locally the default is fine.
    BACKEND_PUBLIC_URL: str = "http://127.0.0.1:8000"

    # Email (SMTP)
    SMTP_HOST: str = "smtp-mail.outlook.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # AI / Chatbot provider
    # Set AI_PROVIDER=ollama to use a local Ollama instance instead.
    AI_PROVIDER: str = "openai-compatible"
    OPENAI_COMPATIBLE_BASE_URL: str = "https://api.groq.com/openai/v1"
    OPENAI_COMPATIBLE_API_KEY: str = ""
    OPENAI_COMPATIBLE_MODEL: str = "llama-3.1-8b-instant"
    # Ollama (only used when AI_PROVIDER=ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3"

    @property
    def ai_base_url(self) -> str:
        if self.AI_PROVIDER == "ollama":
            return self.OLLAMA_BASE_URL
        return self.OPENAI_COMPATIBLE_BASE_URL

    @property
    def ai_api_key(self) -> str:
        if self.AI_PROVIDER == "ollama":
            return "ollama"
        return self.OPENAI_COMPATIBLE_API_KEY

    @property
    def ai_model(self) -> str:
        if self.AI_PROVIDER == "ollama":
            return self.OLLAMA_MODEL
        return self.OPENAI_COMPATIBLE_MODEL

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_USER and self.SMTP_PASSWORD)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
