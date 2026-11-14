
import sys
from queue import Queue, Empty

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.config import config
from src.utils.logger import get_logger
from src.utils.thread_executor import executor

logger = get_logger()


class TransparentOverlayQt(QMainWindow):
    """A transparent overlay displaying transcriptions and responses."""

    def __init__(self, message_timeout=5, exit_callback=None):
        super().__init__()

        self.message_timeout = message_timeout
        self.exit_callback = exit_callback
        self.message_queue = Queue()
        self.running = True
        self.on_new_message = None
        self.drag_position = None

        self.setup_ui()

        # Process queued messages on the GUI thread.
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.process_messages)
        self.queue_timer.start(50)

    def setup_ui(self):
        """Set up the user interface."""

        self.setWindowTitle(f"{config.ASSISTANT_NAME} Assistant")

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint
        )

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setGeometry(
            config.OVERLAY_X,
            config.OVERLAY_Y,
            config.OVERLAY_WIDTH,
            config.OVERLAY_HEIGHT,
        )

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")

        central_widget.setStyleSheet("""
            #centralWidget {
                background-color: rgba(0, 0, 0, 150);
                border-radius: 10px;
            }
        """)

        main_layout = QVBoxLayout(central_widget)

        # Status bar
        top_layout = QHBoxLayout()

        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 10))
        self.status_indicator.setStyleSheet("color: gray;")

        self.status_text = QLabel("Idle")
        self.status_text.setFont(QFont("Arial", 10))
        self.status_text.setStyleSheet("color: white;")

        top_layout.addWidget(self.status_indicator)
        top_layout.addWidget(self.status_text)
        top_layout.addStretch()

        # Minimize button
        self.minimize_btn = QToolButton()

        self.minimize_btn.setIcon(
            self.style().standardIcon(
                self.style().SP_TitleBarMinButton
            )
        )

        self.minimize_btn.setIconSize(QSize(16, 16))

        self.minimize_btn.setStyleSheet("""
            background: transparent;
            border: none;
            margin: 2px;
        """)

        self.minimize_btn.clicked.connect(self.hide)

        top_layout.addWidget(self.minimize_btn)
        main_layout.addLayout(top_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #333333;")

        main_layout.addWidget(separator)

        # Message area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }

            QWidget {
                background: transparent;
            }
        """)

        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)

        self.log_layout.addStretch()

        self.scroll_area.setWidget(self.log_container)

        main_layout.addWidget(self.scroll_area)

        # Input area
        control_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type your message...")

        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #222222;
                color: white;
                padding: 5px;
                border-radius: 5px;
            }
        """)

        self.send_btn = QPushButton("Send")

        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #555555;
            }
        """)

        self.send_btn.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)

        control_layout.addWidget(self.input_box, 1)
        control_layout.addWidget(self.send_btn)

        main_layout.addLayout(control_layout)

        self.setCentralWidget(central_widget)

    # --------------------------------------------------
    # Window dragging
    # --------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPos() -
                self.frameGeometry().topLeft()
            )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() == Qt.LeftButton
            and self.drag_position is not None
        ):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        super().mouseReleaseEvent(event)

    # --------------------------------------------------
    # Close event
    # --------------------------------------------------

    def closeEvent(self, event):
        self.running = False

        if hasattr(self, "queue_timer"):
            self.queue_timer.stop()

        if self.exit_callback:
            try:
                self.exit_callback()
            except Exception as e:
                logger.error(f"Exit callback error: {e}")

        event.accept()

    # --------------------------------------------------
    # Message queue
    # --------------------------------------------------

    def update_status(self, status, color="gray"):
        """Safely queue a status update."""
        self.message_queue.put(("status", status, color))

    def add_log_message(self, text, color="white"):
        """Safely queue a message for display."""
        self.message_queue.put(("log", text, color))

    def put_message(self, msg_type, *args):
        """Queue a message."""
        self.message_queue.put((msg_type, *args))

    def process_messages(self):
        """Process messages on the GUI thread."""

        while True:
            try:
                msg = self.message_queue.get_nowait()

            except Empty:
                break

            try:
                msg_type, *args = msg

                if msg_type == "status":
                    status, color = args

                    self.status_indicator.setStyleSheet(
                        f"color: {color};"
                    )

                    self.status_text.setText(status)

                elif msg_type == "query":
                    text = args[0]
                    self._add_log_message(
                        f"You: {text}",
                        "#00FFFF"
                    )

                elif msg_type == "response":
                    text = args[0]

                    self._add_log_message(
                        f"{config.ASSISTANT_NAME}: {text}",
                        "#00FF00"
                    )

                elif msg_type == "log":
                    text, color = args

                    self._add_log_message(text, color)

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    # --------------------------------------------------
    # Display messages
    # --------------------------------------------------

    def _add_log_message(self, text, color="white"):
        """Display a message in the scroll area."""

        label = QLabel(str(text))
        label.setFont(QFont("Arial", 10))
        label.setStyleSheet(f"color: {color};")
        label.setWordWrap(True)

        self.log_layout.insertWidget(
            self.log_layout.count() - 1,
            label
        )

        # Scroll to the latest message.
        QTimer.singleShot(
            50,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        )

        # Automatically remove old messages.
        if self.message_timeout > 0:
            QTimer.singleShot(
                self.message_timeout * 1000,
                lambda: self._remove_message(label)
            )

    def _remove_message(self, label):
        """Remove a message after its timeout."""

        if label is not None:
            self.log_layout.removeWidget(label)
            label.deleteLater()

    # --------------------------------------------------
    # Application controls
    # --------------------------------------------------

    def start(self):
        """Start the overlay."""
        self.running = True
        self.show()

        self.update_status(
            f"{config.ASSISTANT_NAME} Active",
            "lightgreen"
        )

    def shutdown(self):
        """Shut down the overlay."""
        self.running = False
        self.close()

    def send_message(self):
        """Send the user's message."""

        message = self.input_box.text().strip()

        if not message:
            return

        self.input_box.clear()

        self.put_message("query", message)

        if self.on_new_message:
            try:
                executor.submit(
                    self.on_new_message,
                    message
                )
            except Exception as e:
                logger.error(f"Message submission error: {e}")


# --------------------------------------------------
# Application initialization
# --------------------------------------------------

def main():

    app = QApplication(sys.argv)

    overlay = TransparentOverlayQt(message_timeout=5)

    overlay.start()

    # Demo status updates
    QTimer.singleShot(
        1000,
        lambda: overlay.update_status("Listening", "lightblue")
    )

    QTimer.singleShot(
        2000,
        lambda: overlay.add_log_message(
            f"{config.ASSISTANT_NAME}, what's the weather today?"
        )
    )

    QTimer.singleShot(
        3000,
        lambda: overlay.update_status("Processing", "yellow")
    )

    QTimer.singleShot(
        4000,
        lambda: overlay.update_status("Responding", "lightgreen")
    )

    QTimer.singleShot(
        4500,
        lambda: overlay.add_log_message(
            "It's currently sunny and 22°C outside with a light breeze."
        )
    )

    QTimer.singleShot(
        6000,
        lambda: overlay.update_status("Listening", "lightblue")
    )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

