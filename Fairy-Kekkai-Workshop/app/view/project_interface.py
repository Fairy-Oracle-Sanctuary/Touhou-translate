# coding:utf-8
from qfluentwidgets import (SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, isDarkTheme, setFont)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCardGroup as CardGroup
from qfluentwidgets import InfoBar, TitleLabel, ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, PushButton, TransparentToolButton, FluentIcon, PrimaryPushButton, FlyoutViewBase, FlyoutAnimationType, Flyout, Dialog, MessageBox
from qframelesswindow.utils import getSystemAccentColor

from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout, QVBoxLayout, QStackedWidget, QApplication

import os
import shutil
from pathlib import Path

from ..service.project_service import project

from ..common.event_bus import event_bus
from ..common.events import EventBuilder

from ..components.infobar import NotificationService

from ..components.dialog import AddProject, CustomDoubleMessageBox
from .project_detail_interface import ProjectDetailInterface

class ProjectInterface(ScrollArea):
    projectDeleted = Signal(str) 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)

        self._initWidgets()

    def _initWidgets(self):
        self.projectsLayout = QVBoxLayout(self.view)
        
        # 创建堆叠窗口，用于切换项目列表和项目详情
        self.stackedWidget = QStackedWidget(self.view)
        
        # 项目列表页面
        self.projectListPage = QWidget()
        self.projectListLayout = QVBoxLayout(self.projectListPage)
        
        # 项目详情页面
        self.projectDetailInterface = ProjectDetailInterface()
        
        # 初始化页面
        self.stackedWidget.addWidget(self.projectListPage)
        self.stackedWidget.addWidget(self.projectDetailInterface)
        
        # 创建顶部按钮卡片
        self.topButtonCard = TopButtonCard()
        
        # 项目卡片容器
        self.cardsContainer = QWidget()
        self.cardsLayout = QVBoxLayout(self.cardsContainer)
        self.cardsLayout.setSpacing(10)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        # 设置项目列表页面布局
        self.projectListLayout.addWidget(self.topButtonCard)
        self.projectListLayout.addWidget(self.cardsContainer)
        self.projectListLayout.setSpacing(10)
        self.projectListLayout.setContentsMargins(10, 10, 10, 10)
        
        # 设置主布局
        self.projectsLayout.addWidget(self.stackedWidget)
        
        # 初始化项目卡片
        self.refreshProjectList(isMessage=False)

        self.setWidget(self.view)
        event_bus.project_interface = self.view
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.resize(780, 800)
        self.setObjectName("projectInterface")
        self.enableTransparentBackground()

    def _connectSignalToSlot(self):
        self.projectDetailInterface.backToProjectListSignal.connect(self.showProjectList)
        self.topButtonCard.newProjectButton.clicked.connect(self.addNewProjectCard)
        self.topButtonCard.importProjectButton.clicked.connect(self.importProjectCard)
        self.topButtonCard.refreshButton.clicked.connect(lambda: self.refreshProjectList(isMessage=True))
        self.projectDeleted.connect(self.deleteProject)

    def addNewProjectCard(self):
        """添加新的项目卡片"""
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break

        dialog = AddProject(parent=main_window if main_window else self.window())
        if dialog.exec():
            dialog.yesButton.setDisabled(True)
            project.creat_files(
                dialog.nameInput.text().strip(),
                int(dialog.numInput.text().strip()),
                dialog.titleInput.text().strip(),                
            )
            event_bus.notification_service.show_success("成功", f"已创建新项目: {dialog.nameInput.text().strip()}")
        else:
            pass
        self.refreshProjectList(isMessage=False)
        
    def importProjectCard(self):
        """导入新项目"""
        folder_path = QFileDialog.getExistingDirectory(
            self,                   
            "选择文件夹",
            "",                      
            QFileDialog.ShowDirsOnly
        )
        if not project.is_project(folder_path):
            event_bus.notification_service.show_error("错误", f"{folder_path} 并不是一个合法的项目")
            return
        if folder_path:
            try:
                shutil.copytree(f'{folder_path}', f'{project.projects_location}/{Path(folder_path).name}')
                self.refreshProjectList(False)
                event_bus.notification_service.show_success("成功", f"已添加 {folder_path}")
            except Exception as e:
                event_bus.notification_service.show_error("错误", f"{e}")

    def addProjectFromPlaylist(self):
        """根据播放列表新建项目 - 触发页面跳转"""
        # 发出信号，通知主窗口切换到播放列表界面
        self.switchToPlaylistInterface.emit()
    
    def refreshProjectList(self, isMessage):
        """刷新项目列表"""
        # 清空当前所有卡片
        for i in reversed(range(self.cardsLayout.count())): 
            self.cardsLayout.itemAt(i).widget().setParent(None)
        
        #重置卡片id
        card_id = 0

        # 重新加载项目
        project.__init__()
        for project_num in range(len(project.project_title)):
            self.addProjectCard(
                project,
                ":/app/images/logo.png", 
                project.project_name[project_num], 
                project.project_title[project_num],
                card_id,
                project.project_path[card_id],
            )
            card_id += 1
        if isMessage:
            event_bus.notification_service.show_success("成功", "已刷新项目列表")

    def addProjectCard(self, project, icon, title, content, id, path):
        """添加项目卡片到布局"""
        project_card = ProjectCard(project, icon, title, content, id, path)
        project_card.openProjectSignal.connect(self.openProjectDetail)  # 连接信号
        project_card.refreshProject.connect(lambda isMessage: self.refreshProjectList(isMessage))  # 连接信号
        self.cardsLayout.addWidget(project_card, 0, Qt.AlignmentFlag.AlignTop)

    def openProjectDetail(self, project_ifm):
        """打开项目详情页面"""
        # 加载项目详情
        self.projectDetailInterface.loadProject(project_ifm[0], project_ifm[1])

        # 切换到项目详情页面
        self.stackedWidget.setCurrentWidget(self.projectDetailInterface)

        event_bus.notification_service.show_success("打开成功", f"已打开项目 {project_ifm[0]}")

    def handleDownloadRequest(self, url, download_path, file_name):
        """处理下载请求"""
        # 获取主窗口
        # if hasattr(main_window, 'download_interface'):
        #     print("c")
        self.downloadRequested.emit(
            url, download_path, file_name
        )
        # main_window.downloadInterface.addDownloadFromProject(
        #     url=url,
        #     download_path=download_path,
        #     quality='best',
        #     project_name=project_name,
        #     episode_num=episode_num
        # )

    def deleteProject(self, project_path):
        isSuccess = project.delete_project(project_path)
        if isSuccess:
            event_bus.notification_service.show_success("成功", f"项目 {project_path} 已删除")
        else:
            event_bus.notification_service.show_error("错误", f"删除项目失败")
        self.refreshProjectList(isMessage=False)

    def showProjectList(self):
        """显示项目列表页面"""
        self.stackedWidget.setCurrentWidget(self.projectListPage)

class TopButtonCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建三个按钮
        self.newProjectButton = PushButton('新建项目', self)
        self.importProjectButton = PushButton('导入项目', self)
        # self.newFromPlaylistButton = PushButton('根据播放列表新建项目', self)
        self.refreshButton = PrimaryPushButton('刷新项目列表', self)
        
        # 设置按钮样式
        self.newProjectButton.setFixedWidth(120)
        self.importProjectButton.setFixedWidth(120)
        self.refreshButton.setFixedWidth(120)
        
        # 创建水平布局
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.hBoxLayout.setSpacing(15)
        
        # 添加按钮到布局
        self.hBoxLayout.addWidget(self.newProjectButton)
        self.hBoxLayout.addWidget(self.importProjectButton)
        # self.hBoxLayout.addWidget(self.newFromPlaylistButton)
        self.hBoxLayout.addStretch(1)  # 添加弹性空间
        self.hBoxLayout.addWidget(self.refreshButton)
        
        # 设置卡片高度
        self.setFixedHeight(70)


class ProjectCard(CardWidget):
    openProjectSignal = Signal(list)
    refreshProject = Signal(bool)
    def __init__(self, project, icon, title, content, id, path, parent=None):
        super().__init__(parent)
        self.main_window = event_bus.project_interface
        #同步
        self.project = project
        self.card_id = id
        self.path = path

        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.titleLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.contentLabel = CaptionLabel(content, self)
        self.contentLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.openButton = PrimaryPushButton('打开项目', self)
        self.editButton = TransparentToolButton(FluentIcon.EDIT, self)
        self.moreButton = TransparentToolButton(FluentIcon.MORE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.openButton.clicked.connect(self.openProject)
        self.editButton.clicked.connect(self.editProject)
        self.moreButton.clicked.connect(self.showFlyout)

        self.setFixedHeight(73)
        self.iconWidget.setFixedSize(48, 48)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.openButton.setFixedWidth(120)

        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.addWidget(self.iconWidget)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.openButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.editButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.moreButton, 0, Qt.AlignRight)

    def openProject(self):
        """打开项目"""
        self.openProjectSignal.emit([self.path, self.card_id])

    def editProject(self):
        """修改文件夹名和原标题"""
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break

        dialog = CustomDoubleMessageBox(
            title="修改项目文件名和原标题",
            input1="文件夹名:",
            input2="原标题:",
            text1=f"{project.project_name[self.card_id]}",
            text2=f"{project.project_title[self.card_id]}",
            error1="请输入文件夹名",
            error2="请输入原标题",
            parent=main_window if main_window else self.window(),
            )
        dialog.LineEdit_1.setText(f"{project.project_name[self.card_id]}")
        dialog.LineEdit_2.setText(f"{project.project_title[self.card_id]}")

        if dialog.exec():
            project.change_name(f"{project.project_path[self.card_id]}/{project.project_title[self.card_id]}.txt", dialog.LineEdit_2.text()+'.txt')
            project.change_name(f"{project.project_path[self.card_id]}", dialog.LineEdit_1.text())
            self.refreshProject.emit(False)
            event_bus.notification_service.show_success("成功", "已修改项目文件名和原标题")
        else:
            pass

    def showFlyout(self):
        flyout_view = CustomFlyoutView(self.path)
        flyout_view.deleteRequested.connect(self.handleDeleteRequest)
        flyout = Flyout.make(flyout_view, self.moreButton, self, aniType=FlyoutAnimationType.PULL_UP)
        flyout_view.setFlyout(flyout)  # 设置Flyout引用

    def handleDeleteRequest(self, project_path):
        """处理删除请求"""
        parent = self.parent()
        while parent:
            if isinstance(parent, ProjectInterface):
                parent.deleteProject(project_path)
                break
            parent = parent.parent()

