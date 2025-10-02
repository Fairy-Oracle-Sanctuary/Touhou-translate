# coding:utf-8
import os
import sys
from enum import Enum

from PySide6.QtCore import QLocale, QStandardPaths
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, Theme, FolderValidator, ConfigSerializer, RangeConfigItem,
                            RangeValidator, FolderListValidator)

from .setting import CONFIG_FILE, CONFIG_FOLDER
from pathlib import Path
import json

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

class ProjectConfig():
    """项目配置"""
    def __init__(self, config_file=CONFIG_FOLDER):
        self.config_file = config_file / "project.json"
        self.config = {}
        self.load()
    
    def load(self):
        """读取配置文件"""
        if not self.config_file.exists():
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.set("project_link", [])
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError:
            self.config = {}
    
    def save(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save()
    
    def remove(self, key):
        """删除配置项"""
        if key in self.config:
            del self.config[key]
            self.save()
    
    def get_all(self):
        """获取所有配置"""
        return self.config.copy()
    
class Config(QConfig):
    """ Config of application """

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    accentColor = OptionsConfigItem(
        "MainWindow", "AccentColor", "#009faa", OptionsValidator(["#009faa", "Auto"]))

    # project
    linkProject = ProjectConfig()
    
cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load(str(CONFIG_FILE.absolute()), cfg)