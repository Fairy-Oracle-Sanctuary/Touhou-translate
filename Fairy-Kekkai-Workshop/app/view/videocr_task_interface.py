# coding:utf-8


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import (
    ScrollArea,
    SegmentedWidget,
)

from ..common.event_bus import event_bus
from ..components.videocr_card import OcrItemWidget
from ..service.ocr_service import OCRTask, OCRThread


class OcrTaskInterface(ScrollArea):
    """提取字幕界面"""

    log_signal = Signal(str, bool, bool)
    returnOcrTask = Signal(bool, list, bool)  # 是否重复的任务 任务路径列表 是否发送消息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.ocr_tasks = []  # 所有提取任务
        self.ocr_paths = []  # 所有待提取文件路径
        self.active_ocr = []  # 活跃的ocr线程
        self.max_concurrent_ocr = 1

        self._initWidget()

    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("ocrTaskInterface")
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
            self.downloadingTab, "提取中", lambda: self.filterTasks("提取中")
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

        # 连接信号
        # self.retryDownloadSignal.connect(self.retryDownload)
        # self.removeTaskSignal.connect(self.removeTask)

        # self.task_item = OcrItemWidget(
        #     OCRTask({"file_path": r"C:\Users\ZHANGBaoHang\Desktop\test.mp4"}),
        #     self.taskListContainer,
        # )
        # self.taskListLayout.insertWidget(0, self.task_item)

    def _updateMaxConcurrentDownloads(self, value):
        """更新最大并发提取数"""
        self.max_concurrent_ocr = value
        # 如果当前活跃提取数超过新的限制，需要停止一些任务
        active_count = len([t for t in self.ocr_tasks if t.status == "提取中"])
        if active_count > self.max_concurrent_ocr:
            # 停止超出限制的任务
            excess_count = active_count - self.max_concurrent_ocr
            stopped = 0
            for task in reversed(self.ocr_tasks):
                if task.status == "提取中" and stopped < excess_count:
                    # 找到对应的线程并停止
                    for thread in self.active_ocr:
                        if thread.task.id == task.id:
                            thread.cancel()
                            task.status = "等待中"
                            self.updateTaskUI(task.id)
                            stopped += 1
                            break

    def addOcrTask(self, args):
        """添加提取任务"""
        task = OCRTask(args)
        self.ocr_tasks.append(task)

        video_path = task.video_path
        if video_path in self.ocr_paths:
            self.returnOcrTask.emit(True, self.ocr_paths, True)
            return
        else:
            self.ocr_paths.append(video_path)
            self.returnOcrTask.emit(False, self.ocr_paths, True)

        # 创建任务项
        self.task_item = OcrItemWidget(task, self.taskListContainer)
        self.taskListLayout.insertWidget(0, self.task_item)

        # 连接信号 - 添加这四行代码
        self.task_item.removeTaskSignal.connect(self.removeTask)
        self.task_item.retryOcrSignal.connect(self.retryOcr)

        # 开始提取（如果没有超过最大并发数）
        self.startNextOcr()

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def startNextOcr(self):
        """开始下一个提取任务"""
        # 检查当前活跃提取数
        active_count = len([t for t in self.ocr_tasks if t.status == "提取中"])

        if active_count >= self.max_concurrent_ocr:
            return

        # 查找等待中的任务
        waiting_tasks = [t for t in self.ocr_tasks if t.status == "等待中"]

        if waiting_tasks:
            task = waiting_tasks[0]
            self.startOcr(task)
            self.log_signal.emit("正在开始字幕提取...", False, False)

    def startOcr(self, task):
        """开始提取任务"""
        # 创建提取线程
        ocr_thread = OCRThread(task)
        ocr_thread.progress_signal.connect(
            lambda progress, speed, filename: self.onOcrProgress(
                task.id, progress, speed, filename
            )
        )
        ocr_thread.finished_signal.connect(
            lambda success, message: self.onOcrFinished(task.id, success, message)
        )
        # 新增：连接print输出信号
        ocr_thread.print_signal.connect(
            lambda message: self.onPrintOutput(task.id, message)
        )

        # 存储线程引用到对应的OcrItemWidget
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, OcrItemWidget) and widget.task.id == task.id:
                widget.ocr_thread = ocr_thread
                break

        # 存储线程引用
        self.active_ocr.append(ocr_thread)

        # 更新任务状态
        task.status = "提取中"

        # 更新UI
        self.updateTaskUI(task.id)

        # 开始提取
        ocr_thread.start()

    def onPrintOutput(self, task_id, message):
        """处理print输出并计算进度"""

        # 解析输出消息计算进度
        progress = self.parseOCRProgress(message)
        if progress is not None:
            # 更新任务进度
            self.onOcrProgress(task_id, progress)

    def parseOCRProgress(self, message):
        """
        解析OCR输出消息并计算进度
        返回: 进度百分比 (0-100) 或 None (如果无法解析)
        """
        try:
            # Step 1: Processing image {current} of {total}
            if "Step 1: Processing image" in message:
                # 提取数字：格式 "Processing image 5 of 100"
                import re

                match = re.search(r"Processing image\s+(\d+)\s+of\s+(\d+)", message)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        # Step 1 占总进度的50%
                        progress = (current / total) * 50
                        self.log_signal.emit(
                            f"步骤1: 正在处理图像 {current}/{total}", False, True
                        )
                        return min(progress, 50)  # 确保不超过50%

            # Step 2: Performing OCR on image {current} of {total}
            elif "Step 2: Performing OCR on image" in message:
                # 提取数字：格式 "Performing OCR on image 5 of 100"
                import re

                match = re.search(
                    r"Performing OCR on image\s+(\d+)\s+of\s+(\d+)", message
                )
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if total > 0:
                        # Step 2 占总进度的50%，从50%开始
                        progress = 50 + (current / total) * 50
                        self.log_signal.emit(
                            f"步骤2: 正在对图像进行OCR {current}/{total}",
                            False,
                            True,
                        )

                        return min(progress, 100)  # 确保不超过100%

            return None
        except Exception as e:
            print(f"解析进度失败: {e}")
            return None

    def onOcrProgress(self, task_id, progress):
        """提取进度更新"""
        for task in self.ocr_tasks:
            if task.id == task_id:
                task.progress = progress
                self.updateTaskUI(task_id)
                break

    def onOcrFinished(self, task_id, success, message):
        """提取完成"""
        for task in self.ocr_tasks:
            if task.id == task_id:
                if success:
                    task.status = "已完成"
                    event_bus.notification_service.show_success(
                        "提取完成", f"-{task.video_path}- 提取完成"
                    )
                    self.log_signal.emit(
                        f"字幕提取成功: {task.video_path}", False, False
                    )
                else:
                    task.status = "失败"
                    event_bus.notification_service.show_error(
                        "提取失败", message.strip()
                    )
                    self.log_signal.emit(
                        f"字幕提取失败: {task.video_path} - {message}", True, False
                    )

                # 移除活跃提取
                for thread in self.active_ocr[:]:
                    if thread.task.id == task_id:
                        self.active_ocr.remove(thread)
                        break

                self.updateTaskUI(task_id)

                # 开始下一个提取
                self.startNextOcr()
                break

    def updateTaskUI(self, task_id):
        """更新任务UI"""
        # 查找对应的任务项
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, OcrItemWidget) and widget.task.id == task_id:
                widget.updateProgress(
                    0 if widget.task.status == "已取消" else widget.task.progress,
                    widget.task.video_path,
                )
                widget.updateStatus(widget.task.status)
                break

        # 更新过滤视图
        self.filterTasks(self.segmentedWidget.currentItem().text())

    def filterTasks(self, filter_type):
        """过滤任务显示"""
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, OcrItemWidget):
                if filter_type == "全部" or widget.task.status == filter_type:
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)

    def retryOcr(self, task_id):
        """重新提取任务"""
        for task in self.ocr_tasks:
            if task.id == task_id:
                task.status = "等待中"
                task.progress = 0
                task.error_message = ""

                self.updateTaskUI(task_id)
                self.startNextOcr()
                break

    def removeTask(self, task_id):
        """移除任务"""
        for num, task in enumerate(self.ocr_tasks[:]):
            if task.id == task_id:
                self.ocr_tasks.remove(task)
                self.ocr_paths.pop(num)
                self.returnOcrTask.emit(False, self.ocr_paths, False)

        # 从UI中移除
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, OcrItemWidget) and widget.task.id == task_id:
                self.taskListLayout.removeWidget(widget)
                widget.deleteLater()
                break

    def addOcrFromProject(self, request_data):
        """从项目界面添加提取任务"""
        task = OCRThread(
            url=request_data["url"],
            download_path=request_data["save_path"],
            file_name="生肉.mp4",
        )
        self.addOcrTask(task)
