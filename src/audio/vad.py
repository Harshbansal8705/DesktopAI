"""Backward-compatible name for the active listener implementation.

The former standalone implementation duplicated Listener and initialized the
Linux-only wake-word stack at import time. Keeping one implementation ensures
that platform and wake-word guards apply consistently.
"""

from src.audio.listener import Listener


class VoiceActivityDetector(Listener):
    """Compatibility alias for callers that use the former VAD class."""
