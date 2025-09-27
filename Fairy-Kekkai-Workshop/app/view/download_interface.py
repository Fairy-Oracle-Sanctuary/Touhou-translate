# coding:utf-8
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, 
                           PushButton, PrimaryPushButton, FluentIcon, StrongBodyLabel, 
                        InfoBar, TitleLabel, SubtitleLabel, ListWidget, TransparentToolButton,
                        FlowLayout, MessageBox, Dialog, LineEdit, Dialog, SpinBox,
                        ProgressBar, ProgressRing, IndeterminateProgressBar, ComboBox,
                        SimpleCardWidget, PillPushButton, ToolButton, SegmentedWidget)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer, QThread, QSize, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidgetItem, QFileDialog, QHBoxLayout, QLabel, QFrame, QTextEdit, QDialog, QApplication
import os
import shutil
import subprocess
import platform
import yt_dlp
import json
from datetime import datetime
import time
import re
import requests

from ..components.dialog import CustomMessageBox

from ..service.event_bus import event_bus
from ..service.events import EventBuilder

class DownloadInterface(ScrollArea):
    """下载界面"""
    
    # 定义返回信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        
        self.download_tasks = []  # 所有下载任务
        self.active_downloads = []  # 活跃的下载线程
        self.max_concurrent_downloads = 2  # 最大同时下载数
        
        self._initWidget()

        event_bus.download_requested.connect(self.addDownloadFromProject)

    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName('downloadInterface')
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
        
        self.segmentedWidget.addItem(self.allTab, "全部", lambda: self.filterTasks("全部"))
        self.segmentedWidget.addItem(self.downloadingTab, "下载中", lambda: self.filterTasks("下载中"))
        self.segmentedWidget.addItem(self.completedTab, "已完成", lambda: self.filterTasks("已完成"))
        self.segmentedWidget.addItem(self.failedTab, "失败", lambda: self.filterTasks("失败"))
        
        self.segmentedWidget.setCurrentItem(self.allTab)
        self.segmentedWidget.setMaximumHeight(30)
        
        # 创建任务列表容器
        self.taskListContainer = QWidget(self)
        self.taskListLayout = QVBoxLayout(self.taskListContainer)
        self.taskListLayout.setAlignment(Qt.AlignTop)
        
        # 空状态提示
        self.emptyStateLabel = BodyLabel("暂无下载任务", self.taskListContainer)
        self.emptyStateLabel.setAlignment(Qt.AlignCenter)
        self.emptyStateLabel.setStyleSheet("color: gray; padding: 50px;")
        self.taskListLayout.addWidget(self.emptyStateLabel)
        
        # 设置布局
        self.vBoxLayout.addWidget(addDownloadBtn)
        self.vBoxLayout.addWidget(self.segmentedWidget)
        self.vBoxLayout.addWidget(self.taskListContainer)
        
        # 连接信号
        # self.retryDownloadSignal.connect(self.retryDownload)
        # self.removeTaskSignal.connect(self.removeTask)
    
    def showAddDownloadDialog(self):
        """显示添加下载对话框"""
        # 这里需要从主窗口获取项目信息
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break

        dialog = CustomMessageBox(
            title=f"请输入视频ID", 
            text=f"https://www.youtube.com/watch?v=", 
            parent= main_window if main_window else self.window(),
            minwidth=400,
            )
        if dialog.exec():
            url = dialog.LineEdit.text().strip()
            task = DownloadTask(
                url="https://www.youtube.com/watch?v=" + url,
                download_path=os.path.expanduser(r"~\Downloads"),
                quality="best",
                file_name="",
            )
            self.addDownloadTask(task)
        else:
            pass
        
        # def onOk():
        #     url = dialog.LineEdit.text().strip()
        #     if url:
        #         # 创建一个示例任务
        #         task = DownloadTask(
        #             url=url,
        #             download_path=os.path.expanduser("~/Downloads"),
        #             quality="best",
        #             project_name="示例项目",
        #             episode_num=1
        #         )
        #         self.addDownloadTask(task)
        #         dialog.accept()  
    
    def addDownloadTask(self, task):
        """添加下载任务"""
        self.download_tasks.append(task)
        
        # 创建任务项
        self.task_item = DownloadItemWidget(task, self.taskListContainer)
        self.taskListLayout.insertWidget(0, self.task_item)

        # 连接信号 - 添加这四行代码
        self.task_item.removeTaskSignal.connect(self.removeTask)
        self.task_item.retryDownloadSignal.connect(self.retryDownload)

        # 隐藏空状态提示
        self.emptyStateLabel.setVisible(False)
        
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
    
    def startDownload(self, task):
        """开始下载任务"""
        # 创建下载线程
        download_thread = DownloadThread(task)
        download_thread.progress_signal.connect(
            lambda progress, speed, filename: self.onDownloadProgress(task.id, progress, speed, filename)
        )
        download_thread.finished_signal.connect(
            lambda success, message: self.onDownloadFinished(task.id, success, message)
        )

        # 存储线程引用到对应的DownloadItemWidget
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget) and widget.task.id == task.id:
                widget.download_thread = download_thread  # 添加这一行
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
                    event_bus.notification_service.show_success("下载完成", f"-{task.filename}- 下载完成")
                else:
                    task.status = "失败"
                    event_bus.notification_service.show_error("下载失败", message.strip())
                
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
                    widget.task.progress, 
                    widget.task.speed, 
                    widget.task.filename
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
        
        # 检查是否有可见的任务
        has_visible = False
        for i in range(self.taskListLayout.count()):
            widget = self.taskListLayout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget) and widget.isVisible():
                has_visible = True
                break
        
        self.emptyStateLabel.setVisible(not has_visible)
        if not has_visible:
            self.emptyStateLabel.setText(f"暂无{filter_type}的任务")
    
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
            
            # 检查是否还有任务
            if not self.download_tasks:
                self.emptyStateLabel.setVisible(True)
                self.emptyStateLabel.setText("暂无下载任务")

            # 开始下一个下载
            self.startNextDownload()
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"任务移除失败: {e}")
            
    
    def addDownloadFromProject(self, request_data):
        """从项目界面添加下载任务"""
        task = DownloadTask(
            url=request_data['url'],
            download_path=request_data['save_path'],
            file_name = '生肉.mp4'
        )
        self.addDownloadTask(task)

