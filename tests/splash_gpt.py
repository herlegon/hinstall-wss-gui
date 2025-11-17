from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal
import time

class InstallerThread(QThread):
    status_update = Signal(str)
    finished_installation = Signal()

    def run(self):
        steps = [
            "Checking internet connection...",
            "Downloading Python...",
            "Installing packages...",
            "Downloading pynnlib...",
            "Finalizing..."
        ]
        for step in steps:
            self.status_update.emit(step)
            time.sleep(1)  # replace with real installation functions
        self.finished_installation.emit()  # signals that installation is complete

class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Company Installer")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.logo = QLabel("COMPANY LOGO")
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)

        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # endless
        layout.addWidget(self.progress)

        self.setLayout(layout)

        self.thread = InstallerThread()
        self.thread.status_update.connect(self.status_label.setText)
        self.thread.finished_installation.connect(self.launch_main_app)
        self.thread.start()

    def launch_main_app(self):
        self.close()  # close installer window
        # Here you can launch your main GUI or backend
        # Example:
        # from main_app import MainWindow
        # self.main_window = MainWindow()
        # self.main_window.show()

        print("launch application")

if __name__ == "__main__":
    app = QApplication([])
    window = InstallerWindow()
    window.show()
    app.exec()
