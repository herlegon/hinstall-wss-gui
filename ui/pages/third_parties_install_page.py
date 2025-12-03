from pprint import pprint
import sys
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
from hinstall import (
    ExtPackages,
    download_install_ext_packages,
)
from hwidgets import (
    Theme,
)
from hytils import lightgreen, red, yellow
from ..designer.ui_third_party_install_widget import Ui_ThirdPartiesInstall
from .page import Page
from .ffmpeg_selection_page import FfmpegSelection
from ..install_workers import InstallWorker


class ThirdPartiesInstallPage(Page, Ui_ThirdPartiesInstall):
    # signal_settings_modified = Signal()

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = "Third parties"
        self.progress_bar.setValue(0)

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
        print(yellow(f"{self.objectName()}"))
        pprint(settings)
        self.settings: dict = settings
        self.packages = None


        self.packages = self.settings.get('packages', None)
        if self.packages is None:
            return

        ffmpeg_selection = self.settings.get('ffmpeg_selection', "")
        if ffmpeg_selection:
            self.packages = self.packages.get_all_except('ffmpeg')


    def start_installation(self):
        print(red("start install"))
        print(self.packages)

        # No packages to install
        if self.packages is None or not self.packages:
            self._on_finished(success=True, files=[])
            return


        print(self.packages)

        installed: bool = download_install_ext_packages(
            packages=self.packages,
            reinstall=True,
            threads=1,
            use_local_host=True
        )
        if installed:
            print(lightgreen("All packages installed"))

        else:
            self.progress_bar.setValue(0)
            self.indicator_step.setText("Failed.")
            self.indicator_progress
            print(red("Error: missing package(s)"))

        # """Start the installation worker."""
        # steps = [
        #     "Downloading third-party software...",
        #     "Installing components...",
        #     "Finalizing installation..."
        # ]

        # # Create and start worker
        # self.worker = InstallWorker(steps)
        # self.worker.progress.connect(self._update_progress)
        # self.worker.status.connect(self.label.setText)
        # self.worker.finished_signal.connect(self._on_finished)

        # # Reset progress bar
        # self.progress_bar.setValue(0)
        # self.label_2.setText("0%")

        # Start worker
        # self.worker.start()


    def _update_progress(self, value: int):
        """Update progress bar and percentage label."""
        self.progress_bar.setValue(value)
        self.indicator_progress.setText(f"{value}%")


    def _on_finished(self, success: bool, files: list):
        """Handle completion of installation."""
        self._installation_started = False
        self.progress_bar.setValue(100)

        if success:
            self.indicator_step.setText("Installation complete.")
            self.indicator_progress.setText("100%")
            self.installed_files = files
            self.completed.emit(True)
        else:
            self.indicator_step.setText("Installation failed.")
            self.indicator_progress.setText("✗")
            self.completed.emit(False)


    def get_result(self) -> dict:
        return {
            'installed_files': self.installed_files
        }


