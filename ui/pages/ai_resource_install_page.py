from typing import Type
from PySide6.QtCore import (
    Signal,
)
from PySide6.QtGui import (
    QPaintEvent,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSizePolicy
)
from hwidgets import (
    Theme,
)
from ..designer.ui_ai_resource_install_widget import Ui_AiResourceInstallWidget
from .base_page import BasePage


class AiResourceInstallPage(BasePage, Ui_AiResourceInstallWidget):
    # signal_settings_modified = Signal()

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = "AI Computational Resource"


    def start_installation(self, version_type, custom_path=None):
        if version_type == "custom":
            steps = ["Verifying FFmpeg executable...", "Checking version...", "Configuring paths..."]
        else:
            steps = [
                f"Downloading FFmpeg ({version_type})...",
                "Extracting archive...",
                "Verifying binaries...",
                "Configuring paths...",
                "Cleaning up..."
            ]

        # self.worker = InstallWorker(steps)
        # self.worker.progress.connect(self.progress_bar.setValue)
        # self.worker.status.connect(self.status_label.setText)
        # self.worker.finished_signal.connect(self._on_finished)
        # self.worker.start()


    # def _on_finished(self, success):
    #     if success:
    #         self.status_label.setText("✓ FFmpeg installed!")
    #         self.status_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold;")
    #         self.install_complete.emit()
