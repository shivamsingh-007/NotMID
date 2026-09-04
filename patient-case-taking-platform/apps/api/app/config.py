from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql://notmid:notmid-local-only@localhost:5432/notmid"
    MONGODB_URL: str = "mongodb://localhost:27017"
    REDIS_URL: str = "redis://localhost:6379"
    KAFKA_BROKERS: str = "localhost:9092"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_BUCKET: str = "notmid-clinical"
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    )
    ENABLE_DEMO_ROUTES: bool = False
    READINESS_TIMEOUT_SECONDS: float = 1.5
    ASR_PROVIDER: str = "mock"  # "mock", "ai4bharat"
    ASR_MODEL_REVISION: str = "e9b71b369c048e2c6b634d4c131061c34e441179"
    ASR_DECODING: str = "ctc"
    ASR_ENGLISH_PROVIDER: str = "whisper"
    ASR_ENGLISH_MODEL: str = "openai/whisper-small.en"
    ASR_PARTIAL_INTERVAL_BYTES: int = 64_000
    ASR_MIN_SIGNAL_QUALITY: float = 0.35
    ASR_MIN_CONFIDENCE: float = 0.65
    VOICE_CONTEXT_TTL_SECONDS: int = 1_800
    VOICE_REDIS_ENABLED: bool = False
    VOICE_KAFKA_ENABLED: bool = False
    AUDIO_RETENTION_ENABLED: bool = False
    AUDIO_ENCRYPTION_KEY: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""
    OCR_PROVIDER: str = "mock"  # "mock", "paddleocr_fast", "paddleocr_vl"
    OCR_LANGUAGE: str = "en"
    OCR_ENABLE_MKLDNN: bool = False
    MODEL_WARMUP_ON_START: bool = False
    LLM_PROVIDER: str = "mock"

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
