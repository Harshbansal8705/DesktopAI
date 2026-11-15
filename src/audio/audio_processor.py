# audio_processor.py
"""Audio processing functionality separated from the main assistant."""

import os

import numpy as np
import soundfile as sf
from groq import Groq

from src.config import config
from src.utils.logger import get_logger

logger = get_logger()


class AudioProcessor:
    """Handles audio transcription and processing."""

    def __init__(self):
        self.groq_client = Groq(api_key=config.GROQ_API_KEY, timeout=config.TRANSCRIPTION_TIMEOUT)
        self.last_error: str | None = None

    def process_audio(self, audio_data):
        """Process audio data and return transcription."""
        self.last_error = None
        temp_file = config.TEMP_AUDIO_FILE

        try:
            # Both sounddevice's manual recorder and the Linux listener produce
            # signed 16-bit mono samples. Persist an explicit PCM WAV accepted
            # by Groq's transcription endpoint.
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if not len(audio_array):
                raise ValueError("The recording is empty.")
            duration = len(audio_array) / config.SAMPLE_RATE
            rms = float(np.sqrt(np.mean(np.square(audio_array.astype(np.float32) / np.iinfo(np.int16).max))))
            logger.info(
                "Preparing transcription: %.2fs, %d samples, %d bytes, PCM_16 mono/%dHz, rms=%.5f",
                duration,
                len(audio_array),
                audio_array.nbytes,
                config.SAMPLE_RATE,
                rms,
            )
            if rms < config.SILENCE_RMS_THRESHOLD:
                raise ValueError("The recording is silent or below the configured microphone threshold.")
            sf.write(temp_file, audio_array, config.SAMPLE_RATE, subtype="PCM_16")

            with open(temp_file, "rb") as f:
                payload = f.read()
                logger.info(
                    "Sending %d-byte WAV to Groq transcription model %s.", len(payload), config.TRANSCRIPTION_MODEL
                )
                transcription = self.groq_client.audio.transcriptions.create(
                    file=("jasper-recording.wav", payload),
                    model=config.TRANSCRIPTION_MODEL,
                    response_format="text",
                    prompt=config.TRANSCRIPTION_PROMPT,
                    language=config.TRANSCRIPTION_LANGUAGE,
                )
                text = getattr(transcription, "text", transcription)
                text = str(text).strip()
                if not text:
                    raise ValueError("Groq returned an empty transcription.")
                logger.info("Groq transcription completed (%d characters).", len(text))
                return text

        except Exception as e:
            self.last_error = str(e)
            logger.error("Transcription failed: %s", self.last_error)
            return None
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
