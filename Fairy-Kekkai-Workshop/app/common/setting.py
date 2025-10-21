# coding: utf-8
import sys
from pathlib import Path

AUTHOR = "baby2016"
VERSION = "1.7.0"
YEAR = "2025"

RELEASE_URL = "https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases"

CONFIG_FOLDER = Path("AppData").absolute()

CONFIG_FILE = CONFIG_FOLDER / "config.json"
DB_PATH = CONFIG_FOLDER / "database.db"

COVER_FOLDER = CONFIG_FOLDER / "Cover"
COVER_FOLDER.mkdir(exist_ok=True, parents=True)

if sys.platform == "win32":
    EXE_SUFFIX = ".exe"
else:
    EXE_SUFFIX = ""
