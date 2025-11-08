import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox, scrolledtext
import threading
import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config
import requests
import traceback
import log_parser
from datetime import datetime, timezone
from utils.calc_elo import estimate_opponent_elo
import json
import sys, subprocess
from match_duration import roll_up_durations
from log_parser import RIVALS_LOG_FOLDER
config = Config()

logger = logging.getLogger()

characters = {}
stages = {}
moves = {}
top_moves = []
STARTING_DEFAULT = config.opp_dir

class AutocompleteEntry(tk.Entry):
    def __init__(self, autocomplete_list, *args, **kwargs):
        self.var = kwargs.get("textvariable") or tk.StringVar()
        kwargs["textvariable"] = self.var
        super().__init__(*args, **kwargs)

        self.autocomplete_list = autocomplete_list
        self.listbox = None

        self.bind('<KeyRelease>', self.check_autocomplete)

    def check_autocomplete(self, event):
        typed = self.var.get()
        if not typed:
            self.close_listbox()
            return

        matches = [name for name in self.autocomplete_list 
                   if typed.lower() in name.lower()]

        if matches:
            self.show_listbox(matches)
        else:
            self.close_listbox()

    def show_listbox(self, matches):
        if self.listbox:
            self.listbox.destroy()

        self.listbox = tk.Listbox(self.winfo_toplevel(), width=self["width"])
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        self.listbox.place(x=x, y=y)

        for match in matches:
            self.listbox.insert(tk.END, match)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)

    def on_select(self, event):
        if self.listbox:
            selection = self.listbox.get(self.listbox.curselection())
            self.var.set(selection)
            self.close_listbox()

    def close_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    def update_autocomplete_list(self, new_list: list[str]):
        """Call this to refresh the list of autocomplete names."""
        self.autocomplete_list = new_list

def open_log_file(file_name):
    log_path = None
    if file_name == "config":
        log_path = os.path.join("config.ini")
    if file_name == "app":
        log_path = os.path.join(config.log_dir, config.log_file)
    if file_name == "rivals":
        log_path = os.path.expanduser("~")
        if sys.platform.startswith('darwin'):  # macOS
            pass
        elif os.name == "nt":
            log_path = os.path.join(log_path, "AppData", "Local", "Rivals2", "Saved", "Logs", "Rivals2.log" )
        elif os.name == 'posix':  # Linux
            pass
        else:
            return
    print(log_path)
    if log_path == None: return
    if sys.platform.startswith('darwin'):  # macOS
        subprocess.call(('open', log_path))
    elif os.name == 'nt':  # Windows
        os.startfile(log_path)
    elif os.name == 'posix':  # Linux
        subprocess.call(('xdg-open', log_path))

def get_final_move_top_list() -> dict:
    res = requests.get(f"http://{config.be_host}:{config.be_port}/movelist/top")
    res.raise_for_status()
    if res.status_code == 200:
        json = res.json()
        return json
    return {"status":"FAIL","data":{"current_elo":-2,"tier":"N/A","tier_short":"N/A", "last_game_number": -2}}

def get_current_elo() -> dict:
    res = requests.get(f"http://{config.be_host}:{config.be_port}/current_tier")
    res.raise_for_status()
    if res.status_code == 200:
        json = res.json()
        return json
    return {"status":"FAIL","data":{"current_elo":-2,"tier":"N/A","tier_short":"N/A", "last_game_number": -2}}

def refresh_top_row() -> None:
    my_elo.set(get_current_elo()["data"]["current_elo"])
    change_elo.set(0)

def get_match_times() -> None:
    data = roll_up_durations([os.path.join(RIVALS_LOG_FOLDER, "Rivals2.log")])
    if not data:
        return
    output_text.configure(state="normal")
    output_text.insert(tk.END, f"{str(data)}\n")
    output_text.see(tk.END)
    output_text.configure(state="disabled")
    last = data[list(data.keys())[-1]]['durations']
    for i, d in enumerate(duration_entries):
        d.set(int(last[i]))


def get_opponent_names():
    response = requests.get(f"http://{config.be_host}:{config.be_port}/opponent_names", timeout=5)
    response.raise_for_status()
    return response.json()["data"]['names']

def setup_logging():
    os.makedirs(config.log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(config.debug) else logging.INFO) 
    logger.info(logger.level)

    formatter = logging.Formatter(
        '%(asctime)s - %(module)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        os.path.join(config.log_dir, config.log_file), 
        maxBytes=int(config.max_log_size), 
        backupCount=int(config.backup_count)
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if int(config.debug) else logging.INFO)

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

