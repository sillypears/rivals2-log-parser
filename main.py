import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox, scrolledtext
import threading
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import requests
import traceback
import log_parser

load_dotenv()
logger = logging.getLogger()

characters = {}
stages = {}
moves = {}
STARTING_DEFAULT = 1000


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

def update_option_menu(option_menu: OptionMenu, var, options):
    menu: tk.Menu = option_menu["menu"]
    menu.delete(0, "end")
    for opt in options:
        if "sepior" in opt:
            menu.add_separator()
        else:
            menu.add_command(label=opt, command=lambda v=opt: var.set(v))
    if options:
        var.set(options[0])

def populate_dropdowns(opp_dropdowns: list[OptionMenu], stage_dropdowns: list[OptionMenu], move_dropdowns: list[OptionMenu]):
    try:
        stages1 = {}
        response = requests.get("http://192.168.1.30:8005/characters", timeout=5)
        response.raise_for_status()
        characters_json = response.json()
        for char in characters_json['data']:
            characters[char["display_name"]] = char["id"]
            if char["id"] == -1: characters["sepior1"] = -1
        character_names = list(characters.keys())
    except Exception as e:
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        logger.error(f"Charlist failed to generate: {e}")

    try:
        response = requests.get("http://192.168.1.30:8005/stages", timeout=5)
        response.raise_for_status()
        stage_json = response.json()
        counter = -1
        for stage in stage_json['data']:
            if stage['stage_type'] != "Doubles":
                if counter == -1 and stage["counter_pick"] == -1:
                    stages1[stage["display_name"]] = stage["id"]
                if counter == -1 and stage["counter_pick"] == 0:
                    stages["sepior1"] = -1
                    stages1["sepior1"] = -1
                if stage["counter_pick"] == 0 :
                    counter = 0
                    stages1[stage["display_name"]] = stage["id"]
                if counter == 0 and stage["counter_pick"] == 1:
                    stages["sepior2"] = -1
                    counter = 1
                stages[stage["display_name"]] = stage["id"]
                    
        stage_names = list(stages.keys())
    except Exception as e:
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        logger.error(f"Stagelist failed to generate: {e}")

    try:
        response = requests.get("http://192.168.1.30:8005/movelist", timeout=5)
        response.raise_for_status()
        moves_json = response.json()
        sorted_moves = sorted(moves_json['data'], key=lambda x: x['list_order'])
        for move in sorted_moves:
            moves[move["display_name"]] = move["id"]
            if move["id"] == -1: move["sepior1"] = -1
        move_names = list(moves.keys())
    except Exception as e:
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        logger.error(f"Movelist failed to generate: {e}")

    output_text.insert(tk.END, f"Fetched {len([x for x in characters_json['data'] if x['list_order'] > 0])} characters, {len([x for x in stage_json['data'] if x['list_order'] > 0])} stages and {len([x for x in moves_json['data'] if x['list_order'] > 0])} moves.\n")
    output_text.see(tk.END)

    try:            
        for x in range(3):
            update_option_menu(opp_dropdowns[x], opp_vars[x], character_names)
            if x == 0:
                update_option_menu(stage_dropdowns[x], stage_vars[x], list(stages1.keys()))
            else:
                update_option_menu(stage_dropdowns[x], stage_vars[x], stage_names)
            update_option_menu(move_dropdowns[x], move_vars[x], move_names)


    except Exception as e:
        output_text.insert(tk.END, f"Error updating character data: {e}\n")
        output_text.see(tk.END)

def populate_movelist(move_list: OptionMenu):
    try:
        response = requests.get("http://192.168.1.30:8005/movelist", timeout=5)
        response.raise_for_status()
        moves_json = response.json()
        for move in moves_json['data']:
            moves[move["display_name"]] = move["id"]
            if move["id"] == -1: move["sepior1"] = -1


        move_names = list(moves.keys())
    except Exception as e:
        logger.error(f"Movelist failed to generate: {e}")
    update_option_menu(move_list, move_var, move_names)

def are_required_dropdowns_filled():
    return all([
        opp_vars[0].get().strip() != "N/A",
        stage_vars[0].get().strip() != "N/A",
        opp_vars[1].get().strip() != "N/A",
        stage_vars[1].get().strip() != "N/A",
    ])

def run_parser(dev: int = 0):
    # output_text.insert(tk.END, "Running log parser...\n")
    output_text.see(tk.END)
    run_button.config(state="disabled")

    def worker():
        try:
            log_parser.setup_logging()
            extra_data = {}
            if are_required_dropdowns_filled():
                for x in range(3): int(moves.get(move_vars[x].get(), -1))
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
                    "game_1_winner": 2 if winner_vars[0].get() else (1 if opp_vars[0].get() != "N/A" else -1),
                    "game_2_winner": 2 if winner_vars[1].get() else (1 if opp_vars[1].get() != "N/A" else -1),
                    "game_3_winner": 2 if winner_vars[2].get() else (1 if opp_vars[2].get() != "N/A" else -1),
                    "game_1_final_move_id": int(moves.get(move_vars[0].get(), -1)),
                    "game_2_final_move_id": int(moves.get(move_vars[1].get(), -1)),
                    "game_3_final_move_id": int(moves.get(move_vars[2].get(), -1)),
                    "opponent_elo": int(opp_elo.get()),
                    "final_move_id": -1
                }
            logger.debug(extra_data)
            result = log_parser.parse_log(dev=cbvar.get(), extra_data=extra_data)
            if result == -1:
                output_text.insert(tk.END, "No matches found or no new matches to add.\n")
                output_text.see(tk.END)
                run_button.config(state="normal")
                return
            output_text.insert(tk.END, f"Log parsing complete. Added {len(result)} match{'es' if len(result) != 1 else ''}: {[",".join(str(x["elo_rank_new"]) for x in result)] if result else ""}\n") # type: ignore
            output_text.see(tk.END)
            if cbvar.get():
                #log_parser.truncate_db(cbvar.get())
                #output_text.insert(tk.END, "Truncating\n")
                output_text.see(tk.END)
        except Exception as e:
            output_text.insert(tk.END, f"Error: {e}\n")
            # messagebox.showerror("Error", str(e))
            traceback.print_exc()
        finally:
            run_button.config(state="normal")

    threading.Thread(target=worker).start()

