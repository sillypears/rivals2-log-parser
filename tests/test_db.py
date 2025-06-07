from db.database import MariaDBInterface
import os, sys
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()
logger = logging.getLogger()

def setup_logging():
    os.makedirs(os.environ.get("LOG_DIR"), exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        os.path.join(os.environ.get("LOG_DIR"), 'test_db.log'), 
        maxBytes=int(os.environ.get("MAX_LOG_SIZE")), 
        backupCount=int(os.environ.get("BACKUP_COUNT"))
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

def main():
    db = MariaDBInterface(host=os.environ.get('DB_HOST'), port=os.environ.get('DB_PORT'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'), database=os.environ.get('DB_SCHEMA'))
    db.see_if_game_exists(666)

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