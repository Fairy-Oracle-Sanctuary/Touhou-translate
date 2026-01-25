# coding:utf-8
import logging
import re
import time
import weakref

from ..common.event_bus import event_bus
from .setting import CONFIG_FOLDER

LOG_FOLDER = CONFIG_FOLDER / "Log"
_loggers = weakref.WeakValueDictionary()


class NoColorFormatter(logging.Formatter):
    def format(self, record):
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        record.msg = ansi_escape.sub("", record.msg)
        return super().format(record)


def loggerCache(cls):
    """decorator for caching logger"""

    def wrapper(name, log_name, *args, **kwargs):
        if name not in _loggers:
            instance = cls(name, log_name, *args, **kwargs)
            _loggers[name] = instance
        else:
            instance = _loggers[name]

        return instance

    return wrapper


@loggerCache
class Logger:
    """Logger class"""

    def __init__(self, fileName: str, log_name: str, printConsole=True):
        """
        Parameters
        ----------
        fileName: str
            log filename which doesn't contain `.log` suffix

        printConsole: bool
            print log to console
        """
        LOG_FOLDER.mkdir(exist_ok=True, parents=True)

        self.logFile = LOG_FOLDER / (fileName + ".log")
        self.logFile.parent.mkdir(exist_ok=True, parents=True)

        self.__logger = logging.getLogger(fileName)
        self.__consoleHandler = logging.StreamHandler()
        self.__fileHandler = logging.FileHandler(self.logFile, encoding="utf-8")

        # set log level
        self.__logger.setLevel(logging.DEBUG)
        self.__consoleHandler.setLevel(logging.DEBUG)
        self.__fileHandler.setLevel(logging.DEBUG)

        # set log format
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.__consoleHandler.setFormatter(fmt)

        formatter = NoColorFormatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.__fileHandler.setFormatter(formatter)

        if not self.__logger.hasHandlers():
            if printConsole:
                self.__logger.addHandler(self.__consoleHandler)

            self.__logger.addHandler(self.__fileHandler)

        self.log_name = log_name

    def info(self, msg):
        self.__logger.info(msg)
        self.send_log("info", msg)

    def error(self, msg, exc_info=False):
        self.__logger.error(msg, exc_info=exc_info)
        self.send_log("error", msg)

    def debug(self, msg):
        self.__logger.debug(msg)
        self.send_log("debug", msg)

    def warning(self, msg):
        self.__logger.warning(msg)
        self.send_log("warning", msg)

    def critical(self, msg):
        self.__logger.critical(msg)
        self.send_log("critical", msg)

    def send_log(self, level, msg):
        """时间 - 日志等级 - 日志内容"""
        event_bus.log_message.emit(
            self.log_name,
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} - {level.upper()} - {msg}\n",
        )
