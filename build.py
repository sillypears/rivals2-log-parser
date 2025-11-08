# build.py
import subprocess
import sys
import shutil
from pathlib import Path

def run_build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--icon=icon.ico",
        '--add-data', 'config.ini;.',   # <-- your exact data flag
        "--add-data", "icon.png;.",
        "main.py"
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)

def clean():
    for p in ["build", "dist", "__pycache__"]:
        shutil.rmtree(p, ignore_errors=True)
    for spec in Path(".").glob("*.spec"):
        spec.unlink()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "clean"], nargs="?", default="build")
    args = parser.parse_args()
    if args.command == "build":
        run_build()
    else:
        clean()