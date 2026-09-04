from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql://notmid:notmid-local-only@localhost:5432/notmid"
    DATABASE_MAINTENANCE_URL: str = ""
    MONGODB_URL: str = "mongodb://localhost:27017"
    REDIS_URL: str = "redis://localhost:6379"
    KAFKA_BROKERS: str = "localhost:9092"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_PUBLIC_ENDPOINT: str = ""
    S3_BUCKET: str = "notmid-clinical"
    S3_SERVER_SIDE_ENCRYPTION: str = ""
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    )
    ENABLE_DEMO_ROUTES: bool = False
    DOCUMENT_WORKFLOW_ENABLED: bool = False
    DOCUMENT_UPLOAD_GRANT_TTL_SECONDS: int = 300
    DOCUMENT_PREVIEW_GRANT_TTL_SECONDS: int = 300
    DOCUMENT_UPLOAD_SESSION_TTL_SECONDS: int = 900
    DOCUMENT_UPLOAD_CLEANUP_INTERVAL_SECONDS: int = 60
    DOCUMENT_UPLOAD_CLEANUP_BATCH_SIZE: int = 100
    CLAMAV_HOST: str = "localhost"
    CLAMAV_PORT: int = 3310
    CLAMAV_TIMEOUT_SECONDS: float = 30
    DOCUMENT_SCAN_MAX_BYTES: int = 10 * 1024 * 1024
    DOCUMENT_SCAN_BATCH_SIZE: int = 10
    DOCUMENT_SCAN_POLL_INTERVAL_SECONDS: float = 2
    DOCUMENT_NORMALIZATION_MAX_PAGES: int = 20
    DOCUMENT_NORMALIZATION_MAX_PIXELS_PER_PAGE: int = 25_000_000
    DOCUMENT_NORMALIZATION_MAX_TOTAL_PIXELS: int = 100_000_000
    DOCUMENT_NORMALIZATION_RENDER_DPI: int = 200
    DOCUMENT_NORMALIZATION_TIMEOUT_SECONDS: float = 30
    DOCUMENT_NORMALIZATION_BATCH_SIZE: int = 2
    DOCUMENT_NORMALIZATION_POLL_INTERVAL_SECONDS: float = 2
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
    OCR_ALLOW_COMPLEX_LAYOUT_PROVIDER: bool = False
    OCR_ARTIFACT_DATABASE: str = "notmid"
    OCR_ARTIFACT_COLLECTION: str = "document_ocr_artifacts"
    EXTRACTION_DRAFT_COLLECTION: str = "document_extraction_drafts"
    DOCUMENT_OCR_TIMEOUT_SECONDS: float = 60
    DOCUMENT_OCR_MAX_PAGE_BYTES: int = 50 * 1024 * 1024
    DOCUMENT_OCR_LEASE_SECONDS: int = 120
    DOCUMENT_OCR_MAX_ATTEMPTS: int = 3
    DOCUMENT_OCR_BATCH_SIZE: int = 2
    DOCUMENT_OCR_POLL_INTERVAL_SECONDS: float = 2
    DOCUMENT_OCR_AUTOMATION_ENABLED: bool = True
    DOCUMENT_EXTRACTION_LEASE_SECONDS: int = 60
    DOCUMENT_EXTRACTION_MAX_ATTEMPTS: int = 3
    DOCUMENT_EXTRACTION_BATCH_SIZE: int = 2
    DOCUMENT_EXTRACTION_POLL_INTERVAL_SECONDS: float = 2
    DOCUMENT_EXTRACTION_AUTOMATION_ENABLED: bool = True
    DOCUMENT_PROMOTION_BATCH_SIZE: int = 10
    DOCUMENT_PROMOTION_POLL_INTERVAL_SECONDS: float = 2
    DOCUMENT_OUTBOX_LEASE_SECONDS: int = 30
    DOCUMENT_OUTBOX_MAX_ATTEMPTS: int = 3
    DOCUMENT_OUTBOX_BATCH_SIZE: int = 25
    DOCUMENT_OUTBOX_POLL_INTERVAL_SECONDS: float = 1
    DOCUMENT_EVENT_TOPIC: str = "clinical.documents.v1"
    MODEL_WARMUP_ON_START: bool = False
    LLM_PROVIDER: str = "mock"
    SUMMARY_WORKFLOW_ENABLED: bool = False

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
