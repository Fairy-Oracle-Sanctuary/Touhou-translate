# coding:utf-8
import os

from PySide6.QtCore import QFileInfo, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileIconProvider, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    ImageLabel,
    MessageBox,
    ProgressBar,
    TransparentToolButton,
)

from ..common.event_bus import event_bus


class OcrItemWidget(CardWidget):
    """下载任务项组件"""

    # 定义信号
    removeTaskSignal = Signal(int)  # 任务ID
    retryTaskSignal = Signal(int)  # 任务ID

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_thread = None

        self._initUI()

    def _initUI(self):
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()

        self.fileNameLabel = BodyLabel(self.task.video_path)

        self.imageLabel = ImageLabel()
        self.imageLabel.setImage(
            QFileIconProvider().icon(QFileInfo(self.task.video_path)).pixmap(32, 32)
        )

        self.filePathLabel = BodyLabel(self.task.video_path)
        self.progressBar = ProgressBar()

        self.statusLabel = CaptionLabel(self.task.status)

        self.openFolderBtn = TransparentToolButton(FluentIcon.FOLDER, self)
        self.openFolderBtn.setToolTip("打开文件夹")
        self.openFolderBtn.setVisible(self.task.status == "已完成")
        self.openFolderBtn.clicked.connect(self.openFolder)

        self.cancelBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.cancelBtn.setToolTip("取消提取")
        self.cancelBtn.setVisible(self.task.status == "提取中")
        self.cancelBtn.clicked.connect(self.cancelOcr)

        self.retryBtn = TransparentToolButton(FluentIcon.SYNC, self)
        self.retryBtn.setToolTip("重新提取")
        self.retryBtn.setVisible(self.task.status == "失败")
        self.retryBtn.clicked.connect(self.retryOcr)

        self.removeBtn = TransparentToolButton(FluentIcon.DELETE, self)
        self.removeBtn.setToolTip("移除任务")
        self.removeBtn.setDisabled(True)
        self.removeBtn.clicked.connect(self.removeTask)

        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)
        self.hBoxLayout.addWidget(self.openFolderBtn)
        self.hBoxLayout.addWidget(self.cancelBtn)
        self.hBoxLayout.addWidget(self.retryBtn)
        self.hBoxLayout.addWidget(self.removeBtn)

        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)
        self.vBoxLayout.addWidget(self.progressBar)

        self.infoLayout.addWidget(self.statusLabel)

    def updateStatusStyle(self, statusPill):
        """更新状态标签样式"""
        if self.task.status == "等待中":
            statusPill.setProperty("isSecondary", True)
        elif self.task.status == "提取中":
            statusPill.setProperty("isPrimary", True)
        elif self.task.status == "已完成":
            statusPill.setProperty("isSuccess", True)
        elif self.task.status == "失败":
            statusPill.setProperty("isError", True)
        statusPill.setStyle(statusPill.style())

    def updateProgress(self, progress, video_path):
        """更新进度"""
        self.task.progress = progress
        if video_path and not self.task.video_path:
            self.task.video_path = video_path
            self.fileNameLabel.setText(self.task.video_path)

        self.progressBar.setValue(progress)

        # 更新状态标签
        self.statusLabel.setText(self.task.status)

    def updateStatus(self, status, success=True, error_message=""):
        """更新状态"""
        self.task.status = status
        if not success:
            self.task.error_message = error_message
        self.statusLabel.setText(self.task.status)

        # 显示/隐藏按钮
        self.openFolderBtn.setVisible(status == "已完成")
        self.cancelBtn.setVisible(status == "提取中")
        self.retryBtn.setVisible(status == "失败")

        # 设置按钮可用性
        self.removeBtn.setEnabled(status == "已完成" or status == "失败")

    def openFolder(self):
        """打开文件夹"""
        # 获取视频文件所在的目录
        if self.task.video_path and os.path.exists(self.task.video_path):
            folder_path = os.path.dirname(self.task.video_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        else:
            event_bus.notification_service.show_warning(
                "打开文件夹失败", "视频文件路径不存在，无法打开文件夹。"
            )

    def cancelOcr(self):
        """取消下载 - 异步版本"""
        # 添加确认对话框
        box = MessageBox("确认取消", "确定要取消这个提取任务吗？", self.window())
        box.yesButton.setText("确定")
        box.cancelButton.setText("取消")
        if box.exec():
            # 如果任务正在提取，找到对应的提取线程并取消
            if self.task_thread:
                # 连接取消完成信号
                self.task_thread.cancelled_signal.connect(self._onCancellationComplete)

                # 立即更新UI状态，不等待线程结束
                self.task.status = "正在取消..."
                self.task.progress = 0
                self.updateStatus("正在取消...")

                # 异步取消，不阻塞界面
                self.task_thread.cancel()

                # 禁用取消按钮，避免重复点击
                self.cancelBtn.setEnabled(False)
            else:
                # 如果没有线程引用，直接更新状态
                self._completeCancellation()

    def _onCancellationComplete(self):
        """取消完成后的处理"""
        self._completeCancellation()

        # 断开信号连接，避免重复调用
        if self.task_thread:
            try:
                self.task_thread.cancelled_signal.disconnect(
                    self._onCancellationComplete
                )
            except Exception:
                pass

    def _completeCancellation(self):
        """完成取消操作"""
        # 更新任务状态
        self.task.status = "已取消"
        self.task.progress = 0
        self.task.speed = ""

        # 更新UI状态
        self.updateStatus("已取消")

        # 恢复按钮状态
        self.removeBtn.setDisabled(False)
        self.retryBtn.setVisible(True)
        self.cancelBtn.setVisible(False)

        # 重新启用取消按钮（虽然它已经隐藏了）
        self.cancelBtn.setEnabled(True)

        # 显示取消提示
        event_bus.notification_service.show_info(
            "提取已取消", f"任务 '{self.task.video_path}' 已被取消"
        )

    def retryOcr(self):
        """重新下载"""
        # 发送重新下载信号
        self.retryTaskSignal.emit(self.task.id)

    def removeTask(self):
        """移除任务"""
        # 发送移除任务信号
        self.removeTaskSignal.emit(self.task.id)
