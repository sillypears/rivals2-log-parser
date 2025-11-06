import re
duration_re = re.compile(r'RivalsCharacterXpEndMatchReportMessage::OnReceivedFromServer LocalPlayerIndex 0, matchDuration (\d+)')
rank_update_re = re.compile(r'URivalsRankUpdateMessage::OnReceivedFromServer .*: .*?, .*?, .*?, (\d+),')

def roll_up_durations(files: list):
    # Only match RivalsCharacterXpEndMatchReportMessage durations and RankUpdate summaries
    duration_re = re.compile(
        r"RivalsCharacterXpEndMatchReportMessage::OnReceivedFromServer LocalPlayerIndex 0, matchDuration (\d+)"
    )
    rank_update_re = re.compile(
        r"URivalsRankUpdateMessage::OnReceivedFromServer LocalPlayerIndex 0: (\d+), (\d+), (-?\d+), (\d+), (\d+), (\d+)"
    )
    results = {}
    durations = []
    skip_index = None  # remember which line index we already used as a trailing duration
    for file in files:
        with open(file, 'r') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                line = lines[i]

                # Skip a trailing duration line that was already consumed for previous match
                if i == skip_index:
                    i += 1
                    continue

                m_d = duration_re.search(line)
                if m_d:
                    durations.append(int(m_d.group(1)))
                    i += 1
                    continue

                m_r = rank_update_re.search(line)
                if m_r:
                    new_elo, old_elo, delta, match_id, charxp, unknown = map(int, m_r.groups())

                    # Look ahead for one trailing duration belonging to this match
                    lookahead_duration = None
                    for j in range(1, 6):
                        if i + j < len(lines):
                            next_line = lines[i + j]
                            m_next = duration_re.search(next_line)
                            if m_next:
                                lookahead_duration = int(m_next.group(1))
                                skip_index = i + j  # mark this duration line as used
                                break

                    combined = durations[:]
                    if lookahead_duration is not None:
                        combined.append(lookahead_duration)

                    # Deduplicate consecutive duplicates
                    cleaned = []
                    for d in combined:
                        if not cleaned or d != cleaned[-1]:
                            cleaned.append(d)
                    cleaned = cleaned[:3]  # cap at 3 games

                    results[match_id] = {
                        "new_elo": new_elo,
                        "old_elo": old_elo,
                        "delta": delta,
                        "charxp": charxp,
                        "unknown": unknown,
                        "durations": cleaned,
                    }

                    # Reset for next match
                    durations.clear()

                i += 1

    return results

def main():
    matches = {}
    files = [os.path.join(RIVALS_LOG_FOLDER, "Rivals2.log")]
    matches = roll_up_durations(files)
    print(matches)
    if matches:
        return matches
    return 0

if __name__ == "__main__":
    import sys
    import os
    RIVALS_FOLDER = os.path.join(os.path.dirname(os.getenv("APPDATA")), "Local", "Rivals2", "Saved")
    RIVALS_LOG_FOLDER = os.path.join(RIVALS_FOLDER, "Logs")
    print(main())
    sys.exit(0)