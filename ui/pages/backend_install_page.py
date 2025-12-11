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
        )
        self.worker.progress.connect(self.slot_update_progress)
        self.worker.task_name.connect(self.indicator_step.setText)
        self.worker.finished.connect(self.slot_on_finished)

        # Start worker
        self.worker.start()


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

