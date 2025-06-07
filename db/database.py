# db_interface.py
import os, sys
import sqlite3
import mysql
from mysql.connector import Error
from datetime import datetime

class SQLiteInterface:
    def __init__(self, db_path='rivals2.sqlite'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_date TEXT,
                elo_rank_new INTEGER,
                elo_rank_old INTEGER,
                elo_change INTEGER,
                ranked_game_number INTEGER,
                total_wins INTEGER,
                win_streak_value INTEGER,
                opponent_elo INTEGER DEFAULT -1,
                game_1_char_pick TEXT DEFAULT "None",
                game_1_opponent_pick TEXT DEFAULT "None",
                game_1_stage TEXT DEFAULT "None",
                game_1_winner INTEGER DEFAULT -1,
                game_2_char_pick TEXT DEFAULT "None",
                game_2_opponent_pick TEXT DEFAULT "None",
                game_2_stage TEXT DEFAULT "None",
                game_2_winner INTEGER DEFAULT -1,
                game_3_char_pick TEXT DEFAULT "None",
                game_3_opponent_pick TEXT DEFAULT "None",
                game_3_stage TEXT DEFAULT "None",
                game_3_winner INTEGER DEFAULT -1
            )
        ''')
        self.conn.commit()

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
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data["match_date"].isoformat(),
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
        self.cursor.execute("SELECT id FROM matches WHERE ranked_game_number = ?", (game_no,))
        return self.cursor.fetchone() is not None
    
    def fetch_all_logs(self):
        self.cursor.execute('SELECT * FROM logs')
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


class MariaDBInterface:
    def __init__(self, host, port, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()
        self.create_table()
    def create_table(self):
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
        self.cursor.execute("SELECT id FROM matches WHERE ranked_game_number = %s", (game_no,))
        return self.cursor.fetchone() is not None

    def close(self):
        self.cursor.close()
        self.conn.close()

def main():
    return 0

if __name__ == "__main__":
    sys.exit(main())