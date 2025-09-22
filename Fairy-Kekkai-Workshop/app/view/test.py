# coding:utf-8
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, 
                           PushButton, PrimaryPushButton, FluentIcon, StrongBodyLabel, 
                        InfoBar, TitleLabel, SubtitleLabel, ListWidget)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidgetItem, QFileDialog, QHBoxLayout
import os
import shutil
import subprocess
import platform

class ProjectDetailInterface(ScrollArea):
    """项目详情界面"""
    
    # 定义返回信号
    backToProjectListSignal = Signal()
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.path = ''
        self.project = project
        self.card_id = -1
        # print(self.project.project_subtitle[0])

        self._initWidget()
    
    def _initWidget(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setObjectName('projectDetailView')
        self.setStyleSheet("#projectDetailView {background-color: transparent;}")
    
    def loadProject(self, project_path, id, project):
        """加载项目详情"""
        # 同步参数
        self.card_id = id
        self.project = project
        # print(self.card_id)

        # 清空当前布局
        for i in reversed(range(self.vBoxLayout.count())): 
            widget = self.vBoxLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # 创建返回按钮
        backButton = PrimaryPushButton("返回项目列表", self.view)
        backButton.clicked.connect(self.backToProjectListSignal.emit)
        
        # 创建项目标题
        projectTitle = TitleLabel(os.path.basename(project_path), self.view)
                
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
            # 创建文件夹标题
            folderLabel = StrongBodyLabel(f"第 {folder_num} 集 - {self.project.project_subtitle[self.card_id][folder_num-1]}", fileListContainer)
            fileListLayout.addWidget(folderLabel)
            
            # 创建文件列表
            fileListWidget = ListWidget(fileListContainer)
            fileListWidget.setMinimumHeight(200)

            # 定义期望的文件
            expected_files = [
                ("封面.jpg", FluentIcon.PHOTO),
                ("生肉.mp4", FluentIcon.VIDEO),
                ("熟肉.mp4", FluentIcon.VIDEO),
                ("原文.srt", FluentIcon.DOCUMENT),
                ("译文.srt", FluentIcon.DOCUMENT),
            ]
            
            # 检查文件是否存在
            for file_name, icon in expected_files:
                file_path = os.path.join(folder_path, file_name)
                item = QListWidgetItem(file_name)
                item.setData(Qt.UserRole, file_path)  # 存储文件路径
                
                if os.path.exists(file_path):
                    item.setIcon(icon.icon())
                    item.setForeground(Qt.black)
                else:
                    item.setIcon(FluentIcon.CLOSE.icon())
                    item.setForeground(Qt.red)
                    item.setToolTip("文件缺失 - 点击上传")
                
                fileListWidget.addItem(item)
            
            # 连接文件列表的点击事件
            fileListWidget.itemClicked.connect(lambda item: self.handleFileItemClick(item, project_path))
            
            fileListLayout.addWidget(fileListWidget)
        
        # 设置布局
        self.vBoxLayout.addWidget(backButton)
        self.vBoxLayout.addWidget(projectTitle)
        self.vBoxLayout.addWidget(fileListContainer)
    
    def handleFileItemClick(self, item, project_path):
        """处理文件项点击事件"""
        file_path = item.data(Qt.UserRole)
        
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
            self.uploadMissingFile(file_path, project_path)

    def openTextFile(self, file_path):
        """使用文本编辑器打开文件"""
        try:
            # 根据不同平台使用不同的方式打开文本文件
            if platform.system() == "Windows":
                # 在Windows上，使用记事本打开
                os.system(f'notepad "{file_path}"')
            elif platform.system() == "Darwin":
                # 在macOS上，使用TextEdit打开
                subprocess.call(('open', '-a', 'TextEdit', file_path))
            else:
                # 在Linux上，使用xdg-open打开
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            InfoBar.error(
                title="错误",
                content=f"打开文件失败: {str(e)}",
                parent=self,
                duration=3000
            )

    def uploadMissingFile(self, file_path, project_path):
        """上传缺失的文件"""
        # 获取文件目录和文件名
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        # 打开文件选择对话框
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(f"{file_name} (*{os.path.splitext(file_name)[1]})")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]
                destination_path = file_path
                
                try:
                    # 复制文件到目标位置
                    shutil.copy2(source_path, destination_path)
                    
                    # 刷新项目详情页面
                    self.loadProject(project_path, self.card_id, self.project)
                    
                    InfoBar.success(
                        title="成功",
                        content=f"已上传文件: {file_name}",
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
    
    def uploadFile(self, project_path):
        """上传文件到项目"""
        # 打开文件选择对话框
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("视频文件 (*.mp4);;字幕文件 (*.srt);;所有文件 (*)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = selected_files[0]
                file_name = os.path.basename(source_path)
                
                # 创建选择文件夹的菜单
                from qfluentwidgets import RoundMenu, Action, MenuAnimationType
                menu = RoundMenu(parent=self)
                
                # 获取所有子文件夹
                subfolders = []
                for item in os.listdir(project_path):
                    item_path = os.path.join(project_path, item)
                    if os.path.isdir(item_path) and item.isdigit():
                        subfolders.append((int(item), item_path))
                
                # 按数字排序
                subfolders.sort(key=lambda x: x[0])
                
                # 为每个文件夹添加菜单项
                for folder_num, folder_path in subfolders:
                    action = Action(f"第 {folder_num} 集")
                    action.triggered.connect(
                        lambda checked, path=folder_path: self.copyFileToFolder(source_path, path, file_name, project_path)
                    )
                    menu.addAction(action)
                
                # 显示菜单
                menu.exec(menu.getPopupPos(self.mapToGlobal(self.rect().center())), aniType=MenuAnimationType.DROP_DOWN)
    
    def copyFileToFolder(self, source_path, folder_path, file_name, project_path):
        """复制文件到指定文件夹"""
        destination_path = os.path.join(folder_path, file_name)
        
        try:
            # 复制文件到目标位置
            shutil.copy2(source_path, destination_path)
            
            # 刷新项目详情页面
            self.loadProject(project_path, self.card_id, self.project)
            
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