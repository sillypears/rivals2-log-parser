import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import requests

import log_parser

load_dotenv()
logger = logging.getLogger()

characters = {}
stages = {}

def setup_logging():
    os.makedirs(os.environ.get("LOG_DIR"), exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(os.environ.get("RIV2_DEBUG")) else logging.INFO) 
    logger.info(logger.level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        os.path.join(os.environ.get("LOG_DIR"), os.environ.get("LOG_FILE")), 
        maxBytes=int(os.environ.get("MAX_LOG_SIZE")), 
        backupCount=int(os.environ.get("BACKUP_COUNT"))
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if int(os.environ.get("RIV2_DEBUG")) else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if int(os.environ.get("RIV2_DEBUG")) else logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

def update_option_menu(option_menu, var, options):
    menu = option_menu["menu"]
    menu.delete(0, "end")
    for opt in options:
        menu.add_command(label=opt, command=lambda v=opt: var.set(v))
    if options:
        var.set(options[0])

def populate_dropdowns(opp_dropdowns: list, stage_dropdowns: list):
    try:
        response = requests.get("http://192.168.1.30:8005/characters", timeout=5)
        response.raise_for_status()
        characters_json = response.json()
        for char in characters_json:
            characters[char["display_name"]] = char["id"]
        character_names = list(characters.keys())

        response = requests.get("http://192.168.1.30:8005/stages", timeout=5)
        response.raise_for_status()
        stage_json = response.json()
        for stage in stage_json:
            stages[stage["display_name"]] = stage["id"]
        stage_names = list(stages.keys())

        output_text.insert(tk.END, f"Fetched {len(character_names)} characters and {len(stage_names)} stages.\n")
        output_text.see(tk.END)

    except Exception as e:
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)

    try:            
        for x in range(3):
            update_option_menu(opp_dropdowns[x], opp_vars[x], character_names)
            update_option_menu(stage_dropdowns[x], stage_vars[x], stage_names)

    except Exception as e:
        output_text.insert(tk.END, f"Error updating character data: {e}\n")
        output_text.see(tk.END)

def are_required_dropdowns_filled():
    return all([
        opp_vars[0].get().strip() != "N/A",
        stage_vars[0].get().strip() != "N/A",
        opp_vars[1].get().strip() != "N/A",
        stage_vars[1].get().strip() != "N/A",
    ])

def run_parser(dev: int = 0):
    output_text.insert(tk.END, "Running log parser...\n")
    output_text.see(tk.END)
    run_button.config(state="disabled")

    def worker():
        try:
            log_parser.setup_logging()
            extra_data = {}
            if are_required_dropdowns_filled():
                extra_data = {
                    "game_1_char_pick": int(characters.get("Loxodont", -1)),
                    "game_2_char_pick": int(characters.get("Loxodont", -1)),
                    "game_3_char_pick": int(characters.get("Loxodont", -1)),
                    "game_1_opponent_pick": int(characters.get(opp_vars[0].get(), -1)),
                    "game_1_stage": int(stages.get(stage_vars[0].get(), -1)),
                    "game_2_opponent_pick": int(characters.get(opp_vars[1].get(), -1)),
                    "game_2_stage": int(stages.get(stage_vars[1].get(), -1)),
                    "game_3_opponent_pick": int(characters.get(opp_vars[2].get(), -1)),
                    "game_3_stage": int(stages.get(stage_vars[2].get(), -1)),
                    "game_1_winner": 2 if winner_vars[0].get() else 1,
                    "game_2_winner": 2 if winner_vars[1].get() else 1,
                    "game_3_winner": 2 if winner_vars[2].get() else 1,
                    "opponent_elo": int(opp_elo.get())
                }
            
            result = log_parser.parse_log(dev=cbvar.get(), extra_data=extra_data)
            
            output_text.insert(tk.END, "Log parsing complete.\n")
            output_text.insert(tk.END, f"Added {len(result)} match{'es' if len(result) != 1 else ''}: {[",".join(str(x["elo_rank_new"]) for x in result)] if result else ""}\n")
            output_text.see(tk.END)
            if cbvar.get():
                #log_parser.truncate_db(cbvar.get())
                #output_text.insert(tk.END, "Truncating\n")
                output_text.see(tk.END)
        except Exception as e:
            output_text.insert(tk.END, f"Error: {e}\n")
            messagebox.showerror("Error", str(e))
        finally:
            run_button.config(state="normal")

    threading.Thread(target=worker).start()