class CustomFlyoutView(FlyoutViewBase):
    deleteRequested = Signal(str)
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.mainwindow = event_bus.project_interface
        self.flyout = None  # 用于存储Flyout引用

        self.vBoxLayout = QVBoxLayout(self)
        self.openButton = PrimaryPushButton('打开项目路径')
        self.deleteButton = PushButton('永久删除项目')

        self.openButton.clicked.connect(self.openProjectPath)
        self.deleteButton.clicked.connect(self.delateProjectConfirm)

        self.openButton.setFixedWidth(140)
        self.deleteButton.setFixedWidth(140)
        
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(20, 16, 20, 16)
        self.vBoxLayout.addWidget(self.openButton)
        self.vBoxLayout.addWidget(self.deleteButton)
    
    def setFlyout(self, flyout):
        """设置Flyout引用"""
        self.flyout = flyout

    def openProjectPath(self):
        """打开项目路径"""
        if self.flyout:
            self.flyout.hide()  # 先关闭Flyout
        
        if os.path.exists(self.path):
            # 使用系统默认的文件管理器打开路径
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.path))
        else:
            # 如果路径不存在，显示错误信息
            event_bus.notification_service.show_success("错误", f"路径不存在: {self.path}")
    
    def delateProjectConfirm(self):
        '''永久删除项目'''
        if self.flyout:
            self.flyout.hide()  # 先关闭Flyout
            
        title = "确认删除"
        content = "确定要删除项目吗？此操作不可撤销。"
        
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break
        
        dialog = MessageBox(title, content, main_window)
        dialog.yesButton.setText("确定")
        dialog.cancelButton.setText("取消")
        if dialog.exec():
            self.deleteRequested.emit(self.path)
        else:
            pass