import os
import platform
import subprocess
import re
import logging
from logging.handlers import RotatingFileHandler
from collections import deque
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
)
from PySide6.QtGui import QFont

from config import Config

config = Config()


class PingWorker(QThread):
    new_ping = Signal(str)

    def __init__(self, target="8.8.8.8", parent=None):
        super().__init__(parent)
        self.target = target
        self._running = True
        os.makedirs(config.app_log_dir, exist_ok=True)
        self.recent_lines = deque(maxlen=500)

        log_path = os.path.join(config.app_log_dir, "ping_check.log")
        self.logger = logging.getLogger("ping_check")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        handler = RotatingFileHandler(log_path, maxBytes=1_048_576, backupCount=3)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        self.logger.addHandler(handler)

    def run(self):
        system = platform.system().lower()
        while self._running:
            start = datetime.now()
            try:
                if system == "windows":
                    cmd = ["ping", "-n", "1", self.target]
                else:
                    cmd = ["ping", "-c", "1", "-W", "2", self.target]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10
                )
                time_ms = None
                if result.returncode == 0:
                    m = re.search(
                        r'time[=<]\s*(\d+\.?\d*)', result.stdout, re.IGNORECASE
                    )
                    if m:
                        time_ms = float(m.group(1))
                    status = f"{time_ms}ms" if time_ms is not None else "OK"
                else:
                    m = re.search(
                        r'time[=<]\s*(\d+\.?\d*)', result.stdout, re.IGNORECASE
                    )
                    if m:
                        time_ms = float(m.group(1))
                        status = f"{time_ms}ms"
                    else:
                        status = "FAIL"
            except subprocess.TimeoutExpired:
                status = "TIMEOUT"
            except Exception as e:
                status = f"ERROR: {e}"

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"{self.target} - {status}"
            display = f"{ts} - {line}"
            self.recent_lines.append(display)
            try:
                self.logger.info(line)
            except Exception:
                pass
            self.new_ping.emit(display)

            elapsed = (datetime.now() - start).total_seconds()
            sleep_ms = max(100, int((1.0 - elapsed) * 1000))
            for _ in range(sleep_ms // 100):
                if not self._running:
                    return
                self.msleep(100)
            if not self._running:
                return

    def stop(self):
        self._running = False


class PingDialog(QDialog):
    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ping Check - 8.8.8.8")
        self.setMinimumSize(650, 450)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        font = QFont()
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(9)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit, 1)

        for line in list(worker.recent_lines):
            self.text_edit.append(line)

        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        self.worker = worker
        worker.new_ping.connect(self._on_ping)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _on_ping(self, line):
        self.text_edit.append(line)
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        try:
            self.worker.new_ping.disconnect(self._on_ping)
        except (TypeError, RuntimeError):
            pass
        super().closeEvent(event)
