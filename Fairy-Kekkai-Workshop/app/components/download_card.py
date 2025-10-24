# coding:utf-8
import os
from datetime import datetime

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    CaptionLabel,
    FluentIcon,
    IconWidget,
    MessageBox,
    PillPushButton,
    ProgressBar,
    SimpleCardWidget,
    StrongBodyLabel,
    TransparentToolButton,
)

from ..common.event_bus import event_bus


class DownloadItemWidget(SimpleCardWidget):
    """下载任务项组件"""

    # 定义信号
    removeTaskSignal = Signal(int)  # 任务ID
    retryDownloadSignal = Signal(int)  # 任务ID

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.download_thread = None

        self.setFixedHeight(120)

        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # 第一行：标题和状态
        titleLayout = QHBoxLayout()

        # 文件图标
        iconWidget = IconWidget(FluentIcon.VIDEO, self)

        # 标题和项目信息
        titleInfoLayout = QVBoxLayout()
        self.titleLabel = StrongBodyLabel("视频下载", self)

        projectInfo = StrongBodyLabel(f"{self.task.download_path}", self)

        titleInfoLayout.addWidget(self.titleLabel)
        titleInfoLayout.addWidget(projectInfo)

        # 状态标签
        statusPill = PillPushButton(self.task.status, self)
        statusPill.setDisabled(True)
        statusPill.setChecked(True)
        self.updateStatusStyle(statusPill)

        titleLayout.addWidget(iconWidget)
        titleLayout.addLayout(titleInfoLayout)
        titleLayout.addStretch()
        titleLayout.addWidget(statusPill)

        # 第二行：进度条和速度
        progressLayout = QHBoxLayout()

        self.progressBar = ProgressBar(self)
        self.progressBar.setValue(self.task.progress)

        speedLabel = CaptionLabel(self.task.speed or "初始化中", self)

        progressLayout.addWidget(self.progressBar, 4)
        progressLayout.addWidget(speedLabel, 1)

        # 第三行：URL信息和操作按钮
        infoLayout = QHBoxLayout()

        urlLabel = CaptionLabel(
            f"URL: {self.task.url[:50]}..."
            if len(self.task.url) > 50
            else f"URL: {self.task.url}",
            self,
        )
        urlLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # 操作按钮
        buttonLayout = QHBoxLayout()

        self.openFolderBtn = TransparentToolButton(FluentIcon.FOLDER, self)
        self.openFolderBtn.setToolTip("打开文件夹")
        self.openFolderBtn.setVisible(self.task.status == "已完成")
        self.openFolderBtn.clicked.connect(self.openFolder)

        self.cancelBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.cancelBtn.setToolTip("取消下载")
        self.cancelBtn.setVisible(self.task.status == "下载中")
        self.cancelBtn.clicked.connect(self.cancelDownload)

        self.retryBtn = TransparentToolButton(FluentIcon.SYNC, self)
        self.retryBtn.setToolTip("重新下载")
        self.retryBtn.setVisible(self.task.status == "失败")
        self.retryBtn.clicked.connect(self.retryDownload)

        self.removeBtn = TransparentToolButton(FluentIcon.DELETE, self)
        self.removeBtn.setToolTip("移除任务")
        self.removeBtn.setDisabled(True)
        self.removeBtn.clicked.connect(self.removeTask)

        buttonLayout.addWidget(self.openFolderBtn)
        buttonLayout.addWidget(self.cancelBtn)
        buttonLayout.addWidget(self.retryBtn)
        buttonLayout.addWidget(self.removeBtn)

        infoLayout.addWidget(urlLabel)
        infoLayout.addStretch()
        infoLayout.addLayout(buttonLayout)

        # 添加所有布局
        layout.addLayout(titleLayout)
        layout.addLayout(progressLayout)
        layout.addLayout(infoLayout)

    def updateStatusStyle(self, statusPill):
        """更新状态标签样式"""
        if self.task.status == "等待中":
            statusPill.setProperty("isSecondary", True)
        elif self.task.status == "下载中":
            statusPill.setProperty("isPrimary", True)
        elif self.task.status == "已完成":
            statusPill.setProperty("isSuccess", True)
        elif self.task.status == "失败":
            statusPill.setProperty("isError", True)
        statusPill.setStyle(statusPill.style())

    def updateProgress(self, progress, speed, filename):
        """更新进度"""
        self.task.progress = progress
        self.task.speed = speed
        if filename and not self.task.filename:
            self.task.filename = filename
            self.titleLabel.setText(self.task.filename)

        self.progressBar.setValue(progress)

        # 更新状态标签
        for i in range(self.layout().count()):
            item = self.layout().itemAt(0)
            if isinstance(item, QHBoxLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, PillPushButton):
                        self.updateStatusStyle(widget)
                        break
                break

        # 更新速度标签
        for i in range(self.layout().count()):
            item = self.layout().itemAt(1)
            if isinstance(item, QHBoxLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, CaptionLabel):
                        widget.setText(f"{progress}% {speed}")
                        break
                break

    def updateStatus(self, status, success=True, error_message=""):
        """更新状态"""
        self.task.status = status
        if not success:
            self.task.error_message = error_message

        # 更新状态标签
        for i in range(self.layout().count()):
            item = self.layout().itemAt(0)
            if isinstance(item, QHBoxLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, PillPushButton):
                        widget.setText(status)
                        self.updateStatusStyle(widget)
                        break
                break

        # 显示/隐藏按钮
        self.openFolderBtn.setVisible(status == "已完成")
        self.cancelBtn.setVisible(status == "下载中")
        self.retryBtn.setVisible(status == "失败")

        if status == "已完成":
            self.removeBtn.setDisabled(False)
        if status == "失败":
            self.removeBtn.setDisabled(False)

    def openFolder(self):
        """打开文件夹"""
        if os.path.exists(self.task.download_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.task.download_path))

    def cancelDownload(self):
        """取消下载"""
        # 添加确认对话框
        box = MessageBox("确认取消", "确定要取消这个下载任务吗？", self.window())
        box.yesButton.setText("确定")
        box.cancelButton.setText("取消")
        if box.exec():
            # 如果任务正在下载，找到对应的下载线程并取消
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.cancel()
                # 等待线程安全结束
                # self.download_thread.wait(1000)  # 最多等待1秒

            # 更新任务状态
            self.task.status = "已取消"
            self.task.progress = 0
            self.task.speed = ""
            self.task.end_time = datetime.now()

            # 更新UI状态
            self.updateStatus("已取消")

            # 恢复按钮
            self.removeBtn.setDisabled(False)
            self.retryBtn.setVisible(True)

            # 显示取消提示
            event_bus.notification_service.show_info(
                "下载已取消", f"任务 '{self.task.filename}' 已被取消"
            )

    def retryDownload(self):
        """重新下载"""
        # 发送重新下载信号
        self.retryDownloadSignal.emit(self.task.id)

    def removeTask(self):
        """移除任务"""
        # 发送移除任务信号
        self.removeTaskSignal.emit(self.task.id)
