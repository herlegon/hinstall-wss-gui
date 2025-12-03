from typing import Any, Literal, Type
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
from hytils import red
from ..designer.ui_ffmpeg_selection_widget import Ui_FFmpegSelectionWidget
from .page import Page


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
        # self.show()
        # self.updateGeometry()

        self.invalidate_all_layouts()
        self.reset_widgets()


    def reset_widgets(self) -> None:
        super().reset_widgets()

        # Use by default
        self.radio_button_minimal.setChecked(True)



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


