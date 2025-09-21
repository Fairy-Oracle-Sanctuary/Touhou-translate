# coding:utf-8
from qfluentwidgets import (SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, isDarkTheme, setFont)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCardGroup as CardGroup
from qfluentwidgets import InfoBar, TitleLabel, ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, PushButton, TransparentToolButton, FluentIcon, PrimaryPushButton
from qframelesswindow.utils import getSystemAccentColor

from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout, QVBoxLayout

from ..service.project import Project
from .dialog import AddProject

class ProjectInterface(ScrollArea):
    # 定义信号，用于通知主窗口切换页面    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.projectsLayout = QVBoxLayout(self.view)
        
        # 创建顶部按钮卡片
        self.topButtonCard = TopButtonCard()
        self.topButtonCard.newProjectButton.clicked.connect(self.addNewProjectCard)
        # self.topButtonCard.newFromPlaylistButton.clicked.connect(self.addProjectFromPlaylist)
        self.topButtonCard.refreshButton.clicked.connect(self.refreshProjectList)
        
        # 项目卡片容器
        self.cardsContainer = QWidget()
        self.cardsLayout = QVBoxLayout(self.cardsContainer)
        self.cardsLayout.setSpacing(10)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 设置主布局
        self.projectsLayout.addWidget(self.topButtonCard)
        self.projectsLayout.addWidget(self.cardsContainer)
        self.projectsLayout.setSpacing(10)
        self.projectsLayout.setContentsMargins(10, 10, 10, 10)
        
        # 初始化项目卡片
        self.project = Project()
        self.refreshProjectList()
        
        self._initWidget()

    def _initWidget(self):
        self.setWidget(self.view)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.resize(780, 800)
        self.setObjectName("projectInterface")
        self.enableTransparentBackground()
    
    def addNewProjectCard(self):
        """添加新的项目卡片"""
        dialog = AddProject(self)
        if dialog.exec():
            dialog.yesButton.setDisabled(True)
            self.project.creat_files(
                dialog.nameInput.text().strip(),
                int(dialog.numInput.text().strip()),
                dialog.titleInput.text().strip(),                
            )
            InfoBar.success(
            title="成功",
            content=f"已创建新项目: {dialog.nameInput.text().strip()}",
            parent=self,
            duration=3000,
            )
        else:
            pass
        
    
    def addProjectFromPlaylist(self):
        """根据播放列表新建项目 - 触发页面跳转"""
        # 发出信号，通知主窗口切换到播放列表界面
        self.switchToPlaylistInterface.emit()
    
    def refreshProjectList(self):
        """刷新项目列表"""
        # 清空当前所有卡片
        for i in reversed(range(self.cardsLayout.count())): 
            self.cardsLayout.itemAt(i).widget().setParent(None)
        
        # 重新加载项目
        self.project = Project()
        for project_num in range(len(self.project.project_title)):
            self.addProjectCard(
                ":/qfluentwidgets/images/logo.png", 
                self.project.project_name[project_num], 
                self.project.project_title[project_num]
            )
        InfoBar.success(
        title="成功",
        content="已刷新项目列表",
        parent=self,
        )

    def addProjectCard(self, icon, title, content):
        """添加项目卡片到布局"""
        project_card = ProjectCard(icon, title, content)
        self.cardsLayout.addWidget(project_card, 0, Qt.AlignmentFlag.AlignTop)


class TopButtonCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建三个按钮
        self.newProjectButton = PushButton('新建项目', self)
        self.newFromPlaylistButton = PushButton('根据播放列表新建项目', self)
        self.refreshButton = PrimaryPushButton('刷新项目列表', self)
        
        # 设置按钮样式
        self.newProjectButton.setFixedWidth(120)
        self.newFromPlaylistButton.setFixedWidth(180)
        self.refreshButton.setFixedWidth(120)
        
        # 创建水平布局
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.hBoxLayout.setSpacing(15)
        
        # 添加按钮到布局
        self.hBoxLayout.addWidget(self.newProjectButton)
        self.hBoxLayout.addWidget(self.newFromPlaylistButton)
        self.hBoxLayout.addStretch(1)  # 添加弹性空间
        self.hBoxLayout.addWidget(self.refreshButton)
        
        # 设置卡片高度
        self.setFixedHeight(70)


class ProjectCard(CardWidget):
    def __init__(self, icon, title, content, parent=None):
        super().__init__(parent)
        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.openButton = PushButton('Open', self)
        self.moreButton = TransparentToolButton(FluentIcon.MORE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

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
        self.hBoxLayout.addWidget(self.moreButton, 0, Qt.AlignRight)

        self.moreButton.setFixedSize(32, 32)