def update_option_menu_with_category_separators(option_menu: OptionMenu, var: tk.StringVar, sorted_moves: list[dict]):
    menu: tk.Menu = option_menu["menu"]
    menu.delete(0, "end")
    top_moves = [x["final_move_name"] for x in get_final_move_top_list()['data']]
    last_category = sorted_moves[0]["category"] if sorted_moves else None

    for i, move in enumerate(sorted_moves):
        display_name = move["display_name"]
        category = move["category"]
        if display_name in top_moves:
            display_name += " *"
        menu.add_command(label=display_name, command=lambda v=display_name: var.set(v))

        next_move = sorted_moves[i + 1] if i + 1 < len(sorted_moves) else None
        next_category = next_move["category"] if next_move else None

        if category != next_category:
            menu.add_separator()

    if sorted_moves:
        var.set(sorted_moves[0]["display_name"])


def populate_dropdowns(opp_dropdowns: list[OptionMenu], stage_dropdowns: list[OptionMenu], move_dropdowns: list[OptionMenu]):
    try:
        stages1 = {}
        response = requests.get(f"http://{config.be_host}:{config.be_port}/characters", timeout=5)
        response.raise_for_status()
        characters_json = response.json()
        for char in characters_json['data']:
            characters[char["display_name"]] = char["id"]
            if char["id"] == -1: characters["sepior1"] = -1
        character_names = list(characters.keys())
    except Exception as e:
        output_text.configure(state="normal")
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        output_text.configure(state="disabled")
        logger.error(f"Charlist failed to generate: {e}")

    try:
        response = requests.get(f"http://{config.be_host}:{config.be_port}/stages", timeout=5)
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
        output_text.configure(state="normal")
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        output_text.configure(state="disabled")        
        logger.error(f"Stagelist failed to generate: {e}")

    try:
        response = requests.get(f"http://{config.be_host}:{config.be_port}/movelist", timeout=5)
        response.raise_for_status()
        moves_json = response.json()
        sorted_moves = sorted(moves_json['data'], key=lambda x: x['list_order'])
        for move in sorted_moves:
            moves[move["display_name"]] = move["id"]
            if move["id"] == -1: 
                moves["sepior"] = -1
        move_names = list(moves.keys())
    except Exception as e:
        output_text.configure(state="normal")
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        output_text.configure(state="disabled")
        logger.error(f"Movelist failed to generate: {e}")
    
    output_text.configure(state="normal")
    output_text.insert(tk.END, f"Fetched {len([x for x in characters_json['data'] if x['list_order'] > 0])} characters, {len([x for x in stage_json['data'] if x['list_order'] > 0])} stages and {len([x for x in moves_json['data'] if x['list_order'] > 0])} moves.\n")
    output_text.see(tk.END)
    output_text.configure(state="disabled")

    try:            
        for x in range(3):
            update_option_menu(opp_dropdowns[x], opp_vars[x], character_names)
            if x == 0:
                update_option_menu(stage_dropdowns[x], stage_vars[x], list(stages1.keys()))
            else:
                update_option_menu(stage_dropdowns[x], stage_vars[x], stage_names)
            update_option_menu_with_category_separators(move_dropdowns[x], move_vars[x], sorted_moves)


    except Exception as e:
        output_text.configure(state="normal")
        output_text.insert(tk.END, f"Error updating data: {e}\n")
        output_text.see(tk.END)
        output_text.configure(state="disabled")

# def populate_movelist(move_list: OptionMenu):
#     try:
#         response = requests.get(f"http://{config.be_host}:{config.be_port}/movelist", timeout=5)
#         response.raise_for_status()
#         moves_json = response.json()
#         sorted_moves = sorted(moves_json['data'], key=lambda x: x['list_order'])
#         print(sorted_moves)
#         for move in sorted_moves:
#             moves[move["display_name"]] = move["id"]
#             if move["id"] == -1: move["sepior1"] = -1
#         move_names = list(moves.keys())
#     except Exception as e:
#         logger.error(f"Movelist failed to generate: {e}")
#     update_option_menu_with_categories(move_list, move_var, move_names)

def are_required_dropdowns_filled():
    return all([
        opp_vars[0].get().strip() != "N/A",
        stage_vars[0].get().strip() != "N/A",
        opp_vars[1].get().strip() != "N/A",
        stage_vars[1].get().strip() != "N/A",
    ])

def show_debug():
    output_text.configure(state="normal")
    output_text.insert(tk.END, f"{cbvar.get()}\n")
    output_text.configure(state="disabled")
# def adjust_elo(delta):
#     try:
#         current = opp_elo.get()
#     except tk.TclError:
#         current = 0
#     opp_elo.set(current + delta)

