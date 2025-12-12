from typing import Any, Literal, Type
import os
import sys
import subprocess



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
    QFileDialog,
)



from hwidgets import (
    Theme,
    HMessageBox,
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

        self.outlined_button_browse.clicked.connect(self.slot_select_ffmpeg)

        self.radio_button_minimal.toggled.connect(self._update_ui_state)
        self.radio_button_third_party.toggled.connect(self._update_ui_state)
        self.radio_button_user.toggled.connect(self._update_ui_state)

        self.reset_widgets()


    def reset_widgets(self) -> None:
        super().reset_widgets()

        # Use by default
        self.radio_button_minimal.setChecked(True)
        self.line_edit_ffmpeg_dir.setText("")
        self.line_edit_ffmpeg_dir.setEnabled(False)
        self.line_edit_ffmpeg_dir.setReadOnly(True)
        self.outlined_button_browse.setEnabled(True)


    def update_settings(self, settings: dict[str, Any]) -> None:
        self.set_default_settings(settings=settings)


    def get_selection(self) -> FfmpegSelection:
        if self.radio_button_user.isChecked():
            return 'user'

        if self.radio_button_third_party.isChecked():
            return 'gpl'

        return 'lgpl'


    def get_result(self) -> dict:
        return {
            'ffmpeg_selection': self.get_selection(),
            'ffmpeg_user_dir': self.line_edit_ffmpeg_dir.text(),
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

        path = settings.get('ffmpeg_user_dir', "")
        self.line_edit_ffmpeg_dir.setText(path)

        self._update_ui_state()


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
    def slot_select_ffmpeg(self):
        self.radio_button_user.blockSignals(True)
        self.radio_button_user.setChecked(True)
        self.radio_button_user.blockSignals(False)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FFmpeg Executable",
            "",
            "FFmpeg (ffmpeg.exe)" if sys.platform == 'win32' else "FFmpeg (ffmpeg)"
        )

        if not file_path:
            return

        parent_dir = os.path.dirname(file_path)
        if self.validate_ffmpeg_dir(parent_dir):
            self.line_edit_ffmpeg_dir.setText(str(file_path))
        else:
            HMessageBox.critical(
                self,
                "Invalid FFmpeg/FFprobe",
                "FFmpeg and FFprobe must be in the same directory and be valid executables.",
                theme=self.theme,
            )


    def validate_ffmpeg_dir(self, directory: str) -> bool:
        ffmpeg_exe = "ffmpeg.exe" if sys.platform == 'win32' else "ffmpeg"
        ffprobe_exe = "ffprobe.exe" if sys.platform == 'win32' else "ffprobe"

        ffmpeg_path = os.path.join(directory, ffmpeg_exe)
        ffprobe_path = os.path.join(directory, ffprobe_exe)

        if not (os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path)):
            self.completed.emit(False)
            return False

        # Check if they are valid executables
        if not (self._check_executable(ffmpeg_path) and self._check_executable(ffprobe_path)):
            self.completed.emit(False)
            return False

        self.completed.emit(True)
        return True


    def _check_executable(self, path: str) -> bool:
        try:
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(
                [path, "-version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )
            return True

        except (subprocess.CalledProcessError, OSError):
            return False


    def _update_ui_state(self):
        is_user_defined = self.radio_button_user.isChecked()

        self.line_edit_ffmpeg_dir.setEnabled(is_user_defined)
        # self.outlined_button_browse.setEnabled(is_user_defined)

        if is_user_defined:
            self.validate_ffmpeg_dir(self.line_edit_ffmpeg_dir.text())
        else:
            self.completed.emit(True)





