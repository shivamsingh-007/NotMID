from app.config import settings
from app.tts.base import TTSProvider
from app.tts.mock_provider import MockTTSProvider

_mock_provider = MockTTSProvider()


def get_active_provider() -> TTSProvider:
    if settings.TTS_PROVIDER != "mock":
        raise RuntimeError("Only the offline mock TTS provider is enabled")
    return _mock_provider
