from argparse import Namespace
from functools import partial
from pathlib import Path
from pprint import pprint
import sys
import tomllib
from typing import Any, Type

from PySide6.QtCore import (
    Qt, QTimer,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QApplication,
    QSizePolicy,
)

from hinstall import (
    parse_config_,
    ExtPackages,
)
from hwidgets import (
    HComment,
    HHorizontalDivider,
    HStrongButton,
    StyleManager,
    HStepIndicator,
    HStrongGreyButton,
    HFramelessButton,
    HLogViewer,
    HProgressBar,
)
from PySide6.QtWidgets import QDialog, QLabel
from .install_workers import CleanupWorker

from .title_bar import TitleBar

from .pages.page import Page
from .pages.welcome_page import WelcomePage
from .pages.ffmpeg_selection_page import FFmpegSelectionPage
from .pages.third_parties_install_page import ThirdPartiesInstallPage
from .pages.backend_install_page import BackendInstallPage
from .pages.ai_resource_install_page import AiResourceInstallPage


class InstallerWindow(QMainWindow):
    def __init__(
        self,
        tool: str = "hconvert",
        args: Namespace = None
    ):
        super().__init__()

        # self.dev: bool = args.dev
        self.dev: bool = True

        theme = StyleManager().get_theme()

        config_fp = (Path(__file__).parent.parent / "tests" / "configs" / f"{tool}.toml").resolve()

        # Load config and populate a list of pages
        print(f"loading config: {config_fp}")
        with open(config_fp, "rb") as f:
            data: dict[str, Any] = tomllib.load(f)
        packages_cfg = parse_config_(data)
        xtal_pkgs = ExtPackages(packages_cfg, sys.platform)

        self.pages: list[Type[Page]] = [
            WelcomePage(self, theme=theme),
            ThirdPartiesInstallPage(self, theme=theme),
            BackendInstallPage(self, theme=theme),
            AiResourceInstallPage(self, theme=theme),
        ]
        if xtal_pkgs.get_by_key('ffmpeg') is not None:
            self.pages.insert(1, FFmpegSelectionPage(self, theme=theme))

        self.settings: dict[str, Any] = {
            'packages': xtal_pkgs,
        }


        self.setWindowTitle("First time installer")
        self.setFixedWidth(900)
        content_hpadding: int= 64
        content_vpadding: int = 16
        for p in self.pages:
            p.setMainLayoutSpacing(12)
            p.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            # Don't call show() here - it will be called by QStackedWidget when page becomes current
            p.updateGeometry()

        # Frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Main container with rounded corners and border
        container = QFrame()
        container.setObjectName("main_container")
        default_style = theme.default

        # Enable proper rendering for rounded corners on Linux
        container.setAttribute(Qt.WA_StyledBackground, True)
        radius: int = default_style.radius * 3
        # Apply stylesheet to container for rounded border
        main_stylesheet = f"""
            QFrame#main_container {{
                background-color: {theme.window_bgd};
                border-radius: {radius}px;
                border: 1px solid {default_style.selection};
            }}
        """
        container.setStyleSheet(main_stylesheet)
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(1, 1, 1, 1)

        # Title bar
        self.title_bar = TitleBar(
            parent=self,
            theme=theme,
            title=self.windowTitle(),
            icon=None
        )

        # Step indicator (wrapped in container for proper centering)
        step_container = QWidget()
        step_container.setStyleSheet(f"background-color: {theme.window_bgd};")
        step_container_layout = QHBoxLayout(step_container)
        step_container_layout.setContentsMargins(0, 0, 0, 0)

        self.step_indicator = HStepIndicator(self, theme=theme)
        step_labels: list[str] = list(
            [p.step_label() for p in self.pages]
        )
        self.step_indicator.setSteps(step_labels)
        self.step_indicator.setStyleSheet(f"background-color: {theme.window_bgd};")

        # Center the step indicator in the container
        step_container_layout.addStretch()
        step_container_layout.addWidget(self.step_indicator)
        step_container_layout.addStretch()


        # Page area
        page_widget = QWidget()
        page_widget.setStyleSheet(f"background-color: {theme.window_bgd};")
        content_layout = QVBoxLayout(page_widget)
        content_layout.setContentsMargins(
            content_hpadding, content_vpadding, content_hpadding, 4
        )

        # Pages in a QstackedWidget
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(
            self.stack.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Minimum
        )

        # Set the stack to resize to the current widget's size
        from PySide6.QtWidgets import QLayout
        if self.stack.layout():
            self.stack.layout().setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.stack.setStyleSheet(f"background-color: {theme.window_bgd};")
        for p in self.pages:
            self.stack.addWidget(p)

        # Update sizing when page changes
        # self.stack.currentChanged.connect(self._update_stack_sizing)

        content_layout.addWidget(self.stack)


        # Navigation buttons
        self.cancel_button = HStrongGreyButton(self, theme=theme, text="Cancel")
        self.cancel_button.clicked.connect(self.slot_cancel)
        self.cancel_button.setEnabled(True)

        if self.dev:
            self.previous_button = HStrongGreyButton(self, theme=theme, text="Previous")
            self.previous_button.clicked.connect(self.slot_go_previous)
            self.previous_button.setEnabled(True)

        self.next_button = HStrongButton(self, theme=theme, text="Next →")
        self.next_button.clicked.connect(self.slot_go_next)
        self.next_button.setEnabled(True)

        navigation_widget = QWidget()
        navigation_widget.setFixedHeight(64)
        navigation_widget.setStyleSheet(f"""
            background-color: transparent;
            border-bottom-left-radius: {radius}px;
            border-bottom-right-radius: {radius}px;
        """)

        navigation_layout = QHBoxLayout(navigation_widget)
        navigation_layout.setContentsMargins(content_hpadding,8,24,8)
        navigation_layout.setSpacing(16)

        self.info = HComment(parent=self, theme=theme, text = "Requires at least 8GB. (Available: 30GB)")
        self.info.setWordWrap(False)
        navigation_layout.addWidget(self.info)
        navigation_layout.addStretch()
        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addWidget(self.cancel_button)
        navigation_layout.addWidget(self.next_button)


        # Log Section (Button + Viewer)
        self.log_container = QWidget()
        self.log_container.setStyleSheet(f"background-color: {theme.window_bgd}")
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(
            content_hpadding, 8, 0, 4
        )
        self.log_layout.setSpacing(4)

        # Log Toggle Button
        self.log_button = HFramelessButton(parent=self, text="Show Log", theme=theme)
        self.log_button.setCheckable(True)
        self.log_button.setFixedWidth(self.log_button.sizeHint().width())

        self.log_viewer = HLogViewer(parent=self, theme=theme)
        self.log_viewer.setVisible(False)
        self.log_layout.addWidget(self.log_button)
        self.log_layout.addWidget(self.log_viewer)


        # Window layout
        main_layout.addWidget(self.title_bar)
        # main_layout.addWidget(HHorizontalDivider(parent=self, theme=theme))
        main_layout.addWidget(step_container)
        main_layout.addWidget(HHorizontalDivider(parent=self, theme=theme))
        main_layout.addWidget(page_widget)
        main_layout.addWidget(self.log_container)
        main_layout.addWidget(HHorizontalDivider(parent=self, theme=theme))
        main_layout.addWidget(navigation_widget)


        # Initial
        self.current_index: int = 0
        self.step_indicator.setCurrentStep(self.current_index)
        self.stack.setCurrentIndex(self.current_index)

        # Adjust window size to fit content
        # self._update_stack_sizing()
        self.adjustSize()


        # Signals
        for p in self.pages:
            p.completed.connect(partial(self.slot_task_completed, p))

        # Track all installed files across all pages
        self.all_installed_files: list[str] = []
        # self.page2.install_complete.connect(lambda: self.next_button.setEnabled(True))
        # self.page3.install_complete.connect(self._go_next)
        # self.page4.install_complete.connect(lambda: self.next_button.setEnabled(True))
        # self.page5.install_complete.connect(self._on_complete)

        # self.log_btn.clicked.connect(self._toggle_log)
        # self.log_layout.addWidget(self.log_btn)
        # self.page5.log_message.connect(self._append_log)


        # # Start
        # QTimer.singleShot(500, self.page1.start_installation)

        self.center_on_screen()
        self.setFixedSize(self.sizeHint())

        # Ensure the first page's showEvent is triggered after window is fully set up
        # Use a timer to ensure all initialization is complete
        page: Type[Page] = self.stack.currentWidget()
        page.update_settings(self.settings)
        QTimer.singleShot(50, lambda: self.stack.currentWidget().show())


    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)



    def _update_stack_sizing(self, index=None):
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if i == self.stack.currentIndex():
                widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
                widget.show()
                widget.updateGeometry()
            else:
                widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
                widget.hide() # Explicitly hide, though stack does this

        # Force stack to recalculate
        self.stack.adjustSize()
        self.stack.updateGeometry()


    def slot_task_completed(self, p: Type[Page], result: bool) -> None:
        """Handle task completion from a page."""
        if not result:
            print("Error during installation")
            # TODO: show error dialog
            self.next_button.setEnabled(False)
        else:
            # Track files installed by this page
            files = p.get_installed_files()
            self.all_installed_files.extend(files)
            print(f"Page completed. Installed files: {files}")

            # Enable next button
            self.next_button.setEnabled(True)


    def slot_go_next(self):
        """Handle next button click."""
        print("next")
        current = self.stack.currentIndex()

        #  Update settings
        page: Type[Page] = self.stack.currentWidget()
        results = page.get_result()
        self.settings.update(results)

        # End of installation
        if current >= self.stack.count() - 1:
            # TODO: last tasks
            self.close()
            return

        # Update settings before showing it
        current += 1
        next_page: Type[Page] = self.stack.widget(current)
        next_page.update_settings(self.settings)


        self.stack.setCurrentIndex(current)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setVisible(True)

        # Check if new page has progress bar
        current_page = self.pages[current]
        if current_page.has_progress_bar():
            # Disable next button until installation completes
            self.next_button.setEnabled(False)
        else:
            # No progress bar, next button stays enabled
            self.next_button.setEnabled(True)

        if current >= self.stack.count() - 1:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setVisible(False)
            self.next_button.setText("Finish")

            if self.dev:
                self.cancel_button.setEnabled(True)
                self.cancel_button.setVisible(True)

        self.step_indicator.setCurrentStep(current)
        self.current_index = current
        if current == 0:
            self.info.setVisible(True)
        else:
            self.info.setVisible(False)

        # Resize window to fit the new page
        # self.adjustSize()


    def slot_go_previous(self):
        current = self.stack.currentIndex()
        if current > 0:
            current -= 1
            self.stack.setCurrentIndex(current)
            self.step_indicator.setCurrentStep(current)
            self.current_index = current

            # Check if new page has progress bar
            current_page = self.pages[current]
            if current_page.has_progress_bar():
                # Disable next button until installation completes
                self.next_button.setEnabled(False)
            else:
                # No progress bar, next button stays enabled
                self.next_button.setEnabled(True)

            # Resize window to fit the new page
            # self.adjustSize()


    def slot_cancel(self):
        """Handle cancel button click with confirmation."""
        from PySide6.QtWidgets import QMessageBox

        # Show confirmation dialog
        theme = self.theme if hasattr(self, 'theme') else StyleManager().get_theme()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Cancel Installation")
        msg_box.setText("Are you sure you want to cancel the installation?")
        msg_box.setInformativeText("This will stop the current process and remove all installed files.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        result = msg_box.exec()

        if result == QMessageBox.Yes:
            # Cancel any running workers
            current_page = self.pages[self.current_index]
            current_page.cancel_worker()

            # Show cleanup dialog
            self._show_cleanup_dialog()


    def _show_cleanup_dialog(self):
        """Show a dialog with progress bar while cleaning up installed files."""
        theme = StyleManager().get_theme()

        # Create cleanup dialog
        cleanup_dialog = QDialog(self)
        cleanup_dialog.setWindowTitle("Cleaning Up")
        cleanup_dialog.setModal(True)
        cleanup_dialog.setFixedSize(400, 150)

        # Dialog layout
        dialog_layout = QVBoxLayout(cleanup_dialog)
        dialog_layout.setContentsMargins(24, 24, 24, 24)
        dialog_layout.setSpacing(16)

        # Status label
        status_label = QLabel("Removing installed files...")
        dialog_layout.addWidget(status_label)

        # Progress bar
        progress_bar = HProgressBar(cleanup_dialog, theme=theme)
        progress_bar.setValue(0)
        dialog_layout.addWidget(progress_bar)

        # File count label
        file_count_label = QLabel(f"0 / {len(self.all_installed_files)} files removed")
        dialog_layout.addWidget(file_count_label)

        # Create cleanup worker
        cleanup_worker = CleanupWorker(self.all_installed_files)

        # Connect signals
        def update_progress(value):
            progress_bar.setValue(value)
            removed = int(value * len(self.all_installed_files) / 100)
            file_count_label.setText(f"{removed} / {len(self.all_installed_files)} files removed")

        cleanup_worker.progress.connect(update_progress)
        cleanup_worker.status.connect(status_label.setText)
        cleanup_worker.finished_signal.connect(lambda success: self._on_cleanup_finished(cleanup_dialog, success))

        # Start cleanup
        cleanup_worker.start()

        # Show dialog
        cleanup_dialog.exec()


    def _on_cleanup_finished(self, dialog: QDialog, success: bool):
        """Handle cleanup completion."""
        if success:
            # Close the dialog
            dialog.accept()
            # Close the installer window
            self.close()
        else:
            # Show error but still close
            dialog.accept()
            self.close()


    def _on_complete(self):
        print("completed")
        self.next_button.setEnabled(True)
        self.next_button.clicked.disconnect()
        self.next_button.clicked.connect(self.close)

    # def _toggle_log(self, checked):
    #     self.log_viewer.setVisible(checked)
    #     if checked:
    #         self.log_button.setText("Hide Log")
    #         self.setFixedSize(750, 760) # Expand window (more height for button + log + padding)
    #     else:
    #         self.log_button.setText("Show Log")
    #         self.setFixedSize(750, 580) # Restore size

    def _append_log(self, message):
        self.log_viewer.append(message)
        # Auto-scroll
        sb = self.log_viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

