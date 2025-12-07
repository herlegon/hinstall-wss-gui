from __future__ import annotations
from pathlib import Path
from typing import Any, Type
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
from hytils import red
from ..designer.ui_ai_resource_install_widget import Ui_AiResourceInstallWidget
from .page import Page
# from ..workers.pkg_install_worker import InstallWorker


class AiResourceInstallPage(Page, Ui_AiResourceInstallWidget):

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = "AI Computational Resource"

        self.reset_widgets()


    def update_settings(self, settings: dict[str, Any]) -> None:
        print(red("todo"))


    def start_installation(self):
        """Start the installation worker."""
        steps = [
            "Downloading AI models...",
            "Installing computational resources...",
            "Setting up environment..."
        ]

        # Create and start worker
        # self.worker = InstallWorker(steps)
        # self.worker.progress.connect(self._update_progress)
        # self.worker.status.connect(self.label.setText)
        # self.worker.finished_signal.connect(self._on_finished)

        # Reset progress bar
        self.progress_bar.setValue(0)
        self.label_2.setText("0%")

        # Start worker
        # self.worker.start()


    def slot_update_progress(self, value: int):
        """Update progress bar and percentage label."""
        duration: int = 0
        if value == 100:
            duration = self.progress_bar.getAnimationDuration()
            self.progress_bar.setAnimationDuration(0)

        self.progress_bar.setValue(value)
        self.indicator_progress.setText(f"{value}%")

        if duration:
            self.progress_bar.setAnimationDuration(value)


    def slot_on_finished(self, success: bool, files: list[Path]):
        """Handle completion of installation."""
        self._installation_started = False

        duration = self.progress_bar.getAnimationDuration()
        self.progress_bar.setAnimationDuration(0)

        if success:
            self.progress_bar.setValue(100)
            self.indicator_progress.setText("")

        else:
            self.progress_bar.setValue(0)
            self.indicator_progress.setText("❌")

        self.progress_bar.setAnimationDuration(duration)

        self.installed_files = files
        self.completed.emit(success)



    def _update_progress(self, value: int):
        """Update progress bar and percentage label."""
        self.progress_bar.setValue(value)
        self.label_2.setText(f"{value}%")


    def _on_finished(self, success: bool, files: list):
        """Handle completion of installation."""
        self._installation_started = False
        if success:
            self.installed_files = files
            self.label.setText("✓ AI resources installed!")
            self.label_2.setText("100%")
            self.completed.emit(True)
        else:
            self.label.setText("✗ Installation failed")
            self.completed.emit(False)


    def get_result(self) -> dict:
        return {'installed_files': self.installed_files}

