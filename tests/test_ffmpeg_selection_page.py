'''\
Simple test script to display the FFmpegSelectionPage.
Make sure to activate the conda environment `f` before running this script:
    conda activate f
'''\

from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from hytils import lightgreen, red, yellow
sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import ilog
from ui.pages.ffmpeg_selection_page import FFmpegSelectionPage
from hwidgets import Theme, StyleManager


def main():
    # Create the Qt application
    app = QApplication(sys.argv)
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # Create a main window to host the page
    main_window = QMainWindow()
    main_window.setWindowTitle("FFmpeg Selection Page Test")

    # **Resize handling**
    # Set an initial width; let height adapt to the page's minimum size
    main_window.resize(800, 0)
    # Adjust the window size to fit the central widget's minimum height
    main_window.adjustSize()

    # Instantiate the page with a default theme (you may replace with your custom Theme subclass)
    page = FFmpegSelectionPage(parent=main_window, theme=StyleManager().get_theme())
    main_window.setCentralWidget(page)
    main_window.show()
    # Execute the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
