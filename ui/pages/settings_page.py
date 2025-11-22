
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



class SettingsPage(BasePage):
    install_complete = Signal()

    def __init__(self):
        super().__init__(
            "Settings & Packages",
            "Configure installation preferences and install required packages."
        )

        # Settings
        settings_frame = QFrame()
        settings_frame.setStyleSheet("""
            QFrame { background-color: #16213e; border-radius: 12px; }
        """)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(12)

        cb_style = """
            QCheckBox {
                color: #ccc;
                font-size: 14px;
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

        self.auto_update_cb = QCheckBox("  Always keep application up to date")
        self.auto_update_cb.setChecked(True)
        self.auto_update_cb.setStyleSheet(cb_style)
        settings_layout.addWidget(self.auto_update_cb)

        self.cache_cb = QCheckBox("  Cache large packages locally")
        self.cache_cb.setChecked(True)
        self.cache_cb.setStyleSheet(cb_style)
        settings_layout.addWidget(self.cache_cb)

        self.layout.addWidget(settings_frame)

        # Package installation
        pkg_label = QLabel("External Packages")
        pkg_label.setStyleSheet("color: #fff; font-size: 16px; font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(pkg_label)

        self.package_list = QTextEdit()
        self.package_list.setReadOnly(True)
        self.package_list.setMaximumHeight(80)
        self.package_list.setStyleSheet("""
            QTextEdit {
                background-color: #0f0f1a;
                color: #888;
                border: 1px solid #2d2d44;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        self.layout.addWidget(self.package_list)

        self.progress_bar = StyledProgressBar("#a55eea")
        self.layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Waiting...")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        self.layout.addWidget(self.status_label)

        self.layout.addStretch()
        self.worker = None
        self._complete = False

    def start_installation(self):
        packages = ["numpy", "pandas", "opencv-python", "pillow", "requests"]
        self.package_list.setText("  •  ".join(packages))

        steps = [f"Installing {p}..." for p in packages]
        self.worker = InstallWorker(steps)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success):
        if success:
            self._complete = True
            self.status_label.setText("✓ All packages installed!")
            self.status_label.setStyleSheet("color: #a55eea; font-size: 12px; font-weight: bold;")
            self.install_complete.emit()

    def is_complete(self):
        return self._complete

