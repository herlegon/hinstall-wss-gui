import sys
import time
from pathlib import Path
from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QTextEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QRegion


class InstallWorker(QThread):
    """Worker thread for simulating installation process.
    
    For demo purposes, uses a 3-second timer.
    Tracks files created/modified during installation.
    """
    progress = Signal(int)
    status = Signal(str)
    finished_signal = Signal(bool, list)  # success, list of files

    def __init__(self, steps):
        super().__init__()
        self.steps = steps
        self.installed_files: List[str] = []
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the installation."""
        self._cancelled = True

    def run(self):
        """Simulate installation with a 3-second timer for demo."""
        try:
            # Demo: 3 second installation with 10 update steps
            total_time_ms = 3000
            update_interval_ms = 100
            num_updates = total_time_ms // update_interval_ms
            
            for i in range(num_updates):
                if self._cancelled:
                    self.status.emit("Installation cancelled")
                    self.finished_signal.emit(False, self.installed_files)
                    return
                
                # Update progress
                progress = int((i + 1) * 100 / num_updates)
                self.progress.emit(progress)
                
                # Simulate different status messages
                if i < num_updates // 3:
                    step_name = self.steps[0] if self.steps else "Downloading..."
                elif i < 2 * num_updates // 3:
                    step_name = self.steps[1] if len(self.steps) > 1 else "Installing..."
                else:
                    step_name = self.steps[2] if len(self.steps) > 2 else "Finalizing..."
                
                self.status.emit(step_name)
                
                # Simulate file creation at different stages
                if i == num_updates // 4:
                    self.installed_files.append("/tmp/demo_file_1.txt")
                elif i == num_updates // 2:
                    self.installed_files.append("/tmp/demo_file_2.txt")
                    self.installed_files.append("/tmp/demo_lib.so")
                elif i == 3 * num_updates // 4:
                    self.installed_files.append("/tmp/demo_config.ini")
                
                self.msleep(update_interval_ms)
            
            # Completion
            self.progress.emit(100)
            self.status.emit("Installation complete")
            self.finished_signal.emit(True, self.installed_files)
            
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, self.installed_files)


class CleanupWorker(QThread):
    """Worker thread for cleaning up installed files.
    
    Shows progress while removing files that were installed.
    """
    progress = Signal(int)
    status = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, files_to_remove: List[str]):
        super().__init__()
        self.files_to_remove = files_to_remove

    def run(self):
        """Remove files and report progress."""
        try:
            total = len(self.files_to_remove)
            if total == 0:
                self.status.emit("No files to remove")
                self.progress.emit(100)
                self.finished_signal.emit(True)
                return
            
            for i, file_path in enumerate(self.files_to_remove):
                self.status.emit(f"Removing {Path(file_path).name}...")
                
                # Simulate file removal (for demo, don't actually delete)
                # In production: Path(file_path).unlink(missing_ok=True)
                self.msleep(200)  # Simulate deletion time
                
                progress = int((i + 1) * 100 / total)
                self.progress.emit(progress)
            
            self.status.emit("Cleanup complete")
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.status.emit(f"Cleanup error: {str(e)}")
            self.finished_signal.emit(False)