class DownloadTask:
    """下载任务类"""
    _id_counter = 0

    def __init__(self, url, download_path, file_name, quality='best', project_name="", episode_num=0):
        self.url = url
        self.download_path = download_path
        self.file_name = file_name
        self.quality = quality
        self.project_name = project_name
        self.episode_num = episode_num
        self.status = "等待中"  # 等待中, 下载中, 已完成, 失败
        self.progress = 0
        self.speed = ""
        self.filename = ""
        self.start_time = None
        self.end_time = None
        self.error_message = ""

        DownloadTask._id_counter += 1
        self.id = DownloadTask._id_counter

class DownloadThread(QThread):
    """下载线程"""
    
    # 定义信号
    progress_signal = Signal(int, str, str)  # 进度百分比, 速度, 文件名
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        self.is_cancelled = False
    
    def run(self):
        # 先测试能否访问youtube
        # 先测试能否访问youtube
        try:
            # 设置超时时间为10秒
            resp = requests.get("https://www.youtube.com", timeout=10)
            if resp.status_code != 200:
                self.finished_signal.emit(False, f"无法访问YouTube，HTTP状态码: {resp.status_code}")
                return
                
        except requests.exceptions.Timeout:
            self.finished_signal.emit(False, "连接YouTube超时，请检查网络连接")
            return
        except requests.exceptions.ConnectionError:
            self.finished_signal.emit(False, "无法连接到YouTube，请检查网络连接")
            return
        except requests.exceptions.RequestException as e:
            self.finished_signal.emit(False, f"网络错误: {str(e)}")
            return
        except Exception as e:
            self.finished_signal.emit(False, f"检测网络连接时发生未知错误: {str(e)}")
            return
                    
        self.task.status = "下载中"
        self.task.start_time = datetime.now()
        
        try:
            # 创建下载选项
            ydl_opts = {
                'format': 'bv[ext=mp4]+ba[ext=m4a]',
                'embedmetadata': True,
                'merge_output_format': 'mp4',
                'outtmpl': f'{self.task.download_path if self.task.file_name else self.task.download_path+"/%(title)s.%(ext)s"}',
                'progress_hooks': [self.progress_hook],
            }

            # 开始下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(self.task.url, download=False)
                self.task.filename = f"{info.get('title', '未知标题')}.{info.get('ext', 'mp4')}"
                
                # 开始下载
                ydl.cache.remove()
                ydl.download([self.task.url])
                
            if not self.is_cancelled:
                self.task.status = "已完成"
                self.task.end_time = datetime.now()
                self.finished_signal.emit(True, "下载完成")
                
        except Exception as e:
            if not self.is_cancelled:
                self.task.status = "失败"
                self.task.error_message = str(e)
                self.task.end_time = datetime.now()
                self.finished_signal.emit(False, f"下载失败: {str(e)}")
    
    def progress_hook(self, d):
        """进度回调函数"""
        if self.is_cancelled:
            raise Exception("下载已取消")
        
        # 获取视频名称
        video_name = d.get('filename', d.get('info_dict', {}).get('title', '未知视频'))
        if video_name and not self.task.filename:
            self.task.filename = video_name
            print(video_name)

        if d['status'] == 'downloading':
            # 计算下载进度
            if 'total_bytes' in d and d['total_bytes']:
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes'])
                speed = d.get('_speed_str', 'N/A').split()
                speed = speed[-1][0:-4]
                self.task.progress = percent
                self.task.speed = speed
                self.progress_signal.emit(percent, speed, self.task.filename)
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes_estimate'])
                speed = d.get('_speed_str', 'N/A')
                self.task.progress = percent
                self.task.speed = speed
                self.progress_signal.emit(percent, speed, self.task.filename)
            else:
                self.progress_signal.emit(0, "未知速度", self.task.filename)
        
        elif d['status'] == 'finished':
            self.task.progress = 100
            self.progress_signal.emit(100, "完成", self.task.filename)
    
    def cancel(self):
        """取消下载"""
        self.is_cancelled = True

