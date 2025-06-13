import numpy as np
import torch

torch.set_num_threads(1)
import pyaudio
import collections, os, threading
from logger import setup_logger
from thread_executor import executor

model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad")

(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

logger = setup_logger("vad", "logs/vad.log", level=os.environ["LOG_LEVEL"])


class VoiceActivityDetector:
    def __init__(self):
        # Audio config
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SAMPLE_RATE = 16000
        self.CHUNK = int(self.SAMPLE_RATE / 10)
        self.audio = pyaudio.PyAudio()
        self.num_samples = 512
        self.recording = False
        self.listening = False
        self.lock = threading.Lock()

        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        calibration_frames = 30  # ~1.0 second
        calibration_confidences = []

        logger.info("🤫 Calibrating... stay silent for 1 second")
        for i in range(calibration_frames):
            audio_chunk = self.stream.read(self.num_samples)
            audio_int16 = np.frombuffer(audio_chunk, np.int16)
            audio_float32 = self.int2float(audio_int16)
            confidence = model(torch.from_numpy(audio_float32), self.SAMPLE_RATE).item()
            calibration_confidences.append(confidence)

        mean_noise_conf = np.mean(calibration_confidences)
        max_noise_conf = np.max(calibration_confidences)
        self.threshold = 0.7 * mean_noise_conf + 0.3 * max_noise_conf + 0.05

        logger.info("✅ Calibration done.")
        logger.info(f"→ Mean noise confidence: {mean_noise_conf:.3f}")
        logger.info(f"→ Max noise confidence: {max_noise_conf:.3f}")
        logger.info(f"→ Adaptive threshold set to: {self.threshold:.3f}\n")

    def int2float(self, sound):
        abs_max = np.abs(sound).max()
        sound = sound.astype("float32")
        if abs_max > 0:
            sound *= 1 / 32768
        return sound.squeeze()

    def record_audio(self, frames=[]):
        with self.lock:
            self.recording = True
            logger.debug("Recording started...")
            silence_frames = 0
            max_silence_frames = 60  # Stop recording after ~2 seconds of silence

            while silence_frames < max_silence_frames:
                audio_chunk = self.stream.read(self.num_samples)
                audio_int16 = np.frombuffer(audio_chunk, np.int16)
                audio_float32 = self.int2float(audio_int16)
                frames.append(audio_chunk)

                confidence = model(torch.from_numpy(audio_float32), self.SAMPLE_RATE).item()

                if confidence > self.threshold:
                    silence_frames = 0
                else:
                    silence_frames += 1

            # Convert frames to numpy array
            audio_data = np.frombuffer(b"".join(frames[:-60]), dtype=np.int16)
            self.recording = False
            logger.debug("Recording stopped...")
            return audio_data

    def on_speech(self, func):
        # Initialize a queue to store the last 10 frames
        self.listening = True
        frame_queue = collections.deque(maxlen=10)

        while self.listening:
            audio_chunk = self.stream.read(self.num_samples)
            audio_int16 = np.frombuffer(audio_chunk, np.int16)
            audio_float32 = self.int2float(audio_int16)

            # Add current frame to queue
            frame_queue.append(audio_chunk)
            if len(frame_queue) == 10:
                frame_queue.popleft()

            confidence = model(torch.from_numpy(audio_float32), self.SAMPLE_RATE).item()
            if not self.recording and confidence > self.threshold:
                logger.debug(f"🎤 Speech Detected – Confidence: {confidence:.3f}")
                # Pass the queue contents to record_audio
                audio_data = self.record_audio(list(frame_queue))

                # Send audio data if it's at least 1 second long
                if len(audio_data) / self.SAMPLE_RATE >= 1:
                    # Process in a separate thread to avoid blocking the main loop
                    future = executor.submit(func, audio_data)
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error processing audio: {e}")

        print("👋 Stopped listening")

    def stop_listening(self):
        self.listening = False

    def play_audio(self, audio_data):
        duration_seconds = len(audio_data) / self.SAMPLE_RATE
        logger.debug(
            f"Received audio data of length: {len(audio_data)} samples ({duration_seconds:.2f} seconds)"
        )

        # Play back the recorded audio
        playback_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            output=True,
        )
        playback_stream.write(audio_data.tobytes())
        playback_stream.stop_stream()
        playback_stream.close()


if __name__ == "__main__":
    # Example usage
    vad = VoiceActivityDetector()
    vad.on_speech(vad.play_audio)
