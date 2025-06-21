import sounddevice as sd
import soundfile as sf
import time, os
from logger import setup_logger

SAMPLE_RATE = 16000
OWNER_FILE = "data/owner.wav"

logger = setup_logger("record_owner_voice", "logs/record_owner_voice.log", level=os.environ["LOG_LEVEL"])


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
