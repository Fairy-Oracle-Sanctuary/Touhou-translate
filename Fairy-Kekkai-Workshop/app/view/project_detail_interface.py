# coding:utf-8
import os
import platform
import shutil
import subprocess
from pathlib import Path

import requests
from PySide6.QtCore import Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    IconWidget,
    MessageBox,
    PipsPager,
    PipsScrollButtonDisplayMode,
    PrimaryPushButton,
    PrimaryToolButton,
    PushButton,
    ScrollArea,
    SimpleCardWidget,
    StrongBodyLabel,
    TitleLabel,
    TransparentToolButton,
    isDarkTheme,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.events import EventBuilder
from ..components.dialog import (
    CustomDoubleMessageBox,
    CustomMessageBox,
    CustomTripleMessageBox,
)
from ..service.project_service import project


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

        self.path = ""
        self.card_id = -1
        self.current_project_path = None  # 添加当前项目路径存储

        # 分页相关变量
        self.current_page = 1
        self.items_per_page = cfg.get(cfg.detailProjectItemNum)
        self.total_episodes = 0
        self.subfolders = []
        self.topPipsPager = None
        self.bottomPipsPager = None

        self._initWidgets()

    def _initWidgets(self):
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setObjectName("projectDetailView")
        self.enableTransparentBackground()

        # 连接信号
        self.downloadPic.connect(
            lambda pic_url, save_path: self.downloadPicture(pic_url, save_path)
        )

    def downloadPicture(self, pic_url, save_path):
        # https://i.ytimg.com/vi/4r2guMZPVJw/maxresdefault.jpg
        self.download_image(
            f"https://i.ytimg.com/vi/{pic_url}/maxresdefault.jpg", save_path
        )

    def download_image(self, image_url, save_path):
        """使用多线程下载图片"""
        # 创建并启动下载线程
        self.download_thread = ImageDownloadThread(image_url, save_path)
        self.download_thread.downloadFinished.connect(self.on_image_download_finished)
        self.download_thread.start()

        # 显示下载中的提示
        event_bus.notification_service.show_info("开始下载", "正在下载图片...")

    def on_image_download_finished(self, success, message, save_path):
        """图片下载完成回调"""
        if success:
            event_bus.notification_service.show_success(
                "成功", f"图片已下载到: {save_path}"
            )
            # 刷新项目详情页面
            self.loadProject(
                self.current_project_path, self.card_id, project, isMessage=False
            )
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

    def get_subfolders(self, project_path):
        """获取所有子文件夹"""
        subfolders = []
        for item in os.listdir(project_path):
            item_path = os.path.join(project_path, item)
            if os.path.isdir(item_path) and item.isdigit():  # 只处理数字命名的文件夹
                subfolders.append((int(item), item_path))

        # 按数字排序
        subfolders.sort(key=lambda x: x[0])
        return subfolders

    def loadProject(self, project_path, id, isMessage=False):
        """加载项目详情"""
        project.refresh_project(id)

        self.items_per_page = cfg.get(cfg.detailProjectItemNum)

        # 存储当前项目路径
        self.current_project_path = project_path

        # 同步参数
        self.card_id = id

        # 获取所有子文件夹
        self.subfolders = self.get_subfolders(project_path)
        self.total_episodes = len(self.subfolders)

        # 清空当前布局
        try:
            # 递归删除所有子控件
            self._clearLayout(self.vBoxLayout)
        except Exception as e:
            event_bus.notification_service.show_error(
                "错误", f"刷新时出错: {str(e).strip()}"
            )
            self.backToProjectListSignal.emit()

        # 创建返回按钮
        backButton = PrimaryPushButton("返回项目列表", self.view)
        backButton.clicked.connect(self.backToProjectListSignal.emit)

        # 创建刷新按钮
        refreshButton = PushButton("刷新项目列表", self.view)
        refreshButton.clicked.connect(
            lambda: self.loadProject(
                self.current_project_path, self.card_id, isMessage=True
            )
        )

        # 创建项目标题
        projectTitle = TitleLabel(os.path.basename(project_path), self.view)
        projectTitle.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        # 创建分页信息标签
        total_pages = (
            self.total_episodes + self.items_per_page - 1
        ) // self.items_per_page
        self.current_page = (
            total_pages if self.current_page > total_pages else self.current_page
        )
        page_info_label = BodyLabel(
            f"共 {self.total_episodes} 集，第 {self.current_page}/{total_pages} 页",
            self.view,
        )

        # 创建顶部PipsPager分页控件
        if self.total_episodes > self.items_per_page:
            self.topPipsPager = PipsPager(self)
            self.topPipsPager.setPageNumber(total_pages)
            self.topPipsPager.setCurrentIndex(self.current_page - 1)
            self.topPipsPager.setVisibleNumber(total_pages if total_pages <= 5 else 5)
            self.topPipsPager.setNextButtonDisplayMode(
                PipsScrollButtonDisplayMode.ALWAYS
            )
            self.topPipsPager.setPreviousButtonDisplayMode(
                PipsScrollButtonDisplayMode.ALWAYS
            )
            self.topPipsPager.currentIndexChanged.connect(self.on_pips_page_changed)

        # 创建文件列表容器
        fileListContainer = QWidget(self.view)
        fileListLayout = QVBoxLayout(fileListContainer)

        # 计算当前页的起始和结束索引
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = min(start_index + self.items_per_page, self.total_episodes)

        # 为当前页的子文件夹创建文件列表
        for i in range(start_index, end_index):
            folder_num, folder_path = self.subfolders[i]
            self._create_episode_widget(folder_num, folder_path, fileListLayout)

        # 创建底部PipsPager分页控件
        if self.total_episodes > self.items_per_page:
            self.bottomPipsPager = PipsPager(self)
            self.bottomPipsPager.setPageNumber(total_pages)
            self.bottomPipsPager.setCurrentIndex(self.current_page - 1)
            self.bottomPipsPager.setVisibleNumber(
                total_pages if total_pages <= 5 else 5
            )
            self.bottomPipsPager.setNextButtonDisplayMode(
                PipsScrollButtonDisplayMode.ALWAYS
            )
            self.bottomPipsPager.setPreviousButtonDisplayMode(
                PipsScrollButtonDisplayMode.ALWAYS
            )
            self.bottomPipsPager.currentIndexChanged.connect(self.on_pips_page_changed)

        # 底部增加集数按钮
        hBoxLayout = QHBoxLayout()
        if self.current_page == total_pages:
            addButtonBottom = PrimaryToolButton(FIF.ADD)
            addButtonBottom.setToolTip("插入新的一集")
            addButtonBottom.clicked.connect(
                lambda checked,
                fn=len(project.project_subtitle[self.card_id]) + 1: self.addEpisode(fn)
            )
            hBoxLayout.addWidget(addButtonBottom)

        # 设置布局
        self.vBoxLayout.addWidget(backButton)
        self.vBoxLayout.addWidget(refreshButton)
        self.vBoxLayout.addWidget(projectTitle)
        self.vBoxLayout.addWidget(page_info_label)

        # 添加顶部PipsPager分页控件
        if self.topPipsPager:
            top_pager_layout = QHBoxLayout()
            top_pager_layout.addStretch(1)
            top_pager_layout.addWidget(self.topPipsPager)
            top_pager_layout.addStretch(1)
            self.vBoxLayout.addLayout(top_pager_layout)

        self.vBoxLayout.addWidget(fileListContainer)

        # 添加底部PipsPager分页控件
        if self.bottomPipsPager:
            bottom_pager_layout = QHBoxLayout()
            bottom_pager_layout.addStretch(1)
            bottom_pager_layout.addWidget(self.bottomPipsPager)
            bottom_pager_layout.addStretch(1)
            self.vBoxLayout.addLayout(bottom_pager_layout)

        self.vBoxLayout.addLayout(hBoxLayout)
        self.vBoxLayout.addStretch(1)
        event_bus.project_detail_interface = self.view

        if isMessage:
            event_bus.notification_service.show_success("成功", "已刷新文件列表")

    def _create_episode_widget(self, folder_num, folder_path, parent_layout):
        """创建单集的小部件"""
        # 创建文件夹标题容器（水平布局，包含标题和编辑按钮）
        folderTitleWidget = QWidget()
        folderTitleLayout = QHBoxLayout(folderTitleWidget)
        folderTitleLayout.setContentsMargins(0, 0, 0, 0)

        # 文件夹标题
        folderLabel = StrongBodyLabel(
            f"第 {folder_num} 集 - {project.project_subtitle[self.card_id][folder_num - 1]}",
            folderTitleWidget,
        )
        folderLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        # 插入按钮
        addEpisodeButton = TransparentToolButton(FIF.ADD, folderTitleWidget)
        addEpisodeButton.setToolTip("在这之前插入新的一集")
        addEpisodeButton.clicked.connect(
            lambda checked, fn=folder_num: self.addEpisode(fn)
        )

        # 删除按钮
        deleteButton = TransparentToolButton(FIF.DELETE, folderTitleWidget)
        deleteButton.setToolTip("删除这一集(不可撤销)")
        if len(self.subfolders) <= 1:
            deleteButton.setDisabled(True)
        deleteButton.clicked.connect(
            lambda checked, fn=folder_num: self.deleteEpisode(fn)
        )

        # 编辑标题按钮
        editTitleButton = TransparentToolButton(FIF.EDIT, folderTitleWidget)
        editTitleButton.setToolTip("编辑本集标题和视频url")
        editTitleButton.clicked.connect(
            lambda checked, fn=folder_num: self.editEpisodeTitle(fn)
        )

        # 打开链接标签
        openurlButton = TransparentToolButton(FIF.LINK, folderTitleWidget)
        openurlButton.setToolTip(
            f"打开本集链接: {project.project_video_url[self.card_id][folder_num - 1]}"
        )
        openurlButton.clicked.connect(
            lambda checked,
            url=project.project_video_url[self.card_id][folder_num - 1]: self.openUrl(
                url
            )
        )

        folderTitleLayout.addWidget(folderLabel)
        folderTitleLayout.addWidget(addEpisodeButton)
        folderTitleLayout.addWidget(deleteButton)
        folderTitleLayout.addWidget(editTitleButton)
        folderTitleLayout.addWidget(openurlButton)

        parent_layout.addWidget(folderTitleWidget)

        # 创建自定义文件列表widget
        fileListWidget = FileListWidget(self.view, self.card_id, folder_num)
        fileListWidget.setMinimumHeight(270)

        # 定义期望的文件
        expected_files = [
            ("封面.jpg", FIF.PHOTO, True, False, False, False),
            ("生肉.mp4", FIF.VIDEO, True, False, False, False),
            ("熟肉.mp4", FIF.VIDEO, False, False, False, True),
            ("原文.srt", FIF.DOCUMENT, False, True, False, False),
            ("译文.srt", FIF.DOCUMENT, False, False, True, False),
        ]

        # 检查文件是否存在并添加到列表
        for (
            file_name,
            icon,
            donwload_need,
            extract_need,
            translate_need,
            ffmpeg_need,
        ) in expected_files:
            file_path = os.path.join(folder_path, file_name)
            file_exists = os.path.exists(file_path)
            fileListWidget.addFileItem(
                file_name,
                file_path,
                icon,
                file_exists,
                donwload_need,
                extract_need,
                translate_need,
                ffmpeg_need,
            )

        parent_layout.addWidget(fileListWidget)

    def on_pips_page_changed(self, index):
        """PipsPager分页改变时的处理"""
        self.current_page = index + 1  # PipsPager索引从0开始，我们内部从1开始
        self.loadProject(self.current_project_path, self.card_id, isMessage=False)

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
                parent=main_window if main_window else self.window(),
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
                parent=main_window if main_window else self.window(),
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
                    isTranslated=True,
                )
            else:
                result = project.addEpisode(
                    self.card_id,
                    folder_num,
                    dialog.LineEdit_1.text().strip(),
                    "",
                    dialog.LineEdit_2.text().strip(),
                    isTranslated=False,
                )

            if result[0]:
                self.loadProject(
                    self.current_project_path, self.card_id, isMessage=False
                )
                event_bus.notification_service.show_success("成功", "已插入新的一集")
            else:
                event_bus.notification_service.show_error("错误", result[-1])
        else:
            pass

    def deleteEpisode(self, folder_num):
        """删除一集"""
        title = "确认删除"
        content = "确定要删除这一集吗？此操作不可撤销。"

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
            result = project.deleteEpisode(self.card_id, folder_num)
            if result[0]:
                self.loadProject(
                    self.current_project_path, self.card_id, isMessage=False
                )
                event_bus.notification_service.show_success(
                    "成功", f"已删除第 {folder_num} 集"
                )
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
            text1=f"{project.project_subtitle[self.card_id][folder_num - 1]}",
            text2=f"{project.project_video_url[self.card_id][folder_num - 1]}",
            parent=main_window if main_window else self.window(),
            error1="请输入标题",
            error2="请输入视频url",
        )
        dialog.LineEdit_1.setText(
            f"{project.project_subtitle[self.card_id][folder_num - 1]}"
        )
        dialog.LineEdit_2.setText(
            f"{project.project_video_url[self.card_id][folder_num - 1]}"
        )
        if dialog.exec():
            project.change_subtitle(
                self.card_id, folder_num, dialog.LineEdit_1.text().strip()
            )
            project.change_subtitle(
                self.card_id, folder_num, dialog.LineEdit_2.text().strip(), offset=1
            )
            event_bus.notification_service.show_success(
                "成功", f"编辑第 {folder_num} 集标题和视频url成功"
            )
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

            event_bus.notification_service.show_success(
                "成功", f"已上传文件到: {os.path.basename(folder_path)}/{file_name}"
            )
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"上传文件失败: {str(e)}")

    def openUrl(self, url):
        QDesktopServices.openUrl(QUrl(url))

    def showEvent(self, event):
        """每次切换到该界面时自动刷新项目详情"""
        super().showEvent(event)
        # 只有在 current_project_path 和 card_id 已经设置的情况下才刷新
        if self.current_project_path and self.card_id != -1:
            self.loadProject(self.current_project_path, self.card_id, isMessage=False)


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

            self.downloadFinished.emit(
                True, f"图片成功下载并保存到: {self.save_path}", self.save_path
            )

        except requests.exceptions.RequestException as e:
            self.downloadFinished.emit(False, f"下载图片时出错: {e}", self.save_path)
        except Exception as e:
            self.downloadFinished.emit(False, f"发生未知错误: {e}", self.save_path)