# def on_mousewheel(event: tk.Event):
#     # event.delta is positive (up) or negative (down)
#     shift = event.state & 0x0001 #type: ignore
#     delta = 5 if shift else 1
#     direction = 1 if event.delta > 0 else -1
#     adjust_elo(delta * direction)

def clear_matchup_fields():
    for x in opp_vars:
        x.set("N/A")
    for x in stage_vars:
        x.set("N/A")
    for x in winner_vars:
        x.set(False)
    for x in move_vars:
        x.set("N/A")
    for x in duration_vars:
        x.set(-1)
    name_var.set("")
    opp_elo.set(STARTING_DEFAULT)

def clear_field(event, field_name_var: tk.StringVar, value: str):
    logger.debug(f"{event} - {field_name_var} set to {value}")
    field_name_var.set(value)

def generate_json():
    elo_values = get_current_elo()
    jsond = {}
    jsond["match_date"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    jsond["elo_rank_new"] = int(my_elo.get())
    jsond["elo_change"] = int(change_elo.get())
    jsond["elo_rank_old"] = jsond["elo_rank_new"] - jsond["elo_change"]
    jsond["match_win"] =  1 if jsond["elo_change"] >= 0 else 0
    jsond["match_forfeit"] =  -1
    jsond["ranked_game_number"] = int(elo_values["data"]["last_game_number"])+1
    jsond["total_wins"] = int(elo_values["data"]["total_wins"]) + 1 if jsond["match_win"] else int(elo_values["data"]["total_wins"])
    jsond["win_streak_value"] = int(elo_values["data"]["win_streak_value"]) + 1 if jsond["match_win"] else int(elo_values["data"]["win_streak_value"])
    jsond["opponent_elo"] = int(opp_elo.get())
    jsond["opponent_name"] = name_var.get() if name_var.get() is not None else ""
    for x in range(3):
        jsond[f"game_{x+1}_char_pick"] = 2
        jsond[f"game_{x+1}_opponent_pick"] = int(characters.get(opp_vars[x].get(), -1))
        jsond[f"game_{x+1}_stage"] = int(stages.get(stage_vars[x].get(), -1))
        jsond[f"game_{x+1}_final_move_id"] = int(moves.get(move_vars[x].get().replace(" *", ""), -1))
        jsond[f"game_{x+1}_winner"] = 2 if winner_vars[x].get() else (1 if opp_vars[x].get() != "N/A" else -1)
        jsond[f"game_{x+1}_duration"] = int(duration_vars[x].get())
    jsond["final_move_id"] = -2
    jsond["notes"] = "Added via JSON lol"
    logger.debug(json.dumps(jsond))
    root.clipboard_clear()
    root.clipboard_append(json.dumps(jsond, indent=4))
    root.update()

def run_parser(dev: int = 0):
    # output_text.insert(tk.END, "Running log parser...\n")
    output_text.configure(state="normal")
    output_text.see(tk.END)
    output_text.configure(state="disabled")
    run_button.config(state="disabled")

    def worker():
        try:
            log_parser.setup_logging()
            extra_data = {}
            if are_required_dropdowns_filled():
                for x in range(3): int(moves.get(move_vars[x].get(), -1))
                extra_data = {
                    "game_1_char_pick": int(characters.get("Loxodont", -1)),
                    "game_1_opponent_pick": int(characters.get(opp_vars[0].get(), -1)),
                    "game_1_stage": int(stages.get(stage_vars[0].get(), -1)),
                    "game_1_winner": 2 if winner_vars[0].get() else (1 if opp_vars[0].get() != "N/A" else -1),
                    "game_1_final_move_id": int(moves.get(move_vars[0].get().replace(" *", ""), -1)),
                    "game_1_duration": int(duration_vars[0].get()),
                    "game_2_char_pick": int(characters.get("Loxodont", -1)),
                    "game_2_opponent_pick": int(characters.get(opp_vars[1].get(), -1)),
                    "game_2_stage": int(stages.get(stage_vars[1].get(), -1)),
                    "game_2_winner": 2 if winner_vars[1].get() else (1 if opp_vars[1].get() != "N/A" else -1),
                    "game_2_final_move_id": int(moves.get(move_vars[1].get().replace(" *", ""), -1)),
                    "game_2_duration": int(duration_vars[1].get()),
                    "game_3_char_pick": int(characters.get("Loxodont", -1)),
                    "game_3_opponent_pick": int(characters.get(opp_vars[2].get(), -1)),
                    "game_3_stage": int(stages.get(stage_vars[2].get(), -1)),
                    "game_3_winner": 2 if winner_vars[2].get() else (1 if opp_vars[2].get() != "N/A" else -1),
                    "game_3_final_move_id": int(moves.get(move_vars[2].get().replace(" *", ""), -1)),
                    "game_3_duration": int(duration_vars[2].get()),
                    "opponent_elo": int(opp_elo.get()),
                    "opponent_name": name_var.get() if name_var.get() is not None else "",
                    "final_move_id": -1
                }
            result = log_parser.parse_log(dev=cbvar.get(), extra_data=extra_data)
            if result == -1:
                output_text.configure(state="normal")
                output_text.insert(tk.END, "No matches found or no new matches to add.\n")
                output_text.see(tk.END)
                output_text.configure(state="disabled")
                run_button.config(state="normal")
                return
            output_text.configure(state="normal")
            output_text.insert(tk.END, f"Log parsed. Added {len(result)} match{'es' if len(result) != 1 else ''}: {[",".join(f"{str(x.elo_rank_new)}({str(x.elo_change)})" for x in result)] if result else ""}\n") # type: ignore
            output_text.see(tk.END)
            output_text.configure(state="disabled")
            if cbvar.get():
                output_text.see(tk.END)
        except Exception as e:
            output_text.configure(state="normal")
            output_text.insert(tk.END, f"Error: {e}\n")
            output_text.configure(state="disabled")
            traceback.print_exc()
        finally:
            run_button.config(state="normal")
            refresh_top_row()
            name_field.update_autocomplete_list(get_opponent_names())

    threading.Thread(target=worker).start()


setup_logging()

root = tk.Tk()
root.title("Rivals 2 Log Parser")

# --- SET WINDOW ICON ---
icon_file = "icon.ico" if sys.platform.startswith("win") else "icon.png"
icon_path = os.path.join(icon_file)

if os.path.isfile(icon_path):
    if sys.platform.startswith("win"):
        root.iconbitmap(icon_path)                    # Windows: .ico
    else:
        img = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, img)                     # Linux/macOS: .png
