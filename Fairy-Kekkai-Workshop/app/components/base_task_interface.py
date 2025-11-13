# coding:utf-8

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import ScrollArea, SegmentedWidget


class BaseTaskInterface(ScrollArea):
    """基础任务界面"""

    returnTask = Signal(bool, list, bool)  # 是否重复的任务 任务路径列表 是否发送消息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.tasks = []  # 所有任务
        self.task_paths = []  # 所有任务文件路径
        self.active_threads = []  # 活跃的线程
        self.max_concurrent_tasks = 1

        # 配置项 - 子类可以在初始化后修改这些属性
        self.object_name = "BaseTaskInterface"
        self.processing_text = "处理中"
        self.task_type = "任务"  # 用于消息显示

        self._initWidget()

    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName(self.object_name)
        self.enableTransparentBackground()

        # 创建分段控件
        self.segmentedWidget = SegmentedWidget(self)
        self.allTab = QWidget()
        self.processingTab = QWidget()
        self.completedTab = QWidget()
        self.failedTab = QWidget()

        self.segmentedWidget.addItem(
            self.allTab, "全部", lambda: self.filterTasks("全部")
        )
        self.segmentedWidget.addItem(
            self.processingTab,
            self.processing_text,
            lambda: self.filterTasks(self.processing_text),
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

    def createTask(self, args):
        """创建任务对象 - 子类应该重写此方法"""
        raise NotImplementedError("子类必须实现 createTask 方法")

    def createTaskItem(self, task, parent):
        """创建任务项组件 - 子类应该重写此方法"""
        raise NotImplementedError("子类必须实现 createTaskItem 方法")

    def createTaskThread(self, task):
        """创建任务线程 - 子类应该重写此方法"""
        raise NotImplementedError("子类必须实现 createTaskThread 方法")

    def getTaskPath(self, task):
        """获取任务的路径 - 子类应该重写此方法"""
        raise NotImplementedError("子类必须实现 getTaskPath 方法")

    def getSuccessMessage(self, task_path):
        """获取成功消息"""
        return f"-{task_path}- {self.task_type}完成"

    def getFailureMessage(self, task_path, message):
        """获取失败消息"""
        return f"-{task_path}- {self.task_type}失败: {message}"

    def _updateMaxConcurrentTasks(self, value):
        """更新最大并发任务数"""
        self.max_concurrent_tasks = value
        active_count = len([t for t in self.tasks if t.status == self.processing_text])

        if active_count > self.max_concurrent_tasks:
            excess_count = active_count - self.max_concurrent_tasks
            stopped = 0
            for task in reversed(self.tasks):
                if task.status == self.processing_text and stopped < excess_count:
                    for thread in self.active_threads:
                        if thread.task.id == task.id:
                            thread.cancel()
                            task.status = "等待中"
                            self.updateTaskUI(task.id)
                            stopped += 1
                            break

    def addTask(self, args):
        """添加任务"""
        task = self.createTask(args)
        task_path = self.getTaskPath(task)

        if task_path in self.task_paths:
            self.returnTask.emit(True, self.task_paths, True)
            return
        else:
            self.task_paths.append(task_path)
            self.returnTask.emit(False, self.task_paths, True)

        # 添加任务
        self.tasks.append(task)

        # 创建任务项
        task_item = self.createTaskItem(task, self.taskListContainer)
        self.taskListLayout.insertWidget(0, task_item)

        # 连接信号
        if hasattr(task_item, "removeTaskSignal"):
            task_item.removeTaskSignal.connect(self.removeTask)
        if hasattr(task_item, "retryTaskSignal"):
            task_item.retryTaskSignal.connect(self.retryTask)

        # 开始任务（如果没有超过最大并发数）
        self.startNextTask()

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def startNextTask(self):
        """开始下一个任务"""
        active_count = len([t for t in self.tasks if t.status == self.processing_text])

        if active_count >= self.max_concurrent_tasks:
            return

        # 查找等待中的任务
        waiting_tasks = [t for t in self.tasks if t.status == "等待中"]

        if waiting_tasks:
            task = waiting_tasks[0]
            self.startTask(task)

    def startTask(self, task):
        """开始任务"""
        task_thread = self.createTaskThread(task)
        task_thread.finished_signal.connect(
            lambda success, message: self.onTaskFinished(task.id, success, message)
        )

        # 如果有进度信号，连接它
        if hasattr(task_thread, "progress_signal"):
            task_thread.progress_signal.connect(
                lambda progress, speed, filename: self.onTaskProgress(
                    task.id, progress, speed, filename
                )
            )

        # 如果有打印输出信号，连接它
        if hasattr(task_thread, "print_signal"):
            task_thread.print_signal.connect(
                lambda message: self.onPrintOutput(task.id, message)
            )

        # 存储线程引用到对应的任务项
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if (
                hasattr(widget, "task")
                and hasattr(widget.task, "id")
                and widget.task.id == task.id
            ):
                widget.task_thread = task_thread
                break

        # 存储线程引用
        self.active_threads.append(task_thread)

        # 更新任务状态
        task.status = self.processing_text

        # 更新UI
        self.updateTaskUI(task.id)

        # 开始任务
        task_thread.start()

    def onPrintOutput(self, task_id, message):
        """处理打印输出 - 子类可以重写此方法来实现特定的输出处理"""
        pass

    def onTaskProgress(self, task_id, progress, speed=None, filename=None):
        """任务进度更新"""
        for task in self.tasks:
            if task.id == task_id:
                if hasattr(task, "progress"):
                    task.progress = progress
                self.updateTaskUI(task_id)
                break

    def onTaskFinished(self, task_id, success, message):
        """任务完成"""
        from ..common.event_bus import event_bus

        for task in self.tasks:
            if task.id == task_id:
                task_path = self.getTaskPath(task)
                if success:
                    task.status = "已完成"
                    event_bus.notification_service.show_success(
                        f"{self.task_type}完成", self.getSuccessMessage(task_path)
                    )
                else:
                    task.status = "失败"
                    event_bus.notification_service.show_error(
                        f"{self.task_type}失败", message.strip()
                    )

                # 移除活跃线程
                for thread in self.active_threads[:]:
                    if thread.task.id == task_id:
                        self.active_threads.remove(thread)
                        break

                self.updateTaskUI(task_id)

                # 开始下一个任务
                self.startNextTask()
                break

    def updateTaskUI(self, task_id):
        """更新任务UI"""
        # 查找对应的任务项
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if (
                hasattr(widget, "task")
                and hasattr(widget.task, "id")
                and widget.task.id == task_id
            ):
                if hasattr(widget, "updateProgress") and hasattr(
                    widget.task, "progress"
                ):
                    progress = (
                        0 if widget.task.status == "已取消" else widget.task.progress
                    )
                    widget.updateProgress(progress, self.getTaskPath(widget.task))

                if hasattr(widget, "updateStatus"):
                    widget.updateStatus(widget.task.status)
                break

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def filterTasks(self, filter_type):
        """过滤任务显示"""
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if hasattr(widget, "task") and hasattr(widget.task, "status"):
                if filter_type == "全部" or widget.task.status == filter_type:
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def retryTask(self, task_id):
        """重新执行任务"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = "等待中"
                if hasattr(task, "progress"):
                    task.progress = 0
                if hasattr(task, "error_message"):
                    task.error_message = ""

                self.updateTaskUI(task_id)
                self.startNextTask()
                break

    def removeTask(self, task_id):
        """移除任务"""
        for num, task in enumerate(self.tasks[:]):
            if task.id == task_id:
                self.tasks.remove(task)
                if num < len(self.task_paths):
                    self.task_paths.pop(num)
                self.returnTask.emit(False, self.task_paths, False)
                break

        # 从UI中移除
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if (
                hasattr(widget, "task")
                and hasattr(widget.task, "id")
                and widget.task.id == task_id
            ):
                self.taskListLayout.removeWidget(widget)
                widget.deleteLater()
                break
