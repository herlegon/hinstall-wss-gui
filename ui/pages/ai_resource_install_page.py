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
from ..install_workers import InstallWorker


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
        self.set_has_progress_bar(True)  # This page has a progress bar


    def start_installation(self):
        """Start the installation worker."""
        steps = [
            "Downloading AI models...",
            "Installing computational resources...",
            "Setting up environment..."
        ]
        
        # Create and start worker
        self.worker = InstallWorker(steps)
        self.worker.progress.connect(self._update_progress)
        self.worker.status.connect(self.label.setText)
        self.worker.finished_signal.connect(self._on_finished)
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        self.label_2.setText("0%")
        
        # Start worker
        self.worker.start()
    
    
    def _update_progress(self, value: int):
        """Update progress bar and percentage label."""
        self.progress_bar.setValue(value)
        self.label_2.setText(f"{value}%")


    def _on_finished(self, success: bool, files: list):
        """Handle completion of installation."""
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