class FileItemWidget(SimpleCardWidget):
    """自定义文件项widget，使用QFluentWidgets控件"""

    def __init__(
        self,
        window,
        card_id,
        folder_num,
        file_name,
        file_path,
        icon,
        file_exists,
        other_exists,
        donwload_need=False,
        extract_need=False,
        translate_need=False,
        ffmpeg_need=False,
        parent=None,
    ):
        super().__init__(parent)
        self.main_window = window
        self.card_id = card_id
        self.folder_num = folder_num
        self.file_name = file_name
        self.file_path = file_path
        self.file_exists = file_exists
        self.other_exists = other_exists
        self.download_need = donwload_need
        self.extract_need = extract_need
        self.translate_need = translate_need
        self.ffmpeg_need = ffmpeg_need

        self.setFixedHeight(50)
        self.setObjectName("fileItemCard")
        if not isDarkTheme():
            self.setStyleSheet("""
                #fileItemCard {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    margin: 2px;
                }
                #fileItemCard:hover {
                    background-color: #f5f5f5;
                }
            """)
        else:
            self.setStyleSheet("""
                #fileItemCard {
                    background-color: #323232;
                    border: 1px solid #404040;
                    border-radius: 6px;
                    margin: 2px;
                }
                #fileItemCard:hover {
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
        statusLabel.setStyleSheet(
            """
            QLabel {
                color: %s;
                font-weight: bold;
                margin-right: 10px;
            }
        """
            % ("green" if self.file_exists else "red")
        )

        # 按钮区域
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(5)

        # 下载按钮（仅在需要时显示）
        if self.download_need and not self.file_exists:
            self.downloadBtn = TransparentToolButton(FIF.DOWNLOAD, self)
            self.downloadBtn.setToolTip("下载缺失的文件")
            self.downloadBtn.setFixedSize(32, 32)
            self.downloadBtn.clicked.connect(self.donwloadFile)
            buttonLayout.addWidget(self.downloadBtn)

        # 提取字幕按钮 (当有生肉视频但是无原文.srt时显示)
        if self.extract_need and not self.file_exists and self.other_exists[1]:
            self.extractBtn = TransparentToolButton(FIF.ALIGNMENT, self)
            self.extractBtn.setToolTip("提取字幕")
            self.extractBtn.setFixedSize(32, 32)
            self.extractBtn.clicked.connect(self.extractSubtitle)
            buttonLayout.addWidget(self.extractBtn)

        # 翻译字幕按钮 (当有原文.srt但是无译文.srt时显示)
        if self.translate_need and not self.file_exists and self.other_exists[3]:
            self.translateBtn = TransparentToolButton(FIF.GLOBE, self)
            self.translateBtn.setToolTip("翻译字幕")
            self.translateBtn.setFixedSize(32, 32)
            self.translateBtn.clicked.connect(self.translateSubtitle)
            buttonLayout.addWidget(self.translateBtn)

        # 视频压制按钮 (当有熟肉.mp4时显示)
        if self.ffmpeg_need and self.other_exists[2]:
            self.ffmpegBtn = TransparentToolButton(FIF.VIDEO, self)
            self.ffmpegBtn.setToolTip("视频压制")
            self.ffmpegBtn.setFixedSize(32, 32)
            self.ffmpegBtn.clicked.connect(self.ffmpegVideo)
            buttonLayout.addWidget(self.ffmpegBtn)

        # 打开文件路径按钮
        self.openPathBtn = TransparentToolButton(FIF.FOLDER, self)
        self.openPathBtn.setToolTip("打开文件所在路径")
        self.openPathBtn.setFixedSize(32, 32)
        self.openPathBtn.clicked.connect(self.openFileLocation)

        # 删除文件按钮
        self.deleteBtn = TransparentToolButton(FIF.DELETE, self)
        self.deleteBtn.setToolTip("删除文件")
        self.deleteBtn.setFixedSize(32, 32)
        self.deleteBtn.clicked.connect(self.deleteFile)
        self.deleteBtn.setEnabled(self.file_exists)

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
                subprocess.Popen(
                    f'explorer /select,"{self.file_path}"',
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif platform.system() == "Darwin":
                subprocess.Popen(
                    ["open", "-R", self.file_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                # Linux系统
                folder_path = os.path.dirname(self.file_path)
                subprocess.Popen(
                    ["xdg-open", folder_path],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
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
            self.window(),
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
                event_bus.notification_service.show_success(
                    "成功", f"已删除文件: {self.file_name}"
                )
            except Exception as e:
                event_bus.notification_service.show_error(
                    "错误", f"删除文件时出错: {str(e)}"
                )

    def donwloadFile(self):
        """下载缺失的文件"""

        file_ext = os.path.splitext(self.file_name)[1].lower()

        if file_ext in [".jpg", ".jpeg", ".png"]:
            # 下载封面 这个函数就不归进donwload_interface.py里了
            self.donwloadPic()
        else:
            # 下载视频
            self.downloadVideo()

    def donwloadPic(self):
        download_path = os.path.dirname(self.file_path)

        dialog = CustomMessageBox(
            title=f"下载第 {self.folder_num} 集封面",
            text="请输入视频ID: https://www.youtube.com/watch?v=",
            parent=self.window(),
            min_width=450,
        )
        # v = project.project_video_url[self.card_id][self.folder_num - 1]
        # dialog.LineEdit.setText(v)

        if dialog.exec():
            video_url = dialog.LineEdit.text().strip()
            if video_url:
                # 通过信号发送下载请求
                download_path = self.file_path

                # 找到父级ProjectDetailInterface并发射信号
                parent = self.parent()
                while parent:
                    if isinstance(parent, ProjectDetailInterface):
                        parent.downloadPic.emit(video_url, download_path)
                        break
                    parent = parent.parent()

    def downloadVideo(self):
        download_path = os.path.dirname(self.file_path)

        dialog = CustomMessageBox(
            title=f"下载第 {self.folder_num} 集生肉视频",
            text="请输入视频url: https://www.youtube.com/watch?v=",
            parent=self.window(),
            min_width=450,
        )
        v = project.project_video_url[self.card_id][self.folder_num - 1]
        dialog.LineEdit.setText(v)

        if dialog.exec():
            video_url = dialog.LineEdit.text().strip()
            if video_url:
                # 通过信号发送下载请求
                download_path = Path(self.file_path).parent
                print(download_path)
                # 发射信号
                event_bus.download_requested.emit(
                    EventBuilder.download_video(
                        video_url,
                        download_path,
                    )
                )
                # 显示下载中的提示
                # event_bus.notification_service.show_info(
                #     "成功", f"已添加视频下载任务: {video_url}"
                # )

    def extractSubtitle(self):
        """切换到提取界面"""
        video_file = Path(self.file_path)
        if video_file.name == "原文.srt":
            file_path = video_file.parent / "生肉.mp4"
        event_bus.add_video_signal.emit(str(file_path))

        event_bus.switchToSampleCard.emit("VideocrStackedInterfaces", 3)

    def translateSubtitle(self):
        """添加翻译任务"""
        # 自动生成输出文件路径
        output_file = Path(self.file_path)
        if output_file.name == "译文.srt":
            file_path = output_file.parent / "原文.srt"
        else:
            file_path = output_file.parent / f"{output_file.stem}_translated.srt"

        event_bus.translate_requested.emit(str(file_path), str(output_file))

    def ffmpegVideo(self):
        """视频压制"""
        # 自动生成输出文件路径
        output_file = Path(self.file_path)
        if output_file.name == "熟肉.mp4":
            file_path = output_file.parent / "熟肉_压制.mp4"
        else:
            file_path = output_file.parent / f"{output_file.stem}_.mp4"

        event_bus.ffmpeg_requested.emit(str(output_file), str(file_path))


class FileListWidget(QWidget):
    """自定义文件列表widget"""

    def __init__(self, window, card_id, folder_num, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.main_window = window
        self.card_id = card_id
        self.folder_num = folder_num
        self.fileWidgets = []
        self.file_exists = []  # 封面 生肉 熟肉 原文 译文

    def addFileItem(
        self,
        file_name,
        file_path,
        icon,
        file_exists,
        download_need=False,
        extract_need=False,
        translate_need=False,
        ffmpeg_need=False,
    ):
        """添加文件项"""
        self.file_exists.append(file_exists)
        fileWidget = FileItemWidget(
            self.main_window,
            self.card_id,
            self.folder_num,
            file_name,
            file_path,
            icon,
            file_exists,
            self.file_exists,
            download_need,
            extract_need,
            translate_need,
            ffmpeg_need,
            self,
        )
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

            if file_ext == ".srt":
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
                subprocess.Popen(
                    ["notepad", file_path], creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif platform.system() == "Darwin":
                subprocess.call(("open", "-a", "TextEdit", file_path))
            else:
                subprocess.call(("xdg-open", file_path))
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"打开文件失败: {str(e)}")

    def fallbackOpenFile(self, file_path):
        """备用的文件打开方式"""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.call(("open", file_path))
            else:
                subprocess.call(("xdg-open", file_path))
        except Exception as e:
            event_bus.notification_service.show_error("错误", f"无法打开文件: {str(e)}")

    def uploadMissingFile(self, file_path):
        """上传缺失的文件"""
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

                    event_bus.notification_service.show_success(
                        "成功", f"已上传文件: {file_name}"
                    )
                except Exception as e:
                    event_bus.notification_service.show_success(
                        "错误", f"上传文件失败: {str(e)}"
                    )

    def clearFiles(self):
        """清空所有文件项"""
        for widget in self.fileWidgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.fileWidgets.clear()
