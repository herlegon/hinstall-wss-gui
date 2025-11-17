import sys
import os
import subprocess
import json
import zipfile
import shutil
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
QLabel, QProgressBar, QMessageBox, QDialog,
QPushButton, QHBoxLayout, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap


class FirstTimeSetupDialog(QDialog):
    """Dialog to ask user about caching installation files"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.keep_installers = False
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("First Time Setup")
        self.setFixedSize(500, 250)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Welcome to the Application")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)


        # Description
        description = QLabel(
            "The application needs to download and install backend components.\n\n"
            "Would you like to cache the installation files locally?\n"
            "This will use approximately 30-50 MB of disk space but allows\n"
            "faster reinstallation without re-downloading."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)

        # Checkbox
        self.checkbox = QCheckBox("Keep installation files for offline reinstallation")
        self.checkbox.setChecked(True)
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setFixedSize(100, 35)
        self.continue_btn.clicked.connect(self.accept)
        self.continue_btn.setDefault(True)

        button_layout.addWidget(self.continue_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.center_on_screen()


    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


    def accept(self):
        self.keep_installers = self.checkbox.isChecked()
        super().accept()


    def get_choice(self):
        """Show dialog and return user choice"""
        result = self.exec()
        return self.keep_installers if result == QDialog.Accepted else False
