import logging
from typing import Optional

from app.core.interfaces import BaseTTSService
from app.models.models import ServiceConfigModel

logger = logging.getLogger(__name__)


def get_tts_service(config: ServiceConfigModel) -> Optional[BaseTTSService]:
    """Factory function to get the configured TTS service instance."""
    provider = getattr(config, "TTS_PROVIDER", "disabled").lower()

    # Check for disabled providers first
    if provider in ("none", "disabled", "test"):
        logger.info(
            f"TTS provider set to '{provider}'. TTS functionality will be disabled."
        )
        return None

    if provider == "kokoro":
        # Use conditional import to prevent startup crashes
        try:
            from app.tts_services.kokoro_service import KokoroTTSService

            lang_code = str(getattr(config, "KOKORO_LANG_CODE", "a"))
            cache_dir_name = str(getattr(config, "TTS_CACHE_DIR_NAME", "tts_cache"))

            logger.info(
                f"Initializing KokoroTTSService with lang_code='{lang_code}', cache_dir_name='{cache_dir_name}'"
            )
            return KokoroTTSService(
                lang_code=lang_code, cache_dir=f"static/{cache_dir_name}"
            )
        except ImportError as e:
            logger.warning(
                f"Could not import KokoroTTSService: {e}. TTS will be disabled."
            )
            return None
        except Exception as e:
            logger.critical(
                f"Failed to initialize KokoroTTSService: {e}", exc_info=True
            )
            return None
    # Add other TTS providers here in the future (e.g., 'elevenlabs', 'coqui')
    # elif provider == 'elevenlabs':
    #     from app.tts_services.elevenlabs_service import ElevenLabsTTSService
    #     return ElevenLabsTTSService(config)
    else:
        logger.warning(
            f"Unknown or unsupported TTS_PROVIDER: '{provider}'. TTS will be disabled."
        )
        return None
