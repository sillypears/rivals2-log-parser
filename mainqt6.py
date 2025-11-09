#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import logging
import logging.handlers
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timezone

import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QComboBox, QCheckBox,
    QSpinBox, QLineEdit, QTextEdit, QMessageBox, QSpacerItem,
    QSizePolicy, QFileDialog, QCompleter
)
from PyQt6.QtGui import QIcon, QClipboard
from PyQt6.QtCore import Qt, QTimer, QStringListModel, QEvent

# ----------------------------------------------------------------------
# 3rd-party imports (your existing modules)
# ----------------------------------------------------------------------
from config import Config
import log_parser
from utils.calc_elo import estimate_opponent_elo
from match_duration import roll_up_durations
from log_parser import RIVALS_LOG_FOLDER

# ----------------------------------------------------------------------
# Global objects (same as before)
# ----------------------------------------------------------------------
config = Config()
logger = logging.getLogger()

characters: dict[str, int] = {}
stages: dict[str, int] = {}
moves: dict[str, int] = {}
STARTING_DEFAULT = config.opp_dir

# ----------------------------------------------------------------------
# Helper – open a file with the OS default program
# ----------------------------------------------------------------------
def open_log_file(file_name: str) -> None:
    if file_name == "config":
        path = Path("config.ini")
    elif file_name == "app":
        path = Path(config.log_dir) / config.log_file
    elif file_name == "rivals":
        home = Path.home()
        if sys.platform.startswith("win"):
            path = home / "AppData" / "Local" / "Rivals2" / "Saved" / "Logs" / "Rivals2.log"
        else:                                   # macOS / Linux – not implemented
            QMessageBox.warning(None, "Not supported", "Rivals log opening not implemented on this OS.")
            return
    else:
        return

    if not path.is_file():
        QMessageBox.warning(None, "File missing", f"{path} not found.")
        return

    if sys.platform.startswith("darwin"):
        subprocess.call(("open", str(path)))
    elif sys.platform.startswith("win"):
        subprocess.call(("start", str(path)), shell=True)
    else:
        subprocess.call(("xdg-open", str(path)))

# ----------------------------------------------------------------------
# Backend API wrappers (unchanged)
# ----------------------------------------------------------------------
def get_final_move_top_list() -> dict:
    r = requests.get(f"http://{config.be_host}:{config.be_port}/movelist/top")
    r.raise_for_status()
    return r.json()

def get_current_elo() -> dict:
    r = requests.get(f"http://{config.be_host}:{config.be_port}/current_tier")
    r.raise_for_status()
    return r.json()

def get_opponent_names() -> list[str]:
    r = requests.get(f"http://{config.be_host}:{config.be_port}/opponent_names", timeout=5)
    r.raise_for_status()
    return r.json()["data"]["names"]

def refresh_top_row(ui) -> None:
    data = get_current_elo()["data"]
    ui.my_elo_spin.setValue(int(data["current_elo"]))
    ui.change_elo_spin.setValue(0)

def get_match_times(ui) -> None:
    data = roll_up_durations([os.path.join(RIVALS_LOG_FOLDER, "Rivals2.log")])
    if not data:
        return
    ui.output_text.append(str(data))
    logger.debug(data)
    last = data[list(data.keys())[-1]]["durations"]
    logger.debug(data[list(data.keys())[-1]])
    for i in range(len(last)):
        logger.debug(f"Placing {last} -> {last[i]}({i})")
        ui.duration_spins[i].setValue(int(last[i]))

