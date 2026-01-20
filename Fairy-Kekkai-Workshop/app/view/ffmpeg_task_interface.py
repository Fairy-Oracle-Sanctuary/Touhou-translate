# coding:utf-8

from PySide6.QtCore import Signal

from ..common.config import cfg
from ..components.base_task_interface import BaseTaskInterface
from ..components.task_card import FFmpegItemWidget
from ..service.ffmpeg_service import FFmpegProcess, FFmpegTask


class FFmpegTaskInterface(BaseTaskInterface):
    """提取字幕界面"""

    log_signal = Signal(str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(
            object_name="ocrTaskInterface",
            processing_text="压制中",
            task_type="压制",
            max_concurrent_tasks=3,
            parent=parent,
        )
        # 监听配置变化，更新最大并发数
        cfg.concurrentEncodes.valueChanged.connect(self._updateMaxConcurrentTasks)

    def createTask(self, args):
        return FFmpegTask(args)

    def createTaskItem(self, task: FFmpegTask, parent):
        return FFmpegItemWidget(task, parent)

    def createTaskThread(self, task: FFmpegTask):
        return FFmpegProcess(task)

    def getTaskPath(self, task: FFmpegTask):
        return task.input_file

    def addFFmpegTask(self, args):
        self.addTask(args)

    def retryFFmpeg(self, task_id):
        self.retryTask(task_id)
