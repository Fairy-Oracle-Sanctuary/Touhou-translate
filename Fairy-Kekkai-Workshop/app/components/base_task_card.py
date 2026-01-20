# coding:utf-8
import os
import platform
import subprocess

from PySide6.QtCore import QFileInfo, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileIconProvider, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    ImageLabel,
    IndeterminateProgressBar,
    MessageBox,
    ProgressBar,
    TransparentToolButton,
)

from ..common.event_bus import event_bus


class BaseItemWidget(CardWidget):
    """任务项组件"""

    # 定义信号
    removeTaskSignal = Signal(int)  # 任务ID
    retryTaskSignal = Signal(int)  # 任务ID

    def __init__(
        self,
        task,
        progressBar_type="common",
        task_type="默认",
        parent=None,
    ):
        super().__init__(parent)
        self.task = task
        self.task_thread = None
        self.progressBar_type = progressBar_type
        self.task_type = task_type

        self._initUI()

    def _initUI(self):
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()

        self.fileNameLabel = BodyLabel(str(self.task.input_file))

        self.imageLabel = ImageLabel()
        self.imageLabel.setImage(
            QFileIconProvider().icon(QFileInfo(self.task.input_file)).pixmap(32, 32)
        )

        self.filePathLabel = BodyLabel(str(self.task.input_file))

        if self.progressBar_type == "determinate":
            self.progressBar = IndeterminateProgressBar()
        else:
            self.progressBar = ProgressBar()

        self.statusLabel = CaptionLabel(self.task.status)

        self.openFolderBtn = TransparentToolButton(FluentIcon.FOLDER, self)
        self.openFolderBtn.setToolTip("打开文件夹")
        self.openFolderBtn.setVisible(self.task.status == "已完成")
        self.openFolderBtn.clicked.connect(self.openFolder)

        self.cancelBtn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.cancelBtn.setToolTip(f"取消{self.task_type}")
        self.cancelBtn.setVisible(
            self.task.status == f"{self.task_type}中" or self.task.status == "等待中"
        )
        self.cancelBtn.clicked.connect(self.cancelTranslate)

        self.retryBtn = TransparentToolButton(FluentIcon.SYNC, self)
        self.retryBtn.setToolTip(f"重新{self.task_type}")
        self.retryBtn.setVisible(self.task.status == "失败")
        self.retryBtn.clicked.connect(self.retryTranslate)

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

        self.setMinimumHeight(75)

    def updateStatusStyle(self, statusPill):
        """更新状态标签样式"""
        if self.task.status == "等待中":
            statusPill.setProperty("isSecondary", True)
        elif self.task.status == f"{self.task_type}中":
            statusPill.setProperty("isPrimary", True)
        elif self.task.status == "已完成":
            statusPill.setProperty("isSuccess", True)
        elif self.task.status == "失败":
            statusPill.setProperty("isError", True)
        statusPill.setStyle(statusPill.style())

    def updateStatus(self, status, success=True, error_message=""):
        """更新状态"""
        self.task.status = status
        if not success:
            self.task.error_message = error_message
        self.statusLabel.setText(self.task.status)

        # 显示/隐藏按钮
        self.openFolderBtn.setVisible(status == "已完成")
        self.cancelBtn.setVisible(status == f"{self.task_type}中")
        self.retryBtn.setVisible(status == "失败")

        # 设置按钮可用性
        self.removeBtn.setEnabled(
            status == "已完成" or status == "失败" or status == "已取消"
        )

        # 进度条
        self.progressBar.setVisible(status == f"{self.task_type}中")

    def updateProgress(self, progress, input_file):
        """更新进度"""
        if self.progressBar_type == "determinate":
            return
        self.task.progress = progress
        if input_file and not self.task.input_file:
            self.task.input_file = input_file
            self.fileNameLabel.setText(str(self.task.input_file))

        self.progressBar.setValue(progress)

        # 更新状态标签
        self.statusLabel.setText(self.task.status)

    def openFolder(self):
        """打开文件夹"""
        if os.path.exists(self.task.output_file):
            # 打开文件所在文件夹并选中文件
            if platform.system() == "Windows":
                subprocess.Popen(
                    f'explorer /select,"{self.task.output_file}"',
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif platform.system() == "Darwin":
                subprocess.Popen(
                    ["open", "-R", self.task.output_file],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                # Linux系统
                folder_path = os.path.dirname(self.task.output_file)
                subprocess.Popen(
                    ["xdg-open", folder_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
        else:
            # 如果文件不存在，只打开文件夹
            folder_path = os.path.dirname(self.task.output_file)
            if os.path.exists(folder_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

    def cancelTranslate(self):
        """取消下载 - 异步版本"""
        # 添加确认对话框
        box = MessageBox(
            "确认取消", f"确定要取消这个{self.task_type}任务吗？", self.window()
        )
        box.yesButton.setText("确定")
        box.cancelButton.setText("取消")
        if box.exec():
            # 如果任务正在提取，找到对应的提取线程并取消
            if self.task_thread:
                # 连接取消完成信号
                self.task_thread.cancelled_signal.connect(self._onCancellationComplete)

                # 立即更新UI状态，不等待线程结束
                self.task.status = "正在取消..."
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
            f"{self.task_type}已取消", f"任务 '{self.task.input_file}' 已被取消"
        )

    def retryTranslate(self):
        """重新下载"""
        # 发送重新下载信号
        self.retryTaskSignal.emit(self.task.id)

    def removeTask(self):
        """移除任务"""
        # 发送移除任务信号
        self.removeTaskSignal.emit(self.task.id)
