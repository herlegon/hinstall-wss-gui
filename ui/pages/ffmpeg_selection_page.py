from typing import Type
from PySide6.QtCore import (
    Signal,
)
from PySide6.QtGui import (
    QPaintEvent,
    QFont,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSizePolicy,
)
from hwidgets import (
    Theme,
)
from ..designer.ui_ffmpeg_selection_widget import Ui_FFmpegSelectionWidget
from .base_page import BasePage


class FFmpegSelectionPage(BasePage, Ui_FFmpegSelectionWidget):
    # signal_settings_modified = Signal()

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = f"FFmpeg Notice & Selection"

        # Set page size policy to contract to minimum height
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )

        # Set disclaimer to use minimum height
        font = QFont(
            self.disclaimer.font().family(),
            pointSize=8,
            weight=self.disclaimer.font().weight(),
            italic=True,
        )
        self.disclaimer.setFont(font)
        self.disclaimer.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )

        # Force layout updates
        # self.adjustSize()
        # self.updateGeometry()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.set_has_progress_bar(False)  # No progress bar on this page
        # self.show()
        # self.updateGeometry()

        self.invalidate_all_layouts()


    def invalidate_all_layouts(self):
        # Invalidate the layout of the current widget
        layout = self.layout()
        if layout:
            layout.invalidate()  # Invalidate the layout to recalculate geometry

        # Recursively invalidate all layouts of child widgets
        for child in self.findChildren(QWidget):
            child.layout().invalidate() if child.layout() else None

        # Trigger a redraw and geometry recalculation
        self.update()

        # Optionally, you can also call adjustSize to make sure the widget resizes to fit its content
        self.adjustSize()


    def get_selection(self) -> str:
        if self.radio_button_user.isChecked():
            return 'user'

        if self.radio_button_third_party.isChecked():
            return 'third-party'

        return 'minimal'


    def get_user_settings(self) -> dict:
        return {
            'selection': self.get_selection(),
        }


    def get_result(self) -> dict:
        return self.get_user_settings()


