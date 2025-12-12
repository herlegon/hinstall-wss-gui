from PySide6.QtCore import (
    Qt,
    QPoint,
)

from PySide6.QtWidgets import (
    QMessageBox,
    QWidget,
    QLabel,
    QGridLayout,
)
from hwidgets import (
    Theme,
    HHorizontalDivider,
)


class __HMessageBox(QMessageBox):
    def __init__(
        self,
        /,
        parent: QWidget | None = None,
        *,
        theme: Theme,
    ):
        super().__init__(parent)
        self.theme = theme

        # Frameless
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self._update_stylesheet()
        self._layout_arranged = False


    def showEvent(self, event):
        self._arrange_layout()
        self.adjustSize()

        parent = self.parentWidget()
        if parent:
            parent_pos = parent.mapToGlobal(QPoint(0, 0))
            x = parent_pos.x() + (parent.width() - self.width()) // 2
            y = parent_pos.y() + (parent.height() - self.height()) // 2
            self.move(x, y)
        super().showEvent(event)



    def _update_stylesheet(self) -> None:
        mb_style = self.theme.frame
        border_color = self.theme.default.selection
        thickness = 1

        stylesheet = """
            QMessageBox {{
                background-color: {bgd};
                border-radius: {radius};
                border: {thickness}px solid {border};
                color: {font_color};
                margin: 0px;
                padding: 0px;
            }}
            QLabel {{
                background-color: transparent;
                color: {font_color}
            }}
        """.format(
            bgd=mb_style.bgd,
            radius=int(mb_style.radius * 1.5),
            thickness=thickness,
            border=border_color,
            font_color=self.theme.label.font_color,
        )
        self.setStyleSheet(stylesheet)
        self.layout().setContentsMargins(0,0,0,0)


    def _arrange_layout(self):
        if self._layout_arranged:
            return
        self._layout_arranged = True

        layout = self.layout()
        if not isinstance(layout, QGridLayout):
            return

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Get current items
        items = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            # We need to store position
            r, c, rs, cs = layout.getItemPosition(i)
            items.append((item, r, c, rs, cs))

        # Remove all items from layout
        while layout.count():
            layout.takeAt(0)

        # Add Title
        title = QLabel(self.windowTitle(), self)
        title.setStyleSheet(f"""
            color: {self.theme.label.font_color};
            font-weight: bold;
            font-size: 11pt;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title, 0, 0, 1, -1)

        # Add Divider
        divider = HHorizontalDivider(parent=self, theme=self.theme)
        layout.addWidget(divider, 1, 0, 1, -1)

        # Create a container for the content
        content_widget = QWidget(self)
        content_layout = QGridLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        # Re-add original items to the content layout
        for item, r, c, rs, cs in items:
            content_layout.addItem(item, r, c, rs, cs)

        layout.addWidget(content_widget, 2, 0, 1, -1)




    @staticmethod
    def critical(parent: QWidget, title: str, text: str, theme: Theme) -> int:
        msg = HMessageBox(parent, theme=theme)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        return msg.exec()


