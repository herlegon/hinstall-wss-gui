
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


from backend_dirs import BackendDirectories
from install_worker import InstallWorker



class InstallationWindow(QWidget):
    """Installation/Update window with logo and progress"""

    def __init__(
        self,
        backend_dirs: BackendDirectories,
        logo_path=None,
        keep_installers: bool = False
    ):
        super().__init__()
        self.backend_dirs = backend_dirs
        self.logo_path = logo_path
        self.keep_installers = keep_installers
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Backend Installation")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo
        if self.logo_path and os.path.exists(self.logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(self.logo_path)
            pixmap = pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        else:
            # Placeholder
            company_label = QLabel("YOUR COMPANY")
            company_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            company_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(company_label)

        layout.addStretch()

        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.status_label)

        # Progress bar (endless mode)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Endless mode
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        self.setLayout(layout)
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def start_installation(self):
        self.worker = InstallWorker(
            self.backend_dirs,
            keep_installers=self.keep_installers
        )
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.installation_finished)
        self.worker.start()

    def update_status(self, message):
        self.status_label.setText(message)

    def installation_finished(self, success, message):
        self.progress_bar.setMaximum(100)  # Stop endless mode
        self.progress_bar.setValue(100)

        if success:
            QMessageBox.information(self, "Success", message)
            self.close()
            print("launch application")

            # Here you can launch your main GUI or backend
            # from main_app import MainWindow
            # self.main_window = MainWindow()
            # self.main_window.show()


        else:
            QMessageBox.critical(self, "Installation Failed", message)
            QApplication.quit()





# def main():
#     app = QApplication(sys.argv)

#     # Configure your paths
#     backend_dir = get_backend_directory()
#     logo_path = "logo.png"  # Path to your company logo

#     # For testing: use local packages directory
#     # Set to None to always use internet
#     local_packages_dir = Path("./local_packages")  # or None

#     # Check if first time installation
#     keep_installers = False
#     if is_first_time_install(backend_dir):
#         # Show first time setup dialog
#         setup_dialog = FirstTimeSetupDialog()
#         keep_installers = setup_dialog.get_choice()

#     window = InstallationWindow(backend_dir, logo_path, local_packages_dir, keep_installers)
#     window.show()
#     window.start_installation()

#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()
