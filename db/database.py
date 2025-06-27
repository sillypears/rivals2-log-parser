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
        self.create_stages_table()
        self.create_seasons_table()
        self.create_characters_table()
        self.create_matches_table()

    def create_stages_table(self):
        logger.debug("Creating stages table")
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stages (
                id INT PRIMARY KEY AUTO_INCREMENT,
                stage_name VARCHAR(45) NOT NULL,
                display_name VARCHAR(45) NOT NULL
            )
        ''')
        logger.debug("Created stages table")
        self.cursor.execute("SELECT count(id) FROM stages")
        count = int(self.cursor.fetchone()[0])
        if count < 1:
            self.cursor.execute('''
                INSERT INTO stages (id, stage_name, display_name) VALUES
                (-1, 'na', 'N/A'), (1, 'forest', 'Aetherian Forest'), (2, 'godai', 'Godai Delta'), (3, 'hodojo', 'Hodojo'),
                (4, 'jules', 'Julesvale'), (5, 'port', 'Merchant Port'), (6, 'armada', 'Air Armada'),
                (7, 'capital', 'Fire Capital'), (8, 'harbor', 'Hyborean Harbor'), (9, 'rockwall', 'Rock Wall'),
                (10, 'tempest', 'Tempest Peak')
            ''')
        self.conn.commit()
        logger.debug("Loaded stages")

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
    def create_characters_table(self):
        logger.debug("Creating characters table")
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INT PRIMARY KEY AUTO_INCREMENT,
                character_name VARCHAR(45) NOT NULL,
                display_name VARCHAR(45) NOT NULL
            )
        ''')
        logger.debug("Created characters table")
        self.cursor.execute("SELECT count(id) FROM characters")
        count = int(self.cursor.fetchone()[0])
        if count < 1:
            self.cursor.execute('''
                INSERT INTO characters (id, character_name, display_name) VALUES
                (-1, 'na', 'N/A'), (1, 'fors', 'Forsburn'), (2, 'lox', 'Loxodont'), (3, 'clairen', 'Clairen'),
                (4, 'zetter', 'Zetterburn'), (5, 'wrastor', 'Wrastor'), (6, 'fleet', 'Fleet'),
                (7, 'absa', 'Absa'), (8, 'oly', 'Olympia'), (9, 'maypul', 'Maypul'),
                (10, 'kragg', 'Kragg'), (11, 'ranno', 'Ranno'), (12, 'orcane', 'Orcane'),
                (13, 'etalus', 'Etalus')
            ''')
        self.conn.commit()
        logger.debug("Loaded characters")
    
    def create_matches_table(self):
        logger.debug("Creating matches table")
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
                match_date DATETIME NOT NULL,
                elo_rank_new INT NOT NULL,
                elo_rank_old INT NOT NULL,
                elo_change INT NOT NULL,
                win_streak_value INT NOT NULL,
                ranked_game_number INT NOT NULL,
                total_wins INT NOT NULL,
                opponent_elo INT DEFAULT -1 NOT NULL,
                match_win TINYINT DEFAULT 0 NOT NULL,
                game_1_char_pick INT(5) DEFAULT -1 NOT NULL,
                game_1_opponent_pick INT(5) DEFAULT -1 NOT NULL,
                game_1_stage INT(5) DEFAULT -1 NOT NULL,
                game_1_winner INT(5) DEFAULT -1 NOT NULL,
                game_2_char_pick INT(5) DEFAULT -1 NOT NULL,
                game_2_opponent_pick INT(5) DEFAULT -1 NOT NULL,
                game_2_stage INT(5) DEFAULT -1 NOT NULL,
                game_2_winner INT DEFAULT -1 NOT NULL,
                game_3_char_pick INT(5) DEFAULT -1 NOT NULL,
                game_3_opponent_pick INT(5) DEFAULT -1 NOT NULL,
                game_3_stage INT(5) DEFAULT -1 NOT NULL,
                game_3_winner INT DEFAULT -1 NOT NULL,
                UNIQUE KEY `ranked_game_number_UNIQUE` (`ranked_game_number`),
                UNIQUE KEY `id_UNIQUE` (`id`),
                KEY `game_1_stage_fk_idx` (`game_1_stage`),
                KEY `game_2_stage_fk_idx` (`game_2_stage`),
                KEY `game_3_stage_fk_idx` (`game_3_stage`),
                KEY `game_1_char_pick_idx` (`game_1_char_pick`),
                KEY `game_2_char_pick_idx` (`game_2_char_pick`),
                KEY `game_3_char_pick_idx` (`game_3_char_pick`),
                KEY `game_1_opponent_pick_idx` (`game_1_opponent_pick`),
                KEY `game_2_opponent_pick_idx` (`game_2_opponent_pick`),
                KEY `game_3_opponent_pick_idx` (`game_3_opponent_pick`),
                CONSTRAINT `game_1_stage_fk` FOREIGN KEY (`game_1_stage`) REFERENCES `stages` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
                CONSTRAINT `game_2_stage_fk` FOREIGN KEY (`game_2_stage`) REFERENCES `stages` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
                CONSTRAINT `game_3_stage_fk` FOREIGN KEY (`game_3_stage`) REFERENCES `stages` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
                CONSTRAINT `game_1_char_pick_fk` FOREIGN KEY (`game_1_char_pick`) REFERENCES `characters` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
                CONSTRAINT `game_2_char_pick_fk` FOREIGN KEY (`game_2_char_pick`) REFERENCES `characters` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
                CONSTRAINT `game_3_char_pick_fk` FOREIGN KEY (`game_3_char_pick`) REFERENCES `characters` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
                CONSTRAINT `game_1_opponent_pick_fk` FOREIGN KEY (`game_1_opponent_pick`) REFERENCES `characters` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
                CONSTRAINT `game_2_opponent_pick_fk` FOREIGN KEY (`game_2_opponent_pick`) REFERENCES `characters` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
                CONSTRAINT `game_3_opponent_pick_fk` FOREIGN KEY (`game_3_opponent_pick`) REFERENCES `characters` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
            )
        ''')
        self.conn.commit()
        logger.debug("Committing matches table")
        logger.debug("Creating match_view")
        self.cursor.execute(''' 
        CREATE VIEW IF NOT EXISTS matches_vw AS
            SELECT 
                `m`.`id` AS `id`,
                `m`.`match_date` AS `match_date`,
                `m`.`elo_rank_new` AS `elo_rank_new`,
                `m`.`elo_rank_old` AS `elo_rank_old`,
                `m`.`elo_change` AS `elo_change`,
                `m`.`match_win` AS `match_win`,
                `m`.`ranked_game_number` AS `ranked_game_number`,
                `m`.`total_wins` AS `total_wins`,
                `m`.`win_streak_value` AS `win_streak_value`,
                `m`.`opponent_elo` AS `opponent_elo`,
                `m`.`game_1_char_pick` AS `game_1_char_pick`,
                `cs1`.`display_name` AS `game_1_char_pick_name`,
                `m`.`game_1_opponent_pick` AS `game_1_opponent_pick`,
                `co1`.`display_name` AS `game_1_opponent_pick_name`,
                `m`.`game_1_stage` AS `game_1_stage`,
                `s1`.`display_name` AS `game_1_stage_name`,
                `m`.`game_1_winner` AS `game_1_winner`,
                `m`.`game_2_char_pick` AS `game_2_char_pick`,
                `cs2`.`display_name` AS `game_2_char_pick_name`,
                `m`.`game_2_opponent_pick` AS `game_2_opponent_pick`,
                `co2`.`display_name` AS `game_2_opponent_pick_name`,
                `m`.`game_2_stage` AS `game_2_stage`,
                `s2`.`display_name` AS `game_2_stage_name`,
                `m`.`game_2_winner` AS `game_2_winner`,
                `m`.`game_3_char_pick` AS `game_3_char_pick`,
                `cs3`.`display_name` AS `game_3_char_pick_name`,
                `m`.`game_3_opponent_pick` AS `game_3_opponent_pick`,
                `co3`.`display_name` AS `game_3_opponent_pick_name`,
                `m`.`game_3_stage` AS `game_3_stage`,
                `s3`.`display_name` AS `game_3_stage_name`,
                `m`.`game_3_winner` AS `game_3_winner`
            FROM
                (((((((((`matches` `m`
                LEFT JOIN `stages` `s1` ON (`m`.`game_1_stage` = `s1`.`id`))
                LEFT JOIN `stages` `s2` ON (`m`.`game_2_stage` = `s2`.`id`))
                LEFT JOIN `stages` `s3` ON (`m`.`game_3_stage` = `s3`.`id`))
                LEFT JOIN `characters` `cs1` ON (`m`.`game_1_char_pick` = `cs1`.`id`))
                LEFT JOIN `characters` `co1` ON (`m`.`game_1_opponent_pick` = `co1`.`id`))
                LEFT JOIN `characters` `cs2` ON (`m`.`game_2_char_pick` = `cs2`.`id`))
                LEFT JOIN `characters` `co2` ON (`m`.`game_2_opponent_pick` = `co2`.`id`))
                LEFT JOIN `characters` `cs3` ON (`m`.`game_3_char_pick` = `cs3`.`id`))
                LEFT JOIN `characters` `co3` ON (`m`.`game_3_opponent_pick` = `co3`.`id`))
            ORDER BY `m`.`ranked_game_number` DESC
        ''')
        logger.debug("Committing matches table and view")
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
                match_win,
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            match_data["match_date"].isoformat() if isinstance(match_data["match_date"], datetime) else match_data["match_date"],
            match_data["elo_rank_new"],
            match_data["elo_rank_old"],
            match_data["elo_change"],
            match_data["ranked_game_number"],
            match_data["total_wins"],
            match_data["win_streak_value"],
            match_data["opponent_elo"],
            1 if match_data["elo_change"] > 0 else 0,
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
        logger.debug(f"Checking match {game_no} existance")
        self.cursor.execute("SELECT id FROM matches WHERE ranked_game_number = %s", (game_no,))
        try:
            found = self.cursor.fetchone()
        except:
            found = None
        return found is not None

    def truncate_db(self, db_name: str, table: str):
        logger.debug(f"TRUNCATE {db_name}.{table};")
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