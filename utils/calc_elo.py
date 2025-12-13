import os, sys
from utils.log import setup_logging
import math

log = setup_logging()

def estimate_opponent_elo(my_elo: int, elo_change: int, result: int, opponent_elo:int, winstreak: int = 0, k: float = 24.0) -> int:
    """Try and guess elo

    Args:
        my_elo (int): The original elo
        elo_change (int): Change from the match result
        result (int): 0/1 depending on match
        opponent_elo (int): Used to determine k value to use. -2 = unranked
        k (int, optional): Algo change. Defaults 24

    Raises:
        ValueError: If the expected elo

    Returns:
        int: Opponent's guessed elo
    """
    k_values = {
        "ranked_elo_placement_k": 120.0,
        "ranked_elo_postplacement_k": 40.0,
        "ranked_elo_established_k": 24.0,
        "ranked_placement_median_k": 80.0,
        "ranked_placement_edge_k": 40.0,
        "ranked_placement_median_elo": 900,
        "ranked_placement_edge_difference": 450
    }
    winstreak_brkpt = {
          0: 0.00,
          1: 0.35,
          2: 0.35,
          3: 0.35,
          4: 0.45,
          5: 0.45,
          6: 0.5,
          7: 0.5,
          8: 0.5,
          9: 0.75,
          10: 1.0
    }
    if winstreak > 10:
        winstreak = 10
    winstreak_bonus = winstreak_brkpt[winstreak]

    if opponent_elo == -2: k = k_values['ranked_elo_postplacement_k']
    if (result == 1 and elo_change < 0) or (result == 0 and elo_change > 0):
        raise ValueError("Mismatch between match result and elo change sign.")
    expected_score = result - (elo_change / k)
    epsilon = 1e-6
    expected_score = max(epsilon, min(1 - epsilon, expected_score))
    odds_ratio = (1 - expected_score) / expected_score
    est_opponent_elo = my_elo + 400 * math.log10(odds_ratio)
    k *= 1 + winstreak_bonus
    log.debug(f"{my_elo}, {elo_change}, {result}, {int(opponent_elo)}, {int(est_opponent_elo)}, {k}")
    return math.floor(est_opponent_elo)

def main():
    print(estimate_opponent_elo(my_elo=1009, elo_change=11, result=1, opponent_elo=-2, winstreak=3))
    return 0

if __name__ == "__main__":
    sys.exit(main())