from __future__ import annotations
from pathlib import Path
from pprint import pprint
import time
from typing import Any, Literal, Type
from PySide6.QtCore import (
    Signal,
    Qt,
)
from PySide6.QtGui import (
    QPaintEvent,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSizePolicy,
    QHBoxLayout,
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
        self.remove_ai_labels()


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


    def remove_ai_labels(self) -> None:
        while self.syscap_layout.count():
            item = self.syscap_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.syscap_layout.invalidate()
        self.syscap_layout.activate()


    def slot_syscap_updated(self, syscap: dict[str, bool]) -> None:
        self.remove_ai_labels()
        bullet: str = "‣"

        def _add_label(text: str) -> None:
            h_layout = QHBoxLayout()
            h_layout.setSpacing(0)
            bullet_label = HLabel(theme=self.theme, text=bullet)
            bullet_label.setFontSize(22)
            bullet_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)
            bullet_label.setStyleSheet(
                bullet_label.styleSheet()
                + "QLabel{margin-bottom: 6px; margin-right: 0px;}"
            )
            text_label = HLabel(theme=self.theme, text=text)
            h_layout.addWidget(bullet_label)
            h_layout.addWidget(text_label)
            h_layout.addStretch()
            self.syscap_layout.addLayout(h_layout)

        # Torch
        if syscap.get('cuda', False):
            torch_variant = "CUDA"
        elif syscap.get('rocm', False):
            torch_variant = "RocM"
        elif syscap.get('intel', False):
            torch_variant = "XPU"
        else:
            torch_variant = "CPU"
        _add_label(f"PyTorch ({torch_variant})")

        # TensorRT
        if syscap.get('tensorrt', False):
            _add_label("NVIDIA TensorRT")

        # DirectML
        if syscap.get('directml', False):
            _add_label("Microsoft Direct ML")

        # ONNX runtime
        _add_label("Microsoft ONNX Runtime")

        self.indet_progress_bar.setVisible(False)
        self.progress_bar.setVisible(True)
        self.indicator_step.setText("Installing AI Computational Resource...")
        self.indicator_progress.setVisible(False)


    def get_result(self) -> dict:
        return {'installed_files': self.installed_files}


