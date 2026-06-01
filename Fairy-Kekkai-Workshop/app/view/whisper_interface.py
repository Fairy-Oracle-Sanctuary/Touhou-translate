# coding:utf-8

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
        self.default_output_suffix = "_transcribe.srt"
        self.special_filename_mapping = {"生肉.mp4": "生肉_transcribe.srt"}

        self.logger = Logger("WhisperInterface", "whisper")

        self.settingsGroup.setVisible(False)

    def get_input_icon(self):
        return FIF.MICROPHONE

    def _create_settings_cards(self):
        """创建基础设置卡片"""
        pass

    def _connect_signals(self):
        """连接信号槽"""
        super()._connect_signals()
        event_bus.whisper_requested.connect(self.addWhisperTaskFromProject)

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
