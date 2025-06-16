# db_interface.py
import os, sys
import mysql
from mysql.connector import Error
from datetime import datetime
import logging

logger = logging.getLogger()

class MariaDBInterface:
    def __init__(self, host, port, user, password, database):
        logger.debug(f"Creating DB interface for {host}:{port}")
        try:
            self.conn = mysql.connector.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database
            )
        except Error as e:
            logger.error(f"Connection error: {e}")
            raise
        logger.debug(f"Created DB interface for {host}:{port}")
        self.cursor = self.conn.cursor()
        self.create_seasons_table()
        self.create_matches_table()

    def create_matches_table(self):
        logger.debug("Creating matches table")
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INT PRIMARY KEY AUTO_INCREMENT,
                match_date DATETIME,
                elo_rank_new INT,
                elo_rank_old INT,
                elo_change INT,
                ranked_game_number INT,
                total_wins INT,
                win_streak_value INT,
                opponent_elo INT DEFAULT -1,
                game_1_char_pick VARCHAR(255) DEFAULT 'None',
                game_1_opponent_pick VARCHAR(255) DEFAULT 'None',
                game_1_stage VARCHAR(255) DEFAULT 'None',
                game_1_winner INT DEFAULT -1,
                game_2_char_pick VARCHAR(255) DEFAULT 'None',
                game_2_opponent_pick VARCHAR(255) DEFAULT 'None',
                game_2_stage VARCHAR(255) DEFAULT 'None',
                game_2_winner INT DEFAULT -1,
                game_3_char_pick VARCHAR(255) DEFAULT 'None',
                game_3_opponent_pick VARCHAR(255) DEFAULT 'None',
                game_3_stage VARCHAR(255) DEFAULT 'None',
                game_3_winner INT DEFAULT -1
            )
        ''')
        self.conn.commit()
        logger.debug("Committing matches table")
    def create_seasons_table(self):
        logger.debug("Creating seasons")
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasons (
                id INT PRIMARY KEY AUTO_INCREMENT,
                start_date DATETIME,
                end_date DATETIME,
                short_name VARCHAR(100),
                display_name VARCHAR(100)
            )
        ''')
        self.cursor.execute("SELECT count(id) FROM seasons")
        count = int(self.cursor.fetchone()[0])
        if count < 1:
            self.cursor.execute(''' 
                INSERT INTO seasons (
                    start_date,
                    end_date,
                    short_name,
                    display_name
                ) VALUES ("2024-10-23T00:00:00", "2025-03-03T23:59:59", "ranked_lite", "Ranked Lite")
            ''', ())
            self.cursor.execute('''
                INSERT INTO seasons (
                    start_date, 
                    end_date,
                    short_name,
                    display_name
                ) VALUES ("2025-03-04T00:00:00", "2025-07:01T21:59:59", "spring_2025", "Spring 2025")
            ''', ())
        self.conn.commit()
        logger.debug("Loaded seasons")
    def insert_match(self, match_data: dict):
        self.cursor.execute('''
            INSERT INTO matches (
                match_date,
                elo_rank_new,
                elo_rank_old,
                elo_change,
                ranked_game_number,
                total_wins,
                win_streak_value,
                opponent_elo,
                game_1_char_pick,
                game_1_opponent_pick,
                game_1_stage,
                game_1_winner,
                game_2_char_pick,
                game_2_opponent_pick,
                game_2_stage,
                game_2_winner,
                game_3_char_pick,
                game_3_opponent_pick,
                game_3_stage,
                game_3_winner
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            match_data["match_date"].isoformat() if isinstance(match_data["match_date"], datetime) else match_data["match_date"],
            match_data["elo_rank_new"],
            match_data["elo_rank_old"],
            match_data["elo_change"],
            match_data["ranked_game_number"],
            match_data["total_wins"],
            match_data["win_streak_value"],
            match_data["opponent_elo"],
            match_data["game_1_char_pick"],
            match_data["game_1_opponent_pick"],
            match_data["game_1_stage"],
            match_data["game_1_winner"],
            match_data["game_2_char_pick"],
            match_data["game_2_opponent_pick"],
            match_data["game_2_stage"],
            match_data["game_2_winner"],
            match_data["game_3_char_pick"],
            match_data["game_3_opponent_pick"],
            match_data["game_3_stage"],
            match_data["game_3_winner"]
        ))
        self.conn.commit()

    def see_if_game_exists(self, game_no: int) -> bool:
        logger.debug("Checking match existance")
        self.cursor.execute("SELECT id FROM matches WHERE ranked_game_number = %s", (game_no,))
        return self.cursor.fetchone() is not None

    def truncate_db(self, db_name: str, table: str):
        print(f"TRUNCATE {db_name}.{table};")
        self.cursor.execute(f"TRUNCATE {db_name}.{table}")
        return 0
    
    def close(self):
        logger.debug("Closing DB interface")
        self.cursor.close()
        self.conn.close()

def main():
    return 0

if __name__ == "__main__":
    sys.exit(main())