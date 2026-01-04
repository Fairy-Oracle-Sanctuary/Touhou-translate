# coding:utf-8
import os

from app.common.config import cfg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon,
    Pivot,
    PrimaryPushButton,
    ScrollArea,
    SegmentedWidget,
)

from ..common.event_bus import event_bus
from ..components.config_card import YTDLPSettingInterface
from ..components.dialog import CustomMessageBox
from ..components.download_card import DownloadItemWidget
from ..service.download_service import DownloadTask, DownloadThread


class DownloadStackedInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建堆叠窗口
        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.downloadInterface = DownloadInterface()
        self.settingInterface = YTDLPSettingInterface()

        # 添加标签页
        self.addSubInterface(self.downloadInterface, "downloadInterface", "下载")
        self.addSubInterface(self.settingInterface, "settingInterface", "设置")

        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.downloadInterface)
        self.pivot.setCurrentItem(self.downloadInterface.objectName())

        self.vBoxLayout.setContentsMargins(30, 0, 30, 30)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)

        self.resize(780, 800)
        self.setObjectName("DownloadStackedInterfaces")

    def addSubInterface(self, widget: QLabel, objectName: str, text: str):
        widget.setObjectName(objectName)
        widget.setAlignment(Qt.AlignCenter)
        self.stackedWidget.addWidget(widget)

        # 使用全局唯一的 objectName 作为路由键
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())


