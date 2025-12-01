from argparse import ArgumentParser
import os
from pathlib import Path
import signal
import sys

from PySide6.QtWidgets import QApplication

sys.path.append(str(Path(__file__).resolve().parent / "ui"))

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "herlegon_install.gui"
    )




def main():
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument(
        "--dev",
        "-dev",
        action="store_true",
        required=False,
        help="Unlock all for dev"
    )

    args = parser.parse_args()


    QApplication.setStyle("Fusion")
    application = QApplication(sys.argv)


    # from install.splash import run_installer_and_wait


    # run_installer_and_wait(
    #     logo_path="logo.png",
    #     rehost_dir=None,
    # )


    from .hinstall_window import InstallerWindow
    installer_window = InstallerWindow(args=args)
    installer_window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

