# coding:utf-8

from PySide6.QtCore import Signal

from ..components.base_task_interface import BaseTaskInterface
from ..components.task_card import ReleaseItemWidget
from ..service.release_service import ReleaseProcess, ReleaseTask


class ReleaseTaskInterface(BaseTaskInterface):
    """B站视频上传任务管理界面"""

    log_signal = Signal(str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(
            object_name="releaseTaskInterface",
            processing_text="上传中",
            task_type="上传",
            max_concurrent_tasks=1,  # B站上传建议单任务执行
            parent=parent,
        )

    def createTask(self, args):
        return ReleaseTask(args)

    def createTaskItem(self, task: ReleaseTask, parent):
        return ReleaseItemWidget(task, parent=parent)

    def createTaskThread(self, task: ReleaseTask):
        return ReleaseProcess(task)

    def getTaskPath(self, task: ReleaseTask):
        return task.video_path

    def addReleaseTask(self, args):
        self.addTask(args)

    def retryRelease(self, task_id):
        self.retryTask(task_id)
