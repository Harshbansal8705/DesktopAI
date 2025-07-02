import sounddevice as sd
import soundfile as sf
import time, os
from src.utils.logger import get_logger
from src.config import config

SAMPLE_RATE = config.SAMPLE_RATE
OWNER_FILE = config.OWNER_VOICE_FILE

logger = get_logger()


def main():
    try:
        print(
            """
        You'll need to speak for 20 seconds to register your voice.
        Please find a quiet place to ensure the best recording quality.
        Press Enter to start recording...
        """
        )
        input("Press Enter to start recording...")
        start_time = time.time()
        audio = sd.rec(
            int(1 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32"
        )
        while int(time.time() - start_time) <= 20:
            print(f"\rRecording for {20 - (int(time.time() - start_time))} seconds...", end="")
            time.sleep(1)
        sd.wait()
        audio = audio.flatten()

        sf.write(OWNER_FILE, audio, SAMPLE_RATE)
        logger.info(f"\n Saved to {OWNER_FILE}")
    except Exception as e:
        logger.error(f"Error during recording: {e}")
        exit(1)


if __name__ == "__main__":
    main()
