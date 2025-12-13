from db.database import MariaDBInterface
import os, sys
from dotenv import load_dotenv
from utils.logging import setup_logging
from datetime import datetime 

load_dotenv()

def main():
    db = MariaDBInterface(host=os.environ.get('DB_HOST'), port=os.environ.get('DB_PORT'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'), database=os.environ.get('DB_SCHEMA'))
    db.see_if_game_exists(666, datetime.now())

if __name__ == "__main__":
    setup_logging()
    import mariadb

    try:
        conn = mariadb.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'),
            database=os.environ.get('DB_SCHEMA'),
            port=int(os.environ.get('DB_PORT'))
        )
        print("✅ Connected successfully")
        conn.close()
    except mariadb.Error as err:
        print("❌ Connection failed:", err)
    sys.exit()
    sys.exit(main())