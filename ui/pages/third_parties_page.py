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


class ThirdPartiesPage(BasePage):
    install_complete = Signal()

    def __init__(self):
        super().__init__(
            "Installing FFmpeg",
            "Downloading and configuring FFmpeg..."
        )

        container = QFrame()
        container.setStyleSheet("QFrame { background-color: #16213e; border-radius: 12px; }")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)

        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet("color: #ccc; font-size: 14px;")
        container_layout.addWidget(self.status_label)

        self.progress_bar = StyledProgressBar("#ff6b6b")
        container_layout.addWidget(self.progress_bar)

        self.layout.addWidget(container)
        self.layout.addStretch()
        self.worker = None

    def start_installation(self, version_type, custom_path=None):
        if version_type == "custom":
            steps = ["Verifying FFmpeg executable...", "Checking version...", "Configuring paths..."]
        else:
            steps = [
                f"Downloading FFmpeg ({version_type})...",
                "Extracting archive...",
                "Verifying binaries...",
                "Configuring paths...",
                "Cleaning up..."
            ]

        self.worker = InstallWorker(steps)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success):
        if success:
            self.status_label.setText("✓ FFmpeg installed!")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
            self.install_complete.emit()
