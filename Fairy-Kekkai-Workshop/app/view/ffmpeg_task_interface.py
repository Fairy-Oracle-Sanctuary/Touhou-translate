# coding:utf-8

from PySide6.QtCore import Signal

from ..components.base_task_interface import BaseTaskInterface
from ..components.ffmpeg_card import FFmpegItemWidget
from ..service.ffmpeg_service import FFmpegTask, FFmpegThread


class FFmpegTaskInterface(BaseTaskInterface):
    """提取字幕界面"""

    log_signal = Signal(str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(
            object_name="ocrTaskInterface",
            processing_text="压制中",
            task_type="压制",
            parent=parent,
        )

    def createTask(self, args):
        return FFmpegTask(args)

    def createTaskItem(self, task, parent):
        return FFmpegItemWidget(task, parent)

    def createTaskThread(self, task):
        return FFmpegThread(task)

    def getTaskPath(self, task):
        return task.video_path

    def addFFmpegTask(self, args):
        self.addTask(args)

    def retryFFmpeg(self, task_id):
        self.retryTask(task_id)
