import logging
from logging.handlers import RotatingFileHandler
import os, sys
from dotenv import load_dotenv
import utils.folders

load_dotenv()
REPLAY_FOLDER = os.path.join(os.path.dirname(os.getenv("APPDATA")), "Local", "Rivals2", "Saved", "Replays")

logger = logging.getLogger()

def setup_logging():
    os.makedirs(os.environ.get("LOG_DIR"), exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if os.environ.get("DEBUG") else logging.INFO) 

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

def get_player_character_file(file: os.path):

    player1 = ""
    player2 = ""
    player3 = ""
    player4 = ""
    
    with open(file, 'rb') as of:
        of.seek(0x1BC)
        player1 = of.read(6)

    print(player1.decode("ascii"))

    return {
        "player_1": player1,
        "player_2": player2,
        "player_3": player3,
        "player_4": player4
    }

def main():
    logger.info(REPLAY_FOLDER)
    replay_files = utils.folders.get_files(REPLAY_FOLDER)
    get_player_character_file(os.path.join(REPLAY_FOLDER, replay_files[0]))
    return 0

if __name__ == "__main__":
    setup_logging()
    sys.exit(main())