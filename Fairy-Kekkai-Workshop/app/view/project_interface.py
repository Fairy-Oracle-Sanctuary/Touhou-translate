# coding:utf-8

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ..common.event_bus import event_bus
from ..components.project_card import ProjectInterface
from .project_detail_interface import ProjectDetailInterface


class ProjectStackedInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建堆叠窗口
        self.stackedWidget = QStackedWidget(self)

        # 创建项目列表界面和项目详情界面
        self.projectInterface = ProjectInterface()
        self.projectDetailInterface = ProjectDetailInterface()

        # 添加到堆叠窗口
        self.stackedWidget.addWidget(self.projectInterface)
        self.stackedWidget.addWidget(self.projectDetailInterface)

        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stackedWidget)

        # 连接信号
        self._connectSignalToSlot()

        self.resize(780, 800)
        self.setObjectName("ProjectStackedInterface")

    def _connectSignalToSlot(self):
        """连接信号和槽"""
        # 项目界面打开项目详情的信号
        self.projectInterface.openProjectDetailSignal.connect(self.openProjectDetail)
        # 项目详情界面返回项目列表的信号
        self.projectDetailInterface.backToProjectListSignal.connect(
            self.showProjectList
        )

    def openProjectDetail(self, project_info):
        """打开项目详情页面"""
        # 加载项目详情
        self.projectDetailInterface.loadProject(project_info[0], project_info[1])
        # 切换到项目详情页面
        self.stackedWidget.setCurrentWidget(self.projectDetailInterface)
        # 通知信息
        event_bus.notification_service.show_success(
            "打开成功", f"已打开项目 {project_info[0]}"
        )

    def showProjectList(self):
        """显示项目列表页面"""
        self.stackedWidget.setCurrentWidget(self.projectInterface)

    def refreshProjectList(self, isMessage=True):
        """刷新项目列表"""
        self.projectInterface.refreshProjectList(isMessage)
