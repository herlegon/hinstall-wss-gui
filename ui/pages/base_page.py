from abc import ABC, abstractmethod
from typing import Any, Type
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
)



class BasePage(QWidget, ABC):
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


    def step_label(self) -> str:
        return self._step_label


    def setMainLayoutSpacing(self, spacing: int) -> None:
        self.main_layout.setSpacing(spacing)


    @abstractmethod
    def get_result(self) -> dict[str, Any]:
        """return a dict of settings
        """
        pass
