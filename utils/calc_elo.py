import os, sys
import logging
import math

logger = logging.getLogger()

def estimate_opponent_elo(my_elo: int, elo_change: int, result: int, k: int = 25) -> int:
    """Try and guess elo

    Args:
        my_elo (int): The original elo
        elo_change (int): Change from the match result
        result (int): 0/1 depending on match
        k (int, optional): Algo change. Defaults 25

    Raises:
        ValueError: If the expected elo

    Returns:
        int: Opponent's guessed elo
    """
    k_values = {
        "ranked_elo_start_value": 1000,
        "ranked_elo_placement_k": 120,
        "ranked_elo_postplacement_k": 40,
        "ranked_elo_established_k": 24,
        "ranked_placement_median_k": 80,
        "ranked_placement_edge_k": 40,
        "ranked_placement_median_elo": 900,
        "ranked_placement_edge_difference": 450
    }
    if (result == 1 and elo_change < 0) or (result == 0 and elo_change > 0):
        raise ValueError("Mismatch between match result and elo change sign.")
    expected_score = result - (elo_change / k)
    epsilon = 1e-6
    expected_score = max(epsilon, min(1 - epsilon, expected_score))
    odds_ratio = (1 - expected_score) / expected_score
    opponent_elo = my_elo + 400 * math.log10(odds_ratio)
    return math.floor(opponent_elo)

def main():

    return 0

if __name__ == "__main__":
    sys.exit(main())