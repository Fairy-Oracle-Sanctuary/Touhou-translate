# coding:utf-8
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, 
                           PushButton, PrimaryPushButton, FluentIcon, StrongBodyLabel, 
                        InfoBar, TitleLabel, SubtitleLabel, ListWidget, TransparentToolButton,
                        FlowLayout, MessageBox, isDarkTheme, PrimaryToolButton)
from PySide6.QtCore import Qt, Signal, QUrl, QTimer, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidgetItem, QFileDialog, QHBoxLayout, QLabel, QFrame, QApplication
import os
import shutil
import subprocess
import platform
import requests

from ..service.project_service import project

from ..common.event_bus import event_bus
from ..common.events import EventBuilder

from ..components.dialog import CustomMessageBox, CustomDoubleMessageBox, CustomTripleMessageBox

class ProjectDetailInterface(ScrollArea):
    """项目详情界面"""
    
    # 定义返回信号
    backToProjectListSignal = Signal()
    # 图片下载信号
    downloadPic = Signal(str, str)  
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)

        self.vBoxLayout = QVBoxLayout(self.view)

        self.path = ''
        self.card_id = -1
        self.current_project_path = None  # 添加当前项目路径存储

        self._initWidgets()
    
    def _initWidgets(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setObjectName('projectDetailView')
        self.enableTransparentBackground()   

        #连接信号
        self.downloadPic.connect(lambda pic_url, save_path: self.downloadPicture(pic_url, save_path))
    
    def downloadPicture(self, pic_url, save_path):
        # https://i.ytimg.com/vi/4r2guMZPVJw/maxresdefault.jpg
        self.download_image(f"https://i.ytimg.com/vi/{pic_url}/maxresdefault.jpg", save_path)

    def download_image(self, image_url, save_path):
        """使用多线程下载图片"""
        # 创建并启动下载线程
        self.download_thread = ImageDownloadThread(image_url, save_path)
        self.download_thread.downloadFinished.connect(self.on_image_download_finished)
        self.download_thread.start()
        
        # 显示下载中的提示
        event_bus.notification_service.show_info("开始下载", f"正在下载图片...")

    def on_image_download_finished(self, success, message, save_path):
        """图片下载完成回调"""
        if success:
            event_bus.notification_service.show_success("成功", f"图片已下载到: {save_path}")
            # 刷新项目详情页面
            self.loadProject(self.current_project_path, self.card_id, project)
        else:
            event_bus.notification_service.show_error("错误", message)

    def _clearLayout(self, layout):
        """递归清空布局中的所有控件"""
        if layout is None:
            return
            
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget is not None:
                widget.deleteLater()
            else:
                # 如果是子布局，递归清空
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clearLayout(sub_layout)            
                    
    def loadProject(self, project_path, id, isMessage=False):
        """加载项目详情"""
        project.__init__()

        # 存储当前项目路径
        self.current_project_path = project_path
        
        # 同步参数
        self.card_id = id

        # 清空当前布局
        try:
            # 递归删除所有子控件
            self._clearLayout(self.vBoxLayout)
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"刷新时出错: {str(e).strip()}")     
            self.backToProjectListSignal.emit()

        # 创建返回按钮
        backButton = PrimaryPushButton("返回项目列表", self.view)
        backButton.clicked.connect(self.backToProjectListSignal.emit)

        # 创建刷新按钮
        refreshButton = PushButton("刷新项目列表", self.view)
        refreshButton.clicked.connect(lambda: self.loadProject(self.current_project_path, self.card_id, isMessage=True))
        
        # 创建项目标题
        projectTitle = TitleLabel(os.path.basename(project_path), self.view) 
        projectTitle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # 创建文件列表容器
        fileListContainer = QWidget(self.view)
        fileListLayout = QVBoxLayout(fileListContainer)
        
        # 底部增加集数按钮
        hBoxLayout = QHBoxLayout()
        addButtonBottom = PrimaryToolButton(FluentIcon.ADD)
        addButtonBottom.setToolTip("插入新的一集")
        addButtonBottom.clicked.connect(lambda checked, fn=len(project.project_subtitle[self.card_id])+1: self.addEpisode(fn))
        hBoxLayout.addWidget(addButtonBottom)

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
            folderLabel = StrongBodyLabel(f"第 {folder_num} 集 - {project.project_subtitle[self.card_id][folder_num-1]}", folderTitleWidget)
            folderLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            # 插入按钮
            addEpisodeButton = TransparentToolButton(FluentIcon.ADD, folderTitleWidget)
            addEpisodeButton.setToolTip("在这之前插入新的一集")
            addEpisodeButton.clicked.connect(lambda checked, fn=folder_num: self.addEpisode(fn))

            # 编辑标题按钮
            editTitleButton = TransparentToolButton(FluentIcon.EDIT, folderTitleWidget)
            editTitleButton.setToolTip("编辑本集标题和视频url")
            editTitleButton.clicked.connect(lambda checked, fn=folder_num: self.editEpisodeTitle(fn))

            # 打开链接标签
            openurlButton = TransparentToolButton(FluentIcon.LINK, folderTitleWidget)
            openurlButton.setToolTip(f"打开本集链接: {project.project_video_url[self.card_id][folder_num-1]}")
            openurlButton.clicked.connect(lambda checked, url=project.project_video_url[self.card_id][folder_num-1]: self.openUrl(url))
            
            folderTitleLayout.addWidget(folderLabel)
            folderTitleLayout.addWidget(addEpisodeButton)
            folderTitleLayout.addWidget(editTitleButton)
            folderTitleLayout.addWidget(openurlButton)
            
            fileListLayout.addWidget(folderTitleWidget)
            
            # 创建自定义文件列表widget
            fileListWidget = FileListWidget(self.view, self.card_id, folder_num, fileListContainer)
            fileListWidget.setMinimumHeight(300)
            
            # 连接文件删除信号到刷新函数
            # fileListWidget.fileDeleted.connect(self.delayedRefreshProject)

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
        self.vBoxLayout.addLayout(hBoxLayout)
        self.vBoxLayout.addStretch(1)
        event_bus.project_detail_interface = self.view

        if isMessage:
            event_bus.notification_service.show_success("成功", f"已刷新文件列表")
            
    def delayedRefreshProject(self):
        """延迟刷新项目详情页面"""
        if self.current_project_path:
            self.loadProject(self.current_project_path, self.card_id, isMessage=False)
    
    def addEpisode(self, folder_num):
        """增加新集"""
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break
        
        subtitle_isTranslated = project.project_subtitle_isTranslated[self.card_id]
        if subtitle_isTranslated:
            dialog = CustomTripleMessageBox(
                title=f"在第 {folder_num} 集处插入",
                input1="原标题:",
                input2="翻译后标题:",
                input3="视频URL:",
                text1="请输入原标题",
                text2="请输入翻译后标题",
                text3="请输入视频URL",
                parent= main_window if main_window else self.window(),
                error1="请输入原标题",
                error2="请输入翻译后标题",
                error3="请输入视频URL",
            )
        else:
            dialog = CustomDoubleMessageBox(
                title=f"在第 {folder_num} 集处插入",
                input1="原标题:",
                input2="视频URL:",
                text1="请输入原标题",
                text2="请输入视频URL",
                parent= main_window if main_window else self.window(),
                error1="请输入原标题",
                error2="请输入视频URL",
            )

        if dialog.exec():
            if subtitle_isTranslated:
                result = project.addEpisode(
                    self.card_id, 
                    folder_num, 
                    dialog.LineEdit_1.text().strip(),
                    dialog.LineEdit_2.text().strip(),
                    dialog.LineEdit_3.text().strip(),
                    isTranslated=True
                    )
            else:
                result = project.addEpisode(
                    self.card_id, 
                    folder_num, 
                    dialog.LineEdit_1.text().strip(),
                    "",
                    dialog.LineEdit_2.text().strip(),
                    isTranslated=False
                    )
       
            if result[0]:
                self.loadProject(self.current_project_path, self.card_id, isMessage=False)
                event_bus.notification_service.show_success("成功", f"已插入新的一集")
            else:
                event_bus.notification_service.show_error("错误", result[-1])
        else:
            pass

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
            text1=f"{project.project_subtitle[self.card_id][folder_num-1]}", 
            text2=f"{project.project_video_url[self.card_id][folder_num-1]}", 
            parent= main_window if main_window else self.window(),
            error1="请输入标题",
            error2="请输入视频url",
            )
        dialog.LineEdit_1.setText(f"{project.project_subtitle[self.card_id][folder_num-1]}")
        dialog.LineEdit_2.setText(f"{project.project_video_url[self.card_id][folder_num-1]}")
        if dialog.exec():
            project.change_subtitle(self.card_id, folder_num, dialog.LineEdit_1.text().strip())
            project.change_subtitle(self.card_id, folder_num, dialog.LineEdit_2.text().strip(), offset=1)
            event_bus.notification_service.show_success("成功", f"编辑第 {folder_num} 集标题和视频url成功")
            self.loadProject(self.current_project_path, self.card_id)
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
            
            event_bus.notification_service.show_success("成功", f"已上传文件到: {os.path.basename(folder_path)}/{file_name}")
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"上传文件失败: {str(e)}")
    
    def openUrl(self, url):
        QDesktopServices.openUrl(QUrl(url))

