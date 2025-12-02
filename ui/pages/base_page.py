from abc import ABC, abstractmethod, ABCMeta
from typing import Any, Type, List, Optional
from PySide6.QtCore import (
    Signal,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLayout,
)
from hwidgets import (
    Theme,
    HProgressBarType
)


# Create a metaclass that combines QWidget's metaclass and ABCMeta
class QWidgetABCMeta(type(QWidget), ABCMeta):
    pass


class BasePage(QWidget, ABC, metaclass=QWidgetABCMeta):
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
        self._has_progress_bar = False
        self._installation_started = False  # Flag to prevent multiple starts


    def showEvent(self, event):
        """Called when the page becomes visible."""
        super().showEvent(event)
        # Start installation only once when page is shown
        if self._has_progress_bar and not self._installation_started:
            self._installation_started = True
            # Use QTimer to ensure UI is fully rendered
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._start_installation_if_exists)


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
            if isinstance(child, HProgressBarType):  # Check if child is one of the HProgressBarType
                return True
        return False


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

