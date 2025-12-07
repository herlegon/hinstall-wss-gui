from pprint import pprint
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

        self.reset_widgets()
        if self.icon_button_browse.isEnabled():
            self.icon_button_browse.released.connect(self.slot_select_dir)


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


    def get_result(self) -> dict:
        return {
            'cache': self.checkbox_cache.isChecked(),
            'custom_install_dir': self.checkbox_custom_dir.isChecked(),
            'install_dir': self.lineedit_custom_dir.text(),
            'use_as_global': self.checkbox_use_as_global.isChecked(),
        }


    def slot_select_dir(self):
        print("select directory")




