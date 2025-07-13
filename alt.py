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
from PIL import Image, ImageTk
from io import BytesIO

load_dotenv()
logger = logging.getLogger()

characters = {}
stages = {}
character_images = {}  # Store character images

class ImageDropdown:
    def __init__(self, parent, textvariable, row, column):
        self.parent = parent
        self.var = textvariable
        self.options = []
        self.images = {}
        self.is_open = False
        self.option_buttons = []
        
        # Create the main button that shows current selection
        self.button = tk.Button(parent, text="Loading...", command=self.toggle_dropdown,
                               anchor='w', relief='raised', bd=1, width=20)
        self.button.grid(row=row, column=column, padx=5, sticky="w")
        
        # Create dropdown window (initially hidden)
        self.dropdown = tk.Toplevel(parent)
        self.dropdown.withdraw()
        self.dropdown.overrideredirect(True)
        self.dropdown.wm_attributes('-topmost', True)
        
        # Create frame inside dropdown for better styling
        self.frame = tk.Frame(self.dropdown, relief='raised', bd=1, bg='white')
        self.frame.pack(fill='both', expand=True)
        
        # Bind escape key to close dropdown
        self.dropdown.bind('<KeyPress-Escape>', self.hide_dropdown)
        
    def add_option(self, text, image=None):
        self.options.append(text)
        if image:
            self.images[text] = image
    
    def clear_options(self):
        self.options = []
        self.images = {}
        self.option_buttons = []
        for widget in self.frame.winfo_children():
            widget.destroy()
    
    def update_options(self, options_data):
        self.clear_options()
        
        for i, (text, image) in enumerate(options_data):
            if "sepior" in text:
                # Add separator
                separator = tk.Frame(self.frame, height=2, bg='gray')
                separator.pack(fill='x', pady=2)
                continue
                
            self.add_option(text, image)
            
            # Create button for this option
            option_btn = tk.Button(self.frame, text=text, 
                                 command=lambda t=text: self.select_option(t),
                                 anchor='w', relief='flat', bd=0, pady=4, padx=8,
                                 bg='white', activebackground='lightblue',
                                 width=18, justify='left')
            
            if image:
                option_btn.config(image=image, compound='left')
                
            option_btn.pack(fill='x', padx=1, pady=1)
            self.option_buttons.append(option_btn)
            
            # Hover effects
            def on_enter(event, btn=option_btn):
                btn.config(bg='lightblue')
            def on_leave(event, btn=option_btn):
                btn.config(bg='white')
                
            option_btn.bind('<Enter>', on_enter)
            option_btn.bind('<Leave>', on_leave)
    
    def select_option(self, option):
        self.var.set(option)
        self.update_button_display()
        self.hide_dropdown()
    
    def update_button_display(self):
        current = self.var.get()
        if current in self.images:
            self.button.config(text=current, image=self.images[current], compound='left')
        else:
            self.button.config(text=current, image='', compound='none')
    
    def toggle_dropdown(self):
        if self.is_open:
            self.hide_dropdown()
        else:
            self.show_dropdown()
    
    def show_dropdown(self):
        if not self.options:
            return
            
        self.is_open = True
        
        # Position dropdown below button
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        
        self.dropdown.geometry(f"+{x}+{y}")
        self.dropdown.deiconify()
        self.dropdown.lift()
        self.dropdown.focus_set()
        
        # Bind click outside to close - do this after showing
        self.dropdown.bind('<FocusOut>', self.on_focus_out)
        
        # Set up global click handler to close dropdown when clicking elsewhere
        self.parent.bind_all('<Button-1>', self.on_global_click)
    
    def on_focus_out(self, event):
        # Only hide if focus is going to something outside the dropdown
        if event.widget != self.dropdown and not str(event.widget).startswith(str(self.dropdown)):
            self.hide_dropdown()
    
    def on_global_click(self, event):
        # Check if click is outside the dropdown
        if event.widget != self.dropdown and event.widget != self.button:
            # Check if click is on any of the option buttons
            if event.widget not in self.option_buttons:
                self.hide_dropdown()
    
    def hide_dropdown(self, event=None):
        if self.is_open:
            self.is_open = False
            self.dropdown.withdraw()
            # Remove global click handler
            self.parent.unbind_all('<Button-1>')

def setup_logging():
    os.makedirs(os.environ.get("LOG_DIR"), exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(os.environ.get("RIV2_DEBUG")) else logging.INFO) 

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

def update_option_menu(option_menu: tk.OptionMenu, var, options):
    menu: tk.Menu = option_menu["menu"]
    menu.delete(0, "end")
    for opt in options:
        if "sepior" in opt:
            menu.add_separator()
        else:
            menu.add_command(label=opt, command=lambda v=opt: var.set(v))
    if options:
        var.set(options[0])

def load_character_image(character_name):
    """Load and resize character image from local file"""
    try:
        image_path = f"./images/chars/{character_name}.png"
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None
        
        # Open image and resize
        image = Image.open(image_path)
        image = image.resize((24, 24), Image.Resampling.LANCZOS)  # Resize to 24x24
        
        return ImageTk.PhotoImage(image)
    except Exception as e:
        logger.error(f"Error loading image from {image_path}: {e}")
        return None

