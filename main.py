import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

import log_parser

load_dotenv()
logger = logging.getLogger()

def setup_logging():
    os.makedirs(os.environ.get("LOG_DIR"), exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(os.environ.get("RIV2_DEBUG"))  else logging.INFO) 

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
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

def run_parser(dev: int = 0):
    output_text.insert(tk.END, "Running log parser...\n")
    output_text.see(tk.END)
    run_button.config(state="disabled")

    def worker():
        try:
            ranks = []
            log_parser.setup_logging()
            result = log_parser.parse_log(cbvar.get())
            try:
                print(",".join(str(x["elo_rank_new"]) for x in result))
            except Exception as e:
                print("i dunno:", e)
            output_text.insert(tk.END, "Log parsing complete.\n")
            output_text.insert(tk.END, f"Added {len(result)} matches: {[",".join(str(x["elo_rank_new"]) for x in result)] if result else ""}\n")
            output_text.see(tk.END)
            # messagebox.showinfo("Done", "Log parsing complete.")
            if cbvar.get():
                log_parser.truncate_db(cbvar.get())
                output_text.insert(tk.END, "Truncating\n")
                output_text.see(tk.END)
        except Exception as e:
            output_text.insert(tk.END, f"Error: {e}\n")
            messagebox.showerror("Error", str(e))
        finally:
            run_button.config(state="normal")

    threading.Thread(target=worker).start()

def show_debug():
    output_text.insert(tk.END, f"{cbvar.get()}\n")

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

root.mainloop()
