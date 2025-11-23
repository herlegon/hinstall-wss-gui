import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QRegion

from install_workers import InstallWorker
from components.styled_progress_bar import StyledProgressBar
from .base_page import BasePage



class BackendInstallPage(BasePage):
    install_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(
            parent,
            "Python Environment",
            "Setting up the Python runtime environment. This won't take long."
        )

        # Progress container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)

        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #ccc; font-size: 14px;")
        container_layout.addWidget(self.status_label)

        self.progress_bar = StyledProgressBar("#00d2d3")
        container_layout.addWidget(self.progress_bar)

        self.layout.addWidget(container)
        self.layout.addStretch()

        self.worker = None

    def start_installation(self):
        steps = [
            "Detecting system Python...",
            "Creating virtual environment...",
            "Installing pip...",
            "Configuring paths...",
            "Finalizing setup..."
        ]
        self.worker = InstallWorker(steps)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success):
        if success:
            self.status_label.setText("✓ Python environment ready!")
            self.status_label.setStyleSheet("color: #00d2d3; font-size: 14px; font-weight: bold;")
            self.install_complete.emit()
