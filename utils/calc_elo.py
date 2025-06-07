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
        k (int, optional): Algo change. Defaults to 25.

    Raises:
        ValueError: If the expected elo

    Returns:
        int: Opponent's guessed elo
    """
        
    if (result == 1 and elo_change < 0) or (result == 0 and elo_change > 0):
        raise ValueError("Mismatch between match result and elo change sign.")
    
    expected_score = result - (elo_change / k)

    # Clamp expected score within (0, 1) to avoid log math domain errors
    epsilon = 1e-6
    expected_score = max(epsilon, min(1 - epsilon, expected_score))

    # Calculate opponent Elo
    odds_ratio = (1 - expected_score) / expected_score
    opponent_elo = my_elo + 400 * math.log10(odds_ratio)

    return math.floor(opponent_elo)

def main():

    return 0

if __name__ == "__main__":
    sys.exit(main())