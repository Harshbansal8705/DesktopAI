"""Focused regression tests for the overlay's real Qt event-loop behavior."""

import threading
import time
import unittest

from src.ui.overlay import TransparentOverlayQt, app


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.overlay = TransparentOverlayQt()

    def tearDown(self):
        self.overlay.exit_callback = None
        self.overlay.close()
        app.processEvents()

    def test_start_shows_window_and_focuses_input(self):
        self.overlay.start()
        app.processEvents()

        assert self.overlay.isVisible()
        assert self.overlay.input_box.hasFocus()

    def test_worker_message_is_delivered_on_qt_main_thread(self):
        worker = threading.Thread(
            target=self.overlay.put_message,
            args=("status", "Processing...", "gold"),
        )
        worker.start()
        worker.join()
        app.processEvents()

        assert self.overlay.status_text.text() == "Processing..."

    def test_voice_button_dispatches_and_updates_state(self):
        received = []

        def record(active):
            received.append(active)
            self.overlay.put_message("recording", active)

        self.overlay.on_recording_toggled = record
        self.overlay.voice_btn.click()
        for _ in range(20):
            app.processEvents()
            if received:
                break
            time.sleep(0.01)

        assert received == [True]
        assert self.overlay.voice_btn.text() == "Stop voice"


if __name__ == "__main__":
    unittest.main()