def populate_dropdowns(opp_dropdowns: list, stage_dropdowns: list):
    try:
        stages1 = {}
        response = requests.get("http://192.168.1.30:8005/characters", timeout=5)
        response.raise_for_status()
        characters_json = response.json()
        
        character_options = []
        
        for char in characters_json:
            characters[char["display_name"]] = char["id"]
            
            if char["id"] == -1: 
                characters["sepior1"] = -1
                character_options.append(("sepior1", None))
            else:
                # Load character image using character_name
                image = None
                if char["character_name"] and char["character_name"] != "na":
                    image = load_character_image(char["character_name"])
                    if image:
                        character_images[char["display_name"]] = image
                
                character_options.append((char["display_name"], image))
        
        character_names = list(characters.keys())

        response = requests.get("http://192.168.1.30:8005/stages", timeout=5)
        response.raise_for_status()
        stage_json = response.json()
        counter = -1
        for stage in stage_json:
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

        output_text.insert(tk.END, f"Fetched {len(character_names)} characters and {len(stage_names)} stages.\n")
        output_text.see(tk.END)

    except Exception as e:
        output_text.insert(tk.END, f"Error fetching character data: {e}\n")
        output_text.see(tk.END)
        return

    try:            
        for x in range(3):
            # Update image dropdowns for characters
            opp_dropdowns[x].update_options(character_options)
            opp_dropdowns[x].update_button_display()
            
            # Update regular dropdowns for stages
            if x == 0:
                update_option_menu(stage_dropdowns[x], stage_vars[x], list(stages1.keys()))
            else:
                update_option_menu(stage_dropdowns[x], stage_vars[x], stage_names)

    except Exception as e:
        output_text.insert(tk.END, f"Error updating character data: {e}\n")
        output_text.see(tk.END)

def are_required_dropdowns_filled():
    logger.debug(all([
        opp_vars[0].get().strip() != "N/A",
        stage_vars[0].get().strip() != "N/A",
        opp_vars[1].get().strip() != "N/A",
        stage_vars[1].get().strip() != "N/A",
    ]))
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
            if result == -1:
                output_text.insert(tk.END, "No matches found or no new matches to add.\n")
                output_text.see(tk.END)
                run_button.config(state="normal")
                return
            output_text.insert(tk.END, "Log parsing complete.\n")
            output_text.insert(tk.END, f"Added {len(result)} match{'es' if len(result) != 1 else ''}: {[",".join(str(x["elo_rank_new"]) for x in result)] if result else ""}\n")
            output_text.see(tk.END)
            if cbvar.get():
                output_text.see(tk.END)
        except Exception as e:
            output_text.insert(tk.END, f"Error: {e}\n")
            traceback.print_exc()
        finally:
            run_button.config(state="normal")

    threading.Thread(target=worker).start()

def show_debug():
    output_text.insert(tk.END, f"{cbvar.get()}\n")

setup_logging()

root = tk.Tk()
root.title("Rivals 2 Log Parser")
root.resizable(0,0)

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

# bottom
bottom_frame = Frame(root, padding=10)
bottom_frame.pack(fill="x")

def adjust_elo(delta):
    try:
        current = opp_elo.get()
    except tk.TclError:
        current = 0
    opp_elo.set(current + delta)

def on_mousewheel(event: tk.Event):
    shift = event.state & 0x0001
    delta = 5 if shift else 1
    direction = 1 if event.delta > 0 else -1
    adjust_elo(delta * direction)

Label(bottom_frame, text="Opp ELO:").grid(row=0, column=0, sticky="e")
opp_elo = tk.IntVar()
opp_elo.set(950)
opp_elo_entry = Spinbox(bottom_frame, from_=0, to_=3000, increment=1, textvariable=opp_elo, width=10)
opp_elo_entry.grid(row=0, column=1, padx=5)

opp_elo_entry.bind("<MouseWheel>", on_mousewheel)

# chars
opp_vars = []
opp_dropdowns: list[ImageDropdown] = []
stage_vars = []
stage_dropdowns = []
winner_vars = []

def sync_games(*args):
    opp_vars[1].set(opp_vars[0].get())

for x in range(3):
    Label(bottom_frame, text=f"Game {x+1}").grid(row=x+2, column=0, sticky="e")

    opp_var = tk.StringVar()
    stage_var = tk.StringVar()
    winner_var = tk.BooleanVar()

    # Create custom image dropdown instead of OptionMenu
    opp_dropdown = ImageDropdown(bottom_frame, opp_var, x+2, 1)
    if x == 0:
        opp_var.trace_add("write", sync_games)
    
    stage_dropdown = OptionMenu(bottom_frame, stage_var, "Loading...")
    winner_checkbox = Checkbutton(bottom_frame, text="OppWins", variable=winner_var)

    stage_dropdown.grid(row=x+2, column=2, padx=5, sticky="w")
    winner_checkbox.grid(row=x+2, column=3, padx=5, sticky="w")
    
    opp_vars.append(opp_var)
    stage_vars.append(stage_var)
    winner_vars.append(winner_var)

    opp_dropdowns.append(opp_dropdown)
    stage_dropdowns.append(stage_dropdown)

def clear_matchup_fields():
    for x in opp_vars:
        x.set("N/A")
    for x in stage_vars:
        x.set("N/A")
    for x in winner_vars:
        x.set(False)
    opp_elo.set(950)
    
    # Update button displays
    for dropdown in opp_dropdowns:
        dropdown.update_button_display()

clear_button = Button(bottom_frame, text="Clear", command=clear_matchup_fields)
clear_button.grid(row=0, column=10, padx=10)

style = Style()
style.theme_use(themename="classic")
populate_dropdowns(opp_dropdowns, stage_dropdowns)

root.mainloop()