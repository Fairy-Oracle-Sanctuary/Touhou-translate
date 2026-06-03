# coding:utf-8

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from qfluentwidgets import (
    BodyLabel,
    ComboBoxSettingCard,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger
from ..components.base_function_interface import BaseFunctionInterface
from ..components.base_stacked_interface import BaseStackedInterfaces
from ..components.config_card import WhisperSettingInterface
from ..view.whisper_task_interface import WhisperTaskInterface


class WhisperStackedInterfaces(BaseStackedInterfaces):
    """语音识别堆叠界面"""

    def __init__(self, parent=None):

        super().__init__(
            parent=parent,
            main_interface_class=WhisperInterface,
            task_interface_class=WhisperTaskInterface,
            setting_interface_class=WhisperSettingInterface,
            interface_name="语音识别",
        )

        # 连接专用信号
        self.mainInterface.addTask.connect(self.taskInterface.addWhisperTask)
        self.taskInterface.returnTask.connect(self.mainInterface.updateTask)


class WhisperInterface(BaseFunctionInterface):
    """语音识别界面"""

    def __init__(self, parent=None):
        self.file_video = None
        super().__init__(parent, "识别")

        self.file_extension = (
            "*.mp4;*.flv;*.mkv;*.avi;*.wmv;*.mpg;*.mov;*.wav;*.mp3;*.flac"
        )
        self.default_output_suffix = "_Whisper.srt"
        self.special_filename_mapping = {"生肉.mp4": "原文_Whisper.srt"}

        self.logger = Logger("WhisperInterface", "whisper")

    def get_input_icon(self):
        return FIF.MICROPHONE

    def _create_settings_cards(self):
        """创建语言与格式设置卡片"""
        self.languageCard = ComboBoxSettingCard(
            cfg.whisperLanguage,
            FIF.LANGUAGE,
            "识别语言",
            "选择要识别的语言",
            texts=[
                "自动检测",
                "中文",
                "日语",
                "英语",
                "韩语",
                "法语",
                "德语",
                "西班牙语",
            ],
            parent=self.settingsGroup,
        )
        self.formatCard = ComboBoxSettingCard(
            cfg.whisperOutputFormat,
            FIF.DOCUMENT,
            "输出格式",
            "选择字幕输出格式",
            texts=["srt", "txt", "vtt"],
            parent=self.settingsGroup,
        )
        self.settingsGroup.addSettingCard(self.languageCard)
        self.settingsGroup.addSettingCard(self.formatCard)

        # 模型说明提示卡片
        hint_label = BodyLabel(
            "内置 <b>Small</b> 模型对油库里语音已够用。"
            '需更高精度可<a href="https://pan.xunlei.com/s/VOu1R3aOfz05uqcbNUBSnEFSA1?pwd=62cr#" '
            'style="color: #0078d4;">手动下载更大模型</a>后替换。',
        )
        hint_label.setWordWrap(True)
        hint_label.linkActivated.connect(
            lambda url: QDesktopServices.openUrl(QUrl(url))
        )
        self.settingsGroup.vBoxLayout.insertSpacing(-1, 8)
        self.settingsGroup.vBoxLayout.addWidget(hint_label)
        self.settingsGroup.vBoxLayout.insertSpacing(-1, 12)

    def _connect_signals(self):
        """连接信号槽"""
        super()._connect_signals()
        event_bus.whisper_requested.connect(self.addWhisperTaskFromProject)
        event_bus.whisper_video_load_signal.connect(self.loadVideoFromProject)

    def _start_processing(self):
        """开始识别"""
        args = self._get_args()
        self.addTask.emit(args)
        self.logger.info(
            f"开始语音识别: -{self.inputFileCard.lineEdit.text()}- 参数: {args}"
        )

    def _get_args(self):
        """获取识别参数"""
        args = {}
        args["video_path"] = self.inputFileCard.lineEdit.text()
        args["output_path"] = self.outputFileCard.lineEdit.text()
        args["model"] = cfg.get(cfg.whisperModelPath)
        # 从主界面卡片读取当前设置值
        args["language"] = cfg.get(cfg.whisperLanguage)
        args["format"] = cfg.get(cfg.whisperOutputFormat)
        args["gpu"] = cfg.get(cfg.whisperGpu) if cfg.get(cfg.whisperUseGpu) else ""
        return args

    def addWhisperTaskFromProject(self, file_path, output_path):
        """从项目界面添加识别任务"""
        args = {}
        args["video_path"] = file_path
        args["output_path"] = output_path
        args["model"] = cfg.get(cfg.whisperModelPath)
        args["language"] = cfg.get(cfg.whisperLanguage)
        args["format"] = cfg.get(cfg.whisperOutputFormat)
        args["gpu"] = cfg.get(cfg.whisperGpu) if cfg.get(cfg.whisperUseGpu) else ""

        self.addTask.emit(args)

    def loadVideoFromProject(self, video_path):
        """从项目加载视频到Whisper界面"""
        if video_path:
            self.file_path = video_path
            self.inputFileCard.lineEdit.setText(video_path)
            output_path = self._generate_output_path(video_path)
            self.outputFileCard.lineEdit.setText(str(output_path))
