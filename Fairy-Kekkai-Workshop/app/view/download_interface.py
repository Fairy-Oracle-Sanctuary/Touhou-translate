# coding:utf-8
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, 
                           PushButton, TransparentToolButton, FluentIcon, ProgressBar,
                           PrimaryPushButton, InfoBar, ToolButton, StrongBodyLabel,
                           SimpleCardWidget, HorizontalSeparator, TitleLabel)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame

class DownloadInterface(ScrollArea):
    """下载界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DownloadInterface")
        
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        
        # 标题
        self.titleLabel = TitleLabel("下载管理", self.view)
        
        # 控制按钮区域
        self.controlCard = ControlCard()
        self.controlCard.startAllButton.clicked.connect(self.startAllDownloads)
        self.controlCard.pauseAllButton.clicked.connect(self.pauseAllDownloads)
        self.controlCard.clearAllButton.clicked.connect(self.clearCompletedDownloads)
        
        # 下载任务列表
        self.downloadListLayout = QVBoxLayout()
        self.downloadListLayout.setSpacing(10)
        self.downloadListLayout.setContentsMargins(0, 0, 0, 0)
        
        # 示例下载任务
        # self.addDownloadTask("视频教程.mp4", 1024, 512)  # 50% 完成
        # self.addDownloadTask("音乐专辑.zip", 512, 0)    # 0% 完成
        # self.addDownloadTask("文档.pdf", 256, 256)      # 100% 完成
        
        # 设置布局
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.controlCard)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.downloadListLayout)
        self.vBoxLayout.addStretch(1)
        
        self._initWidget()
    
    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setObjectName('downloadView')
        self.enableTransparentBackground()

    
    def addDownloadTask(self, filename, total_size, downloaded_size):
        """添加下载任务卡片"""
        task_card = DownloadTaskCard(filename, total_size, downloaded_size)
        self.downloadListLayout.addWidget(task_card)
        return task_card
    
    def startAllDownloads(self):
        """开始所有下载任务"""
        for i in range(self.downloadListLayout.count()):
            item = self.downloadListLayout.itemAt(i)
            if item and item.widget():
                item.widget().startDownload()
        
        InfoBar.success(
            title="操作成功",
            content="已开始所有下载任务",
            parent=self
        )
    
    def pauseAllDownloads(self):
        """暂停所有下载任务"""
        for i in range(self.downloadListLayout.count()):
            item = self.downloadListLayout.itemAt(i)
            if item and item.widget():
                item.widget().pauseDownload()
        
        InfoBar.info(
            title="操作成功",
            content="已暂停所有下载任务",
            parent=self
        )
    
    def clearCompletedDownloads(self):
        """清除已完成的下载任务"""
        # 从后往前删除，避免索引问题
        for i in range(self.downloadListLayout.count() - 1, -1, -1):
            item = self.downloadListLayout.itemAt(i)
            if item and item.widget() and item.widget().isCompleted():
                widget = item.widget()
                self.downloadListLayout.removeWidget(widget)
                widget.deleteLater()
        
        InfoBar.info(
            title="操作完成",
            content="已清除所有已完成的任务",
            parent=self
        )


class ControlCard(CardWidget):
    """下载控制卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.startAllButton = PrimaryPushButton("全部开始", self)
        self.pauseAllButton = PushButton("全部暂停", self)
        self.clearAllButton = PushButton("清除已完成", self)
        
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.hBoxLayout.setSpacing(15)
        
        self.hBoxLayout.addWidget(self.startAllButton)
        self.hBoxLayout.addWidget(self.pauseAllButton)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.clearAllButton)
        
        self.setFixedHeight(70)


