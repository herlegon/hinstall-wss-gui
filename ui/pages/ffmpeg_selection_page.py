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


class FFmpegSelectionPage(BasePage):
    install_complete = Signal()



    def __init__(self, parent=None):
        super().__init__(
            parent,
            title="FFmpeg Setup",
            subtitle="Select which FFmpeg build to use for media processing."
        )

        self.button_group = QButtonGroup(self)

        options_frame = QFrame()
        options_frame.setStyleSheet("QFrame { background-color: #16213e; border-radius: 12px; }")
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(20, 20, 20, 20)
        options_layout.setSpacing(8)

        rb_style = """
            QRadioButton {
                color: #ccc;
                font-size: 14px;
                spacing: 10px;
                padding: 8px 0;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #3d3d5c;
                background-color: #1a1a2e;
            }
            QRadioButton::indicator:checked {
                background-color: #ff6b6b;
                border-color: #ff6b6b;
            }
            QRadioButton::indicator:hover {
                border-color: #ff6b6b;
            }
        """

        # Option 1: Fallback
        self.fallback_rb = QRadioButton("Fallback FFmpeg (Recommended)")
        self.fallback_rb.setChecked(True)
        self.fallback_rb.setStyleSheet(rb_style)
        self.button_group.addButton(self.fallback_rb, 0)
        options_layout.addWidget(self.fallback_rb)

        desc1 = QLabel(
            "Free codecs included: AV1, VP8, VP9, DNxHD, Vorbis, Opus, FLAC, PCM.\n"
            "H.264/H.265 decoding included for playback support.\n"
            "Hardware-accelerated H.264/H.265 encoders (requires an NVIDIA GPU).\n"
            "Does NOT include software H.264/H.265, AAC, or MP3 encoders.\n"
            "Safe for personal or commercial use without additional licenses."
        )
        desc1.setStyleSheet("color: #888; font-size: 12px; margin-left: 32px; margin-bottom: 10px;")
        options_layout.addWidget(desc1)

        # Option 2: System
        self.system_rb = QRadioButton("Use an existing FFmpeg on your system")
        self.system_rb.setStyleSheet(rb_style)
        self.button_group.addButton(self.system_rb, 1)
        options_layout.addWidget(self.system_rb)

        desc2 = QLabel(
            "Select a pre-installed FFmpeg binary. Your software will call it externally.\n"
            "You are responsible for license and patent compliance, including commercial use."
        )
        desc2.setStyleSheet("color: #888; font-size: 12px; margin-left: 32px; margin-bottom: 5px;")
        options_layout.addWidget(desc2)

        # Option 3: Download
        self.download_rb = QRadioButton("Download FFmpeg from a third-party")
        self.download_rb.setStyleSheet(rb_style)
        self.button_group.addButton(self.download_rb, 2)
        options_layout.addWidget(self.download_rb)

        desc3 = QLabel(
            "Includes full software H.264/H.265/AAC/MP3 encoders (GPL and patent-encumbered).\n"
            "Provided by a third party (e.g., BtbN). You are responsible for any licenses or patents.\n"
            "Commercial use may require separate patent licenses."
        )
        desc3.setStyleSheet("color: #888; font-size: 12px; margin-left: 32px;")
        options_layout.addWidget(desc3)

        # Custom path
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(30, 5, 0, 0)

        self.path_label = QLabel("No file selected")
        self.path_label.setStyleSheet("color: #666; font-size: 12px;")

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setEnabled(False)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d44;
                color: #aaa;
                border: none;
                padding: 6px 15px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #3d3d5c; color: #fff; }
            QPushButton:disabled { background-color: #1a1a2e; color: #444; }
        """)
        self.browse_btn.clicked.connect(self._browse_ffmpeg)

        path_layout.addWidget(self.path_label, 1)
        path_layout.addWidget(self.browse_btn)
        options_layout.addLayout(path_layout)

        self.layout.addWidget(options_frame)
        self.layout.addWidget(options_frame)
        # self.custom_rb.toggled.connect(self.browse_btn.setEnabled) # Removed custom browse logic for now as per new requirements text, or adapted if "Use existing" implies browsing.
        # The requirement says "Select a pre-installed FFmpeg binary", so I should probably keep the browse button for the second option.
        
        self.system_rb.toggled.connect(self.browse_btn.setEnabled)

        disclaimer_text = (
            "**Disclaimer:**\n"
            "Neither Herlogon nor their developers is not responsible for the choice of FFmpeg binary. "
            "By selecting an external or third-party FFmpeg, you acknowledge that you are responsible for "
            "complying with all applicable licenses and patent obligations, including any requirements for commercial use."
        )
        self.disclaimer_label = QLabel(disclaimer_text)
        self.disclaimer_label.setWordWrap(True)
        self.disclaimer_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic; margin-top: 20px;")
        self.layout.addWidget(self.disclaimer_label)

        self.layout.addStretch()
        self.custom_path = None # Kept for compatibility if needed, though logic changed

        self.main_window.next_btn.setEnabled(True)

        self.fallback_rb.toggled.connect(
            lambda: self.main_window.next_btn.setEnabled(True)
        )
        self.system_rb.toggled.connect(
            lambda: self.main_window.next_btn.setEnabled(True)
        )
        self.download_rb.toggled.connect(
            lambda: self.main_window.next_btn.setEnabled(True)
        )

    def _browse_ffmpeg(self):
        self.main_window.next_btn.setEnabled(False)
        path, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg", "", "Executable (*.exe);;All Files (*)")
        if path:
            self.custom_path = path
            short = path if len(path) < 45 else "..." + path[-42:]
            self.path_label.setText(short)
            self.path_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        self.main_window.next_btn.setEnabled(True)


    def get_selection(self):
        if self.fallback_rb.isChecked():
            return "fallback", None
        elif self.system_rb.isChecked():
            return "system", None
        return "download", None

    def is_complete(self):
        return self._complete

    # def selection_valid(self) -> None:

