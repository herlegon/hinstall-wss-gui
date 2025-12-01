from pathlib import Path
import sys
from typing import Type
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QRegion
from hwidgets import (
    Theme,
    HAppTitle,
)

class TitleBar(QWidget):
    def __init__(
        self,
        parent,
        theme: Type[Theme],
        title: str = "",
        icon: Path = None,
    ):
        super().__init__(parent)
        self.parent_window = parent
        self.dragging = False
        self.drag_position = QPoint()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {theme.window_bgd};")

        layout = QHBoxLayout(self)
        radius: int = theme.default.radius * 3

        layout.setContentsMargins(15, 0, radius, 0)
        layout.setSpacing(0)

        # Icon/Logo
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)

        # Title
        self.title = HAppTitle(self, theme=theme, text=title)

        layout.addWidget(self.title)

        layout.addStretch()

        self.setStyleSheet(f"""
            background-color: transparent;
            border-top-left-radius: {radius}px;
            border-top-right-radius: {radius}px;
        """)

        # Window controls
        btn_style = """
            QPushButton {{
                background-color: {bgd};
                color: #888;
                border: none;
                font-size: 16px;
                padding: 8px 12px;
                border-radius: 0px;
            }}
            QPushButton:hover {{ color: #fff; background-color: #333; }}
        """.format(bgd={theme.window_bgd})
        close_btn_style = """
            QPushButton {{
                background-color: {bgd};
                color: #888;
                border: none;
                font-size: 16px;
                padding: 8px 12px;
                border-radius: 0px;
                margin-right: 0px;
            }}
            QPushButton:hover {{ color: #fff; background-color: #e74c3c; }}
        """.format(
            bgd={theme.window_bgd}, radius={radius}
        )

        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setStyleSheet(btn_style)
        self.minimize_btn.setFixedSize(40, 40)
        self.minimize_btn.clicked.connect(parent.showMinimized)

        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet(close_btn_style)
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.clicked.connect(parent.close)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)


    def setTitle(self, title: str) -> None:
        self.title.setText(title)



    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
