from typing import Any, Literal, Type
from PySide6.QtCore import (
    Signal,
)
from PySide6.QtGui import (
    QPaintEvent,
    QFont,
    QPainter,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSizePolicy,
)
from hwidgets import (
    Theme,
)
from hytils import red
from ..designer.ui_ffmpeg_selection_widget import Ui_FFmpegSelectionWidget
from .page import Page

from hwidgets.debug import *


FfmpegSelection = Literal['lgpl', 'gpl', 'user']


class FFmpegSelectionPage(Page, Ui_FFmpegSelectionWidget):
    # signal_settings_modified = Signal()

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme]
    ):
        super().__init__(parent=parent, theme=theme)
        self.setupUi(self, theme=theme)
        self._step_label = f"FFmpeg Notice & Selection"

        # Set page size policy to fit content
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.setMinimumHeight(0)

        # Set disclaimer to properly calculate height for word-wrapped text
        self.disclaimer.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        # Remove minimum height constraint to allow proper expansion
        self.disclaimer.setMinimumHeight(0)
        self.disclaimer.setMaximumHeight(16777215)  # Remove any max height constraint

        # Set maximum width to match content area (window width - padding)
        # This is necessary for QLabel to properly calculate height for word-wrapped text
        content_width = 900 - (64 * 2)  # window width - horizontal padding
        self.disclaimer.setMaximumWidth(content_width)

        font = QFont(
            self.disclaimer.font().family(),
            pointSize=8,
            weight=self.disclaimer.font().weight(),
            italic=True,
        )
        self.disclaimer.setFont(font)

        # Modify the vertical spacer to not take space from disclaimer
        # Find the spacer item in the layout
        for i in range(self.selection_layout.count()):
            item = self.selection_layout.itemAt(i)
            if item and item.spacerItem():
                # Change spacer from Expanding to Fixed with small size
                spacer = item.spacerItem()
                spacer.changeSize(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
                break

        # Force the disclaimer to recalculate its size based on content
        self.disclaimer.adjustSize()
        self.disclaimer.updateGeometry()

        # Explicitly set minimum height based on size hint to ensure full text is visible
        hint_height = self.disclaimer.sizeHint().height()
        self.disclaimer.setMinimumHeight(hint_height)

        # Invalidate layouts to force recalculation
        self.selection_layout.invalidate()
        self.selection_layout.activate()
        self.main_layout.invalidate()
        self.main_layout.activate()

        # Update the page geometry
        self.updateGeometry()

        self.reset_widgets()


    def reset_widgets(self) -> None:
        super().reset_widgets()

        # Use by default
        self.radio_button_minimal.setChecked(True)
        self.line_edit_ffmpeg_dir.setText("")
        self.line_edit_ffmpeg_dir.setEnabled(False)
        self.outlined_button_browse.setEnabled(False)


    def update_settings(self, settings: dict[str, Any]) -> None:
        self.set_default_settings(settings=settings)


    def get_selection(self) -> FfmpegSelection:
        if self.radio_button_user.isChecked():
            return 'user'
        if self.radio_button_third_party.isChecked():
            return 'gpl'
        return 'lgpl'


    def get_user_settings(self) -> dict:
        return {
            'ffmpeg_selection': self.get_selection(),
        }


    def set_default_settings(self, settings: dict[str, Any]) -> None:
        ffmpeg_selection: FfmpegSelection = settings.get('ffmpeg_selection', 'lgpl')
        if ffmpeg_selection == 'gpl':
            self.radio_button_third_party.setChecked(True)
        elif ffmpeg_selection == 'user':
            self.radio_button_user.setChecked(True)
        else:
            # minimal (lgpl)
            self.radio_button_minimal.setChecked(True)



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




    def get_result(self) -> dict:
        return self.get_user_settings()


