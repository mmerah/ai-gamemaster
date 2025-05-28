import logging
import os
import uuid
import numpy as np
import soundfile as sf
from typing import List, Optional, Dict
from flask import current_app, has_app_context

from app.core.interfaces import BaseTTSService

logger = logging.getLogger(__name__)

try:
    from kokoro import KPipeline
except ImportError:
    logger.warning("Kokoro library not installed. TTS functionality will be disabled.")
    KPipeline = None


class KokoroTTSService(BaseTTSService):
    """TTS Service implementation using Kokoro."""

    # Hardcoded English voices for now. Can be expanded.
    # Format: { "id": "kokoro_voice_id", "name": "User Friendly Name (kokoro_voice_id)" }
    # Using American English voices primarily.
    KOKORO_ENGLISH_VOICES = [
        {"id": "af_heart", "name": "Kokoro Heart (US Female)"},
        {"id": "af_bella", "name": "Bella (US Female)"},
        {"id": "af_nova", "name": "Nova (US Female)"},
        {"id": "am_onyx", "name": "Onyx (US Male)"},
        {"id": "am_michael", "name": "Michael (US Male)"},
        {"id": "am_puck", "name": "Puck (US Male)"},
        # British English examples (would require lang_code='b' for pipeline)
        # {"id": "bf_emma", "name": "Emma (UK Female)"},
        # {"id": "bm_george", "name": "George (UK Male)"},
    ]

    def __init__(self, lang_code: str = 'a', cache_dir: str = 'static/tts_cache'):
        self.lang_code = lang_code
        self.pipeline = None
        self.cache_dir_name = cache_dir.split('/')[-1]  # e.g., "tts_cache"
        
        # Construct full path based on Flask's static folder
        # This assumes cache_dir is relative to the 'static' folder
        if has_app_context():
            self.full_cache_dir = os.path.join(current_app.static_folder, self.cache_dir_name)
        else:
            # Fallback for testing or when no Flask app context is available
            self.full_cache_dir = os.path.join(os.getcwd(), cache_dir)
            logger.warning("No Flask app context available. Using fallback TTS cache directory: %s", self.full_cache_dir)
        
        if KPipeline:
            try:
                logger.info(f"Initializing Kokoro KPipeline with lang_code='{self.lang_code}'...")
                self.pipeline = KPipeline(lang_code=self.lang_code)
                logger.info("Kokoro KPipeline initialized successfully.")
                os.makedirs(self.full_cache_dir, exist_ok=True)
                logger.info(f"TTS cache directory ensured at: {self.full_cache_dir}")
            except Exception as e:
                logger.error(f"Failed to initialize Kokoro KPipeline: {e}", exc_info=True)
                self.pipeline = None
        else:
            logger.warning("Kokoro KPipeline could not be imported. TTS disabled.")

    def synthesize_speech(self, text: str, voice_id: str) -> Optional[str]:
        if not self.pipeline:
            logger.error("Kokoro pipeline not initialized. Cannot synthesize speech.")
            return None
        if not text:
            logger.warning("Empty text provided for TTS synthesis.")
            return None
        
        # Validate voice_id
        if not any(v['id'] == voice_id for v in self.KOKORO_ENGLISH_VOICES):
            logger.warning(f"Voice ID '{voice_id}' not found in available English voices. Using default 'af_heart'.")
            voice_id = "af_heart"

        try:
            logger.info(f"Synthesizing speech with Kokoro: voice='{voice_id}', text='{text[:50]}...'")
            
            # Kokoro's generator yields segments at natural breaks (sentences, paragraphs)
            # We need to concatenate all segments to get the full narrative
            audio_segments = []
            segment_count = 0
            
            # Collect all audio segments from the generator
            # The generator yields (graphemes, phonemes, audio_tensor)
            for _gs, _ps, audio_segment in self.pipeline(text, voice=voice_id):
                audio_segments.append(audio_segment)
                segment_count += 1
                logger.debug(f"Collected audio segment {segment_count}")
            
            if not audio_segments:
                logger.error("Kokoro synthesis did not yield any audio data.")
                return None
            
            # Concatenate all segments into a single audio array
            if len(audio_segments) == 1:
                audio_data = audio_segments[0]
            else:
                logger.info(f"Concatenating {len(audio_segments)} audio segments...")
                audio_data = np.concatenate(audio_segments)
            
            logger.info(f"Generated audio with {len(audio_segments)} segment(s), total length: {len(audio_data)/24000:.2f} seconds")

            filename = f"{uuid.uuid4().hex}.wav"
            full_output_path = os.path.join(self.full_cache_dir, filename)
            
            sf.write(full_output_path, audio_data, 24000)  # Kokoro default sample rate is 24kHz
            
            # Return path relative to static folder (e.g., "tts_cache/filename.wav")
            relative_path = os.path.join(self.cache_dir_name, filename).replace("\\", "/")
            logger.info(f"Speech synthesized and saved to {full_output_path}. Relative path: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Error during Kokoro speech synthesis: {e}", exc_info=True)
            return None

    def get_available_voices(self, lang_code: Optional[str] = None) -> List[Dict[str, str]]:
        # For now, returns only configured English voices.
        # lang_code param is for future expansion if we support multiple KPipeline instances.
        if lang_code is None or lang_code == self.lang_code:
            return self.KOKORO_ENGLISH_VOICES
        return []