else:
    print(f"[WARN] Icon not found: {icon_path}")

# dropdowns
opp_vars = [] * 3 
opp_dropdowns: list[OptionMenu] = []
stage_vars = []
stage_dropdowns: list[OptionMenu] = []
winner_vars = []
move_dropdowns: list[OptionMenu] = []
move_vars = []
duration_vars = []
duration_entries = []

frame = Frame(root, padding=10)
frame.pack(fill="both", expand=True)

topframe = Frame(frame)
topframe.pack(fill="both", expand=True)

run_button = Button(topframe, text="Run Log Parser", command=run_parser, takefocus=False)
run_button.pack(side=tk.LEFT)

spacer = Label(topframe)
spacer.pack(side=tk.LEFT, expand=True)

Button(topframe, text="Config", command=lambda: open_log_file("config"), takefocus=False).pack(side=tk.RIGHT, pady=10)
Button(topframe, text="App Log", command=lambda: open_log_file("app"), takefocus=False).pack(side=tk.RIGHT, pady=10)
Button(topframe, text="Rivals Log", command=lambda: open_log_file("rivals"), takefocus=False).pack(side=tk.RIGHT, pady=10)

cbvar = tk.IntVar()
run_switch = Checkbutton(topframe, text="Debug",  variable=cbvar, takefocus=False)
run_switch.pack(side=tk.RIGHT)

output_text = scrolledtext.ScrolledText(frame, width=60, height=20, takefocus=False)
output_text.pack(fill="both", expand=True)
output_text.configure(state='disabled')

bottom_frame = Frame(root, padding=10)
bottom_frame.pack(fill="x")

Label(bottom_frame, text="Opp ELO").grid(row=0, column=1)
opp_elo = tk.IntVar(value=STARTING_DEFAULT)
opp_elo_entry = Spinbox(bottom_frame, from_=0, to=3000, textvariable=opp_elo, width=10)
opp_elo_entry.grid(row=1, column=1, padx=5)

Label(bottom_frame, text="My New ELO").grid(row=0, column=2)
my_elo = tk.IntVar()
my_elo.set(int(get_current_elo()["data"]["current_elo"]))
my_elo_entry = Spinbox(bottom_frame, from_=0, to=3000, textvariable=my_elo, width=10, takefocus=False)
my_elo_entry.grid(row=1, column=2, padx=5, sticky="w")

Label(bottom_frame, text="ELO Delta").grid(row=0, column=3 )
change_elo = tk.IntVar(value=0)
change_elo_entry = Spinbox(bottom_frame, from_=-50, to=50, textvariable=change_elo, width=10, takefocus=False)
change_elo_entry.grid(row=1, column=3, padx=5, sticky="w")

