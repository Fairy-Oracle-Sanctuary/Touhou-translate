from qfluentwidgets import FluentIcon as FIF

from ..common.event_bus import event_bus
from ..common.logger import Logger
from ..components.base_function_interface import BaseFunctionInterface
from ..components.base_stacked_interface import BaseStackedInterfaces
from ..components.config_card import FFmpegSettingInterface


class FFmpegStackedInterfaces(BaseStackedInterfaces):
    """翻译堆叠界面"""

    def __init__(self, parent=None):
        from ..view.ffmpeg_task_interface import FFmpegTaskInterface

        super().__init__(
            parent=parent,
            main_interface_class=FFmpegInterface,
            task_interface_class=FFmpegTaskInterface,
            setting_interface_class=FFmpegSettingInterface,
            interface_name="视频压制",
        )

        # 连接专用信号
        self.mainInterface.addTask.connect(self.taskInterface.addFFmpegTask)
        self.taskInterface.returnTask.connect(self.mainInterface.updateTask)


class FFmpegInterface(BaseFunctionInterface):
    """视频压制界面"""

    def __init__(self, parent=None):
        self.file_video = None
        super().__init__(parent, "压制")

        self.file_extension = "*.mp4;*.flv;*.mkv;*.avi;*.wmv;*.mpg;*.avs;*.mov"
        self.default_output_suffix = "_compressed.mp4"
        self.special_filename_mapping = {"熟肉.mp4": "熟肉_compressed.mp4"}

        self.logger = Logger("FFmpegInterface", "ffmpeg")

        self.settingsGroup.setVisible(False)

    def get_input_icon(self):
        return FIF.CALENDAR

    def _create_settings_cards(self):
        """创建基础设置卡片"""
        pass

    def _connect_signals(self):
        """连接信号槽"""
        super()._connect_signals()
        event_bus.ffmpeg_requested.connect(self.addFFmpegTaskFromProject)

    def _start_processing(self):
        """开始压制"""
        args = self._get_args()
        self.addTask.emit(args)
        self.logger.info(
            f"开始压制视频: -{self.inputFileCard.lineEdit.text()}- 参数: {args}"
        )

    def _get_args(self):
        """获取压制参数"""
        args = {}
        args["video_path"] = self.inputFileCard.lineEdit.text()
        args["output_path"] = self.outputFileCard.lineEdit.text()
        return args

    def addFFmpegTaskFromProject(self, file_path, output_path):
        """从项目界面添加压制任务"""
        args = {}
        args["video_path"] = file_path
        args["output_path"] = output_path

        self.addTask.emit(args)