def show_debug():
    output_text.insert(tk.END, f"{cbvar.get()}\n")

setup_logging()

root = tk.Tk()
root.title("Rivals 2 Log Parser")
root.resizable(0,0)

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill="both", expand=True)

topframe = tk.Frame(frame)
topframe.pack(fill="both", expand=True)

run_button = tk.Button(topframe, text="Run Log Parser", command=run_parser)
run_button.pack(side=tk.LEFT)

spacer = tk.Label(topframe)
spacer.pack(side=tk.LEFT, expand=True)

cbvar = tk.IntVar()
run_switch = tk.Checkbutton(topframe, text="Debug",  variable=cbvar)
run_switch.pack(side=tk.RIGHT)

output_text = scrolledtext.ScrolledText(frame, width=80, height=20)
output_text.pack(fill="both", expand=True)

# bottom
bottom_frame = tk.Frame(root, padx=10, pady=10)
bottom_frame.pack(fill="x")

def adjust_elo(delta):
    try:
        current = opp_elo.get()
    except tk.TclError:
        current = 0
    opp_elo.set(current + delta)

def on_mousewheel(event: tk.Event):
    # event.delta is positive (up) or negative (down)
    shift = event.state & 0x0001
    delta = 5 if shift else 1
    direction = 1 if event.delta > 0 else -1
    adjust_elo(delta * direction)

tk.Label(bottom_frame, text="Opp ELO:").grid(row=0, column=0, sticky="e")
opp_elo = tk.IntVar()
opp_elo.set(950)  # Default elo value
opp_elo_entry = tk.Spinbox(bottom_frame, from_=0, to_=3000, increment=1, textvariable=opp_elo, width=10)
opp_elo_entry.grid(row=0, column=1, padx=5)


opp_elo_entry.bind("<MouseWheel>", on_mousewheel)  # Windows
# chars
opp_vars = []
opp_dropdowns = []
stage_vars = []
stage_dropdowns = []
winner_vars = []

for x in range(3):
    tk.Label(bottom_frame, text=f"Game {x+1}").grid(row=x+2, column=0, sticky="e")

    opp_var = tk.StringVar()
    stage_var = tk.StringVar()
    winner_var = tk.BooleanVar()

    opp_dropdown = tk.OptionMenu(bottom_frame, opp_var, "Loading...")
    stage_dropdown = tk.OptionMenu(bottom_frame, stage_var, "Loading...")
    winner_checkbox = tk.Checkbutton(bottom_frame, text="OppWins", variable=winner_var)

    opp_dropdown.grid(row=x+2, column=1, padx=5, sticky="w")
    stage_dropdown.grid(row=x+2, column=2, padx=5, sticky="w")
    winner_checkbox.grid(row=x+2, column=3, padx=5, sticky="w")
    
    opp_vars.append(opp_var)
    stage_vars.append(stage_var)
    winner_vars.append(winner_var)

    opp_dropdowns.append(opp_dropdown)
    stage_dropdowns.append(stage_dropdown)

def clear_matchup_fields():
    for x in opp_vars:
        x.set("")
    for x in stage_vars:
        x.set("")
    for x in winner_vars:
        x.set(False)
    opp_elo.set(950) 
clear_button = tk.Button(bottom_frame, text="Clear", command=clear_matchup_fields)
clear_button.grid(row=0, column=10, padx=10)

populate_dropdowns(opp_dropdowns, stage_dropdowns)

root.mainloop()
