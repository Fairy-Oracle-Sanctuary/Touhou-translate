# coding:utf-8
import os
from datetime import datetime

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    CaptionLabel,
    CardWidget,
    FluentIcon,
    IconWidget,
    MessageBox,
    PillPushButton,
    ProgressBar,
    StrongBodyLabel,
    TransparentToolButton,
)

from ..common.event_bus import event_bus
from ..service.download_service import DownloadTask


class DownloadItemWidget(CardWidget):
    """下载任务项组件"""

    # 定义信号
    removeTaskSignal = Signal(int)  # 任务ID
    retryDownloadSignal = Signal(int)  # 任务ID

    def __init__(self, task: DownloadTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.download_thread = None
        self._is_cancelling = False  # 新增：取消标志

        self.setFixedHeight(120)

        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        # 第一行：标题和状态
        titleLayout = QHBoxLayout()

        # 文件图标（增大并居中）
        iconWidget = IconWidget(FluentIcon.VIDEO, self)
        iconWidget.setFixedSize(44, 44)

        # 标题和项目信息（更清晰的层次）
        titleInfoLayout = QVBoxLayout()
        titleInfoLayout.setSpacing(2)
        # 显示文件名（若有）或默认标题
        self.titleLabel = StrongBodyLabel(self.task.filename or "视频下载", self)
        # 路径或项目信息用较小的说明文本
        projectInfo = CaptionLabel(self.task.download_path, self)
        projectInfo.setToolTip(self.task.download_path)

        titleInfoLayout.addWidget(self.titleLabel)
        titleInfoLayout.addWidget(projectInfo)

        # 状态标签
        # 状态标签：保留 Pill 风格，设置固定宽度便于对齐
        self.statusPill = PillPushButton(self.task.status, self)
        self.statusPill.setDisabled(True)
        self.statusPill.setChecked(True)
        self.statusPill.setFixedWidth(110)
        self.updateStatusStyle(self.statusPill)

        titleLayout.addWidget(iconWidget)
        titleLayout.addLayout(titleInfoLayout)
        titleLayout.addStretch()
        titleLayout.addWidget(self.statusPill)

        # 第二行：进度条和速度
        progressLayout = QHBoxLayout()

        # 进度条与速度（更紧凑的进度条）
        self.progressBar = ProgressBar(self)
        self.progressBar.setValue(self.task.progress)
        self.progressBar.setFixedHeight(8)

        self.speedLabel = CaptionLabel(self.task.speed or "初始化中", self)
        self.speedLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        progressLayout.addWidget(self.progressBar, 4)
        progressLayout.addWidget(self.speedLabel, 1)

        # 第三行：URL信息和操作按钮
        infoLayout = QHBoxLayout()

        # URL 信息（短显示，完整地址在 Tooltip）
        short_url = (
            f"URL: {self.task.url[:50]}..."
            if len(self.task.url) > 50
            else f"URL: {self.task.url}"
        )
        urlLabel = CaptionLabel(short_url, self)
        urlLabel.setToolTip(self.task.url)
        urlLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # 操作按钮
        buttonLayout = QHBoxLayout()

        # 操作按钮（紧凑排列并统一大小）
        btn_size = 26
        self.openFolderBtn = TransparentToolButton(FluentIcon.FOLDER, self)
        self.openFolderBtn.setToolTip("打开文件夹")
        self.openFolderBtn.setVisible(self.task.status == "已完成")
        self.openFolderBtn.setFixedSize(btn_size, btn_size)
        self.openFolderBtn.clicked.connect(self.openFolder)

        self.cancelBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.cancelBtn.setToolTip("取消下载")
        self.cancelBtn.setVisible(self.task.status == "下载中")
        self.cancelBtn.setFixedSize(btn_size, btn_size)
        self.cancelBtn.clicked.connect(self.cancelDownload)

        self.retryBtn = TransparentToolButton(FluentIcon.SYNC, self)
        self.retryBtn.setToolTip("重新下载")
        self.retryBtn.setVisible(self.task.status == "失败")
        self.retryBtn.setFixedSize(btn_size, btn_size)
        self.retryBtn.clicked.connect(self.retryDownload)

        self.removeBtn = TransparentToolButton(FluentIcon.DELETE, self)
        self.removeBtn.setToolTip("移除任务")
        self.removeBtn.setDisabled(True)
        self.removeBtn.setFixedSize(btn_size, btn_size)
        self.removeBtn.clicked.connect(self.removeTask)

        buttonLayout.setSpacing(6)
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
        """更新进度 - 在取消期间忽略更新"""
        # 如果正在取消，忽略进度更新
        if self._is_cancelling:
            return

        self.task.progress = progress
        self.task.speed = speed
        if filename and not self.task.filename:
            self.task.filename = filename
            self.titleLabel.setText(self.task.filename)

        self.progressBar.setValue(progress)
        self.speedLabel.setText(f"{progress}% {speed}")

        # 更新状态标签
        self.statusPill.setText(self.task.status)
        self.updateStatusStyle(self.statusPill)

    def updateStatus(self, status, success=True, error_message=""):
        """更新状态"""
        self.task.status = status
        if not success:
            self.task.error_message = error_message

        # 更新状态标签
        self.statusPill.setText(status)
        self.updateStatusStyle(self.statusPill)

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
        """取消下载 - 异步版本"""
        # 添加确认对话框
        box = MessageBox("确认取消", "确定要取消这个下载任务吗？", self.window())
        box.yesButton.setText("确定")
        box.cancelButton.setText("取消")
        if box.exec():
            # 设置取消标志，阻止进度更新
            self._is_cancelling = True

            # 如果任务正在下载，找到对应的下载线程并取消
            if self.download_thread:
                # 立即更新UI状态，不等待线程结束
                self.task.status = "正在取消..."
                self.updateStatus("正在取消...")

                # 禁用取消按钮，避免重复点击
                self.cancelBtn.setEnabled(False)

                # 连接取消完成信号
                self.download_thread.cancelled_signal.connect(
                    self._onDownloadCancellationComplete
                )

                # 异步取消，不阻塞界面
                self.download_thread.cancel()
            else:
                # 如果没有线程引用，直接完成取消
                self._completeDownloadCancellation()

    def _onDownloadCancellationComplete(self):
        """下载取消完成后的处理"""
        self._completeDownloadCancellation()

        # 断开信号连接
        if self.download_thread:
            try:
                self.download_thread.cancelled_signal.disconnect(
                    self._onDownloadCancellationComplete
                )
            except Exception:
                pass

    def _completeDownloadCancellation(self):
        """完成下载取消操作"""
        # 清除取消标志
        self._is_cancelling = False

        # 更新任务状态
        self.task.status = "已取消"
        self.task.progress = 0
        self.task.speed = ""
        self.task.end_time = datetime.now()

        # 更新UI状态
        self.updateStatus("已取消")

        # 恢复按钮状态
        self.removeBtn.setDisabled(False)
        self.retryBtn.setVisible(True)
        self.cancelBtn.setVisible(False)
        self.cancelBtn.setEnabled(True)

        # 显示取消提示
        event_bus.notification_service.show_info(
            "下载已取消", f"任务 '{self.task.filename or self.task.url}' 已被取消"
        )

    def retryDownload(self):
        """重新下载"""
        # 重置取消相关状态
        self._is_cancelling = False

        # 发送重新下载信号
        self.retryDownloadSignal.emit(self.task.id)

    def removeTask(self):
        """移除任务"""
        # 发送移除任务信号
        self.removeTaskSignal.emit(self.task.id)
