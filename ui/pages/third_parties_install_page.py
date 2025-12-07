from pathlib import Path
from pprint import pprint
import sys
from typing import Any, Type
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
    QSizePolicy
)
from hwidgets import (
    Theme,
)
from hytils import lightgreen, red, yellow
from ..designer.ui_third_party_install_widget import Ui_ThirdPartiesInstall
from .page import Page
from .ffmpeg_selection_page import FfmpegSelection
from ..workers.pkg_install_worker import PkgInstallWorker

from hinstall import (
    parse_config_,
    ExtPackages,
    g_backend_dirs,
    download_install_ext_packages,
)
from tests.local_rehost import get_rehost_dir


class ThirdPartiesInstallPage(Page, Ui_ThirdPartiesInstall):

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = "Third parties"
        self.progress_bar.setValue(0)
        self.progress_bar.setAnimationDuration(20)
        self.indicator_progress.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Settings used to filter some packages to install
        self.settings = {}

        # Packages to install
        self.packages: ExtPackages = None

        self.reset_widgets()


    def reset_widgets(self) -> None:
        super().reset_widgets()

        # Use by default
        self.indicator_step.setText("Initializing")
        self.indicator_progress.setText("")


    def update_settings(self, settings: dict[str, Any]) -> None:
        self.settings: dict = settings
        self.packages = None

        self.packages = self.settings.get('packages', None)
        if self.packages is None:
            return

        ffmpeg_selection = self.settings.get('ffmpeg_selection', "")
        if ffmpeg_selection:
            self.packages = self.packages.get_all_except('ffmpeg')


    def start_installation(self):
        # No packages to install
        if self.packages is None or not self.packages:
            self.slot_on_finished(success=True, files=[])
            return

        # Set the local rehost
        g_backend_dirs.local_host = get_rehost_dir()

        # Create and start worker
        self.worker: PkgInstallWorker = PkgInstallWorker(
            packages=self.packages,
            reinstall=True,
            threads=1,
            use_local_host=True
        )
        self.worker.progress.connect(self.slot_update_progress)
        self.worker.task_name.connect(self.indicator_step.setText)
        self.worker.finished.connect(self.slot_on_finished)

        # Start worker
        self.worker.start()


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


    def get_result(self) -> dict:
        return {
            'installed_files': self.installed_files
        }


