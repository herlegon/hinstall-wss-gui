
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

class PyPackagesPage(BasePage):
    install_complete = Signal()
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(
            parent,
            "Python Packages",
            "Installing Python dependencies via package manager."
        )

        self.status_label = QLabel("Connecting to server...")
        self.status_label.setStyleSheet("color: #ccc; font-size: 14px;")
        self.layout.addWidget(self.status_label)

        self.progress_bar = StyledProgressBar("#1dd1a1")
        self.layout.addWidget(self.progress_bar)

        # Update Checkbox (Moved from Page 1)
        cb_style = """
            QCheckBox {
                color: #fff;
                font-size: 14px;
                font-weight: bold;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3d3d5c;
                background-color: #1a1a2e;
            }
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            QCheckBox::indicator:hover {
                border-color: #667eea;
            }
        """
        self.auto_update_cb = QCheckBox("Keep the computational resources up to date")
        self.auto_update_cb.setChecked(True)
        self.auto_update_cb.setStyleSheet(cb_style)
        self.layout.addWidget(self.auto_update_cb)

        self.layout.addStretch()

        self.sim_timer = None

    def start_installation(self):
        packages = ["torch", "transformers", "scipy", "matplotlib", "scikit-learn"]
        self.sim_index = 0
        self.sim_packages = packages

        self.log_message.emit("[WebSocket] Connecting to ws://localhost:8765...")
        self.log_message.emit("[WebSocket] Connection established")
        self.log_message.emit("[System] Starting package installation...\n")

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._sim_step)
        self.sim_timer.start(400)

    def _sim_step(self):
        total_steps = len(self.sim_packages) * 5
        if self.sim_index >= total_steps:
            self.sim_timer.stop()
            self.status_label.setText("✓ All packages installed!")
            self.status_label.setStyleSheet("color: #1dd1a1; font-size: 14px; font-weight: bold;")
            self.status_label.setStyleSheet("color: #1dd1a1; font-size: 14px; font-weight: bold;")
            self.progress_bar.setValue(100)
            self.log_message.emit("\n[System] Installation complete!")
            self.install_complete.emit()
            return

        pkg_idx = self.sim_index // 5
        step = self.sim_index % 5
        pkg = self.sim_packages[pkg_idx]

        progress = int((self.sim_index / total_steps) * 100)
        self.progress_bar.setValue(progress)

        if step == 0:
            self.log_message.emit(f"[pip] Installing {pkg}...")
            self.status_label.setText(f"Installing {pkg}...")
        elif step == 4:
            self.log_message.emit(f"[pip] ✓ Successfully installed {pkg}")

        self.sim_index += 1

