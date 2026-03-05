import os
import sys
from typing import TextIO
import re
from datetime import datetime
import utils.calc_elo as calc_elo
from utils.match import Match
import requests
import requests.exceptions
import json
from pydantic import TypeAdapter
from config import Config
from utils.log import setup_logging
from match_duration import roll_up_durations


if sys.platform == "win32":
    APPDATAFOLDER = os.path.dirname(os.getenv("APPDATA"))
elif sys.platform.startswith("linux"):
    APPDATAFOLDER = f"{os.path.expanduser('~')}/.local/share/Steam/steamapps/compatdata/2217000/pfx/drive_c/users/steamuser/AppData/"
elif sys.platform == "darwin":
    sys.exit("Dumbass on macOS")
else:
    sys.exit("Unknown OS")

RIVALS_FOLDER = os.path.join(APPDATAFOLDER, "Local", "Rivals2", "Saved")
RIVALS_LOG_FOLDER = os.path.join(RIVALS_FOLDER, "Logs")

config = Config()

logger = setup_logging()

# Patterns for extracting additional match data
PATTERNS = {
    "character": r"Character picked: (\w+)",
    "stage": r"Stage selected: (\w+)",
    "winner": r"Winner: (\w+)",
    "final_move": r"Final move: (\d+)",
}

# Cache file for incremental parsing
CACHE_FILE = os.path.join("logs", "last_parsed.json")


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {"last_timestamp": None, "parsed_matches": []}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def search_file(file: TextIO, string: str):
    lines = []
    file.seek(0)
    for line_no, line in enumerate(file, 1):
        if string in line:
            lines.append(line.strip())
    if lines:
        return lines
    else:
        return False


def extract_timestamp(line: str):
    match = re.search(r"\[(\d{4}\.\d{2}\.\d{2})-(\d{2}\.\d{2}\.\d{2})", line)
    if match:
        try:
            date_str = f"{match.group(1)} {match.group(2)}"
            return datetime.strptime(date_str, "%Y.%m.%d %H.%M.%S")
        except:
            return None
    return None


def see_if_game_exists_batch(match_ids):
    try:
        # Batch check - assuming API supports it; otherwise, loop with individual calls
        existing = []
        for match_id in match_ids:
            res = requests.get(
                f"http://{config.be_host}:{config.be_port}/match-exists?match_number={match_id}",
                timeout=10,
            )
            if res.status_code == 200:
                existing.append(match_id)
        return existing
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking match existence: {e}")
        return []  # Assume none exist on error


def find_rank_in_logs(files: list[str], last_timestamp=None):
    ranks = []
    data = {}
    for file in files:
        with open(file, "r") as f:
            # Incremental: skip lines before last_timestamp
            for line in f:
                timestamp = extract_timestamp(line)
                if last_timestamp and timestamp and timestamp <= last_timestamp:
                    continue
                for key, pattern in PATTERNS.items():
                    match_obj = re.search(pattern, line)
                    if match_obj:
                        if key not in data:
                            data[key] = []
                        value = match_obj.group(1) if match_obj.groups() else None
                        data[key].append((timestamp, value))
                if (
                    "URivalsRankUpdateMessage::OnReceivedFromServer LocalPlayerIndex"
                    in line
                ):
                    ranks.append(extract_numbers(line, data))
    return ranks


def extract_numbers(line: str, extra_data: dict = {}) -> Match:
    result = {}
    numbers = re.findall(r"-?\d+", line)
    ranks = numbers[-6:]
    match_dt = extract_timestamp(line)
    try:
        result = Match(
            match_date=match_dt or datetime(1900, 1, 1),
            elo_rank_new=int(ranks[0]),
            elo_rank_old=int(ranks[1]),
            elo_change=int(ranks[2]),
            ranked_game_number=int(ranks[3]),
            total_wins=int(ranks[4]),
            win_streak_value=int(ranks[5]),
            opponent_estimated_elo=-999,
        )
    except:
        logger.error("Couldn't get ranks")
        result = Match(
            match_date=match_dt or datetime(1900, 1, 1),
            elo_change=-1900,
            win_streak_value=0,
            opponent_estimated_elo=-999,
        )

    # Enrich with extracted data
    if "character" in extra_data and extra_data["character"]:
        result.game_1_char_pick = (
            extra_data["character"][0][1] if extra_data["character"] else None
        )
    if "stage" in extra_data and extra_data["stage"]:
        result.game_1_stage = extra_data["stage"][0][1] if extra_data["stage"] else None
    if "winner" in extra_data and extra_data["winner"]:
        result.game_1_winner = (
            extra_data["winner"][0][1] if extra_data["winner"] else None
        )
    if "final_move" in extra_data and extra_data["final_move"]:
        result.game_1_final_move_id = (
            int(extra_data["final_move"][0][1]) if extra_data["final_move"] else None
        )

    return result


