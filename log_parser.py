import logging
from logging.handlers import RotatingFileHandler
import os, sys
from dotenv import load_dotenv
import utils.folders
from typing import TextIO
from pprint import pprint 
import re
from db.database import MariaDBInterface
from datetime import datetime
import utils.calc_elo as calc_elo
from utils.match import Match
import requests
from pprint import pprint
import json
from pydantic import TypeAdapter
load_dotenv()
RIVALS_FOLDER = os.path.join(os.path.dirname(os.getenv("APPDATA")), "Local", "Rivals2", "Saved")
RIVALS_LOG_FOLDER = os.path.join(RIVALS_FOLDER, "Logs")

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

def search_file(file: TextIO, string: str) -> str:
    lines = []
    file.seek(0)
    for line_no, line in enumerate(file,1):
        if string in line:
            lines.append(line.strip())
    if lines:
        return lines
    else:
        return False

def find_rank_in_logs(files: list[str]):
    ranks = []
    data = []
    with open(os.path.join(RIVALS_LOG_FOLDER, "Rivals2.log"), 'r') as f:
        x = search_file(f, "URivalsRankUpdateMessage::OnReceivedFromServer LocalPlayerIndex")
        if x:
            data.extend(x)
    for file in files:
        with open(os.path.join(RIVALS_LOG_FOLDER, file), 'r') as f:
            x = search_file(f, "URivalsRankUpdateMessage::OnReceivedFromServer LocalPlayerIndex")
            if x:
                data.extend(x)
    for line in data:
        ranks.append(extract_numbers(line))
    return ranks

def extract_numbers(line: str, file: str = None) -> dict:
    result = {}
    numbers = re.findall(r'-?\d+', line)
    ranks = numbers[-6:]
    match = re.search(r'\[(\d{4}\.\d{2}\.\d{2})-(\d{2}\.\d{2}\.\d{2})', line)
    try:
        if match:
            date_str = f"{match.group(1)} {match.group(2)}"
            dt = datetime.strptime(date_str, "%Y.%m.%d %H.%M.%S")
        else:
            dt = None
    except:
        logging.error(f"Couldn't extract date: {match.group(1)} {match.group(2)}")
    numbers = re.findall(r'-?\d+', line)
    ranks = numbers[-6:]
    win_loss = 0 if int(ranks[2]) < 0 else 1
    try:
        result = {
            "match_date": dt,
            "elo_rank_new": int(ranks[0]),
            "elo_rank_old": int(ranks[1]),
            "elo_change": int(ranks[2]),
            "ranked_game_number": int(ranks[3]),
            "total_wins": int(ranks[4]),
            "win_streak_value": int(ranks[5]),
            "opponent_elo":  calc_elo.estimate_opponent_elo(my_elo=int(ranks[1]), elo_change=int(ranks[2]), result=win_loss),
            "game_1_char_pick": "None",
            "game_1_opponent_pick": "None",
            "game_1_stage":  "None",
            "game_1_winner":  -1,
            "game_2_char_pick": "None",
            "game_2_opponent_pick": "None",
            "game_2_stage":  "None",
            "game_2_winner":  -1,
            "game_3_char_pick": "None",
            "game_3_opponent_pick": "None",
            "game_3_stage": "None",
            "game_3_winner": -1
        }
    except:
        logger.error("Couldn't get ranks")
        return {
            "match_date": dt,
            "elo_rank_new": -1,
            "elo_rank_old": -1,
            "elo_change": -1900,
            "ranked_game_number": -1,
            "total_wins": -1,
            "win_streak_value": 0,
            "opponent_elo":  -1,
            "game_1_char_pick": "None",
            "game_1_opponent_pick": "None",
            "game_1_stage":  "None",
            "game_1_winner":  -1,
            "game_2_char_pick": "None",
            "game_2_opponent_pick": "None",
            "game_2_stage":  "None",
            "game_2_winner":  -1,
            "game_3_char_pick": "None",
            "game_3_opponent_pick": "None",
            "game_3_stage": "None",
            "game_3_winner": -1
        }
    return result

def post_match(match: Match):
    res = requests.post(f"http://{os.getenv('BE_HOST')}:{os.getenv('BE_PORT')}/insert-match", data=TypeAdapter(Match).dump_json(match))
    return 0

def parse_log(dev: int) -> dict:
    logger.info("Getting DB")
    try:
        if not dev:
            db = MariaDBInterface(host=os.environ.get('DB_HOST'), port=os.environ.get('DB_PORT'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'), database=os.environ.get('DB_SCHEMA'))
        else:
            db = MariaDBInterface(host=os.environ.get('DEV_DB_HOST'), port=os.environ.get('DEV_DB_PORT'), user=os.environ.get('DEV_DB_USER'), password=os.environ.get('DEV_DB_PASS'), database=os.environ.get('DEV_DB_SCHEMA'))
    except Exception as err:
        logger.error(err)
        return []
    logger.info("Getting log files")
    replay_files = sorted(utils.folders.get_files(RIVALS_LOG_FOLDER))
    replay_files.pop(replay_files.index("Rivals2.log"))
    logger.debug(f"Total files found: {len(replay_files)}")

    logger.info("Parsing data from logs")
    data = find_rank_in_logs(replay_files)
    count = []
    try:
        db.see_if_game_exists(666)
    except:
        logger.debug("No match 666 found")
    for match in data:
        if not db.see_if_game_exists(match["ranked_game_number"]):
            new_match = Match(
                match_date=match["match_date"].isoformat() if isinstance(match["match_date"], datetime) else match["match_date"],
                elo_rank_new=match["elo_rank_new"],
                elo_rank_old=match["elo_rank_old"],
                elo_change=match["elo_change"],
                ranked_game_number=match["ranked_game_number"],
                total_wins=match["total_wins"],
                win_streak_value=match["win_streak_value"],
                opponent_elo=match["opponent_elo"],
                game_1_char_pick=match["game_1_char_pick"],
                game_1_opponent_pick=match["game_1_opponent_pick"],
                game_1_stage=match["game_1_stage"],
                game_1_winner=match["game_1_winner"],
                game_2_char_pick=match["game_2_char_pick"],
                game_2_opponent_pick=match["game_2_opponent_pick"],
                game_2_stage=match["game_2_stage"],
                game_2_winner=match["game_2_winner"],
                game_3_char_pick=match["game_3_char_pick"],
                game_3_opponent_pick=match["game_3_opponent_pick"],
                game_3_stage=match["game_3_stage"],
                game_3_winner=match["game_3_winner"]
            )
            # db.insert_match(match)
            post_match(new_match)
            logger.info(f"Inserting match: Game: {match["ranked_game_number"]} Rank: {match["elo_rank_new"]}")
            count.append(match)
        else:
            logger.debug(f"Match exists: ID {match["ranked_game_number"]}")
    logger.info("Closing DB and exiting")
    db.close()
    logger.debug(count)
    return count

def truncate_db(dev: int) -> None:
    if dev:
        db = MariaDBInterface(host=os.environ.get('DEV_DB_HOST'), port=os.environ.get('DEV_DB_PORT'), user=os.environ.get('DEV_DB_USER'), password=os.environ.get('DEV_DB_PASS'), database=os.environ.get('DEV_DB_SCHEMA'))
        db.truncate_db(os.environ.get('DEV_DB_SCHEMA'), "matches")
    return 0
def main():
    parse_log()

    return 0

if __name__ == "__main__":
    setup_logging()
    sys.exit(main())