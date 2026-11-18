import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QCloseEvent, QMouseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from src.ui.overlay import TransparentOverlayQt


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_window_dragging():
    _get_app()
    overlay = TransparentOverlayQt(message_timeout=0)
    try:
        overlay.move(100, 100)
        start_pos = overlay.frameGeometry().topLeft()

        press_event = QMouseEvent(
            QMouseEvent.MouseButtonPress,
            QPoint(10, 10),
            start_pos + QPoint(10, 10),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        overlay.mousePressEvent(press_event)
        assert overlay.drag_position is not None

        move_event = QMouseEvent(
            QMouseEvent.MouseMove,
            QPoint(60, 50),
            start_pos + QPoint(60, 50),
            Qt.NoButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        overlay.mouseMoveEvent(move_event)
        assert overlay.frameGeometry().topLeft() == start_pos + QPoint(50, 40)

        release_event = QMouseEvent(
            QMouseEvent.MouseButtonRelease,
            QPoint(60, 50),
            start_pos + QPoint(60, 50),
            Qt.LeftButton,
            Qt.NoButton,
            Qt.NoModifier,
        )
        overlay.mouseReleaseEvent(release_event)
        assert overlay.drag_position is None
    finally:
        overlay.close()


def test_close_event_stops_timer_and_calls_callback():
    _get_app()
    closed = []
    overlay = TransparentOverlayQt(message_timeout=0, exit_callback=lambda: closed.append(True))

    assert overlay.running is True
    assert overlay.queue_timer.isActive() is True

    event = QCloseEvent()
    overlay.closeEvent(event)

    assert event.isAccepted() is True
    assert overlay.running is False
    assert overlay.queue_timer.isActive() is False
    assert closed == [True]


def test_thread_safe_queue_and_status_updates():
    _get_app()
    overlay = TransparentOverlayQt(message_timeout=0)
    try:

        def worker():
            overlay.update_status("Listening", "lightblue")
            overlay.put_message("query", "Hello AI")
            overlay.put_message("response", "Hi there!")

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()

        QTest.qWait(120)

        assert overlay.status_text.text() == "Listening"
        assert "lightblue" in overlay.status_indicator.styleSheet()
        # 2 message QLabels + 1 trailing stretch item = 3 layout items
        assert overlay.log_layout.count() == 3
    finally:
        overlay.close()


def test_message_timeout_auto_removal():
    _get_app()
    overlay = TransparentOverlayQt(message_timeout=0.1)
    try:
        overlay.add_log_message("Temporary message")
        assert overlay.log_layout.count() == 2  # label + stretch

        QTest.qWait(220)
        assert overlay.log_layout.count() == 1  # only stretch remains
    finally:
        overlay.close()


def test_malformed_messages_do_not_crash():
    _get_app()
    overlay = TransparentOverlayQt(message_timeout=0)
    try:
        overlay.message_queue.put(("status",))  # missing color
        overlay.message_queue.put(("unknown_type", "data"))
        overlay.message_queue.put("not_a_tuple")
        overlay.process_messages()
        assert overlay.running is True
    finally:
        overlay.close()
