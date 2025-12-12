from pathlib import Path
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
    Theme,
    HProgressBar,
    HIndetProgressBarM2,
)
from hytils import lightgreen, red
from ..workers.backend_install_worker import BackendInstallWorker
from ..designer.ui_backend_install_widget import Ui_BackendWidget
from .page import Page
from hinstall import (
    parse_config_,
    ExtPackages,
    g_backend_dirs,
    download_install_ext_packages,
    get_python_version,
    ilog,
)
from tests.local_rehost import get_rehost_dir


class BackendInstallPage(Page, Ui_BackendWidget):

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme],
        app_cfg: dict[str, str],
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = f"Processing Server"

        self.subtitle.setWordWrap(True)
        size_policy = self.subtitle.sizePolicy()
        self.subtitle.setSizePolicy(
            size_policy.horizontalPolicy(), QSizePolicy.Policy.Minimum
        )
        self.subtitle.setMinimumHeight(0)
        self.subtitle.setMaximumHeight(1024)
        self.subtitle.adjustSize()
        self.adjustSize()

        self.reset_widgets()

        self.user_settings: dict[str, Any] = {}
        self.app_cfg = app_cfg

        self.indet_progress_bar: HIndetProgressBarM2 = HIndetProgressBarM2(
            self, theme=theme
        )
        self.progress_layout.addWidget(self.indet_progress_bar)
        self.indet_progress_bar.setVisible(False)
        self.reset_widgets()
        self.indicator_step_stylesheet = self.indicator_step.styleSheet()


    def reset_widgets(self) -> None:
        super().reset_widgets()
        self.indicator_step.setText("Installing backend...")
        self.indicator_progress.setText("")


    def update_settings(self, settings: dict[str, Any]) -> None:
        self.reset_widgets()
        self.user_settings = settings


    def start_installation(self):
        self.indicator_step.setText("Installing backend...")
        # Create a worker that will communicate with the websocket server
        self.worker: BackendInstallWorker = BackendInstallWorker(
            settings=self.user_settings,
            app_cfg=self.app_cfg,
            stages=1,
        )
        self.worker.progress.connect(self.slot_update_progress)
        self.worker.task_name.connect(self.indicator_step.setText)
        self.worker.finished.connect(self.slot_on_finished)

        # Start worker
        self.worker.start()





    def get_result(self) -> dict:
        return {'installed_files': self.installed_files}

