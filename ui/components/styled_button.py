import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QRegion

class StyledButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #764ba2, stop:1 #667eea);
                }
                QPushButton:disabled {
                    background: #3d3d5c;
                    color: #666;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d44;
                    color: #aaa;
                    border: 1px solid #3d3d5c;
                    padding: 12px 30px;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #3d3d5c;
                    color: #fff;
                }
                QPushButton:disabled {
                    background-color: #1a1a2e;
                    color: #444;
                    border-color: #2d2d44;
                }
            """)