class DownloadTaskCard(CardWidget):
    """下载任务卡片"""
    
    def __init__(self, filename, total_size, downloaded_size=0, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.total_size = total_size
        self.downloaded_size = downloaded_size
        self.is_downloading = False
        self.is_paused = False
        
        # 文件图标
        self.iconWidget = IconWidget(FluentIcon.DOCUMENT, self)
        
        # 文件信息
        self.filenameLabel = StrongBodyLabel(filename, self)
        self.infoLabel = CaptionLabel(self._formatFileInfo(), self)
        
        # 进度条
        self.progressBar = ProgressBar(self)
        self.progressBar.setValue(self._calculateProgress())
        
        # 控制按钮
        self.startButton = TransparentToolButton(FluentIcon.PLAY, self)
        self.pauseButton = TransparentToolButton(FluentIcon.PAUSE, self)
        self.cancelButton = TransparentToolButton(FluentIcon.CLOSE, self)
        self.openButton = TransparentToolButton(FluentIcon.FOLDER, self)
        
        self.startButton.clicked.connect(self.startDownload)
        self.pauseButton.clicked.connect(self.pauseDownload)
        self.cancelButton.clicked.connect(self.cancelDownload)
        self.openButton.clicked.connect(self.openFileLocation)
        
        # 布局
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        
        self._setupUI()
        self._updateButtonState()
    
    def _setupUI(self):
        self.setFixedHeight(110)
        self.iconWidget.setFixedSize(32, 32)
        
        self.hBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.addWidget(self.iconWidget)
        
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.addWidget(self.filenameLabel)
        self.vBoxLayout.addWidget(self.infoLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.progressBar)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(5)
        self.buttonLayout.addWidget(self.startButton)
        self.buttonLayout.addWidget(self.pauseButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addWidget(self.openButton)
        self.hBoxLayout.addLayout(self.buttonLayout)
    
    def _formatFileInfo(self):
        """格式化文件大小信息"""
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        
        progress = self._calculateProgress()
        return f"{format_size(self.downloaded_size)} / {format_size(self.total_size)} ({progress}%)"
    
    def _calculateProgress(self):
        """计算下载进度百分比"""
        if self.total_size == 0:
            return 0
        return int((self.downloaded_size / self.total_size) * 100)
    
    def _updateButtonState(self):
        """更新按钮状态"""
        completed = self.isCompleted()
        
        self.startButton.setVisible(not self.is_downloading and not completed)
        self.pauseButton.setVisible(self.is_downloading and not completed)
        self.openButton.setVisible(completed)
        
        self.progressBar.setVisible(not completed)
        
        if completed:
            self.infoLabel.setText("下载完成")
    
    def startDownload(self):
        """开始下载"""
        if self.isCompleted():
            return
            
        self.is_downloading = True
        self.is_paused = False
        
        # 模拟下载进度更新
        self.downloadTimer = QTimer(self)
        self.downloadTimer.timeout.connect(self._updateDownloadProgress)
        self.downloadTimer.start(100)  # 每100ms更新一次
        
        self._updateButtonState()
    
    def pauseDownload(self):
        """暂停下载"""
        self.is_downloading = False
        self.is_paused = True
        
        if hasattr(self, 'downloadTimer'):
            self.downloadTimer.stop()
        
        self._updateButtonState()
    
    def cancelDownload(self):
        """取消下载"""
        self.is_downloading = False
        self.is_paused = False
        
        if hasattr(self, 'downloadTimer'):
            self.downloadTimer.stop()
        
        self.downloaded_size = 0
        self.progressBar.setValue(0)
        self.infoLabel.setText(self._formatFileInfo())
        
        self._updateButtonState()
    
    def openFileLocation(self):
        """打开文件位置"""
        # 这里应该实现打开文件所在位置的逻辑
        InfoBar.info(
            title="打开位置",
            content=f"将打开 {self.filename} 所在位置",
            parent=self
        )
    
    def isCompleted(self):
        """检查是否已完成下载"""
        return self.downloaded_size >= self.total_size and self.total_size > 0
    
    def _updateDownloadProgress(self):
        """更新下载进度（模拟）"""
        if self.downloaded_size < self.total_size:
            # 模拟下载速度：每秒增加总大小的1%
            increment = max(1, self.total_size // 100)
            self.downloaded_size = min(self.downloaded_size + increment, self.total_size)
            
            self.progressBar.setValue(self._calculateProgress())
            self.infoLabel.setText(self._formatFileInfo())
            
            if self.downloaded_size >= self.total_size:
                self.downloadTimer.stop()
                self.is_downloading = False
                self._updateButtonState()