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

TRESHOLD = config.ping_threshold
PING_GOLD_WINDOW = config.ping_gold_window
PING_RED_WINDOW = config.ping_red_window

class PingWorker(QThread):
    new_ping = Signal(str)
    ping_result = Signal(object)

    def __init__(self, targets=None, parent=None):
        super().__init__(parent)
        self.targets = targets or config.ping_targets
        self._running = True
        os.makedirs(config.app_log_dir, exist_ok=True)
        self.recent_lines = deque(maxlen=500)
        self.recent_results = {}

        log_path = os.path.join(config.app_log_dir, "ping_check.log")
        self.logger = logging.getLogger("ping_check")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        handler = RotatingFileHandler(log_path, maxBytes=1_048_576, backupCount=3)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        self.logger.addHandler(handler)

    def _ping_one(self, target, system):
        ping_data = {"target": target, "time_ms": None, "failed": False}
        try:
            if system == "windows":
                cmd = ["ping", "-n", "1", target]
            else:
                cmd = ["ping", "-c", "1", "-W", "2", target]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            time_ms = None
            time_over_thresh = ""
            if result.returncode == 0:
                m = re.search(r'time[=<]\s*(\d+\.?\d*)', result.stdout, re.IGNORECASE)
                if m:
                    time_ms = float(m.group(1))
                    ping_data["time_ms"] = time_ms
                if time_ms is not None and time_ms > TRESHOLD:
                    time_over_thresh = " <--"
                ping_data["status"] = f"{time_ms}ms{time_over_thresh}" if time_ms is not None else "OK"
            else:
                m = re.search(r'time[=<]\s*(\d+\.?\d*)', result.stdout, re.IGNORECASE)
                if m:
                    time_ms = float(m.group(1))
                    ping_data["time_ms"] = time_ms
                    ping_data["status"] = f"{time_ms}ms"
                else:
                    ping_data["failed"] = True
                    ping_data["status"] = "FAIL"
        except subprocess.TimeoutExpired:
            ping_data["failed"] = True
            ping_data["status"] = "TIMEOUT"
        except Exception as e:
            ping_data["failed"] = True
            ping_data["status"] = f"ERROR: {e}"
        return ping_data

    def run(self):
        system = platform.system().lower()
        target_width = max(len(t) for t in self.targets)
        while self._running:
            round_start = datetime.now()
            for target in self.targets:
                if not self._running:
                    return
                ping_data = self._ping_one(target, system)
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                line = f"{target:{target_width}} - {ping_data['status']}"
                display = f"{ts} - {line}"
                self.recent_lines.append(display)
                if target not in self.recent_results:
                    self.recent_results[target] = deque(maxlen=PING_GOLD_WINDOW)
                self.recent_results[target].append(ping_data)
                try:
                    self.logger.info(line)
                except Exception:
                    pass
                self.new_ping.emit(display)
                self.ping_result.emit(ping_data)

            elapsed = (datetime.now() - round_start).total_seconds()
            sleep_ms = max(100, int((config.ping_interval - elapsed) * 1000))
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
        targets_str = ", ".join(worker.targets)
        self.setWindowTitle(f"Ping Check - {targets_str}")
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