class ImageDownloadThread(QThread):
    """图片下载线程"""
    
    # 定义信号
    downloadFinished = Signal(bool, str, str)  # 成功/失败, 消息, 保存路径
    
    def __init__(self, image_url, save_path, parent=None):
        super().__init__(parent)
        self.image_url = image_url
        self.save_path = save_path
    
    def run(self):
        """执行下载任务"""
        try:
            # 发送GET请求
            response = requests.get(self.image_url)
            response.raise_for_status()  # 如果请求失败会抛出异常
            
            # 以二进制写入模式打开文件
            with open(self.save_path, "wb") as f:
                # 将响应的二进制内容写入文件
                f.write(response.content)
            
            self.downloadFinished.emit(True, f"图片成功下载并保存到: {self.save_path}", self.save_path)
            
        except requests.exceptions.RequestException as e:
            self.downloadFinished.emit(False, f"下载图片时出错: {e}", self.save_path)
        except Exception as e:
            self.downloadFinished.emit(False, f"发生未知错误: {e}", self.save_path)

class FileItemWidget(QFrame):
    """自定义文件项widget"""
    # fileDeleted = Signal()
    def __init__(self, window, card_id, folder_num, file_name, file_path, icon, file_exists, donwload_need, parent=None):
        super().__init__(parent)
        self.main_window = window
        self.card_id = card_id
        self.folder_num = folder_num
        self.file_name = file_name
        self.file_path = file_path
        self.file_exists = file_exists
        self.download_need = donwload_need
        
        self.setFixedHeight(60)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        if not isDarkTheme():
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
        else:
            self.setStyleSheet("""
                FileItemWidget {
                    border: 1px solid #404040;
                    border-radius: 5px;
                    margin: 2px;
                    padding: 5px;
                    background-color: #323232;
                }
                FileItemWidget:hover {
                    background-color: #2a2a2a;
                }
            """)

        self._initUI(icon)
    
    def _initUI(self, icon):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 文件图标和名称
        iconWidget = IconWidget(icon.icon(), self)
        fileNameLabel = BodyLabel(self.file_name, self)
        if not isDarkTheme():
            fileNameLabel.setStyleSheet("""
                margin-left: 10px;
                color: black;
            """)
        else:
            fileNameLabel.setStyleSheet("""
                margin-left: 10px;
                color: white;
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
        dialog = MessageBox(
            "确认删除",
            f"确定要删除文件 '{self.file_name}' 吗？此操作不可撤销。",
            self.window()
        )

        dialog.yesButton.setText("确定")
        dialog.cancelButton.setText("取消")
        
        if dialog.exec():
            try:
                os.remove(self.file_path)
                # 发射文件删除信号
                parent = self.parent()
                while parent:
                    if isinstance(parent, ProjectDetailInterface):
                        parent.delayedRefreshProject()
                        break
                    parent = parent.parent()
                event_bus.notification_service.show_success("成功", f"已删除文件: {self.file_name}")
            except Exception as e:
                event_bus.notification_service.show_error("错误", f"删除文件时出错: {str(e)}")

    def donwloadFile(self):
        """下载缺失的文件"""

        file_ext = os.path.splitext(self.file_name)[1].lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png']:
            # 下载封面 这个函数就不归进donwload_interface.py里了
            self.donwloadPic()
        else:
            # 下载视频
            self.downloadVideo()
    
    def donwloadPic(self):
        download_path = os.path.dirname(self.file_path)

        dialog = CustomMessageBox(
            title=f"下载第 {self.folder_num} 集封面",
            text="请输入视频id: https://www.youtube.com/watch?v=",
            parent=self.window(),
            minwidth=450,
        )
        v = project.project_video_url[self.card_id][self.folder_num-1].split("=")[-1]
        if v and "youtube" not in v:
            dialog.LineEdit.setText(v)

        
        if dialog.exec():
            video_url = dialog.LineEdit.text().strip()
            if video_url:
                # 通过信号发送下载请求
                download_path = self.file_path

                # 找到父级ProjectDetailInterface并发射信号
                parent = self.parent()
                while parent:
                    if isinstance(parent, ProjectDetailInterface):
                        parent.downloadPic.emit(
                            video_url, download_path
                        )
                        break
                    parent = parent.parent()

    def downloadVideo(self):
        download_path = os.path.dirname(self.file_path)

        dialog = CustomMessageBox(
            title=f"下载第 {self.folder_num} 集生肉视频",
            text="请输入视频id: https://www.youtube.com/watch?v=",
            parent=self.window(),
            minwidth=450,
        )
        v = project.project_video_url[self.card_id][self.folder_num-1].split("=")[-1]
        if v and "youtube" not in v:
            dialog.LineEdit.setText(v)

        if dialog.exec():
            video_url = "https://www.youtube.com/watch?v=" + dialog.LineEdit.text().strip()
            if video_url:
                # 通过信号发送下载请求
                download_path = os.path.dirname(self.file_path) + '\生肉.mp4'
                print(download_path)
                # 发射信号
                event_bus.download_requested.emit(
                    EventBuilder.download_video(
                        video_url,
                        download_path,
                    )
                )
                # 显示下载中的提示
                event_bus.notification_service.show_info("开始下载", f"正在下载视频: {video_url}")

class FileListWidget(QWidget):
    """自定义文件列表widget"""
    def __init__(self, window, card_id, folder_num, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.main_window = window
        self.card_id = card_id
        self.folder_num = folder_num
        self.fileWidgets = []

    def addFileItem(self, file_name, file_path, icon, file_exists, download_need):
        """添加文件项"""
        fileWidget = FileItemWidget(self.main_window, self.card_id, self.folder_num, file_name, file_path, icon, file_exists, download_need, self)
        fileWidget.setCursor(Qt.PointingHandCursor)
        
        # 连接点击事件（整个widget的点击）
        fileWidget.mousePressEvent = lambda event: self.handleFileItemClick(fileWidget)
        
        self.layout.addWidget(fileWidget)
        self.fileWidgets.append(fileWidget)
        
        # 连接删除信号
        # fileWidget.deleteBtn.clicked.connect(event_bus.fileDeletedSignal.emit)
    

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
            event_bus.notification_service.show_error("错误", f"打开文件失败: {str(e)}")
    
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
            event_bus.notification_service.show_error("错误", f"无法打开文件: {str(e)}")
    
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

                    # 上传成功后刷新页面
                    parent = self.parent()
                    while parent:
                        if isinstance(parent, ProjectDetailInterface):
                            # 调用ProjectDetailInterface的刷新方法
                            parent.delayedRefreshProject()
                            break
                        parent = parent.parent()
                    
                    event_bus.notification_service.show_success("成功", f"已上传文件: {file_name}")
                except Exception as e:
                    event_bus.notification_service.show_success("错误", f"上传文件失败: {str(e)}")
    
    def clearFiles(self):
        """清空所有文件项"""
        for widget in self.fileWidgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.fileWidgets.clear()

