from pathlib import Path
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QRegion

from components.styled_button import StyledButton

from pages.ffmpeg_page import FFmpegPage
from pages.py_packages_page import PyPackagesPage
from pages.third_parties_page import ThirdPartiesPage
from pages.backend_page import PythonInstallPage
from pages.settings_page import SettingsPage

from components.title_bar import TitleBar



# add this folder
sys.path.append(str(Path(__file__).resolve().parent))

class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Installer")
        self.setFixedSize(750, 580)

        # Frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main container with rounded corners
        container = QWidget()
        container.setObjectName("mainContainer")
        container.setStyleSheet("""
            #mainContainer {
                background-color: #1a1a2e;
                border-radius: 12px;
            }
        """)
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Content area
        content = QWidget()
        content.setStyleSheet("background-color: #1a1a2e;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Step indicator
        self.step_indicator = QWidget()
        self.step_indicator.setFixedHeight(50)
        self.step_indicator.setStyleSheet("background-color: #16213e;")
        step_layout = QHBoxLayout(self.step_indicator)
        step_layout.setContentsMargins(40, 0, 40, 0)

        self.step_labels = []
        steps = ["Python", "Settings", "FFmpeg", "Download", "Packages"]
        for i, name in enumerate(steps):
            lbl = QLabel(f"{i+1}. {name}")
            lbl.setStyleSheet("color: #444; font-size: 12px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.step_labels.append(lbl)
            step_layout.addWidget(lbl)

        self._update_step_indicator(0)
        content_layout.addWidget(self.step_indicator)

        # Pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #1a1a2e;")

        self.page1 = SettingsPage()
        self.page2 = PythonInstallPage()
        self.page3 = FFmpegPage()
        self.page4 = ThirdPartiesPage()
        self.page5 = PyPackagesPage()

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)
        self.stack.addWidget(self.page3)
        self.stack.addWidget(self.page4)
        self.stack.addWidget(self.page5)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(content)

        # Navigation
        nav = QWidget()
        nav.setFixedHeight(70)
        nav.setStyleSheet("background-color: #16213e; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(30, 0, 30, 0)

        # self.back_btn = StyledButton("← Back")
        # self.back_btn.clicked.connect(self._go_back)
        # self.back_btn.setEnabled(False)

        self.next_btn = StyledButton("Next →", primary=True)
        self.next_btn.clicked.connect(self._go_next)
        self.next_btn.setEnabled(False)

        # nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)

        main_layout.addWidget(nav)

        # Signals
        self.page1.install_complete.connect(lambda: self.next_btn.setEnabled(True))
        self.page2.install_complete.connect(lambda: self.next_btn.setEnabled(True))
        self.page4.install_complete.connect(lambda: self.next_btn.setEnabled(True))
        self.page5.install_complete.connect(self._on_complete)

        # Start
        QTimer.singleShot(500, self.page1.start_installation)

    def _update_step_indicator(self, current):
        for i, lbl in enumerate(self.step_labels):
            if i < current:
                lbl.setStyleSheet("color: #667eea; font-size: 12px;")
            elif i == current:
                lbl.setStyleSheet("color: #fff; font-size: 12px; font-weight: bold;")
            else:
                lbl.setStyleSheet("color: #444; font-size: 12px;")

    def _go_next(self):
        current = self.stack.currentIndex()

        if current == 2:
            version, path = self.page3.get_selection()
            if version == "custom" and not path:
                return
            self.stack.setCurrentIndex(3)
            self._update_step_indicator(3)
            self.page4.start_installation(version, path)
            self.next_btn.setEnabled(False)
            self.back_btn.setEnabled(True)
            return

        if current < self.stack.count() - 1:
            self.stack.setCurrentIndex(current + 1)
            self._update_step_indicator(current + 1)
            self.back_btn.setEnabled(True)

            if current + 1 == 1:
                self.page2.start_installation()
                self.next_btn.setEnabled(False)
            elif current + 1 == 2:
                self.next_btn.setEnabled(True)
            elif current + 1 == 4:
                self.page5.start_installation()
                self.next_btn.setText("Finish")
                self.next_btn.setEnabled(False)

    def _go_back(self):
        current = self.stack.currentIndex()
        if current > 0:
            # Skip page 4 (FFmpeg progress) when going back
            new_idx = current - 1 if current != 4 else 2
            self.stack.setCurrentIndex(new_idx)
            self._update_step_indicator(new_idx)
            self.back_btn.setEnabled(new_idx > 0)
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Next →")

    def _on_complete(self):
        self.next_btn.setEnabled(True)
        self.next_btn.clicked.disconnect()
        self.next_btn.clicked.connect(self.close)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set dark palette
    from PySide6.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1a1a2e"))
    palette.setColor(QPalette.WindowText, QColor("#ffffff"))
    palette.setColor(QPalette.Base, QColor("#16213e"))
    palette.setColor(QPalette.Text, QColor("#ffffff"))
    palette.setColor(QPalette.Button, QColor("#2d2d44"))
    palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#667eea"))
    app.setPalette(palette)

    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())
