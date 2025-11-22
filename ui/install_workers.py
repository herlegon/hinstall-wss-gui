import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QRegion

class InstallWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, steps):
        super().__init__()
        self.steps = steps

    def run(self):
        try:
            total = len(self.steps)
            for i, step in enumerate(self.steps):
                self.status.emit(step)
                for j in range(20):
                    progress = int(((i * 20 + j) / (total * 20)) * 100)
                    self.progress.emit(progress)
                    self.msleep(40)
            self.progress.emit(100)
            self.finished_signal.emit(True)
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False)

