import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop
import sys

module_path: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "install")
)
sys.path.append(module_path)


from utils import get_backend_dirs, get_rehost_dir

def run_installer_and_wait(
    logo_path=None,
    reinstall: bool = False,
    rehost_dir: Path = None,
    dev: bool = False
):

    from install_window import InstallationWindow
    from first_time_dialog import FirstTimeSetupDialog
    backend_dirs = get_backend_dirs()

    if dev:
        rehost_dir = (
            rehost_dir
            if rehost_dir is not None
            else get_rehost_dir()
        )
        if rehost_dir is not None and rehost_dir.exists():
            backend_dirs.local_rehost = rehost_dir

    if reinstall:
        for subdir in backend_dirs.app.iterdir():
            if subdir.is_dir():
                subdir.rmdir()

    # Check if this is the first time installation
    is_first_time = not backend_dirs.app.exists()

    # First-time dialog
    keep_installers = False
    if is_first_time or reinstall:
        dialog = FirstTimeSetupDialog()
        keep_installers = dialog.get_choice()

    # Create installer window
    installer = InstallationWindow(
        backend_dirs=backend_dirs,
        logo_path=logo_path,
        keep_installers=keep_installers
    )

    installer.show()
    installer.start_installation()

    # Block here until installation_window closes
    loop = QEventLoop()
    installer.destroyed.connect(loop.quit)
    loop.exec()

    return True  # or return relevant info







if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    application = QApplication(sys.argv)
    QApplication.setStyle("Fusion")

    run_installer_and_wait(
        logo_path="logo.png",
        rehost_dir=None,
    )
