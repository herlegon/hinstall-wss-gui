from abc import ABC, abstractmethod, ABCMeta
from pathlib import Path
import time
from typing import Any, Type, List, Optional, Literal
from PySide6.QtCore import (
    Signal,
    QTimer,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLayout,
)
from hwidgets import (
    Theme,
    HProgressBarType,
    HLabel,
    HIndetProgressBarM2,
    HProgressBar,
)
from hytils import red, yellow


# Get the metaclass of QWidget
QWidgetMeta = type(QWidget)

# Create combined metaclass - order matters!
class QWidgetABCMeta(ABCMeta, QWidgetMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls

    def __call__(cls, *args, **kwargs):
        if getattr(cls, "__abstractmethods__", None):
            raise TypeError(
                f"Can't instantiate abstract class {cls.__name__} "
                f"with abstract methods {', '.join(cls.__abstractmethods__)}"
            )
        return super().__call__(*args, **kwargs)

# BasePage with combined metaclass
class Page(QWidget, metaclass=QWidgetABCMeta):
    completed: Signal = Signal(bool)

    def __init__(
        self,
        parent: QMainWindow,
        theme: Type[Theme],
    ):
        super().__init__(parent=parent)
        self.main_window = parent
        self._step_label: str = ""
        self.theme = theme

        self.main_layout: QLayout

        # Worker and installation tracking
        self.worker: Optional[Any] = None
        self.installed_files: List[str] = []
        self._installation_started = False
        self._has_progress_bar: bool | None = None

        # For pages with progress bar
        self.indicator_progress_stylesheet = ""
        try:
            self.indicator_progress_stylesheet = self.indicator_progress.styleSheet()
        except:
            pass



    def _check_for_progress_bar(self) -> bool:
        """Check if this page has a progress bar and set the flag."""
        self._has_progress_bar = self.has_progress_bar()
        if self._has_progress_bar:
            return True
        return False


    def reset_widgets(self) -> None:
        self._has_progress_bar = self.has_progress_bar()
        self.reset_progress_bars()


    def showEvent(self, event):
        """Called when the page becomes visible."""
        # Schedule a check for progress bars after the widget is fully initialized
        if self._has_progress_bar is None:
            self._has_progress_bar = self.has_progress_bar()
            self.reset_progress_bars()

        elif not self._installation_started:
            self.reset_progress_bars()

        super().showEvent(event)

        # Start installation only once when page is shown
        if self._has_progress_bar and not self._installation_started:
            self._installation_started = True
            # Use QTimer to ensure UI is fully rendered
            QTimer.singleShot(10, self._start_installation_if_exists)


    def _start_installation_if_exists(self):
        """Call start_installation if it exists."""
        if hasattr(self, 'start_installation') and callable(self.start_installation):
            self.start_installation()


    def step_label(self) -> str:
        return self._step_label


    def setMainLayoutSpacing(self, spacing: int) -> None:
        self.main_layout.setSpacing(spacing)


    def has_progress_bar(self) -> bool:
        """Check if the QWidget contains any specific progress bars of type HProgressBarType."""
        # Iterate through all children widgets of the given QWidget
        for child in self.findChildren(QWidget):
            if isinstance(child, HProgressBarType):
                return True
        return False


    def reset_progress_bars(self) -> None:
        for child in self.findChildren(QWidget):
            if isinstance(child, HProgressBarType):
                child.reset()


    def get_installed_files(self) -> List[str]:
        """Return list of files created/modified during installation."""
        return self.installed_files


    def cancel_worker(self) -> None:
        """Cancel the running worker if it exists."""
        if self.worker and hasattr(self.worker, 'cancel'):
            self.worker.cancel()


    @abstractmethod
    def get_result(self) -> dict[str, Any]:
        """return a dict of settings
        """
        pass


    @abstractmethod
    def update_settings(self, settings: dict[str, Any]) -> None:
        """Updated settings from the previous pages
        """
        pass


    # Specific to children that have Progress Bar
    def set_progress_value(self, value: int | str) -> None:
        self.indicator_progress: HLabel
        self.indicator_progress_stylesheet: str
        try:
            progress_text: str = ""
            if isinstance(value, int):
                if value == 100:
                    progress_text = "✔"
                    self.indicator_progress.setStyleSheet(
                        self.indicator_progress_stylesheet +
                        rf"QLabel{{font-size: 24px; color: green;}}"
                    )
                    self.indicator_progress.setVisible(True)

                elif value == -1:
                    progress_text = "❌"
                    self.indicator_progress.setStyleSheet(
                        self.indicator_progress_stylesheet +
                        rf"QLabel{{font-size: 24px; color: red;}}"
                    )
                    self.indicator_progress.setVisible(True)

                else:
                    progress_text = f"{int(value + 0.5)}%"
            # else:
            #     self.indicator_progress.setStyleSheet(self.indicator_progress_stylesheet)
            #     progress_text = f"{value}"
            if progress_text:
                self.indicator_progress.setText(progress_text)

        except Exception as e:
            print(red(f"exception: {str(e)}"))


    def slot_update_progress(self, type: Literal['progress', 'indet'], value: int):
        """Update progress bar and percentage label."""
        self.progress_bar: HProgressBar
        self.indet_progress_bar: HIndetProgressBarM2
        try:
            # Show/Hide the correct progress bar
            if type == 'indet':
                if not self.indet_progress_bar.isVisible():
                    self.progress_bar.setVisible(False)
                    self.indet_progress_bar.setVisible(True)
                    self.indet_progress_bar.start()
                    self.indicator_progress.setVisible(False)

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
                self.set_progress_value(100)

            self.progress_bar.setValue(value)
            self.set_progress_value(value)

            if duration:
                self.progress_bar.setAnimationDuration(value)

        except Exception as e:
            print(red(f"exception: {str(e)}"))



    def slot_on_finished(self, success: bool, files: list[Path]):
        self.progress_bar: HProgressBar
        self.indet_progress_bar: HIndetProgressBarM2
        try:
            self._installation_started = False

            duration = self.progress_bar.getAnimationDuration()
            self.progress_bar.setAnimationDuration(0.5)
            self.indicator_progress.setVisible(True)

            if success:
                self.progress_bar.setValue(100)
                self.indet_progress_bar.stop()
                self.set_progress_value(100)

            else:
                self.progress_bar.setValue(0)
                self.indet_progress_bar.stop()
                self.set_progress_value(-1)

            self.progress_bar.setAnimationDuration(duration)

            self.installed_files = files
            time.sleep(0.8)
            self.completed.emit(success)
        except Exception as e:
            print(f"exception: {str(e)}")
