import logging
from logging.handlers import RotatingFileHandler
import os, sys
from dotenv import load_dotenv
import utils.folders
from typing import TextIO
import re
from datetime import datetime
import utils.calc_elo as calc_elo
from utils.match import Match
import requests
from pprint import pprint
import json
from pydantic import TypeAdapter
from config import Config

RIVALS_FOLDER = os.path.join(os.path.dirname(os.getenv("APPDATA")), "Local", "Rivals2", "Saved")
RIVALS_LOG_FOLDER = os.path.join(RIVALS_FOLDER, "Logs")

config = Config()
logger = logging.getLogger()

def setup_logging():
    os.makedirs(config.log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if int(config.debug) else logging.INFO) 
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
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

def search_file(file: TextIO, string: str):
    lines = []
    file.seek(0)
    for line_no, line in enumerate(file,1):
        if string in line:
            lines.append(line.strip())
    if lines:
        return lines
    else:
        return False

def see_if_game_exists(match_id, match_date):
    res = requests.get(f"http://{config.be_host}:{config.be_port}/match-exists?match_number={match_id}")
    if res.status_code == 200:
        return True
    else:
        logger.debug(f"Got {res.status_code}")
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

def extract_numbers(line: str, file: str = None) -> Match:
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
    win_loss = 0 if int(ranks[2]) < 0 else 1
    try:
        result = Match(
            match_date = dt,
            elo_rank_new = int(ranks[0]),
            elo_rank_old = int(ranks[1]),
            elo_change = int(ranks[2]),
            ranked_game_number = int(ranks[3]),
            total_wins = int(ranks[4]),
            win_streak_value = int(ranks[5]),
            opponent_estimated_elo = -999
        )
    except:
        logger.error("Couldn't get ranks")
        result = Match(
            match_date = dt,
            elo_change = -1900,
            win_streak_value = 0,
            opponent_estimated_elo = -999
        )
   
    return result

def post_match(match: Match) -> requests.Response|dict:
    try:
        logger.debug(f"Posting match: {match.ranked_game_number} to BE")
        res = requests.post(f"http://{config.be_host}:{config.be_port}/insert-match{"?debug=1" if int(config.debug) else ""}", data=TypeAdapter(Match).dump_json(match))
        return res.json()
    except:
        logger.error(f"Couldn't post match: {match.ranked_game_number} to BE")
        return {"error": "Couldn't post match to BE"}
    
def parse_log(dev: int, extra_data: dict = {}) -> list[Match]|int:
    logger.debug("Getting log files")
    replay_files = sorted(utils.folders.get_files(RIVALS_LOG_FOLDER))
    if "Rivals2.log" in replay_files:
        replay_files.remove("Rivals2.log")
    logger.debug(f"Total files found: {len(replay_files)}")

    logger.info("Parsing data from logs")
    data = find_rank_in_logs(replay_files)
    count = []
    new_matches = []
    for match in data:
        logger.debug(f"Checking game {match.ranked_game_number}")
        if not see_if_game_exists(match.ranked_game_number, match.match_date):
            new_matches.append(match)
    if len(new_matches) < 1: return count
    for match in new_matches:
        res = None
        if len(new_matches) == 1 and extra_data:
            logger.debug(f"creating new_match, {len(new_matches)}, {extra_data}")
            new_match = Match(
                match_date=match.match_date.isoformat(),
                elo_rank_new=match.elo_rank_new,
                elo_rank_old=match.elo_rank_old,
                elo_change=match.elo_change,
                match_win=1 if match.elo_change >= 0 else 0,
                match_forfeit=0,
                ranked_game_number=match.ranked_game_number,
                total_wins=match.total_wins,
                win_streak_value=match.win_streak_value,
                opponent_elo=extra_data["opponent_elo"],
                opponent_estimated_elo=calc_elo.estimate_opponent_elo(my_elo=match.elo_rank_new, elo_change=match.elo_change, result=1 if match.elo_change >= 0 else 0, opponent_elo=extra_data["opponent_elo"]),
                opponent_name=extra_data["opponent_name"],
                game_1_char_pick=extra_data["game_1_char_pick"],
                game_1_opponent_pick=extra_data["game_1_opponent_pick"],
                game_1_stage=extra_data["game_1_stage"],
                game_1_winner=extra_data["game_1_winner"],
                game_1_final_move_id=extra_data["game_1_final_move_id"],
                game_2_char_pick=extra_data["game_2_char_pick"],
                game_2_opponent_pick=extra_data["game_2_opponent_pick"],
                game_2_stage=extra_data["game_2_stage"],
                game_2_winner=extra_data["game_2_winner"],
                game_2_final_move_id=extra_data["game_2_final_move_id"],
                game_3_char_pick=extra_data["game_3_char_pick"],
                game_3_opponent_pick=extra_data["game_3_opponent_pick"],
                game_3_stage=extra_data["game_3_stage"],
                game_3_winner=extra_data["game_3_winner"],
                game_3_final_move_id=extra_data["game_3_final_move_id"],
                final_move_id=extra_data["final_move_id"]
            )
        else:
            new_match = Match(
                match_date=match.match_date.isoformat(),
                elo_rank_new=match.elo_rank_new,
                elo_rank_old=match.elo_rank_old,
                elo_change=match.elo_change,
                match_win=1 if match.elo_change >= 0 else 0,
                match_forfeit=0,
                ranked_game_number=match.ranked_game_number,
                total_wins=match.total_wins,
                win_streak_value=match.win_streak_value,
                opponent_elo=match.opponent_elo,
                opponent_estimated_elo=calc_elo.estimate_opponent_elo(my_elo=match.elo_rank_new, elo_change=match.elo_change, result=1 if match.elo_change >= 0 else 0, opponent_elo=1000, k=24),
                opponent_name=match.opponent_name,
                game_1_char_pick=match.game_1_char_pick,
                game_1_opponent_pick=match.game_1_opponent_pick,
                game_1_stage=match.game_1_stage,
                game_1_winner=match.game_1_winner,
                game_1_final_move_id=match.game_1_final_move_id,
                game_2_char_pick=match.game_2_char_pick,
                game_2_opponent_pick=match.game_2_opponent_pick,
                game_2_stage=match.game_2_stage,
                game_2_winner=match.game_2_winner,
                game_2_final_move_id=match.game_2_final_move_id,
                game_3_char_pick=match.game_3_char_pick,
                game_3_opponent_pick=match.game_3_opponent_pick,
                game_3_stage=match.game_3_stage,
                game_3_winner=match.game_3_winner,
                game_3_final_move_id=match.game_3_final_move_id,
                final_move_id=match.final_move_id
            )

        try:
            if not dev:
                logger.debug(f"Posting match: {new_match.ranked_game_number} to BE")
                res = post_match(new_match)
        except Exception as e:
            logger.error(f"why did posting fail?? {e}|{res}")
        try:
            if not dev:
                logger.info(f"Inserting match: Game: {match.ranked_game_number} Rank: {match.elo_rank_new}, res: {res}")
        except Exception as e:
            logger.error(f"Something bonked lol: {e}")
        count.append(match)

    return count

def main():
    parse_log(dev=int(config.debug))

    return 0

if __name__ == "__main__":
    setup_logging()
    sys.exit(main())