class DownloadItemWidget(SimpleCardWidget):
    """下载任务项组件"""

    # 定义信号
    removeTaskSignal = Signal(int)     # 任务ID
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
        
        urlLabel = CaptionLabel(f"URL: {self.task.url[:50]}..." if len(self.task.url) > 50 else f"URL: {self.task.url}", self)
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
            statusPill.setProperty('isSecondary', True)
        elif self.task.status == "下载中":
            statusPill.setProperty('isPrimary', True)
        elif self.task.status == "已完成":
            statusPill.setProperty('isSuccess', True)
        elif self.task.status == "失败":
            statusPill.setProperty('isError', True)
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
                        widget.setText(f'{progress}% {speed}')
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
        box = MessageBox(
            "确认取消",
            "确定要取消这个下载任务吗？",
            self.window()
        )
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
            
            #恢复按钮
            self.removeBtn.setDisabled(False)
            self.retryBtn.setVisible(True)

            # 显示取消提示
            event_bus.notification_service.show_info("下载已取消", f"任务 '{self.task.filename}' 已被取消")

    def retryDownload(self):
        """重新下载"""
        # 发送重新下载信号
        self.retryDownloadSignal.emit(self.task.id)
    
    def removeTask(self):
        """移除任务"""
        # 发送移除任务信号
        self.removeTaskSignal.emit(self.task.id)

