# coding: utf-8
import sys
from pathlib import Path
from PySide6.QtCore import QStandardPaths

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2025
AUTHOR = "zhiyiYo"
VERSION = "0.11.0"
APP_NAME = "Fluent-M3U8"
HELP_URL = "https://fluent-m3u8.org"
REPO_URL = "https://github.com/zhiyiYo/Fluent-M3U8"
FEEDBACK_URL = "https://github.com/zhiyiYo/Fluent-M3U8/issues"
RELEASE_URL = "https://github.com/zhiyiYo/Fluent-M3U8/releases"
DOC_URL = "https://fluent-m3u8.org"
AFDIAN_URL = "https://afdian.com/a/zhiyiYo"
VIDEO_URL = "https://www.bilibili.com/video/BV1SHNDebE2d"
KOFI_URL = "https://ko-fi.com/zhiyiyo"

CONFIG_FOLDER = Path('AppData').absolute()

if sys.platform == "win32" and not DEBUG:
    CONFIG_FOLDER = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)) / APP_NAME


CONFIG_FILE = CONFIG_FOLDER / "config.json"
DB_PATH = CONFIG_FOLDER / "database.db"

COVER_FOLDER = CONFIG_FOLDER / "Cover"
COVER_FOLDER.mkdir(exist_ok=True, parents=True)

if sys.platform == "win32":
    EXE_SUFFIX = ".exe"
else:
    EXE_SUFFIX = ""