refresh_button = Button(bottom_frame, text="Refresh", command=refresh_top_row, takefocus=False)
refresh_button.grid(row=1, column=4, padx=10, sticky="w")

times_button = Button(bottom_frame, text="Durations", command=get_match_times, takefocus=False)
times_button.grid(row=1, column=5, padx=10, sticky="w")

copy_button = Button(bottom_frame, text="Copy", command=generate_json, takefocus=False)
copy_button.grid(row=1, column=6, padx=10, sticky="e")

clear_button = Button(bottom_frame, text="Clear", command=clear_matchup_fields, takefocus=False)
clear_button.grid(row=1, column=7, padx=10, sticky='e')

Label(bottom_frame, text=f"").grid(row=2, column=0, sticky='n')
Label(bottom_frame, text=f"OppChar").grid(row=2, column=1, sticky='n')
Label(bottom_frame, text=f"Stage").grid(row=2, column=2, sticky='n')
Label(bottom_frame, text=f"").grid(row=2, column=4, sticky='n')
Label(bottom_frame, text=f"FinalMove").grid(row=2, column=3, sticky='n')

def sync_games(*args):
    opp_vars[1].set(opp_vars[0].get())

for x in range(3):
    delta = 3
    Label(bottom_frame, text=f"Game {x+1}").grid(row=x+delta, column=0, sticky="e")

    opp_var = tk.StringVar()
    stage_var = tk.StringVar()
    winner_var = tk.BooleanVar()
    move_var = tk.StringVar()
    duration_var = tk.IntVar(value=-1)

    opp_dropdown = OptionMenu(bottom_frame, opp_var, "Loading...")
    if x == 0:
        opp_var.trace_add("write", sync_games)
    

    stage_dropdown = OptionMenu(bottom_frame, stage_var, "Loading...")
    winner_checkbox = Checkbutton(bottom_frame, text="OppWins", variable=winner_var)
    move_dropdown = OptionMenu(bottom_frame, move_var, "Loading...")
    duration_entry = Spinbox(bottom_frame, from_=0, to=3000, textvariable=duration_var, width=3, takefocus=False)
    
    opp_dropdown.config(width=10)
    stage_dropdown.config(width=10)
    move_dropdown.config(width=10)

    opp_dropdown.bind(sequence="<Button-3>", func=lambda event, var=opp_var: clear_field(event, var, "N/A"))
    stage_dropdown.bind(sequence="<Button-3>", func=lambda event, var=stage_var: clear_field(event, var, "N/A"))
    move_dropdown.bind(sequence="<Button-3>", func=lambda event, var=move_var: clear_field(event, var, "N/A"))
    duration_entry.bind(sequence="<Button-3>", func=lambda event, var=duration_var: clear_field(event, var, "-1"))

    opp_dropdown.grid(row=x+delta, column=1, padx=5, sticky="w")
    stage_dropdown.grid(row=x+delta, column=2, padx=5, sticky="w")
    winner_checkbox.grid(row=x+delta, column=4, padx=5, sticky="w")
    move_dropdown.grid(row=x+delta, column=3, padx=5, sticky="w")
    duration_entry.grid(row=x+delta, column=5, padx=5, sticky="w")

    opp_dropdown.config(takefocus=False)
    stage_dropdown.config(takefocus=False)
    move_dropdown.config(takefocus=False)
    winner_checkbox.config(takefocus=False)
    
    opp_vars.append(opp_var)
    stage_vars.append(stage_var)
    winner_vars.append(winner_var)
    move_vars.append(move_var)
    duration_vars.append(duration_var)

    opp_dropdowns.append(opp_dropdown)
    stage_dropdowns.append(stage_dropdown)
    move_dropdowns.append(move_dropdown)
    duration_entries.append(duration_entry)


name_label = Label(bottom_frame, text="OppName").grid(row=3, column=6, padx=5, sticky='w')
name_var = tk.StringVar()
name_field = AutocompleteEntry(get_opponent_names(), bottom_frame, textvariable=name_var)
name_field.grid(row=3, column=7, padx=10, sticky='e')
name_field.bind(sequence="<Button-3>", func=lambda event, var=opp_var: clear_field(event, name_var, ""))

style = Style()
style.theme_use(themename="classic")
populate_dropdowns(opp_dropdowns, stage_dropdowns, move_dropdowns)

root.update_idletasks()
root.geometry(root.geometry())
root.resizable(False, False)

root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = root.winfo_width()
window_height = root.winfo_height()
x = screen_width - window_width
y = 0
root.geometry(f"+{x}+{y}")
name_field.focus_set()
root.mainloop()

