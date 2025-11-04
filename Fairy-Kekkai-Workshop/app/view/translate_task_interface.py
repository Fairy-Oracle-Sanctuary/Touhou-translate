# coding:utf-8


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    ScrollArea,
    SegmentedWidget,
)

from ..common.event_bus import event_bus
from ..components.translate_card import TranslateItemWidget
from ..service.deepseek_service import TranslateTask, TranslateThread


class TranslateTaskInterface(ScrollArea):
    """提取字幕界面"""

    returnTranslateTask = Signal(
        bool, list, bool
    )  # 是否重复的任务 任务路径列表 是否发送消息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.translate_tasks = []  # 所有提取任务
        self.translate_paths = []  # 所有待提取文件路径
        self.active_translate = []  # 活跃的ocr线程
        self.max_concurrent_translate = 1

        self._initWidget()

    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("TranslateTaskInterface")
        self.enableTransparentBackground()

        # 创建分段控件
        self.segmentedWidget = SegmentedWidget(self)
        self.allTab = QWidget()
        self.downloadingTab = QWidget()
        self.completedTab = QWidget()
        self.failedTab = QWidget()

        self.segmentedWidget.addItem(
            self.allTab, "全部", lambda: self.filterTasks("全部")
        )
        self.segmentedWidget.addItem(
            self.downloadingTab, "翻译中", lambda: self.filterTasks("翻译中")
        )
        self.segmentedWidget.addItem(
            self.completedTab, "已完成", lambda: self.filterTasks("已完成")
        )
        self.segmentedWidget.addItem(
            self.failedTab, "失败", lambda: self.filterTasks("失败")
        )

        self.segmentedWidget.setCurrentItem(self.allTab)
        self.segmentedWidget.setMaximumHeight(30)

        # 创建任务列表容器
        self.taskListContainer = QWidget(self)
        self.taskListLayout = QVBoxLayout(self.taskListContainer)
        self.taskListLayout.setAlignment(Qt.AlignTop)

        # 设置布局
        self.vBoxLayout.addWidget(self.segmentedWidget)
        self.vBoxLayout.addWidget(self.taskListContainer)

    def _updateMaxConcurrentDownloads(self, value):
        """更新最大并发提取数"""
        self.max_concurrent_translate = value
        # 如果当前活跃提取数超过新的限制，需要停止一些任务
        active_count = len([t for t in self.translate_tasks if t.status == "翻译中"])
        if active_count > self.max_concurrent_translate:
            # 停止超出限制的任务
            excess_count = active_count - self.max_concurrent_translate
            stopped = 0
            for task in reversed(self.translate_tasks):
                if task.status == "翻译中" and stopped < excess_count:
                    # 找到对应的线程并停止
                    for thread in self.active_translate:
                        if thread.task.id == task.id:
                            thread.cancel()
                            task.status = "等待中"
                            self.updateTaskUI(task.id)
                            stopped += 1
                            break

    def addTranslateTask(self, args):
        """添加提取任务"""
        task = TranslateTask(args)

        srt_path = task.srt_path
        if srt_path in self.translate_paths:
            self.returnTranslateTask.emit(True, self.translate_paths, True)
            return
        else:
            self.translate_paths.append(srt_path)
            self.returnTranslateTask.emit(False, self.translate_paths, True)

        # 添加任务
        self.translate_tasks.append(task)

        # 创建任务项
        self.task_item = TranslateItemWidget(task, self.taskListContainer)
        self.taskListLayout.insertWidget(0, self.task_item)

        # 连接信号 - 添加这四行代码
        self.task_item.removeTaskSignal.connect(self.removeTask)
        self.task_item.retryTranslateSignal.connect(self.retryTranslate)

        # 开始提取（如果没有超过最大并发数）
        self.startNextTranslate()

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def startNextTranslate(self):
        """开始下一个提取任务"""
        # 检查当前活跃提取数
        active_count = len([t for t in self.translate_tasks if t.status == "翻译中"])

        if active_count >= self.max_concurrent_translate:
            return

        # 查找等待中的任务
        waiting_tasks = [t for t in self.translate_tasks if t.status == "等待中"]

        if waiting_tasks:
            task = waiting_tasks[0]
            self.startTranslate(task)

    def startTranslate(self, task):
        """开始提取任务"""
        # 创建提取线程
        translate_thread = TranslateThread(task)
        translate_thread.finished_signal.connect(
            lambda success, message: self.onTranslateFinished(task.id, success, message)
        )

        # 存储线程引用到对应的TranslateItemWidget
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, TranslateItemWidget) and widget.task.id == task.id:
                widget.translate_thread = translate_thread
                break

        # 存储线程引用
        self.active_translate.append(translate_thread)

        # 更新任务状态
        task.status = "翻译中"

        # 更新UI
        self.updateTaskUI(task.id)

        # 开始提取
        translate_thread.start()

    def onTranslateFinished(self, task_id, success, message):
        """提取完成"""
        for task in self.translate_tasks:
            if task.id == task_id:
                if success:
                    task.status = "已完成"
                    event_bus.notification_service.show_success(
                        "翻译完成", f"-{task.srt_path}- 翻译完成"
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

    def updateTaskUI(self, task_id):
        """更新任务UI"""
        # 查找对应的任务项
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, TranslateItemWidget) and widget.task.id == task_id:
                widget.updateStatus(widget.task.status)
                break

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def filterTasks(self, filter_type):
        """过滤任务显示"""
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, TranslateItemWidget):
                if filter_type == "全部" or widget.task.status == filter_type:
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def retryTranslate(self, task_id):
        """重新提取任务"""
        for task in self.translate_tasks:
            if task.id == task_id:
                task.status = "等待中"
                task.error_message = ""

                self.updateTaskUI(task_id)
                self.startNextTranslate()
                break

    def removeTask(self, task_id):
        """移除任务"""
        for num, task in enumerate(self.translate_tasks[:]):
            if task.id == task_id:
                self.translate_tasks.remove(task)
                self.translate_paths.pop(num)
                self.returnTranslateTask.emit(False, self.translate_paths, False)

        # 从UI中移除
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, TranslateItemWidget) and widget.task.id == task_id:
                self.taskListLayout.removeWidget(widget)
                widget.deleteLater()
                break
