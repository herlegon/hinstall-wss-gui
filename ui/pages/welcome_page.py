from pprint import pprint
import shutil
import os

from typing import Any, Type
from PySide6.QtCore import (
    Signal,
    QTimer,
)

from PySide6.QtGui import (
    QPaintEvent,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QFileDialog,
)

from hwidgets import (
    Theme,
)
from ..designer.ui_welcome_widget import Ui_WelcomeWidget
from .page import Page




class WelcomePage(Page, Ui_WelcomeWidget):
    # signal_settings_modified = Signal()

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = f"Welcome"

        self.timer_check_space = QTimer(self)
        self.timer_check_space.timeout.connect(self.calculate_required_disk_space)

        self.reset_widgets()
        if self.icon_button_browse.isEnabled():
            self.icon_button_browse.released.connect(self.slot_select_dir)

        self.checkbox_cache.clicked.connect(self.calculate_required_disk_space)
        self.lineedit_custom_dir.textChanged.connect(self.calculate_required_disk_space)


    def reset_widgets(self) -> None:
        super().reset_widgets()

        # Enable cache by default
        self.checkbox_cache.setChecked(True)

        # USe a common directory for all Herlegon software
        self.checkbox_use_as_global.setChecked(True)
        self.checkbox_use_as_global.setEnabled(False)
        self.checkbox_use_as_global.setVisible(False)

        # custom dir not yet available
        self.checkbox_custom_dir.setChecked(False)
        self.checkbox_custom_dir.setEnabled(False)
        self.lineedit_custom_dir.setText("")
        self.lineedit_custom_dir.setEnabled(False)
        self.lineedit_custom_dir.setReadOnly(True)
        self.icon_button_browse.setEnabled(False)


    def update_settings(self, settings: dict[str, Any]) -> None:
        b = settings.get('cache', None)
        if b is not None:
            self.checkbox_cache.setChecked(b)

        b = settings.get('use_as_global', None)
        if b is not None:
            self.checkbox_use_as_global.setChecked(b)

        b = settings.get('custom_install_dir', None)
        if b is not None:
            self.checkbox_custom_dir.setChecked(b)

        s = settings.get('install_dir', None)
        if s is not None:
            self.lineedit_custom_dir.setText(s)

        self.calculate_required_disk_space()


    def get_result(self) -> dict:
        return {
            'cache': self.checkbox_cache.isChecked(),
            'custom_install_dir': self.checkbox_custom_dir.isChecked(),
            'install_dir': self.lineedit_custom_dir.text(),
            'use_as_global': self.checkbox_use_as_global.isChecked(),
        }


    def slot_select_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            self.lineedit_custom_dir.text() or os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.lineedit_custom_dir.setText(directory)


    def calculate_required_disk_space(self) -> None:
        path = self.lineedit_custom_dir.text()
        if not path:
            path = "."

        try:
            if not os.path.exists(path):
                # Check parent directory if path doesn't exist
                parent = os.path.dirname(path)
                if parent and os.path.exists(parent):
                    path = parent
                else:
                    path = "."
            
            total, used, free = shutil.disk_usage(path)
            free_space = free // (2**30)  # Convert to GB
        except OSError:
            free_space = 0

        required_space = 4
        if self.checkbox_cache.isChecked():
            required_space += 4

        self.comment_required_disk_space.setText(
            f"Required space to install this product: {required_space} GB (Available: {free_space}GB)"
        )

        if free_space < required_space:
            if not self.timer_check_space.isActive():
                self.timer_check_space.start(3000)
            self.completed.emit(False)
        else:
            if self.timer_check_space.isActive():
                self.timer_check_space.stop()
            self.completed.emit(True)


