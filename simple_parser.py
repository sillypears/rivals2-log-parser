#!/usr/bin/env python3
import re
from datetime import datetime
import os

# Path to the log file
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "Rivals2.log")


def extract_rank_updates(log_file):
    rank_updates = []
    with open(log_file, "r") as f:
        for line in f:
            if (
                "URivalsRankUpdateMessage::OnReceivedFromServer LocalPlayerIndex"
                in line
            ):
                # Extract timestamp
                timestamp_match = re.search(
                    r"\[(\d{4}\.\d{2}\.\d{2})-(\d{2}\.\d{2}\.\d{2})", line
                )
                if timestamp_match:
                    date_str = f"{timestamp_match.group(1)} {timestamp_match.group(2)}"
                    dt = datetime.strptime(date_str, "%Y.%m.%d %H.%M.%S")
                else:
                    dt = None

                # Extract numbers: Rank, OldRank, RankChange, RankedGameNumber, TotalWins, WinStreakValue
                numbers = re.findall(r"-?\d+", line)
                if len(numbers) >= 6:
                    ranks = numbers[-6:]
                    update = {
                        "timestamp": dt.isoformat() if dt else None,
                        "elo_rank_new": int(ranks[0]),
                        "elo_rank_old": int(ranks[1]),
                        "elo_change": int(ranks[2]),
                        "ranked_game_number": int(ranks[3]),
                        "total_wins": int(ranks[4]),
                        "win_streak_value": int(ranks[5]),
                    }
                    rank_updates.append(update)
    return rank_updates


if __name__ == "__main__":
    updates = extract_rank_updates(LOG_FILE)
    print(f"Found {len(updates)} rank updates:")
    for update in updates:
        print(update)
