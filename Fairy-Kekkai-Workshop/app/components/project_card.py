import os
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    Flyout,
    FlyoutAnimationType,
    FlyoutViewBase,
    IconWidget,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    TransparentToolButton,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger
from ..components.dialog import (
    AddProject,
    AddProjectFromPlaylist,
    CustomDoubleMessageBox,
)
from ..resource import resource_rc  # noqa: F401
from ..service.donwload_list_service import DownloadListThread
from ..service.project_service import project
from .dialog import ProjectProgressDialog


class ProjectInterface(ScrollArea):
    openProjectDetailSignal = Signal(list)
    projectDeleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger("ProjectInterface", "project")
        self.view = QWidget(self)
        self._initWidgets()

    def _initWidgets(self):
        self.projectsLayout = QVBoxLayout(self.view)

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
        # 设置布局 - 现在只有项目列表
        self.projectsLayout.addWidget(self.topButtonCard)
        self.projectsLayout.addWidget(self.cardsContainer)
        self.projectsLayout.setSpacing(10)
        self.projectsLayout.setContentsMargins(10, 10, 10, 10)

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
        # 连接信号
        self.topButtonCard.newProjectButton.clicked.connect(self.addNewProjectCard)
        self.topButtonCard.importProjectButton.clicked.connect(self.importProjectCard)
        self.topButtonCard.newFromPlaylistButton.clicked.connect(
            self.addProjectFromPlaylist
        )
        self.topButtonCard.refreshButton.clicked.connect(
            lambda: self.refreshProjectList(isMessage=True)
        )
        self.projectDeleted.connect(self.deleteProject)

    def addProjectCard(self, project, icon, title, content, id, path, isLink=False):
        """添加项目卡片到布局"""
        project_card = ProjectCard(
            project, icon, title, content, id, path, isLink=isLink
        )
        # 修改信号连接，发送到外部的堆叠窗口管理器
        project_card.openProjectSignal.connect(self.openProjectDetailSignal)
        project_card.refreshProject.connect(
            lambda isMessage: self.refreshProjectList(isMessage)
        )
        project_card.clicked.connect(lambda: self.showProjectProgress(id, title))
        self.cardsLayout.addWidget(project_card, 0, Qt.AlignmentFlag.AlignTop)

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
            event_bus.notification_service.show_success(
                "成功", f"已创建新项目: {dialog.nameInput.text().strip()}"
            )
        else:
            pass
        self.refreshProjectList(isMessage=False)
        self.logger.info(f"添加新项目: {dialog.nameInput.text().strip()}")

    def importProjectCard(self):
        """导入新项目"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "", QFileDialog.ShowDirsOnly
        )

        if folder_path:
            if not project.is_project(folder_path):
                event_bus.notification_service.show_error(
                    "错误", f"{folder_path} 并不是一个合法的项目"
                )
                return
            title = "选择导入模式"
            content = "是否要把整个项目文件夹复制过来"
            folder_path = Path(folder_path)
            path = str(Path(project.projects_location) / folder_path.name)
            # 获取应用程序的顶级窗口
            main_window = None
            for widget in QApplication.topLevelWidgets():
                if widget.isWindow() and widget.isVisible():
                    main_window = widget
                    break

            dialog = MessageBox(title, content, main_window)
            dialog.yesButton.setText("复制")
            dialog.cancelButton.setText("只连接路径")

            if dialog.exec():
                try:
                    shutil.copytree(str(folder_path), path)
                    self.refreshProjectList(False)
                    event_bus.notification_service.show_success(
                        "成功", f"已添加 {path}"
                    )
                    self.logger.info(f"导入新项目: {path}")
                except Exception as e:
                    event_bus.notification_service.show_error("错误", f"{e}")
                    self.logger.error(f"导入新项目失败: {e}")
            else:
                project_path = cfg.linkProject.get("project_link")
                if folder_path in project_path or folder_path in project.project_path:
                    event_bus.notification_service.show_error(
                        "错误", f"已导入此路径 {folder_path}"
                    )
                    self.logger.error(f"导入新项目失败: {folder_path} 已导入此路径")
                else:
                    project_path.append(str(folder_path))
                    cfg.linkProject.set("project_link", project_path)
                    self.refreshProjectList(False)
                    event_bus.notification_service.show_success(
                        "成功", f"已添加 {folder_path}"
                    )
                    self.logger.info(f"导入新项目: {folder_path} 已连接路径")

    def addProjectFromPlaylist(self):
        """根据播放列表新建项目"""
        # 获取应用程序的顶级窗口
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                main_window = widget
                break

        dialog = AddProjectFromPlaylist(
            parent=main_window if main_window else self.window()
        )
        if dialog.exec():
            self.topButtonCard.newFromPlaylistButton.setEnabled(False)
            self.download_list_thread = DownloadListThread(
                dialog.urlInput.text(),
                dialog.nameInput.text(),
                dialog.titleInput.text(),
            )
            self.download_list_thread.finished_signal.connect(
                self.onDownloadListFinished
            )
            self.download_list_thread.start()

    def onDownloadListFinished(self, isSuccess, message, isAllFinished):
        """处理下载信息"""
        if isAllFinished:
            if isSuccess:
                event_bus.notification_service.show_success("成功", "项目创建完毕")
                event_bus.download_list_finished_signal.emit(True, message)
                self.logger.info(f"根据播放列表新建项目: {message}")
            else:
                event_bus.notification_service.show_success("失败", message)
                self.logger.error(f"根据播放列表新建项目失败: {message}")
            self.topButtonCard.newFromPlaylistButton.setEnabled(True)
        else:
            if isSuccess:
                if message == "已创建项目文件夹,正在下载封面":
                    self.refreshProjectList(isMessage=False)
                event_bus.notification_service.show_success("成功", message)
                self.logger.info(f"根据播放列表新建项目: {message}")
            else:
                event_bus.notification_service.show_error("错误", message)
                self.logger.error(f"根据播放列表新建项目失败: {message}")

    def refreshProjectList(self, isMessage):
        """刷新项目列表"""
        # 清空当前所有卡片
        for i in reversed(range(self.cardsLayout.count())):
            self.cardsLayout.itemAt(i).widget().setParent(None)

        # 重置卡片id
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
                isLink=project.isLink[card_id],
            )
            card_id += 1
        if isMessage:
            event_bus.notification_service.show_success("成功", "已刷新项目列表")

    def openProjectDetail(self, project_ifm):
        """打开项目详情页面"""
        self.openProjectDetailSignal.emit(project_ifm)

    def handleDownloadRequest(self, url, download_path, file_name):
        """处理下载请求"""
        # 获取主窗口
        # if hasattr(main_window, 'download_interface'):
        #     print("c")
        self.downloadRequested.emit(url, download_path, file_name)
        # main_window.downloadInterface.addDownloadFromProject(
        #     url=url,
        #     download_path=download_path,
        #     quality='best',
        #     project_name=project_name,
        #     episode_num=episode_num
        # )

    def deleteProject(self, project_path):
        isSuccess = project.delete_project(project_path)
        if isSuccess[0]:
            event_bus.notification_service.show_success(
                "成功", f"项目 {project_path} 已删除"
            )
            self.logger.info(f"删除项目: {project_path} 已删除")
        else:
            event_bus.notification_service.show_error(
                "错误", f"删除项目失败: {isSuccess[-1]}"
            )
            self.logger.error(f"删除项目失败: {project_path} {isSuccess[-1]}")
        self.refreshProjectList(isMessage=False)

    def cancelLinkProject(self, project_path):
        link_path = cfg.linkProject.get("project_link")
        link_path.remove(project_path)
        cfg.linkProject.set("project_link", link_path)
        self.refreshProjectList(isMessage=False)
        event_bus.notification_service.show_success(
            "成功", f"已解除项目 {project_path} 的连接"
        )
        self.logger.info(f"解除项目连接: {project_path} 已解除连接")

    def showProjectList(self):
        """显示项目列表页面"""
        self.stackedWidget.setCurrentWidget(self.projectListPage)

    def showProjectProgress(self, id, title):
        """显示项目进度对话框"""
        dialog = ProjectProgressDialog(
            progress=project.get_project_progress(id), title=title, parent=self
        )
        dialog.exec()


class TopButtonCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建三个按钮
        self.newProjectButton = PushButton("新建项目", self)
        self.importProjectButton = PushButton("导入项目", self)
        self.newFromPlaylistButton = PushButton("根据视频列表创建项目", self)
        self.refreshButton = PrimaryPushButton("刷新项目列表", self)

        # 设置按钮样式
        self.newProjectButton.setFixedWidth(120)
        self.importProjectButton.setFixedWidth(120)
        self.newFromPlaylistButton.setFixedWidth(200)
        self.refreshButton.setFixedWidth(120)

        # 创建水平布局
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.hBoxLayout.setSpacing(15)

        # 添加按钮到布局
        self.hBoxLayout.addWidget(self.newProjectButton)
        self.hBoxLayout.addWidget(self.importProjectButton)
        self.hBoxLayout.addWidget(self.newFromPlaylistButton)
        self.hBoxLayout.addStretch()
        self.hBoxLayout.addWidget(self.refreshButton)

        # 设置卡片高度
        self.setFixedHeight(70)


class ProjectCard(CardWidget):
    openProjectSignal = Signal(list)
    refreshProject = Signal(bool)

    def __init__(
        self, project, icon, title, content, id, path, isLink=False, parent=None
    ):
        super().__init__(parent)
        self.main_window = event_bus.project_interface
        # 同步
        self.project = project
        self.card_id = id
        self.path = path
        self.isLink = isLink

        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.titleLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.contentLabel = CaptionLabel(content, self)
        self.contentLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.openButton = PrimaryPushButton("打开项目", self)
        self.editButton = TransparentToolButton(FIF.EDIT, self)
        self.moreButton = TransparentToolButton(FIF.MORE, self)

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
        if isLink:
            self.linkButton = TransparentToolButton(FIF.LINK, self)
            self.linkButton.setToolTip(f"{self.path}")
            self.hBoxLayout.addWidget(self.linkButton, 0, Qt.AlignRight)

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
            # 修改原标题
            isSuccess_1 = project.change_name(
                f"{project.project_path[self.card_id]}/{project.project_title[self.card_id]}.txt",
                dialog.LineEdit_2.text() + ".txt",
            )
            if not isSuccess_1[0]:
                event_bus.notification_service.show_error("错误", isSuccess_1[-1])

            # 连接文件则需要特殊处理
            if self.isLink:
                link_path = cfg.linkProject.get("project_link")
                cfg.linkProject.set(
                    "project_link",
                    [
                        str(
                            Path(f"{project.project_path[self.card_id]}").with_name(
                                dialog.LineEdit_1.text()
                            )
                        )
                        if item == str(Path(f"{project.project_path[self.card_id]}"))
                        else item
                        for item in link_path
                    ],
                )

            # 修改文件名
            isSuccess_2 = project.change_name(
                f"{project.project_path[self.card_id]}", dialog.LineEdit_1.text()
            )
            if not isSuccess_2[0]:
                event_bus.notification_service.show_error("错误", isSuccess_2[-1])

            self.refreshProject.emit(False)
            if isSuccess_1[0] and isSuccess_2[0]:
                event_bus.notification_service.show_success(
                    "成功", "已修改项目文件名和原标题"
                )
        else:
            pass

    def showFlyout(self):
        flyout_view = CustomFlyoutView(self.path, isLink=self.isLink)
        flyout_view.deleteRequested.connect(self.handleDeleteRequest)
        flyout_view.cancelLinkRequested.connect(self.handleCancelLinkRequest)
        flyout = Flyout.make(
            flyout_view, self.moreButton, self, aniType=FlyoutAnimationType.PULL_UP
        )
        flyout_view.setFlyout(flyout)  # 设置Flyout引用

    def handleDeleteRequest(self, project_path):
        """处理删除请求"""
        parent = self.parent()
        while parent:
            if isinstance(parent, ProjectInterface):
                parent.deleteProject(project_path)
                break
            parent = parent.parent()

    def handleCancelLinkRequest(self, project_path):
        """处理删除请求"""
        parent = self.parent()
        while parent:
            if isinstance(parent, ProjectInterface):
                parent.cancelLinkProject(project_path)
                break
            parent = parent.parent()


class CustomFlyoutView(FlyoutViewBase):
    deleteRequested = Signal(str)
    cancelLinkRequested = Signal(str)

    def __init__(self, path, isLink=False, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.mainwindow = event_bus.project_interface
        self.isLink = isLink
        self.flyout = None  # 用于存储Flyout引用

        self.vBoxLayout = QVBoxLayout(self)
        self.openButton = PrimaryPushButton("打开项目路径")

        self.openButton.clicked.connect(self.openProjectPath)

        self.openButton.setFixedWidth(140)

        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(20, 16, 20, 16)
        self.vBoxLayout.addWidget(self.openButton)

        if isLink:
            self.cancelLinkButton = PushButton("取消项目连接")
            self.cancelLinkButton.setFixedWidth(140)
            self.cancelLinkButton.clicked.connect(self.cancelLinkProjectConfirm)
            self.vBoxLayout.addWidget(self.cancelLinkButton)
        else:
            self.deleteButton = PushButton("永久删除项目")
            self.deleteButton.setFixedWidth(140)
            self.deleteButton.clicked.connect(self.delateProjectConfirm)
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
            event_bus.notification_service.show_success(
                "错误", f"路径不存在: {self.path}"
            )

    def delateProjectConfirm(self):
        """永久删除项目"""
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
            self.deleteRequested.emit(str(self.path))
        else:
            pass

    def cancelLinkProjectConfirm(self):
        """取消项目连接"""
        if self.flyout:
            self.flyout.hide()  # 先关闭Flyout

        title = "确认取消连接"
        content = "确定要取消连接项目吗？此操作并不会删除文件。"

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
            self.cancelLinkRequested.emit(str(self.path))
        else:
            pass
