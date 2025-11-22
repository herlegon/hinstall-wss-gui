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


class FFmpegPage(BasePage):
    def __init__(self):
        super().__init__(
            "FFmpeg Setup",
            "Select which FFmpeg build to use for media processing."
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

        self.minimal_rb = QRadioButton("  Minimal  —  Basic encoding/decoding only (~40 MB)")
        self.minimal_rb.setChecked(True)
        self.minimal_rb.setStyleSheet(rb_style)
        self.button_group.addButton(self.minimal_rb, 0)
        options_layout.addWidget(self.minimal_rb)

        self.gpl_rb = QRadioButton("  GPL  —  Full features with x264/x265 (~80 MB)")
        self.gpl_rb.setStyleSheet(rb_style)
        self.button_group.addButton(self.gpl_rb, 1)
        options_layout.addWidget(self.gpl_rb)

        self.custom_rb = QRadioButton("  Custom  —  Use your own ffmpeg.exe")
        self.custom_rb.setStyleSheet(rb_style)
        self.button_group.addButton(self.custom_rb, 2)
        options_layout.addWidget(self.custom_rb)

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
        self.custom_rb.toggled.connect(self.browse_btn.setEnabled)

        self.layout.addStretch()
        self.custom_path = None

    def _browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg", "", "Executable (*.exe);;All Files (*)")
        if path:
            self.custom_path = path
            short = path if len(path) < 45 else "..." + path[-42:]
            self.path_label.setText(short)
            self.path_label.setStyleSheet("color: #ff6b6b; font-size: 12px;")

    def get_selection(self):
        if self.minimal_rb.isChecked():
            return "minimal", None
        elif self.gpl_rb.isChecked():
            return "gpl", None
        return "custom", self.custom_path
