# config.py
"""Centralized configuration management for Jarvis assistant."""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the Jarvis assistant."""
    
    # API Keys
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    PORCUPINE_ACCESS_KEY = os.environ.get("PORCUPINE_ACCESS_KEY")
    
    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    
    # Audio Configuration
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SIZE = SAMPLE_RATE // 10
    NUM_SAMPLES = 512
    
    # Voice Activity Detection
    CONFIDENCE_THRESHOLD = 0.5
    MAX_SILENCE_FRAMES = 60  # ~2 seconds of silence
    MAX_RECORDING_FRAMES = 20 * SAMPLE_RATE // NUM_SAMPLES  # 20 seconds max
    SPEAKER_SIMILARITY_THRESHOLD = 0.6
    
    # TTS Configuration
    TTS_VOICE = "en-US-RogerNeural"
    TTS_RATE = "+30%"
    TTS_CHUNK_SIZE = 1024
    
    # File Paths
    OWNER_VOICE_FILE = "data/owner.wav"
    WAKE_WORD_MODEL = "wakewordmodels/Jarvis_en_linux_v3_0_0.ppn"
    SCREENSHOT_FILE = "screenshot.png"
    TEMP_AUDIO_FILE = "temp.wav"
    CHECKPOINTS_DB = "checkpoints/sqlite.db"
    
    # Sound Effects
    START_SOUND_FILE = "data/soundeffects/start_recording.mp3"
    STOP_SOUND_FILE = "data/soundeffects/stop_recording.mp3"
    
    # UI Configuration
    OVERLAY_WIDTH = 400
    OVERLAY_HEIGHT = 200
    OVERLAY_X = 50
    OVERLAY_Y = 50
    MESSAGE_TIMEOUT = 5
    
    # Thread Configuration
    MAX_WORKERS = 3
    AUDIO_PROCESSING_TIMEOUT = 10
    
    # Agent Configuration
    THREAD_ID = "4"
    MAX_TOKENS_HISTORY = 10000
    
    # Whisper Configuration
    TRANSCRIPTION_MODEL = "distil-whisper-large-v3-en"
    TRANSCRIPTION_PROMPT = (
        "Please transcribe the following audio accurately, maintaining proper "
        "punctuation and formatting. This is a conversation between a user and "
        "a Desktop Assistant named \"Jarvis\". So, focus on words like 'Jarvis'."
    )

# Create a global config instance
config = Config()
