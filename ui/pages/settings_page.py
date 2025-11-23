
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

    def __init__(self, parent=None):
        super().__init__(
            parent,
            "", # No title in header, handled by content
            ""
        )

        # Main layout
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(20)

        # Welcome Text
        welcome_label = QLabel("Welcome")
        welcome_label.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold;")
        self.layout.addWidget(welcome_label)

        description_label = QLabel(
            "This will install third parties sofwtare and a computational resources based on your system."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #ccc; font-size: 14px; margin-bottom: 20px;")
        self.layout.addWidget(description_label)

        # Settings Container
        settings_frame = QFrame()
        settings_frame.setStyleSheet("""
            QFrame { background-color: #16213e; border-radius: 12px; }
        """)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(20)

        # Checkbox Style
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
        desc_style = "color: #888; font-size: 12px; margin-left: 32px;"

        # Checkbox 1: Cache (Moved to right side as per request)
        # To put it on the right, we can use a QHBoxLayout with a stretch on the left.
        
        cb1_container = QWidget()
        cb1_layout = QHBoxLayout(cb1_container)
        cb1_layout.setContentsMargins(0, 0, 0, 0)
        cb1_layout.addStretch() # Push to right

        # Inner layout for checkbox + description to keep them together
        right_aligned_layout = QVBoxLayout()
        right_aligned_layout.setSpacing(4)
        right_aligned_layout.setAlignment(Qt.AlignRight)

        self.cache_cb = QCheckBox("Cache download packages")
        self.cache_cb.setChecked(True)
        self.cache_cb.setStyleSheet(cb_style)
        self.cache_cb.setLayoutDirection(Qt.RightToLeft) # Text on left, box on right? Or just aligned right?
        # "put the checkboxes below: one to cache... as a simple title and description" -> "on the first page put the checkboxes on the right"
        # Usually means alignment. Let's align the whole block to the right.
        
        right_aligned_layout.addWidget(self.cache_cb)
        
        cb1_desc = QLabel("Used when reinstalling or updating the software to save bandwidth.")
        cb1_desc.setStyleSheet(desc_style)
        cb1_desc.setWordWrap(True)
        cb1_desc.setAlignment(Qt.AlignRight) # Align text to right too
        right_aligned_layout.addWidget(cb1_desc)
        
        cb1_layout.addLayout(right_aligned_layout)
        settings_layout.addWidget(cb1_container)

        # Removed Auto Update Checkbox from here (moved to last page)

        self.layout.addWidget(settings_frame)
        self.layout.addStretch()

    def start_installation(self):
        # No-op for this page now
        self.install_complete.emit()

