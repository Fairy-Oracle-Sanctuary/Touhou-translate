# coding:utf-8

from PySide6.QtCore import Signal

from ..components.base_task_interface import BaseTaskInterface
from ..components.task_card import WhisperItemWidget
from ..service.whisper_service import WhisperProcess, WhisperTask


class WhisperTaskInterface(BaseTaskInterface):
    """语音识别任务界面"""

    log_signal = Signal(str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(
            object_name="whisperTaskInterface",
            processing_text="识别中",
            task_type="识别",
            max_concurrent_tasks=1,
            parent=parent,
        )

    def createTask(self, args):
        return WhisperTask(args)

    def createTaskItem(self, task: WhisperTask, parent):
        return WhisperItemWidget(task, parent)

    def createTaskThread(self, task: WhisperTask):
        return WhisperProcess(task)

    def getTaskPath(self, task: WhisperTask):
        return task.input_file

    def onPrintLog(self, task_id, message, is_error, is_flush):
        """处理日志输出"""
        self.log_signal.emit(message, is_error, is_flush)

    def onPrintOutput(self, task_id, message):
        """处理print输出"""
        pass

    def addWhisperTask(self, args):
        self.addTask(args)

    def retryWhisper(self, task_id):
        self.retryTask(task_id)
