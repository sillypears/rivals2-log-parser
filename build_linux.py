#!/usr/bin/env python3
# build.py  –  PyInstaller helper (Windows + Linux)

import subprocess
import sys
import shutil
from pathlib import Path

# ----------------------------------------------------------------------
# 1. Detect OS → correct separator for --add-data
# ----------------------------------------------------------------------
DATA_SEP = ";" if sys.platform == "win32" else ":"

# ----------------------------------------------------------------------
# 2. Helper: add a binary file (none needed for PySide6)
# ----------------------------------------------------------------------
def extra_binaries():
    """Return list of (src, dest_dir) tuples for extra .so files."""
    return []


# ----------------------------------------------------------------------
# 3. Build command
# ----------------------------------------------------------------------
def run_build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--add-data=config.ini{DATA_SEP}.",   # <-- cross-platform
        f"--add-data=icon_rgb.png{DATA_SEP}.",
    ]

    # Add extra binaries if any
    for src, dest in extra_binaries():
        cmd.extend(["--add-binary", f"{src}{DATA_SEP}{dest}"])

    cmd.append("main.py")

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


# ----------------------------------------------------------------------
# 4. Clean up
# ----------------------------------------------------------------------
def clean():
    for p in ["build", "dist", "__pycache__"]:
        shutil.rmtree(p, ignore_errors=True)
    for spec in Path(".").glob("*.spec"):
        spec.unlink()


# ----------------------------------------------------------------------
# 5. CLI
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Build or clean the PyInstaller bundle"
    )
    parser.add_argument(
        "command",
        choices=["build", "clean"],
        nargs="?",
        default="build",
        help="build = create exe, clean = remove build artefacts",
    )
    args = parser.parse_args()

    if args.command == "build":
        run_build()
    else:
        clean()