# ----------------------------------------------------------------------
# UI class
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rivals 2 Log Parser")
        self.setFixedSize(950, 680)                 # same size as Tk version

        # ------------------------------------------------------------------
        # Icon handling (same logic as Tk)
        # ------------------------------------------------------------------
        icon_file = "icon.ico" if sys.platform.startswith("win") else "icon.png"
        icon_path = Path(icon_file)
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        # ------------------------------------------------------------------
        # UI containers
        # ------------------------------------------------------------------
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ----- Top row (Run button + log buttons) -----
        top_bar = QHBoxLayout()
        self.run_btn = QPushButton("Run Log Parser")
        self.run_btn.clicked.connect(self.run_parser)
        top_bar.addWidget(self.run_btn)

        top_bar.addStretch()

        for txt, name in [("Config", "config"), ("App Log", "app"), ("Rivals Log", "rivals")]:
            btn = QPushButton(txt)
            btn.clicked.connect(lambda _, n=name: open_log_file(n))
            top_bar.addWidget(btn)

        self.debug_cb = QCheckBox("Debug")
        top_bar.addWidget(self.debug_cb)

        main_layout.addLayout(top_bar)

        # ----- Scrolled output -----
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        main_layout.addWidget(self.output_text)

        # ----- Bottom panel (ELO, games, etc.) -----
        bottom = QWidget()
        bottom_grid = QGridLayout(bottom)
        main_layout.addWidget(bottom)

        # ELO row
        bottom_grid.addWidget(QLabel("Opp ELO"), 0, 1)
        self.opp_elo_spin = QSpinBox()
        self.opp_elo_spin.setRange(0, 3000)
        self.opp_elo_spin.setValue(STARTING_DEFAULT)
        bottom_grid.addWidget(self.opp_elo_spin, 1, 1)

        bottom_grid.addWidget(QLabel("My New ELO"), 0, 2)
        self.my_elo_spin = QSpinBox()
        self.my_elo_spin.setRange(0, 3000)
        self.my_elo_spin.setReadOnly(True)
        bottom_grid.addWidget(self.my_elo_spin, 1, 2)

        bottom_grid.addWidget(QLabel("ELO Delta"), 0, 3)
        self.change_elo_spin = QSpinBox()
        self.change_elo_spin.setRange(-50, 50)
        bottom_grid.addWidget(self.change_elo_spin, 1, 3)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(lambda: refresh_top_row(self))
        bottom_grid.addWidget(self.refresh_btn, 1, 4)

        self.durations_btn = QPushButton("Durations")
        self.durations_btn.clicked.connect(lambda: get_match_times(self))
        bottom_grid.addWidget(self.durations_btn, 1, 5)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.generate_json)
        bottom_grid.addWidget(self.copy_btn, 1, 6)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_matchup_fields)
        bottom_grid.addWidget(self.clear_btn, 1, 7)

        # Header for games
        for col, txt in enumerate(["", "OppChar", "Stage", "FinalMove", "", "Duration"], 1):
            bottom_grid.addWidget(QLabel(txt), 2, col, alignment=Qt.AlignmentFlag.AlignCenter)

        # ----- Game rows (3) -----
        self.opp_combos: list[QComboBox] = []
        self.stage_combos: list[QComboBox] = []
        self.winner_cbs: list[QCheckBox] = []
        self.move_combos: list[QComboBox] = []
        self.duration_spins: list[QSpinBox] = []

        for i in range(3):
            row = i + 3
            bottom_grid.addWidget(QLabel(f"Game {i+1}"), row, 0, alignment=Qt.AlignmentFlag.AlignRight)

            # Opponent character
            opp = QComboBox()
            opp.setEditable(False)
            opp.setMinimumWidth(120)
            opp.addItem("N/A")
            if i == 0:  # Connect sync for first game
                opp.currentTextChanged.connect(self.sync_games)
            self.opp_combos.append(opp)
            bottom_grid.addWidget(opp, row, 1)

            # Stage
            stage = QComboBox()
            stage.setEditable(False)
            stage.addItem("N/A")
            self.stage_combos.append(stage)
            bottom_grid.addWidget(stage, row, 2)

            # Final move
            move = QComboBox()
            move.setEditable(False)
            move.addItem("N/A")
            self.move_combos.append(move)
            bottom_grid.addWidget(move, row, 3)

            # Winner check (OppWins)
            win_cb = QCheckBox("OppWins")
            self.winner_cbs.append(win_cb)
            bottom_grid.addWidget(win_cb, row, 4)

            # Duration
            dur = QSpinBox()
            dur.setRange(-1, 3000)
            dur.setValue(-1)
            dur.setFixedWidth(60)
            self.duration_spins.append(dur)
            bottom_grid.addWidget(dur, row, 5)

            # Right-click → clear (disabled for now)
            # for w in (opp, stage, move, dur):
            #     w.installEventFilter(self)

        # Opponent name + autocomplete
        bottom_grid.addWidget(QLabel("OppName"), 3, 6)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("type or pick")
        # Set up completer
        self.name_completer = QCompleter()
        self.name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.name_edit.setCompleter(self.name_completer)
        bottom_grid.addWidget(self.name_edit, 3, 7)

        # ------------------------------------------------------------------
        # Load initial data
        # ------------------------------------------------------------------
        self.populate_dropdowns()
        refresh_top_row(self)

        # Position window top-right (same as Tk)
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.width() - self.width(), 0)



    # ----------------------------------------------------------------------
    # Sync game 2 opponent with game 1 opponent
    # ----------------------------------------------------------------------
    def sync_games(self):
        if self.opp_combos[0].currentText() != "N/A":
            self.opp_combos[1].setCurrentText(self.opp_combos[0].currentText())

    # ----------------------------------------------------------------------
    # Check if required dropdowns are filled
    # ----------------------------------------------------------------------
    def are_required_dropdowns_filled(self):
        return (self.opp_combos[0].currentText() != "N/A" and
                self.stage_combos[0].currentText() != "N/A" and
                self.opp_combos[1].currentText() != "N/A" and
                self.stage_combos[1].currentText() != "N/A")

    # ----------------------------------------------------------------------
    # Dropdown population (same logic as Tk)
    # ------------------------------------------------------------------
    def populate_dropdowns(self):
        try:
            # ---- characters ----
            r = requests.get(f"http://{config.be_host}:{config.be_port}/characters", timeout=5)
            r.raise_for_status()
            for c in r.json()["data"]:
                characters[c["display_name"]] = c["id"]
                if c["id"] == -1:
                    characters["sepior1"] = -1
            char_names = list(characters.keys())

            # ---- stages (split counter-pick) ----
            r = requests.get(f"http://{config.be_host}:{config.be_port}/stages", timeout=5)
            r.raise_for_status()
            stage1 = {}
            counter = -1
            for s in r.json()["data"]:
                if s["stage_type"] == "Doubles":
                    continue
                if counter == -1 and s["counter_pick"] == -1:
                    stage1[s["display_name"]] = s["id"]
                if counter == -1 and s["counter_pick"] == 0:
                    stages["sepior1"] = -1
                    stage1["sepior1"] = -1
                if s["counter_pick"] == 0:
                    counter = 0
                    stage1[s["display_name"]] = s["id"]
                if counter == 0 and s["counter_pick"] == 1:
                    stages["sepior2"] = -1
                    counter = 1
                stages[s["display_name"]] = s["id"]
            stage_names = list(stages.keys())

            # ---- moves (with categories) ----
            r = requests.get(f"http://{config.be_host}:{config.be_port}/movelist", timeout=5)
            r.raise_for_status()
            sorted_moves = sorted(r.json()["data"], key=lambda x: x["list_order"])
            for m in sorted_moves:
                moves[m["display_name"]] = m["id"]
                if m["id"] == -1:
                    moves["sepior"] = -1

            top_move_names = [x["final_move_name"] for x in get_final_move_top_list()["data"]]

            # ---- fill combos ----
            for i in range(3):
                self.opp_combos[i].clear()
                self.opp_combos[i].addItem("N/A")
                self.opp_combos[i].addItems(char_names)

                self.stage_combos[i].clear()
                self.stage_combos[i].addItem("N/A")
                self.stage_combos[i].addItems(list(stage1.keys()) if i == 0 else stage_names)

                # moves with categories + *
                self.move_combos[i].clear()
                self.move_combos[i].addItem("N/A")
                cur_cat = None
                for mv in sorted_moves:
                    disp = mv["display_name"]
                    if disp in top_move_names:
                        disp += " *"
                    self.move_combos[i].addItem(disp)
                    cat = mv["category"]
                    if cur_cat and cur_cat != cat:
                        self.move_combos[i].insertSeparator(self.move_combos[i].count())
                    cur_cat = cat

            self.output_text.append(
                f"Fetched {len([c for c in characters if characters[c] > 0])} characters, "
                f"{len([s for s in stages if stages[s] > 0])} stages and "
                f"{len([m for m in moves if moves[m] > 0])} moves."
            )

            # Set up autocomplete for opponent names
            try:
                names = get_opponent_names()
                model = QStringListModel(names)
                self.name_completer.setModel(model)
            except Exception as e:
                logger.warning(f"Failed to load opponent names for autocomplete: {e}")

        except Exception as e:
            self.output_text.append(f"Error loading dropdown data: {e}")
            logger.error(f"Dropdown population failed: {e}")

    # ----------------------------------------------------------------------
    # Clear all game fields
    # ----------------------------------------------------------------------
    def clear_matchup_fields(self):
        for c in self.opp_combos:
            c.setCurrentIndex(0)
        for c in self.stage_combos:
            c.setCurrentIndex(0)
        for cb in self.winner_cbs:
            cb.setChecked(False)
        for c in self.move_combos:
            c.setCurrentIndex(0)
        for s in self.duration_spins:
            s.setValue(-1)
        self.name_edit.clear()
        self.opp_elo_spin.setValue(STARTING_DEFAULT)

    # ----------------------------------------------------------------------
    # JSON generation (copy to clipboard)
    # ----------------------------------------------------------------------
    def generate_json(self):
        elo_data = get_current_elo()["data"]
        js = {}
        js["match_date"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        js["elo_rank_new"] = int(self.my_elo_spin.value())
        js["elo_change"] = int(self.change_elo_spin.value())
        js["elo_rank_old"] = js["elo_rank_new"] - js["elo_change"]
        js["match_win"] = 1 if js["elo_change"] >= 0 else 0
        js["match_forfeit"] = -1
        js["ranked_game_number"] = int(elo_data["last_game_number"]) + 1
        js["total_wins"] = int(elo_data["total_wins"]) + (1 if js["match_win"] else 0)
        js["win_streak_value"] = int(elo_data["win_streak_value"]) + (1 if js["match_win"] else 0)
        js["opponent_elo"] = int(self.opp_elo_spin.value())
        js["opponent_name"] = self.name_edit.text()

        for i in range(3):
            js[f"game_{i+1}_char_pick"] = 2
            js[f"game_{i+1}_opponent_pick"] = characters.get(self.opp_combos[i].currentText(), -1)
            js[f"game_{i+1}_stage"] = stages.get(self.stage_combos[i].currentText(), -1)
            js[f"game_{i+1}_final_move_id"] = moves.get(self.move_combos[i].currentText().replace(" *", ""), -1)
            js[f"game_{i+1}_winner"] = 2 if not self.winner_cbs[i].isChecked() else 1
            js[f"game_{i+1}_duration"] = self.duration_spins[i].value()

        js["final_move_id"] = -2
        js["notes"] = "Added via JSON lol"

        clip = QApplication.clipboard()
        if clip:
            clip.setText(json.dumps(js, indent=4))
            QMessageBox.information(self, "Copied", "JSON copied to clipboard!")
        else:
            QMessageBox.warning(self, "Error", "Could not access clipboard")

    # ----------------------------------------------------------------------
    # Run the parser (threaded – identical to Tk version)
    # ----------------------------------------------------------------------
    def run_parser(self):
        self.run_btn.setEnabled(False)
        self.output_text.append("Running log parser...")

        def worker():
            try:
                log_parser.setup_logging()
                extra = {}
                if self.are_required_dropdowns_filled():

                    for i in range(3):
                        extra.update({
                            f"game_{i+1}_char_pick": characters.get("Loxodont", -1),
                            f"game_{i+1}_opponent_pick": characters.get(self.opp_combos[i].currentText(), -1),
                            f"game_{i+1}_stage": stages.get(self.stage_combos[i].currentText(), -1),
                            f"game_{i+1}_winner": 2 if not self.winner_cbs[i].isChecked() else 1,
                            f"game_{i+1}_final_move_id": moves.get(self.move_combos[i].currentText().replace(" *", ""), -1),
                            f"game_{i+1}_duration": self.duration_spins[i].value(),
                        })
                    extra.update({
                        "opponent_elo": self.opp_elo_spin.value(),
                        "opponent_name": self.name_edit.text(),
                        "final_move_id": -1
                    })

                result = log_parser.parse_log(dev=self.debug_cb.isChecked(), extra_data=extra)

                if result == -1:
                    QTimer.singleShot(0, lambda: self.output_text.append("No matches found or no new matches to add."))
                else:
                    added = len(result) if isinstance(result, list) else 0
                    elos = ", ".join(f"{r.elo_rank_new}({r.elo_change})" for r in result) if isinstance(result, list) else ""
                    QTimer.singleShot(0, lambda: self.output_text.append(
                        f"Log parsed. Added {added} match{'es' if added != 1 else ''}: {elos}"
                    ))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.output_text.append(f"Error: {e}"))
                logger.exception(e)
            finally:
                QTimer.singleShot(0, lambda: self.run_btn.setEnabled(True))
                QTimer.singleShot(0, lambda: refresh_top_row(self))
                QTimer.singleShot(0, lambda: self.name_edit.setCompleter(None))  # refresh autocomplete if you add it

        threading.Thread(target=worker, daemon=True).start()

# ----------------------------------------------------------------------
# Logging setup (same as before)
# ----------------------------------------------------------------------
def setup_logging():
    os.makedirs(config.log_dir, exist_ok=True)
    logger.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(config.log_dir, config.log_file),
        maxBytes=int(config.max_log_size),
        backupCount=int(config.backup_count)
    )
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    logger.handlers.clear()
    logger.addHandler(fh)
    logger.addHandler(ch)

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    setup_logging()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()