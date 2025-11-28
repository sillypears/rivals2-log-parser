from pathlib import Path
import sys
import os
import logging
import signal
from logging.handlers import RotatingFileHandler
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QLabel,
    QTextEdit,
    QCompleter,
    QMessageBox,
    QFrame,
    QMenu,
    QStatusBar,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices
import requests
import requests.exceptions
import traceback
import json
from datetime import datetime, timezone
from utils.calc_elo import estimate_opponent_elo
import log_parser
from match_duration import roll_up_durations
from log_parser import RIVALS_LOG_FOLDER
from config import Config

config = Config()

logger = logging.getLogger()

characters = {}
stages = {}
moves = {}
top_moves = []
STARTING_DEFAULT = config.opp_dir



def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return base_path / relative_path

minor_version = 0
major_version = 0
version_path = resource_path("version")
major_version, minor_version = version_path.read_text().strip().split('.')

print(f"{major_version}.{minor_version}")

class ParserWorker(QThread):
    finished = Signal(list)
    error = Signal(str)
    update_output = Signal(str)

    def __init__(self, dev, extra_data):
        super().__init__()
        self.dev = dev
        self.extra_data = extra_data

    def run(self):
        try:
            log_parser.setup_logging()
            result = log_parser.parse_log(dev=self.dev, extra_data=self.extra_data)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rivals 2 Log Parser")

        # Set window icon
        icon_file = "icon.ico" if sys.platform.startswith("win") else "icon_rgb.png"
        try:
            from PyInstaller import sys as pyi_sys

            icon_path = os.path.join(pyi_sys._MEIPASS, icon_file)
        except ImportError:
            icon_path = os.path.join(os.path.dirname(__file__), icon_file)
        if os.path.isfile(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)

        # Position window
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width(), 0)

        self.setup_ui()
        self.populate_dropdowns()
        self.setup_reset_menus()
        self.adjustSize()

    def closeEvent(self, event):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top section
        top_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Log Parser")
        self.run_button.clicked.connect(self.run_parser)
        top_layout.addWidget(self.run_button)

        top_layout.addStretch()

        config_button = QPushButton("Config")
        config_button.clicked.connect(lambda: self.open_log_file("config"))
        top_layout.addWidget(config_button)

        app_log_button = QPushButton("App Log")
        app_log_button.clicked.connect(lambda: self.open_log_file("app"))
        top_layout.addWidget(app_log_button)

        rivals_log_button = QPushButton("Rivals Log")
        rivals_log_button.clicked.connect(lambda: self.open_log_file("rivals"))
        top_layout.addWidget(rivals_log_button)

        self.debug_checkbox = QCheckBox("Debug")
        top_layout.addWidget(self.debug_checkbox)

        top_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(
            [
                "Default",
                "Catppuccin Mocha",
                "Catppuccin Latte",
                "Dracula",
                "Nord",
                "Gruvbox Dark",
            ]
        )
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        top_layout.addWidget(self.theme_combo)

        main_layout.addLayout(top_layout)

        # Output text
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(100)
        main_layout.addWidget(self.output_text, 1) 

        # Bottom section
        bottom_layout = QGridLayout()

        # Buttons row
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_top_row)
        bottom_layout.addWidget(refresh_button, 0, 1)

        times_button = QPushButton("Durations")
        times_button.clicked.connect(self.get_match_times)
        bottom_layout.addWidget(times_button, 0, 2)

        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.generate_json)
        bottom_layout.addWidget(copy_button, 0, 3)

        paste_button = QPushButton("Paste JSON")
        paste_button.clicked.connect(self.paste_json)
        bottom_layout.addWidget(paste_button, 0, 4)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_matchup_fields)
        bottom_layout.addWidget(clear_button, 0, 5)

        # ELO section
        bottom_layout.addWidget(QLabel("Opp ELO"), 1, 1)
        self.opp_elo_spin = QSpinBox()
        self.opp_elo_spin.setRange(-2, 3000)
        self.opp_elo_spin.setValue(STARTING_DEFAULT)
        bottom_layout.addWidget(self.opp_elo_spin, 2, 1)

        bottom_layout.addWidget(QLabel("My New ELO"), 1, 2)
        self.my_elo_spin = QSpinBox()
        self.my_elo_spin.setRange(0, 3000)
        self.my_elo_spin.setValue(int(self.get_current_elo()["data"]["current_elo"]))
        bottom_layout.addWidget(self.my_elo_spin, 2, 2)

        bottom_layout.addWidget(QLabel("ELO Delta"), 1, 3)
        self.change_elo_spin = QSpinBox()
        self.change_elo_spin.setRange(-50, 50)
        self.change_elo_spin.setValue(0)
        bottom_layout.addWidget(self.change_elo_spin, 2, 3)

        # Name field
        bottom_layout.addWidget(QLabel("Name"), 3, 1)
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumWidth(30)
        self.name_edit.setCompleter(QCompleter(self.get_opponent_names()))
        bottom_layout.addWidget(self.name_edit, 3, 2, 1, 4)

        # Game sections
        bottom_layout.addWidget(QLabel("OppChar"), 4, 1)
        bottom_layout.addWidget(QLabel("Stage"), 4, 2)
        bottom_layout.addWidget(QLabel("FinalMove"), 4, 3)

        self.opp_combos = []
        self.stage_combos = []
        self.move_combos = []
        self.winner_checks = []
        self.duration_spins = []

        for x in range(3):
            row = x + 5
            bottom_layout.addWidget(QLabel(f"Game {x + 1}"), row, 0, Qt.AlignRight)

            opp_combo = QComboBox()
            opp_combo.addItem("Loading...")
            opp_combo.setMinimumWidth(80)
            bottom_layout.addWidget(opp_combo, row, 1)
            self.opp_combos.append(opp_combo)

            stage_combo = QComboBox()
            stage_combo.addItem("Loading...")
            stage_combo.setMinimumWidth(80)
            bottom_layout.addWidget(stage_combo, row, 2)
            self.stage_combos.append(stage_combo)

            move_combo = QComboBox()
            move_combo.addItem("Loading...")
            move_combo.setMinimumWidth(80)
            bottom_layout.addWidget(move_combo, row, 3)
            self.move_combos.append(move_combo)

            winner_check = QCheckBox("Opp")
            bottom_layout.addWidget(winner_check, row, 4)
            self.winner_checks.append(winner_check)

            duration_spin = QSpinBox()
            duration_spin.setRange(-1, 3000)
            duration_spin.setValue(-1)
            duration_spin.setMinimumWidth(50)
            bottom_layout.addWidget(duration_spin, row, 5)
            self.duration_spins.append(duration_spin)

        main_layout.addLayout(bottom_layout)

        # Set tab order: only name_edit and opp_elo_spin are tabbable
        self.run_button.setFocusPolicy(Qt.NoFocus)
        config_button.setFocusPolicy(Qt.NoFocus)
        app_log_button.setFocusPolicy(Qt.NoFocus)
        rivals_log_button.setFocusPolicy(Qt.NoFocus)
        self.debug_checkbox.setFocusPolicy(Qt.NoFocus)
        self.theme_combo.setFocusPolicy(Qt.NoFocus)
        self.output_text.setFocusPolicy(Qt.NoFocus)
        self.my_elo_spin.setFocusPolicy(Qt.NoFocus)
        self.change_elo_spin.setFocusPolicy(Qt.NoFocus)
        refresh_button.setFocusPolicy(Qt.NoFocus)
        times_button.setFocusPolicy(Qt.NoFocus)
        copy_button.setFocusPolicy(Qt.NoFocus)
        clear_button.setFocusPolicy(Qt.NoFocus)
        paste_button.setFocusPolicy(Qt.NoFocus)
        for combo in self.opp_combos:
            combo.setFocusPolicy(Qt.NoFocus)
        for combo in self.stage_combos:
            combo.setFocusPolicy(Qt.NoFocus)
        for combo in self.move_combos:
            combo.setFocusPolicy(Qt.NoFocus)
        for check in self.winner_checks:
            check.setFocusPolicy(Qt.NoFocus)
        for spin in self.duration_spins:
            spin.setFocusPolicy(Qt.ClickFocus)

        # Connect signals
        self.opp_combos[0].currentTextChanged.connect(self.sync_games)
        
        app_version = f"Version: {major_version}.{minor_version}"
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        version_label = QLabel(app_version)
        version_label.setStyleSheet("QLabel { color: gray; padding: 0 8px; }")
        self.statusBar.addPermanentWidget(version_label)


    def setup_reset_menus(self):
        widgets_to_reset = (
            [
                self.opp_elo_spin,
                self.my_elo_spin,
                self.change_elo_spin,
                self.name_edit,
                self.theme_combo,
                self.debug_checkbox,
            ]
            + self.opp_combos
            + self.stage_combos
            + self.move_combos
            + self.winner_checks
            + self.duration_spins
        )

        for widget in widgets_to_reset:
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda pos, w=widget: self.show_reset_menu(w, pos)
            )

    def show_reset_menu(self, widget, pos):
        self.reset_widget(widget)

    def reset_widget(self, widget):
        if isinstance(widget, QSpinBox):
            if widget == self.opp_elo_spin:
                widget.setValue(STARTING_DEFAULT)
            elif widget == self.my_elo_spin:
                widget.setValue(int(self.get_current_elo()["data"]["current_elo"]))
            elif widget == self.change_elo_spin:
                widget.setValue(0)
            elif widget in self.duration_spins:
                widget.setValue(-1)
        elif isinstance(widget, QComboBox):
            widget.setCurrentIndex(0)
        elif isinstance(widget, QLineEdit):
            widget.clear()
        elif isinstance(widget, QCheckBox):
            widget.setChecked(False)

    def change_theme(self, theme_name):
        themes = {
            "Default": "",
            "Catppuccin Mocha": """
                QWidget {
                    background-color: #1e1e2e;
                    color: #cdd6f4;
                    font-family: Arial;
                }
                QPushButton {
                    background-color: #313244;
                    border: 1px solid #45475a;
                    padding: 5px;
                    color: #cdd6f4;
                }
                QPushButton:hover {
                    background-color: #45475a;
                }
                QTextEdit {
                    background-color: #181825;
                    border: 1px solid #45475a;
                    color: #cdd6f4;
                }
                QComboBox, QSpinBox, QLineEdit {
                    background-color: #313244;
                    border: 1px solid #45475a;
                    color: #cdd6f4;
                }
                QLabel {
                    color: #cdd6f4;
                }
                QCheckBox {
                    color: #cdd6f4;
                }
            """,
            "Catppuccin Latte": """
                QWidget {
                    background-color: #eff1f5;
                    color: #4c4f69;
                    font-family: Arial;
                }
                QPushButton {
                    background-color: #bcc0cc;
                    border: 1px solid #acb0be;
                    padding: 5px;
                    color: #4c4f69;
                }
                QPushButton:hover {
                    background-color: #acb0be;
                }
                QTextEdit {
                    background-color: #e6e9ef;
                    border: 1px solid #acb0be;
                    color: #4c4f69;
                }
                QComboBox, QSpinBox, QLineEdit {
                    background-color: #bcc0cc;
                    border: 1px solid #acb0be;
                    color: #4c4f69;
                }
                QLabel {
                    color: #4c4f69;
                }
                QCheckBox {
                    color: #4c4f69;
                }
            """,
            "Dracula": """
                QWidget {
                    background-color: #282a36;
                    color: #f8f8f2;
                    font-family: Arial;
                }
                QPushButton {
                    background-color: #44475a;
                    border: 1px solid #6272a4;
                    padding: 5px;
                    color: #f8f8f2;
                }
                QPushButton:hover {
                    background-color: #6272a4;
                }
                QTextEdit {
                    background-color: #21222c;
                    border: 1px solid #6272a4;
                    color: #f8f8f2;
                }
                QComboBox, QSpinBox, QLineEdit {
                    background-color: #44475a;
                    border: 1px solid #6272a4;
                    color: #f8f8f2;
                }
                QLabel {
                    color: #f8f8f2;
                }
                QCheckBox {
                    color: #f8f8f2;
                }
            """,
            "Nord": """
                QWidget {
                    background-color: #2e3440;
                    color: #d8dee9;
                    font-family: Arial;
                }
                QPushButton {
                    background-color: #4c566a;
                    border: 1px solid #5e81ac;
                    padding: 5px;
                    color: #d8dee9;
                }
                QPushButton:hover {
                    background-color: #5e81ac;
                }
                QTextEdit {
                    background-color: #3b4252;
                    border: 1px solid #5e81ac;
                    color: #d8dee9;
                }
                QComboBox, QSpinBox, QLineEdit {
                    background-color: #4c566a;
                    border: 1px solid #5e81ac;
                    color: #d8dee9;
                }
                QLabel {
                    color: #d8dee9;
                }
                QCheckBox {
                    color: #d8dee9;
                }
            """,
            "Gruvbox Dark": """
                QWidget {
                    background-color: #282828;
                    color: #ebdbb2;
                    font-family: Arial;
                }
                QPushButton {
                    background-color: #504945;
                    border: 1px solid #7c6f64;
                    padding: 5px;
                    color: #ebdbb2;
                }
                QPushButton:hover {
                    background-color: #7c6f64;
                }
                QTextEdit {
                    background-color: #32302f;
                    border: 1px solid #7c6f64;
                    color: #ebdbb2;
                }
                QComboBox, QSpinBox, QLineEdit {
                    background-color: #504945;
                    border: 1px solid #7c6f64;
                    color: #ebdbb2;
                }
                QLabel {
                    color: #ebdbb2;
                }
                QCheckBox {
                    color: #ebdbb2;
                }
            """,
        }
        self.setStyleSheet(themes.get(theme_name, ""))

    def open_log_file(self, file_name):
        log_path = None
        if file_name == "config":
            log_path = os.path.join("config.ini")
        elif file_name == "app":
            log_path = os.path.join(config.log_dir, config.log_file)
        elif file_name == "rivals":
            log_path = RIVALS_LOG_FOLDER
            if sys.platform.startswith("darwin"):
                pass
            elif os.name == "nt":
                log_path = os.path.join(
                    log_path,
                    "AppData",
                    "Local",
                    "Rivals2",
                    "Saved",
                    "Logs",
                    "Rivals2.log",
                )
            elif os.name == "posix":
                log_path = os.path.join(log_path)
            else:
                return
        if log_path and os.path.exists(log_path):
            import subprocess

            env = os.environ.copy()
            if "LD_LIBRARY_PATH" in env:
                del env["LD_LIBRARY_PATH"]
            if sys.platform == "win32":
                os.startfile(log_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", log_path], env=env)
            else:
                subprocess.run(["xdg-open", log_path], env=env)

    def get_final_move_top_list(self):
        try:
            res = requests.get(
                f"http://{config.be_host}:{config.be_port}/movelist/top", timeout=10
            )
            res.raise_for_status()
            return res.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching final move top list")
            self.output_text.append(
                "Error: Timeout fetching final move data from server."
            )
        except requests.exceptions.ConnectionError:
            logger.error("Connection error fetching final move top list")
            self.output_text.append(
                "Error: Unable to connect to server for final move data."
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching final move top list: {e}")
            self.output_text.append(
                "Error: Failed to fetch final move data from server."
            )
        return {"status": "FAIL", "data": []}

    def get_current_elo(self):
        try:
            res = requests.get(
                f"http://{config.be_host}:{config.be_port}/current_tier", timeout=10
            )
            res.raise_for_status()
            return res.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching current ELO")
            self.output_text.append("Error: Timeout fetching current ELO from server.")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error fetching current ELO")
            self.output_text.append(
                "Error: Unable to connect to server for current ELO."
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching current ELO: {e}")
            self.output_text.append("Error: Failed to fetch current ELO from server.")
        return {
            "status": "FAIL",
            "data": {
                "current_elo": -2,
                "tier": "N/A",
                "tier_short": "N/A",
                "last_game_number": -2,
            },
        }

    def refresh_top_row(self):
        self.my_elo_spin.setValue(int(self.get_current_elo()["data"]["current_elo"]))
        self.change_elo_spin.setValue(0)

    def get_match_times(self):
        data = roll_up_durations([os.path.join(RIVALS_LOG_FOLDER, "Rivals2.log")])
        if not data:
            return
        self.output_text.append(str(data))
        last = data[list(data.keys())[-1]]["durations"]
        for i, d in enumerate(self.duration_spins):
            if i < len(last):
                d.setValue(int(last[i]))
            else:
                d.setValue(-1)

    def get_opponent_names(self):
        try:
            response = requests.get(
                f"http://{config.be_host}:{config.be_port}/opponent_names", timeout=10
            )
            response.raise_for_status()
            return response.json()["data"]["names"]
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching opponent names")
            self.output_text.append(
                "Error: Timeout fetching opponent names from server."
            )
        except requests.exceptions.ConnectionError:
            logger.error("Connection error fetching opponent names")
            self.output_text.append(
                "Error: Unable to connect to server for opponent names."
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching opponent names: {e}")
            self.output_text.append(
                "Error: Failed to fetch opponent names from server."
            )
        return []

    def populate_dropdowns(self):
        stages1 = {}
        character_names = []
        stage_names = []
        move_names = []
        characters_json = {"data": []}
        stage_json = {"data": []}
        moves_json = {"data": []}

        try:
            response = requests.get(
                f"http://{config.be_host}:{config.be_port}/characters", timeout=10
            )
            response.raise_for_status()
            characters_json = response.json()
            for char in characters_json["data"]:
                characters[char["display_name"]] = char["id"]
                if char["id"] == -1:
                    characters["sepior1"] = -1
            character_names = list(characters.keys())
        except requests.exceptions.Timeout:
            self.output_text.append(
                "Error: Timeout fetching character data from server."
            )
            logger.error("Timeout fetching characters")
        except requests.exceptions.ConnectionError:
            self.output_text.append(
                "Error: Unable to connect to server for character data."
            )
            logger.error("Connection error fetching characters")
        except requests.exceptions.RequestException as e:
            self.output_text.append(
                "Error: Failed to fetch character data from server."
            )
            logger.error(f"Request error fetching characters: {e}")

        try:
            response = requests.get(
                f"http://{config.be_host}:{config.be_port}/stages", timeout=10
            )
            response.raise_for_status()
            stage_json = response.json()
            counter = -1
            for stage in stage_json["data"]:
                if stage["stage_type"] != "Doubles":
                    if counter == -1 and stage["counter_pick"] == -1:
                        stages1[stage["display_name"]] = stage["id"]
                    if counter == -1 and stage["counter_pick"] == 0:
                        stages["sepior1"] = -1
                        stages1["sepior1"] = -1
                    if stage["counter_pick"] == 0:
                        counter = 0
                        stages1[stage["display_name"]] = stage["id"]
                    if counter == 0 and stage["counter_pick"] == 1:
                        stages["sepior2"] = -1
                        counter = 1
                    stages[stage["display_name"]] = stage["id"]
            stage_names = list(stages.keys())
        except requests.exceptions.Timeout:
            self.output_text.append("Error: Timeout fetching stage data from server.")
            logger.error("Timeout fetching stages")
        except requests.exceptions.ConnectionError:
            self.output_text.append(
                "Error: Unable to connect to server for stage data."
            )
            logger.error("Connection error fetching stages")
        except requests.exceptions.RequestException as e:
            self.output_text.append("Error: Failed to fetch stage data from server.")
            logger.error(f"Request error fetching stages: {e}")

        try:
            response = requests.get(
                f"http://{config.be_host}:{config.be_port}/movelist", timeout=10
            )
            response.raise_for_status()
            moves_json = response.json()
            sorted_moves = sorted(moves_json["data"], key=lambda x: x["list_order"])
            top_moves_list = [
                x["final_move_name"] for x in self.get_final_move_top_list()["data"]
            ]
            for move in sorted_moves:
                display_name = move["display_name"]
                if display_name in top_moves_list:
                    display_name += " *"
                moves[display_name] = move["id"]
                if move["id"] == -1:
                    moves["sepior"] = -1
            move_names = list(moves.keys())
        except requests.exceptions.Timeout:
            self.output_text.append("Error: Timeout fetching move data from server.")
            logger.error("Timeout fetching moves")
        except requests.exceptions.ConnectionError:
            self.output_text.append("Error: Unable to connect to server for move data.")
            logger.error("Connection error fetching moves")
        except requests.exceptions.RequestException as e:
            self.output_text.append("Error: Failed to fetch move data from server.")
            logger.error(f"Request error fetching moves: {e}")

        self.output_text.append(
            f"Fetched {len([x for x in characters_json['data'] if x['list_order'] > 0])} characters, {len([x for x in stage_json['data'] if x['list_order'] > 0])} stages and {len([x for x in moves_json['data'] if x['list_order'] > 0])} moves."
        )

        for x in range(3):
            self.opp_combos[x].clear()
            self.opp_combos[x].addItems(character_names)
            self.stage_combos[x].clear()
            if x == 0:
                self.stage_combos[x].addItems(list(stages1.keys()))
            else:
                self.stage_combos[x].addItems(stage_names)
            self.move_combos[x].clear()
            self.move_combos[x].addItems(move_names)

        # Add separators for "sepior" items
        for combo in self.opp_combos + self.stage_combos + self.move_combos:
            separators = []
            for i in range(combo.count()):
                if combo.itemText(i).startswith("sepior"):
                    separators.append(i)
            for idx in reversed(separators):
                combo.insertSeparator(idx)
                combo.removeItem(idx + 1)

    def are_required_dropdowns_filled(self):
        return all(
            [
                self.opp_combos[0].currentText().strip() != "N/A",
                self.stage_combos[0].currentText().strip() != "N/A",
                self.opp_combos[1].currentText().strip() != "N/A",
                self.stage_combos[1].currentText().strip() != "N/A",
            ]
        )

    def clear_matchup_fields(self):
        for combo in self.opp_combos + self.stage_combos + self.move_combos:
            combo.setCurrentText("N/A")
        for check in self.winner_checks:
            check.setChecked(False)
        for spin in self.duration_spins:
            spin.setValue(-1)
        self.name_edit.clear()
        self.opp_elo_spin.setValue(STARTING_DEFAULT)

    def generate_json(self):
        elo_values = self.get_current_elo()
        jsond = {}
        jsond["match_date"] = (
            datetime.now(timezone.utc)
            .replace(tzinfo=None)
            .isoformat(timespec="seconds")
        )
        jsond["elo_rank_new"] = self.my_elo_spin.value()
        jsond["elo_change"] = self.change_elo_spin.value()
        jsond["elo_rank_old"] = jsond["elo_rank_new"] - jsond["elo_change"]
        jsond["match_win"] = 1 if jsond["elo_change"] >= 0 else 0
        jsond["match_forfeit"] = -1
        jsond["ranked_game_number"] = int(elo_values["data"]["last_game_number"]) + 1
        jsond["total_wins"] = (
            int(elo_values["data"]["total_wins"]) + 1
            if jsond["match_win"]
            else int(elo_values["data"]["total_wins"])
        )
        jsond["win_streak_value"] = (
            int(elo_values["data"]["win_streak_value"]) + 1
            if jsond["match_win"]
            else int(elo_values["data"]["win_streak_value"])
        )
        jsond["opponent_elo"] = self.opp_elo_spin.value()
        jsond["opponent_name"] = self.name_edit.text() or ""
        for x in range(3):
            jsond[f"game_{x + 1}_char_pick"] = 2
            jsond[f"game_{x + 1}_opponent_pick"] = int(
                characters.get(self.opp_combos[x].currentText(), -1)
            )
            jsond[f"game_{x + 1}_stage"] = int(
                stages.get(self.stage_combos[x].currentText(), -1)
            )
            jsond[f"game_{x + 1}_final_move_id"] = int(
                moves.get(self.move_combos[x].currentText().replace(" *", ""), -1)
            )
            jsond[f"game_{x + 1}_winner"] = (
                2
                if self.winner_checks[x].isChecked()
                else (1 if self.opp_combos[x].currentText() != "N/A" else -1)
            )
            jsond[f"game_{x + 1}_duration"] = self.duration_spins[x].value()

        def get_final_move_id(data):
            for i in [3, 2, 1]:
                fmid = data[f"game_{i}_final_move_id"]
                if fmid != -1:
                    return fmid
            return -2

        jsond["final_move_id"] = get_final_move_id(jsond)
        jsond["notes"] = "Added via JSON lol"
        logger.debug(json.dumps(jsond))
        clipboard = QApplication.clipboard()
        clipboard.setText(json.dumps(jsond, indent=4))

    def paste_json(self):
        clipboard = QApplication.clipboard()
        try:
            data = json.loads(clipboard.text())
            self.my_elo_spin.setValue(data.get("elo_rank_new", 0))
            self.change_elo_spin.setValue(data.get("elo_change", 0))
            self.opp_elo_spin.setValue(data.get("opponent_elo", 1000))
            self.name_edit.setText(data.get("opponent_name", ""))
            for x in range(3):
                opp_id = data.get(f"game_{x + 1}_opponent_pick", -1)
                opp_name = next(
                    (k for k, v in characters.items() if v == opp_id), "N/A"
                )
                self.opp_combos[x].setCurrentText(opp_name)
                stage_id = data.get(f"game_{x + 1}_stage", -1)
                stage_name = next(
                    (k for k, v in stages.items() if v == stage_id), "N/A"
                )
                self.stage_combos[x].setCurrentText(stage_name)
                move_id = data.get(f"game_{x + 1}_final_move_id", -1)
                move_name = next((k for k, v in moves.items() if v == move_id), "N/A")
                self.move_combos[x].setCurrentText(move_name)
                winner = data.get(f"game_{x + 1}_winner", -1)
                self.winner_checks[x].setChecked(winner == 2)
                duration = data.get(f"game_{x + 1}_duration", -1)
                self.duration_spins[x].setValue(duration)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Error", "Invalid JSON in clipboard.")

    def run_parser(self):
        self.run_button.setEnabled(False)
        extra_data = {}
        if self.are_required_dropdowns_filled():
            extra_data = {
                "game_1_char_pick": int(characters.get("Loxodont", -1)),
                "game_1_opponent_pick": int(
                    characters.get(self.opp_combos[0].currentText(), -1)
                ),
                "game_1_stage": int(stages.get(self.stage_combos[0].currentText(), -1)),
                "game_1_winner": 2
                if self.winner_checks[0].isChecked()
                else (1 if self.opp_combos[0].currentText() != "N/A" else -1),
                "game_1_final_move_id": int(
                    moves.get(self.move_combos[0].currentText().replace(" *", ""), -1)
                ),
                "game_1_duration": self.duration_spins[0].value(),
                "game_2_char_pick": int(characters.get("Loxodont", -1)),
                "game_2_opponent_pick": int(
                    characters.get(self.opp_combos[1].currentText(), -1)
                ),
                "game_2_stage": int(stages.get(self.stage_combos[1].currentText(), -1)),
                "game_2_winner": 2
                if self.winner_checks[1].isChecked()
                else (1 if self.opp_combos[1].currentText() != "N/A" else -1),
                "game_2_final_move_id": int(
                    moves.get(self.move_combos[1].currentText().replace(" *", ""), -1)
                ),
                "game_2_duration": self.duration_spins[1].value(),
                "game_3_char_pick": int(characters.get("Loxodont", -1)),
                "game_3_opponent_pick": int(
                    characters.get(self.opp_combos[2].currentText(), -1)
                ),
                "game_3_stage": int(stages.get(self.stage_combos[2].currentText(), -1)),
                "game_3_winner": 2
                if self.winner_checks[2].isChecked()
                else (1 if self.opp_combos[2].currentText() != "N/A" else -1),
                "game_3_final_move_id": int(
                    moves.get(self.move_combos[2].currentText().replace(" *", ""), -1)
                ),
                "game_3_duration": self.duration_spins[2].value(),
                "opponent_elo": self.opp_elo_spin.value(),
                "opponent_name": self.name_edit.text() or "",
                "final_move_id": -1,
            }
        self.worker = ParserWorker(self.debug_checkbox.isChecked(), extra_data)
        self.worker.finished.connect(self.on_parser_finished)
        self.worker.error.connect(self.on_parser_error)
        self.worker.start()

    def on_parser_finished(self, result):
        if result == -1:
            self.output_text.append("No matches found or no new matches to add.")
        else:
            self.output_text.append(
                f"Log parsed. Added {len(result)} match{'es' if len(result) != 1 else ''}: {','.join(f'{str(x.elo_rank_new)}({str(x.elo_change)})' for x in result) if result else ''}"
            )
        self.run_button.setEnabled(True)
        self.refresh_top_row()
        self.name_edit.setCompleter(QCompleter(self.get_opponent_names()))

    def on_parser_error(self, error_msg):
        self.output_text.append(f"Error: {error_msg}")
        self.run_button.setEnabled(True)

    def sync_games(self):
        self.opp_combos[1].setCurrentText(self.opp_combos[0].currentText())


def setup_logging():
    os.makedirs(config.log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)
    logger.info(logger.level)

    formatter = logging.Formatter(
        "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        os.path.join(config.log_dir, config.log_file),
        maxBytes=int(config.max_log_size),
        backupCount=int(config.backup_count),
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)


if __name__ == "__main__":
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    sys.exit(app.exec())