def post_match(match: Match) -> requests.Response | dict:
    try:
        logger.debug(f"Posting match: {match.ranked_game_number} to BE")
        res = requests.post(
            f"http://{config.be_host}:{config.be_port}/insert-match{'?debug=1' if int(config.debug) else ''}",
            data=TypeAdapter(Match).dump_json(match),
            timeout=10,
        )
        res.raise_for_status()
        return res.json()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout posting match: {match.ranked_game_number}")
        return {"error": "Timeout posting match to backend"}
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error posting match: {match.ranked_game_number}")
        return {"error": "Unable to connect to backend for posting match"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error posting match {match.ranked_game_number}: {e}")
        return {"error": f"Failed to post match to backend: {e}"}


def parse_log(dev: int, extra_data: dict = {}) -> list[Match] | int:
    logger.debug("Getting log files")
    replay_files = [os.path.join(RIVALS_LOG_FOLDER, "Rivals2.log")]
    logger.debug(f"Total files found: {len(replay_files)}")

    # Load cache for incremental parsing
    cache = load_cache()
    last_timestamp = cache.get("last_timestamp")
    if last_timestamp:
        last_timestamp = datetime.fromisoformat(last_timestamp)

    logger.info("Parsing data from logs (incremental)")
    data = find_rank_in_logs(replay_files, last_timestamp)
    count = []
    new_matches = []
    match_ids = [match.ranked_game_number for match in data]
    existing = see_if_game_exists_batch(match_ids)
    for match in data:
        if match.ranked_game_number not in existing:
            new_matches.append(match)

    potential_times = roll_up_durations(replay_files)
    logger.debug(potential_times)

    for match in data:
        res = None
        if extra_data:
            logger.debug(f"creating new_match, {len(new_matches)}, {extra_data}")
            new_match = Match(
                match_date=match.match_date or datetime(1900, 1, 1),
                elo_rank_new=match.elo_rank_new,
                elo_rank_old=match.elo_rank_old,
                elo_change=match.elo_change,
                match_win=1 if match.elo_change >= 0 else 0,
                match_forfeit=0,
                ranked_game_number=match.ranked_game_number,
                total_wins=match.total_wins,
                win_streak_value=match.win_streak_value,
                opponent_elo=extra_data["opponent_elo"],
                opponent_estimated_elo=calc_elo.estimate_opponent_elo(
                    my_elo=match.elo_rank_new,
                    elo_change=match.elo_change,
                    result=1 if match.elo_change >= 0 else 0,
                    opponent_elo=extra_data["opponent_elo"],
                ),
                opponent_name=extra_data["opponent_name"],
                game_1_char_pick=match.game_1_char_pick
                or extra_data["game_1_char_pick"],
                game_1_opponent_pick=extra_data["game_1_opponent_pick"],
                game_1_stage=match.game_1_stage or extra_data["game_1_stage"],
                game_1_winner=match.game_1_winner or extra_data["game_1_winner"],
                game_1_final_move_id=match.game_1_final_move_id
                or extra_data["game_1_final_move_id"],
                game_1_duration=extra_data["game_1_duration"],
                game_2_char_pick=extra_data["game_2_char_pick"],
                game_2_opponent_pick=extra_data["game_2_opponent_pick"],
                game_2_stage=extra_data["game_2_stage"],
                game_2_winner=extra_data["game_2_winner"],
                game_2_final_move_id=extra_data["game_2_final_move_id"],
                game_2_duration=extra_data["game_2_duration"],
                game_3_char_pick=extra_data["game_3_char_pick"],
                game_3_opponent_pick=extra_data["game_3_opponent_pick"],
                game_3_stage=extra_data["game_3_stage"],
                game_3_winner=extra_data["game_3_winner"],
                game_3_final_move_id=extra_data["game_3_final_move_id"],
                game_3_duration=extra_data["game_3_duration"],
                final_move_id=extra_data["final_move_id"],
            )
        else:
            new_match = Match(
                match_date=match.match_date or datetime(1900, 1, 1),
                elo_rank_new=match.elo_rank_new,
                elo_rank_old=match.elo_rank_old,
                elo_change=match.elo_change,
                match_win=1 if match.elo_change >= 0 else 0,
                match_forfeit=0,
                ranked_game_number=match.ranked_game_number,
                total_wins=match.total_wins,
                win_streak_value=match.win_streak_value,
                opponent_elo=match.opponent_elo,
                opponent_estimated_elo=calc_elo.estimate_opponent_elo(
                    my_elo=match.elo_rank_new,
                    elo_change=match.elo_change,
                    result=1 if match.elo_change >= 0 else 0,
                    opponent_elo=1000,
                    k=24,
                ),
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
                final_move_id=match.final_move_id,
            )

        try:
            if not dev:
                logger.debug(f"Posting match: {new_match.ranked_game_number} to BE")
                res = post_match(new_match)
                logger.info(res)

        except Exception as e:
            logger.error(f"why did posting fail?? {e}|{res}")
        try:
            if not dev:
                logger.info(
                    f"Inserted match: Game {new_match.ranked_game_number}, Rank {new_match.elo_rank_new}, Change {new_match.elo_change}, Final Move {new_match.final_move_id}, res: {res}"
                )
        except Exception as e:
            logger.error(f"Something bonked lol: {e}")
        count.append(match)

    if data:
        latest_ts = max(
            (m.match_date for m in data if m.match_date), default=last_timestamp
        )
        if latest_ts:
            cache["last_timestamp"] = latest_ts.isoformat()
        save_cache(cache)

    return count


def main():
    parse_log(dev=int(config.debug))

    return 0


if __name__ == "__main__":
    sys.exit(main())
