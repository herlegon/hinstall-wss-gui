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

class BasePage(QWidget):
    def __init__(self, parent: QWidget | None = ..., title="", subtitle=""):
        super().__init__(parent=parent)
        self.setStyleSheet("background-color: transparent;")

        self.main_window = parent

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(40, 30, 40, 20)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet("color: #fff;")
        self.layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("color: #888; font-size: 13px;")
            sub_label.setWordWrap(True)
            self.layout.addWidget(sub_label)

        # Spacer
        self.layout.addSpacing(10)
