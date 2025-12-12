#!/usr/bin/env python3

import subprocess
import sys
import shutil
from pathlib import Path

DATA_SEP = ";" if sys.platform == "win32" else ":"
VERSION = "0.0.0"

def extra_binaries():
    """Return list of (src, dest_dir) tuples for extra .so files."""
    return []

def run_build(args):
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--add-data=version{DATA_SEP}.",
        f"--add-data=config.ini{DATA_SEP}.",
        f"--add-data=icon_rgb.png{DATA_SEP}.",
    ]

    for src, dest in extra_binaries():
        cmd.extend(["--add-binary", f"{src}{DATA_SEP}{dest}"])

    cmd.append("main.py")

    major_version = 0
    minor_version = 0
    version = "0.0"

    with open('version', 'r') as f:
        version = f.read().split(".")
        major_version = version[0]
        minor_version = int(version[1]) + 1

    if int(args.minor) > 0: minor_version = int(args.minor)
    if int(args.major) > 0: 
        major_version = int(args.major)
        minor_version = 0

    with open('version', 'w') as f:
        f.write(f"{major_version}.{minor_version}")
    
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
    parser.add_argument(
        "-M",
        "--major",
        type=int,
        default=-1,
        dest="major",
        help="Major version to increase to"
    )
    parser.add_argument(
        "-m",
        "--minor",
        type=int,
        default=-1,
        dest="minor",
        help="Minor version to increase to"
    )

    args = parser.parse_args()

    if args.command == "build":
        run_build(args)
    else:
        clean()