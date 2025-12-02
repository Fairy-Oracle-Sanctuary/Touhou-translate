# coding:utf-8


from PySide6.QtCore import Signal

from ..common.event_bus import event_bus
from ..components.base_task_interface import BaseTaskInterface
from ..components.task_card import TranslateItemWidget
from ..service.deepseek_service import TranslateTask, TranslateThread


class TranslateTaskInterface(BaseTaskInterface):
    """提取字幕界面"""

    returnTranslateTask = Signal(
        bool, list, bool
    )  # 是否重复的任务 任务路径列表 是否发送消息

    def __init__(self, parent=None):
        super().__init__(
            object_name="translateTaskInterface",
            processing_text="翻译中",
            task_type="翻译",
            parent=parent,
        )

        self.translate_paths = []  # 所有待翻译文件路径

    def createTask(self, args):
        task = TranslateTask(args)

        srt_path = task.input_file
        if srt_path in self.translate_paths:
            self.returnTranslateTask.emit(True, self.translate_paths, True)
            return
        else:
            self.translate_paths.append(srt_path)
            self.returnTranslateTask.emit(False, self.translate_paths, True)

        return task

    def createTaskItem(self, task: TranslateTask, parent):
        return TranslateItemWidget(task, progressBar_type="determinate", parent=parent)

    def createTaskThread(self, task: TranslateTask):
        return TranslateThread(task)

    def getTaskPath(self, task: TranslateTask):
        return task.input_file

    def onTranslateFinished(self, task_id, success, message):
        """提取完成"""
        for task in self.translate_tasks:
            if task.id == task_id:
                if success:
                    task.status = "已完成"
                    event_bus.notification_service.show_success(
                        "翻译完成", f"-{task.input_file}- 翻译完成"
                    )
                else:
                    task.status = "失败"
                    event_bus.notification_service.show_error(
                        "翻译失败", message.strip()
                    )

                # 移除活跃翻译
                for thread in self.active_translate[:]:
                    if thread.task.id == task_id:
                        self.active_translate.remove(thread)
                        break

                self.updateTaskUI(task_id)

                # 开始下一个翻译
                self.startNextTranslate()
                break

    def addTranslateTask(self, args):
        self.addTask(args)

    def retryTranslate(self, task_id):
        self.retryTask(task_id)