def show_debug():
    output_text.insert(tk.END, f"{cbvar.get()}\n")

def adjust_elo(delta):
    try:
        current = opp_elo.get()
    except tk.TclError:
        current = 0
    opp_elo.set(current + delta)

def on_mousewheel(event: tk.Event):
    # event.delta is positive (up) or negative (down)
    shift = event.state & 0x0001 #type: ignore
    delta = 5 if shift else 1
    direction = 1 if event.delta > 0 else -1
    adjust_elo(delta * direction)

def clear_matchup_fields():
    # for x in range(len(opp_vars)
    for x in opp_vars:
        x.set("N/A")
    for x in stage_vars:
        x.set("N/A")
    for x in winner_vars:
        x.set(False)
    for x in move_vars:
        x.set("N/A")

    opp_elo.set(STARTING_DEFAULT)

def clear_field(event, field_name_var: tk.StringVar, value: str):
    print(f"{event} - {field_name_var} set to {value}")
    field_name_var.set(value)

setup_logging()

root = tk.Tk()
root.title("Rivals 2 Log Parser")
root.resizable(0,0) #type: ignore

# dropdowns
opp_vars = [] * 3 
opp_dropdowns: list[OptionMenu] = []
stage_vars = []
stage_dropdowns: list[OptionMenu] = []
winner_vars = []
move_dropdowns: list[OptionMenu] = []
move_vars = []

frame = Frame(root, padding=10)
frame.pack(fill="both", expand=True)

topframe = Frame(frame)
topframe.pack(fill="both", expand=True)

run_button = Button(topframe, text="Run Log Parser", command=run_parser)
run_button.pack(side=tk.LEFT)

spacer = Label(topframe)
spacer.pack(side=tk.LEFT, expand=True)

cbvar = tk.IntVar()
run_switch = Checkbutton(topframe, text="Debug",  variable=cbvar)
run_switch.pack(side=tk.RIGHT)

output_text = scrolledtext.ScrolledText(frame, width=80, height=20)
output_text.pack(fill="both", expand=True)

bottom_frame = Frame(root, padding=10)
bottom_frame.pack(fill="x")

Label(bottom_frame, text="Opp ELO:").grid(row=0, column=0, sticky="e")
opp_elo = tk.IntVar()
opp_elo.set(STARTING_DEFAULT)  
opp_elo_entry = tk.Spinbox(bottom_frame, from_=0, to=3000, textvariable=opp_elo, width=10)
opp_elo_entry.grid(row=0, column=1, padx=5)


opp_elo_entry.bind("<MouseWheel>", on_mousewheel)  # Windows

Label(bottom_frame, text=f"").grid(row=1, column=0, sticky='n')
Label(bottom_frame, text=f"OppChar").grid(row=1, column=1, sticky='n')
Label(bottom_frame, text=f"Stage").grid(row=1, column=2, sticky='n')
Label(bottom_frame, text=f"").grid(row=1, column=4, sticky='n')
Label(bottom_frame, text=f"FinalMove").grid(row=1, column=3, sticky='n')

def sync_games(*args):
    opp_vars[1].set(opp_vars[0].get())

for x in range(3):
    Label(bottom_frame, text=f"Game {x+1}").grid(row=x+2, column=0, sticky="e")

    opp_var = tk.StringVar()
    stage_var = tk.StringVar()
    winner_var = tk.BooleanVar()
    move_var = tk.StringVar()

    opp_dropdown = OptionMenu(bottom_frame, opp_var, "Loading...")
    if x == 0:
        opp_var.trace_add("write", sync_games)
    

    stage_dropdown = OptionMenu(bottom_frame, stage_var, "Loading...")
    winner_checkbox = Checkbutton(bottom_frame, text="OppWins", variable=winner_var)
    move_dropdown = OptionMenu(bottom_frame, move_var, "Loading...")
    
    opp_dropdown.bind(sequence="<Button-3>", func=lambda event, var=opp_var: clear_field(event, var, "N/A"))
    stage_dropdown.bind(sequence="<Button-3>", func=lambda event, var=stage_var: clear_field(event, var, "N/A"))
    move_dropdown.bind(sequence="<Button-3>", func=lambda event, var=move_var: clear_field(event, var, "N/A"))

    opp_dropdown.grid(row=x+2, column=1, padx=5, sticky="w")
    stage_dropdown.grid(row=x+2, column=2, padx=5, sticky="w")
    winner_checkbox.grid(row=x+2, column=4, padx=5, sticky="w")
    move_dropdown.grid(row=x+2, column=3, padx=5, sticky="w")

    opp_vars.append(opp_var)
    stage_vars.append(stage_var)
    winner_vars.append(winner_var)
    move_vars.append(move_var)

    opp_dropdowns.append(opp_dropdown)
    stage_dropdowns.append(stage_dropdown)
    move_dropdowns.append(move_dropdown)



clear_button = Button(bottom_frame, text="Clear", command=clear_matchup_fields)
clear_button.grid(row=0, column=16, padx=10, sticky='es')

style = Style()
style.theme_use(themename="classic")
populate_dropdowns(opp_dropdowns, stage_dropdowns, move_dropdowns)

root.mainloop()

