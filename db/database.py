# db_interface.py
import os, sys
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from utils.logging import setup_logging

class MariaDBInterface:
    def __init__(self, host, port, user, password, database):
        log.debug(f"Creating DB interface for {host}:{port}")
        try:
            self.conn = mysql.connector.connect( # type: ignore
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database
            )
        except Error as e:
            log.error(f"Connection error: {e}")
            raise
        log.debug(f"Created DB interface for {host}:{port}")
        self.cursor = self.conn.cursor()

    def see_if_game_exists(self, game_no: int, date: datetime) -> bool:
        # log.debug(f"Checking match {game_no} existance")
        try:
            self.cursor.execute("SELECT m.id FROM matches_vw m LEFT JOIN seasons s ON m.season_id = s.id WHERE ranked_game_number = %s AND %s BETWEEN s.start_date AND s.end_date ", (game_no, date,))
            found = self.cursor.fetchone()
        except Exception as e:
                found = None
        return found is not None

    def close(self):
        log.debug("Closing DB interface")
        self.cursor.close()
        self.conn.close()

def main():
    return 0

if __name__ == "__main__":
    log = setup_logging()
    sys.exit(main())