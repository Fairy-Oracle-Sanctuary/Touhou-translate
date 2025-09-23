# coding:utf-8
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, 
                           PushButton, PrimaryPushButton, FluentIcon, StrongBodyLabel, 
                        InfoBar, TitleLabel, SubtitleLabel, ListWidget, TransparentToolButton,
                        FlowLayout, MessageBox)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidgetItem, QFileDialog, QHBoxLayout, QLabel, QFrame, QApplication
import os
import shutil
import subprocess
import platform

from .dialog import CustomMessageBox, CustomDoubleMessageBox

class FileItemWidget(QFrame):
    """自定义文件项widget"""
    
    def __init__(self, window, project, card_id, folder_num, file_name, file_path, icon, file_exists, donwload_need, parent=None):
        super().__init__(parent)
        self.main_window = window
        self.project = project
        self.card_id = card_id
        self.folder_num = folder_num
        self.file_name = file_name
        self.file_path = file_path
        self.file_exists = file_exists
        self.download_need = donwload_need
        
        self.setFixedHeight(60)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            FileItemWidget {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin: 2px;
                padding: 5px;
                background-color: white;
            }
            FileItemWidget:hover {
                background-color: #f5f5f5;
            }
        """)
        
        self._initUI(icon)
    
    def _initUI(self, icon):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 文件图标和名称
        iconWidget = IconWidget(icon.icon(), self)
        fileNameLabel = BodyLabel(self.file_name, self)
        fileNameLabel.setStyleSheet("""
            margin-left: 10px;
            color: black;  /* 确保文件名是黑色 */
        """)
        

        # 状态指示器
        statusLabel = QLabel("✓" if self.file_exists else "✗", self)
        statusLabel.setStyleSheet("""
            QLabel {
                color: %s;
                font-weight: bold;
                margin-right: 10px;
            }
        """ % ("green" if self.file_exists else "red"))
        
        # 按钮区域
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(5)
        
        # 打开文件路径按钮
        self.openPathBtn = TransparentToolButton(FluentIcon.FOLDER, self)
        self.openPathBtn.setToolTip("打开文件所在路径")
        self.openPathBtn.clicked.connect(self.openFileLocation)
        
        # 删除文件按钮
        self.deleteBtn = TransparentToolButton(FluentIcon.DELETE, self)
        self.deleteBtn.setToolTip("删除文件")
        self.deleteBtn.clicked.connect(self.deleteFile)
        
        # 只有文件存在时才启用删除按钮
        self.deleteBtn.setEnabled(self.file_exists)
        
        # 下载快捷键 只在封面和mp4文件缺失时并需要下载才启用
        if self.download_need and not self.file_exists:
            self.downloadBtn = TransparentToolButton(FluentIcon.DOWNLOAD, self)
            self.downloadBtn.setToolTip("下载缺失的文件")
            self.downloadBtn.clicked.connect(self.donwloadFile)
            buttonLayout.addWidget(self.downloadBtn)

        buttonLayout.addWidget(self.openPathBtn)
        buttonLayout.addWidget(self.deleteBtn)
        
        layout.addWidget(iconWidget)
        layout.addWidget(fileNameLabel)
        layout.addStretch()
        layout.addWidget(statusLabel)
        layout.addLayout(buttonLayout)
    
    def openFileLocation(self):
        """打开文件所在路径"""
        if os.path.exists(self.file_path):
            # 打开文件所在文件夹并选中文件
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{self.file_path}"')
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", self.file_path])
            else:
                # Linux系统
                folder_path = os.path.dirname(self.file_path)
                subprocess.Popen(["xdg-open", folder_path])
        else:
            # 如果文件不存在，只打开文件夹
            folder_path = os.path.dirname(self.file_path)
            if os.path.exists(folder_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
    
    def deleteFile(self):
        """删除文件"""
        if not os.path.exists(self.file_path):
            return
            
        # 确认对话框
        box = MessageBox(
            "确认删除",
            f"确定要删除文件 '{self.file_name}' 吗？此操作不可撤销。",
            self.window()
        )
        
        if box.exec():
            try:
                os.remove(self.file_path)
                # 发送信号通知文件已删除
                if hasattr(self.parent(), 'fileDeletedSignal'):
                    self.parent().fileDeletedSignal.emit()
                
                InfoBar.success(
                    title="删除成功",
                    content=f"已删除文件: {self.file_name}",
                    parent=self.main_window,
                    duration=3000
                )
            except Exception as e:
                InfoBar.error(
                    title="删除失败",
                    content=f"删除文件时出错: {str(e)}",
                    parent=self.main_window,
                    duration=3000
                )

    def donwloadFile(self):
        """下载缺失的文件"""

        file_ext = os.path.splitext(self.file_name)[1].lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png']:
            # 下载封面 - 这里需要从视频URL获取封面
            # 由于yt-dlp主要下载视频，封面下载需要特殊处理
            # 暂时提示用户手动处理或使用其他方式
            InfoBar.warning(
                title="功能开发中",
                content="封面下载功能正在开发中，请暂时手动处理",
                parent=self.window(),
                duration=3000
            )
            return
        
        download_path = os.path.dirname(self.file_path)

        dialog = CustomMessageBox(
            title=f"下载第 {self.folder_num} 集生肉视频",
            text="请输入视频URL:",
            parent=self.window()
        )
        dialog.LineEdit.setText(self.project.project_video_url[self.card_id][self.folder_num-1])
        
        if dialog.exec():
            video_url = dialog.LineEdit.text().strip()
            if video_url:
                # 通过信号发送下载请求
                download_path = self.file_path
                # 找到父级ProjectDetailInterface并发射信号
                parent = self.parent()
                while parent:
                    if isinstance(parent, ProjectDetailInterface):
                        parent.downloadRequested.emit(
                            video_url, download_path, "生肉"
                        )
                        break
                    parent = parent.parent()

class FileListWidget(QWidget):
    """自定义文件列表widget"""
    
    fileDeletedSignal = Signal()
    
    def __init__(self, window, project, card_id, folder_num, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.main_window = window
        self.project = project
        self.card_id = card_id
        self.folder_num = folder_num
        self.fileWidgets = []
    
    def addFileItem(self, file_name, file_path, icon, file_exists, download_need):
        """添加文件项"""
        fileWidget = FileItemWidget(self.main_window, self.project, self.card_id, self.folder_num, file_name, file_path, icon, file_exists, download_need, self)
        fileWidget.setCursor(Qt.PointingHandCursor)
        
        # 连接点击事件（整个widget的点击）
        fileWidget.mousePressEvent = lambda event: self.handleFileItemClick(fileWidget)
        
        self.layout.addWidget(fileWidget)
        self.fileWidgets.append(fileWidget)
        
        # 连接删除信号
        fileWidget.deleteBtn.clicked.connect(self.fileDeletedSignal.emit)
    
    def handleFileItemClick(self, fileWidget):
        """处理文件项点击事件"""
        file_path = fileWidget.file_path
        
        # 如果文件存在，尝试打开它
        if os.path.exists(file_path):
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.srt':
                # 对于字幕文件，使用文本编辑器打开
                self.openTextFile(file_path)
            else:
                # 对于其他文件，使用系统默认程序打开
                success = QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                if not success:
                    self.fallbackOpenFile(file_path)
        else:
            # 如果文件不存在，提供上传选项
            self.uploadMissingFile(file_path)
    
    def openTextFile(self, file_path):
        """使用文本编辑器打开文件"""
        try:
            if platform.system() == "Windows":
                os.system(f'notepad "{file_path}"')
            elif platform.system() == "Darwin":
                subprocess.call(('open', '-a', 'TextEdit', file_path))
            else:
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"打开文件失败: {str(e)}",
                parent=self.main_window,
                duration=3000
            )
    
    def fallbackOpenFile(self, file_path):
        """备用的文件打开方式"""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.call(('open', file_path))
            else:
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"无法打开文件: {str(e)}",
                parent=self.main_window,
                duration=3000
            )
    
    def uploadMissingFile(self, file_path):
        """上传缺失的文件"""
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(f"{file_name} (*{os.path.splitext(file_name)[1]})")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]
                destination_path = file_path
                
                try:
                    shutil.copy2(source_path, destination_path)
                    self.fileDeletedSignal.emit()  # 使用相同的信号来刷新
                    
                    InfoBar.success(
                        title="成功",
                        content=f"已上传文件: {file_name}",
                        parent=self.main_window,
                        duration=3000
                    )
                except Exception as e:
                    InfoBar.error(
                        title="错误",
                        content=f"上传文件失败: {str(e)}",
                        parent=self.main_window,
                        duration=3000
                    )
    
    def clearFiles(self):
        """清空所有文件项"""
        for widget in self.fileWidgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.fileWidgets.clear()

class ProjectDetailInterface(ScrollArea):
    """项目详情界面"""
    
    # 定义返回信号
    backToProjectListSignal = Signal()
    # 添加下载请求信号
    downloadRequested = Signal(str, str, str)  # url, download_path, project_name, episode_num
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.path = ''
        self.project = project
        self.card_id = -1
        self.current_project_path = None  # 添加当前项目路径存储

        self._initWidget()
    
    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setObjectName('projectDetailView')
        self.setStyleSheet("#projectDetailView {background-color: transparent;}")
    
    def loadProject(self, window, project_path, id, project, isMessage=False):
        """加载项目详情"""
        #同步主窗口
        if window:
            self.main_window = window

        # 存储当前项目路径
        self.current_project_path = project_path
        
        # 同步参数
        self.card_id = id
        self.project = project

        # 清空当前布局
        for i in reversed(range(self.vBoxLayout.count())): 
            widget = self.vBoxLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # 创建返回按钮
        backButton = PrimaryPushButton("返回项目列表", self.view)
        backButton.clicked.connect(self.backToProjectListSignal.emit)

        # 创建刷新按钮
        refreshButton = PushButton("刷新项目列表", self.view)
        refreshButton.clicked.connect(lambda: self.loadProject(self.main_window, self.current_project_path, self.card_id, self.project, isMessage=True))
        
        # 创建项目标题
        projectTitle = TitleLabel(os.path.basename(project_path), self.view)        
        projectTitle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # 创建文件列表容器
        fileListContainer = QWidget(self.view)
        fileListLayout = QVBoxLayout(fileListContainer)
        
        # 获取所有子文件夹
        subfolders = []
        for item in os.listdir(project_path):
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path) and item.isdigit():  # 只处理数字命名的文件夹
                subfolders.append((int(item), item_path))
        
        # 按数字排序
        subfolders.sort(key=lambda x: x[0])
        
        # 为每个子文件夹创建文件列表
        for folder_num, folder_path in subfolders:
            # 创建文件夹标题容器（水平布局，包含标题和编辑按钮）
            folderTitleWidget = QWidget(fileListContainer)
            folderTitleLayout = QHBoxLayout(folderTitleWidget)
            folderTitleLayout.setContentsMargins(0, 0, 0, 0)
            
            # 文件夹标题
            folderLabel = StrongBodyLabel(f"第 {folder_num} 集 - {self.project.project_subtitle[self.card_id][folder_num-1]}", folderTitleWidget)
            folderLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            # 编辑标题按钮
            editTitleButton = TransparentToolButton(FluentIcon.EDIT, folderTitleWidget)
            editTitleButton.setToolTip("编辑本集标题和视频url")
            editTitleButton.clicked.connect(lambda checked, fn=folder_num: self.editEpisodeTitle(fn))

            # 打开链接标签
            openurlButton = TransparentToolButton(FluentIcon.LINK, folderTitleWidget)
            openurlButton.setToolTip(f"打开本集链接: {self.project.project_video_url[self.card_id][folder_num-1]}")
            openurlButton.clicked.connect(lambda checked, url=self.project.project_video_url[self.card_id][folder_num-1]: self.openUrl(url))
            
            folderTitleLayout.addWidget(folderLabel)
            folderTitleLayout.addStretch()
            folderTitleLayout.addWidget(editTitleButton)
            folderTitleLayout.addWidget(openurlButton)
            
            fileListLayout.addWidget(folderTitleWidget)
            
            # 创建自定义文件列表widget
            fileListWidget = FileListWidget(self.main_window, self.project, self.card_id, folder_num, fileListContainer)
            fileListWidget.setMinimumHeight(300)
            
            # 连接文件删除信号到刷新函数
            fileListWidget.fileDeletedSignal.connect(lambda: self.delayedRefreshProject())

            # 定义期望的文件
            expected_files = [
                ("封面.jpg", FluentIcon.PHOTO, True),
                ("生肉.mp4", FluentIcon.VIDEO, True),
                ("熟肉.mp4", FluentIcon.VIDEO, False),
                ("原文.srt", FluentIcon.DOCUMENT, False),
                ("译文.srt", FluentIcon.DOCUMENT, False),
            ]
            
            # 检查文件是否存在并添加到列表
            for file_name, icon, donwload_need in expected_files:
                file_path = os.path.join(folder_path, file_name)
                file_exists = os.path.exists(file_path)
                fileListWidget.addFileItem(file_name, file_path, icon, file_exists, donwload_need)
            
            fileListLayout.addWidget(fileListWidget)
        
        # 设置布局
        self.vBoxLayout.addWidget(backButton)
        self.vBoxLayout.addWidget(refreshButton)
        self.vBoxLayout.addWidget(projectTitle)
        self.vBoxLayout.addWidget(fileListContainer)
        self.vBoxLayout.addStretch(1)

        if isMessage:
            InfoBar.success(
            title="成功",
            content=f"已刷新文件列表",
            parent=self,
            duration=1000
        )
            
    def delayedRefreshProject(self):
        """延迟刷新项目详情页面"""
        if self.current_project_path:
            self.loadProject(self.main_window, self.current_project_path, self.card_id, self.project)
    
    def editEpisodeTitle(self, folder_num):
        """编辑指定集的标题"""
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break

        dialog = CustomDoubleMessageBox(
            title=f"编辑第 {folder_num} 集的标题和视频URL", 
            input1="标题:",
            input2="URL:",
            text1=f"{self.project.project_subtitle[self.card_id][folder_num-1]}", 
            text2=f"{self.project.project_video_url[self.card_id][folder_num-1]}", 
            parent= main_window if main_window else self.window(),
            error1="请输入标题",
            error2="请输入视频url",
            )
        dialog.LineEdit_2.setText(f"{self.project.project_video_url[self.card_id][folder_num-1]}")
        if dialog.exec():
            self.project.change_subtitle(self.card_id, folder_num, dialog.LineEdit_1.text().strip())
            self.project.change_subtitle(self.card_id, folder_num, dialog.LineEdit_2.text().strip(), offset=1)
            InfoBar.success(
                title="成功",
                content=f"编辑第 {folder_num} 集标题和视频url成功",
                parent=self,
                duration=2500,
            )
            self.loadProject(self.main_window, self.current_project_path, self.card_id, self.project)
        else:
            pass
        
        
    def copyFileToFolder(self, source_path, folder_path, file_name):
        """复制文件到指定文件夹"""
        destination_path = os.path.join(folder_path, file_name)
        
        try:
            # 复制文件到目标位置
            shutil.copy2(source_path, destination_path)
            
            # 使用定时器延迟刷新界面
            QTimer.singleShot(100, self.delayedRefreshProject)
            
            InfoBar.success(
                title="成功",
                content=f"已上传文件到: {os.path.basename(folder_path)}/{file_name}",
                parent=self,
                duration=3000
            )
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"上传文件失败: {str(e)}",
                parent=self,
                duration=3000
            )
    
    def openUrl(self, url):
        QDesktopServices.openUrl(QUrl(url))