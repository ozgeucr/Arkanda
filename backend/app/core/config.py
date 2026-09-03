from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "ARKANDA"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GEMINI_API_KEY: str
    GROQ_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

settings = Settings()