import os, sys
import logging

logger = logging.getLogger()

def get_files(folder: os.path) -> list[str]:
    return os.listdir(folder)

def main():

    return 0

if __name__ == "__main__":
    sys.exit(main())