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
)
from hwidgets import (
    Theme,
)
from ..designer.ui_welcome_widget import Ui_WelcomeWidget
from .base_page import BasePage


class WelcomePage(BasePage, Ui_WelcomeWidget):
    # signal_settings_modified = Signal()

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = f"Welcome"

        self.checkbox_custom_dir.setEnabled(False)
        self.icon_button_browse.setEnabled(False)
        # self.h_icon_button_browse.released.connect(self.slot_select_dir)


    def get_user_settings(self) -> dict:
        return {
            'do_cache': self.checkbox_cache.isChecked(),
            'use_as_global': self.checkbox_use_as_global.isChecked(),
            'checkbox_custom_dir': self.checkbox_custom_dir.isChecked(),
            'custom_dir': self.lineedit_custom_dir.text()
        }


    def slot_select_dir(self):
        print("select directory")


    def get_result(self) -> dict:
        return self.get_user_settings()

