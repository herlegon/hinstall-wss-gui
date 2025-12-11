from __future__ import annotations
from pathlib import Path
from pprint import pprint
import time
from typing import Any, Literal, Type
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
    HIndetProgressBarM2,
    Theme,
    HLabel,
)
from ..workers.backend_install_worker import BackendInstallWorker
from ..designer.ui_ai_resource_install_widget import Ui_AiResourceInstallWidget
from .page import Page


class AiResourceInstallPage(Page, Ui_AiResourceInstallWidget):

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme],
        app_cfg: dict[str, str],
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = "AI Computational Resource"

        self.indet_progress_bar: HIndetProgressBarM2 = HIndetProgressBarM2(
            self, theme=theme
        )
        self.progress_layout.addWidget(self.indet_progress_bar)
        self.indet_progress_bar.setVisible(False)

        self.syscap_layout.setSpacing(4)

        self.reset_widgets()
        self.app_cfg = app_cfg


    def reset_widgets(self) -> None:
        super().reset_widgets()
        self.indicator_step.setText("Installing AI Computational Resource...")
        self.indicator_progress.setText("")

        while self.syscap_layout.count():
            item = self.syscap_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.syscap_layout.invalidate()
        self.syscap_layout.activate()


    def update_settings(self, settings: dict[str, Any]) -> None:
        self.reset_widgets()
        self.user_settings = settings


    def start_installation(self):
        self.reset_widgets()

        self.indet_progress_bar.setVisible(False)
        self.progress_bar.setVisible(False)
        self.indicator_step.setText("Analyzing...")
        self.indicator_progress.setVisible(False)

        # Create a worker that will communicate with the websocket server
        self.worker: BackendInstallWorker = BackendInstallWorker(
            settings=self.user_settings,
            app_cfg=self.app_cfg,
            stages=2
        )
        self.worker.progress.connect(self.slot_update_progress)
        self.worker.task_name.connect(self.indicator_step.setText)
        self.worker.finished.connect(self.slot_on_finished)

        self.worker.signal_syscap_updated.connect(self.slot_syscap_updated)

        # Start worker
        self.worker.start()


    def slot_syscap_updated(self, syscap: dict[str, bool]) -> None:
        # Torch
        if syscap.get('cuda', False):
            torch_variant = "CUDA"
        elif syscap.get('rocm', False):
            torch_variant = "RocM"
        elif syscap.get('intel', False):
            torch_variant = "XPU"
        torch_label = HLabel(theme=self.theme, text=f"- PyTorch ({torch_variant})")
        self.syscap_layout.addWidget(torch_label)

        # TensorRT
        if syscap.get('tensorrt', False):
            tensorrt_label = HLabel(theme=self.theme, text=f"- NVIDIA TensorRT")
            self.syscap_layout.addWidget(tensorrt_label)

        # DirectML
        if syscap.get('directml', False):
            directml_label = HLabel(theme=self.theme, text=f"- Microsoft Direct ML")
            self.syscap_layout.addWidget(directml_label)

        self.indet_progress_bar.setVisible(False)
        self.progress_bar.setVisible(True)
        self.indicator_step.setText("Installing AI Computational Resource...")
        self.indicator_progress.setVisible(False)



    def slot_update_progress(self, type: Literal['progress', 'indet'], value: int):
        """Update progress bar and percentage label."""

        # Show/Hide the correct progress bar
        if type == 'indet':
            if not self.indet_progress_bar.isVisible():
                self.progress_bar.setVisible(False)
                self.indet_progress_bar.setVisible(True)
                self.indet_progress_bar.start()
                self.indicator_progress.setText("")

        else:
            if not self.progress_bar.isVisible():
                self.indet_progress_bar.setVisible(False)
                self.progress_bar.setVisible(True)

        # Do not show the % if indeterminate
        if self.indet_progress_bar.isVisible():
            self.indicator_progress.setVisible(False)
        else:
            self.indicator_progress.setVisible(True)

        duration: int = 0
        if value == 100:
            duration = self.progress_bar.getAnimationDuration()
            self.progress_bar.setAnimationDuration(0)
            self.indet_progress_bar.stop()

        self.progress_bar.setValue(value)
        self.indicator_progress.setText(f"{value}%")

        if duration:
            self.progress_bar.setAnimationDuration(value)


    def slot_on_finished(self, success: bool, files: list[Path]):
        """Handle completion of installation."""
        self._installation_started = False

        duration = self.progress_bar.getAnimationDuration()
        self.progress_bar.setAnimationDuration(0.5)
        self.indicator_progress.setVisible(True)

        if success:
            self.progress_bar.setValue(100)
            self.indet_progress_bar.stop()
            self.indicator_progress.setText("")

        else:
            self.progress_bar.setValue(0)
            self.indet_progress_bar.stop()
            self.indicator_progress.setText("❌")

        self.progress_bar.setAnimationDuration(duration)

        self.installed_files = files
        time.sleep(1)
        self.completed.emit(success)


    def get_result(self) -> dict:
        return {'installed_files': self.installed_files}