class DownloadInterface(ScrollArea):
    """下载界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.download_tasks = []  # 所有下载任务
        self.active_downloads = []  # 活跃的下载线程
        self.max_concurrent_downloads = cfg.concurrentDownloads.value  # 最大同时下载数

        self._initWidget()

        event_bus.download_requested.connect(self.addDownloadFromProject)
        # 监听配置变化，更新最大并发数
        cfg.concurrentDownloads.valueChanged.connect(self._updateMaxConcurrentDownloads)

    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("downloadInterface")
        self.enableTransparentBackground()

        # 创建添加下载按钮
        addDownloadBtn = PrimaryPushButton("添加下载任务", self)
        addDownloadBtn.setIcon(FluentIcon.ADD)
        addDownloadBtn.clicked.connect(self.showAddDownloadDialog)

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
            self.downloadingTab, "下载中", lambda: self.filterTasks("下载中")
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
        self.vBoxLayout.addWidget(addDownloadBtn)
        self.vBoxLayout.addWidget(self.segmentedWidget)
        self.vBoxLayout.addWidget(self.taskListContainer)

        # 连接信号
        # self.retryDownloadSignal.connect(self.retryDownload)
        # self.removeTaskSignal.connect(self.removeTask)

    def _updateMaxConcurrentDownloads(self, value):
        """更新最大并发下载数"""
        self.max_concurrent_downloads = value
        # 如果当前活跃下载数超过新的限制，需要停止一些任务
        active_count = len([t for t in self.download_tasks if t.status == "下载中"])
        if active_count > self.max_concurrent_downloads:
            # 停止超出限制的任务
            excess_count = active_count - self.max_concurrent_downloads
            stopped = 0
            for task in reversed(self.download_tasks):
                if task.status == "下载中" and stopped < excess_count:
                    # 找到对应的线程并停止
                    for thread in self.active_downloads:
                        if thread.task.id == task.id:
                            thread.cancel()
                            task.status = "等待中"
                            self.updateTaskUI(task.id)
                            stopped += 1
                            break

    def showAddDownloadDialog(self):
        """显示添加下载对话框"""
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break

        dialog = CustomMessageBox(
            title="添加下载任务",
            text="请输入视频URL:",
            parent=main_window if main_window else self.window(),
            min_width=500,
        )

        if dialog.exec():
            url = dialog.LineEdit.text().strip()
            if not url:
                event_bus.notification_service.show_warning(
                    "输入错误", "请输入有效的URL"
                )
                return

            path = QFileDialog.getExistingDirectory(
                self,
                self.tr("请选择要下载到的目录"),
                os.path.expanduser("~\\Downloads"),
            )
            if not path:
                event_bus.notification_service.show_warning(
                    "输入错误", "请选择要下载到的目录"
                )
                return

            task = DownloadTask(
                url=url,
                download_path=path,
                file_name="",  # 使用配置中的输出模板
            )
            self.addDownloadTask(task)
        else:
            pass

    def addDownloadTask(self, task):
        """添加下载任务"""
        self.download_tasks.append(task)

        # 创建任务项
        self.task_item = DownloadItemWidget(task, self.taskListContainer)
        self.taskListLayout.insertWidget(0, self.task_item)

        # 连接信号 - 添加这四行代码
        self.task_item.removeTaskSignal.connect(self.removeTask)
        self.task_item.retryDownloadSignal.connect(self.retryDownload)

        # 开始下载（如果没有超过最大并发数）
        self.startNextDownload()

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def startNextDownload(self):
        """开始下一个下载任务"""
        # 检查当前活跃下载数
        active_count = len([t for t in self.download_tasks if t.status == "下载中"])

        if active_count >= self.max_concurrent_downloads:
            return

        # 查找等待中的任务
        waiting_tasks = [t for t in self.download_tasks if t.status == "等待中"]

        if waiting_tasks:
            task = waiting_tasks[0]
            self.startDownload(task)

    def startDownload(self, task: DownloadTask):
        """开始下载任务"""
        # 检查 yt-dlp 路径
        if not os.path.exists(cfg.ytdlpPath.value):
            event_bus.notification_service.show_error(
                "配置错误",
                f"yt-dlp 路径不存在: {cfg.ytdlpPath.value}\n请在设置中配置正确的路径",
            )
            task.status = "失败"
            self.updateTaskUI(task.id)
            return

        # 创建下载线程
        download_thread = DownloadThread(task)
        download_thread.progress_signal.connect(
            lambda progress, speed, filename: self.onDownloadProgress(
                task.id, progress, speed, filename
            )
        )
        download_thread.finished_signal.connect(
            lambda success, message: self.onDownloadFinished(task.id, success, message)
        )

        # 存储线程引用到对应的DownloadItemWidget
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget) and widget.task.id == task.id:
                widget.download_thread = download_thread
                break

        # 存储线程引用
        self.active_downloads.append(download_thread)

        # 更新任务状态
        task.status = "下载中"

        # 更新UI
        self.updateTaskUI(task.id)

        # 开始下载
        download_thread.start()

    def onDownloadProgress(self, task_id, progress, speed, filename):
        """下载进度更新"""
        for task in self.download_tasks:
            if task.id == task_id:
                task.progress = progress
                task.speed = speed
                if filename and not task.filename:
                    task.filename = filename
                self.updateTaskUI(task_id)
                break

    def onDownloadFinished(self, task_id, success, message):
        """下载完成"""
        for task in self.download_tasks:
            if task.id == task_id:
                if success:
                    task.status = "已完成"
                    event_bus.notification_service.show_success(
                        "下载完成", f"-{task.filename}- 下载完成"
                    )
                else:
                    task.status = "失败"
                    event_bus.notification_service.show_error(
                        "下载失败", message.strip()
                    )

                # 移除活跃下载
                for thread in self.active_downloads[:]:
                    if thread.task.id == task_id:
                        self.active_downloads.remove(thread)
                        break

                self.updateTaskUI(task_id)

                # 开始下一个下载
                self.startNextDownload()
                break

    def updateTaskUI(self, task_id):
        """更新任务UI"""
        # 查找对应的任务项
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget) and widget.task.id == task_id:
                widget.updateProgress(
                    widget.task.progress, widget.task.speed, widget.task.filename
                )
                widget.updateStatus(widget.task.status)
                break

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def filterTasks(self, filter_type):
        """过滤任务显示"""
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget):
                if filter_type == "全部" or widget.task.status == filter_type:
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def retryDownload(self, task_id):
        """重新下载任务"""
        for task in self.download_tasks:
            if task.id == task_id:
                task.status = "等待中"
                task.progress = 0
                task.speed = ""
                task.error_message = ""
                task.start_time = None
                task.end_time = None

                self.updateTaskUI(task_id)
                self.startNextDownload()
                break

    def removeTask(self, task_id):
        """移除任务"""
        try:
            for task in self.download_tasks[:]:
                if task.id == task_id:
                    # 如果任务正在下载，先取消
                    for thread in self.active_downloads[:]:
                        if thread.task.id == task_id:
                            return
                            thread.cancel()
                            thread.wait()
                            self.active_downloads.remove(thread)
                            break

                    self.download_tasks.remove(task)
                    break

            # 从UI中移除
            for i in range(self.taskListLayout.count()):
                widget = self.taskListLayout.itemAt(i).widget()
                if isinstance(widget, DownloadItemWidget) and widget.task.id == task_id:
                    self.taskListLayout.removeWidget(widget)
                    widget.deleteLater()
                    break

            # 开始下一个下载
            self.startNextDownload()
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"任务移除失败: {e}")

    def addDownloadFromProject(self, request_data):
        """从项目界面添加下载任务"""
        task = DownloadTask(
            url=request_data["url"],
            download_path=request_data["save_path"],
            file_name="生肉.mp4",
        )
        self.addDownloadTask(task)
