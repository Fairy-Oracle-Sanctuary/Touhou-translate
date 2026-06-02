# coding:utf-8
import os
import sys

from PySide6.QtCore import QProcess, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    HyperlinkLabel,
    ImageLabel,
    MessageBox,
    PrimaryPushButton,
    SimpleCardWidget,
    TitleLabel,
    TransparentToolButton,
    VerticalSeparator,
    setFont,
)

from ..common.event_bus import event_bus
from ..common.setting import CONFIG_FILE, GITHUB_URL, UPDATE_TIME, VERSION
from ..resource import resource_rc  # noqa: F401
from ..view.log_interface import LogWindow
from .statistic_widget import StatisticsWidget


class FairyKekkaiWorkshopInfoCard(SimpleCardWidget):
    """M3U8DL information card"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        self.iconLabel = ImageLabel(
            QIcon(":/app/images/logo.png").pixmap(120, 120), self
        )

        self.nameLabel = TitleLabel(self.tr("Fairy Kekkai Workshop"), self)
        self.updateButton = PrimaryPushButton(self.tr("更新"), self)
        self.companyLabel = HyperlinkLabel(
            QUrl("https://space.bilibili.com/499929312"),
            "Baby2016",
            self,
        )

        self.versionWidget = StatisticsWidget(self.tr("版本"), f"v{VERSION}", self)
        self.updateTimeWidget = StatisticsWidget(self.tr("更新时间"), UPDATE_TIME, self)

        self.descriptionLabel = BodyLabel(
            self.tr("仙 · 结界工坊"),
            self,
        )

        self.githubButton = TransparentToolButton(FluentIcon.GITHUB, self)
        self.githubButton.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL))
        )

        self.logButton = PrimaryPushButton(FluentIcon.BOOK_SHELF, self.tr("Log"))
        self.clearLogButton = TransparentToolButton(FluentIcon.DELETE, self)
        self.clearLogButton.setToolTip(self.tr("清空所有日志"))
        self.resetButton = TransparentToolButton(FluentIcon.SYNC, self)
        self.resetButton.setToolTip(self.tr("重置所有设置并重启"))

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.__initWidgets()
        self.__connectSignalToSlot()
        self.__initLog()

    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(120)

        self.updateButton.setFixedWidth(160)

        self.descriptionLabel.setWordWrap(True)
        # self.githubButton.clicked.connect(lambda: openUrl(DEPLOY_URL))

        # self.tagButton.setCheckable(False)
        # setFont(self.tagButton, 12)
        # self.tagButton.setFixedSize(80, 32)

        self.githubButton.setFixedSize(32, 32)
        self.githubButton.setIconSize(QSize(14, 14))

        self.clearLogButton.setFixedSize(32, 32)
        self.clearLogButton.setIconSize(QSize(14, 14))
        self.resetButton.setFixedSize(32, 32)
        self.resetButton.setIconSize(QSize(14, 14))

        setFont(self.logButton, 12)
        self.logButton.setFixedSize(80, 32)

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.initLayout()

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # name label and install button
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.updateButton, 0, Qt.AlignRight)

        # company label
        self.vBoxLayout.addSpacing(3)
        self.vBoxLayout.addWidget(self.companyLabel)

        # statistics widgets
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.statisticsLayout)
        self.statisticsLayout.setContentsMargins(0, 0, 0, 0)
        self.statisticsLayout.setSpacing(10)
        self.statisticsLayout.addWidget(self.versionWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.updateTimeWidget)
        self.statisticsLayout.setAlignment(Qt.AlignLeft)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # button
        self.vBoxLayout.addSpacing(12)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.logButton, 0, Qt.AlignLeft)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.clearLogButton, 0, Qt.AlignRight)
        self.buttonLayout.addWidget(self.resetButton, 0, Qt.AlignRight)
        self.buttonLayout.addWidget(self.githubButton, 0, Qt.AlignRight)

    def __connectSignalToSlot(self):
        self.logButton.clicked.connect(self.__onLogButtonClicked)
        self.clearLogButton.clicked.connect(self.__onClearLogClicked)
        self.resetButton.clicked.connect(self.__onResetClicked)
        event_bus.log_window_closed.connect(lambda: self.logButton.setEnabled(True))
        event_bus.log_message.connect(self.appendLog)

    def __initLog(self):
        self.allLogs = ""
        self.projectLogs = ""
        self.downloadLogs = ""
        self.videoLogs = ""
        self.whisperLogs = ""
        self.aiLogs = ""
        self.ffmpegLogs = ""

    def __onLogButtonClicked(self):
        self.logButton.setEnabled(False)
        self.logWindow = LogWindow()
        self.logWindow.show()
        self.logWindow.setLog(
            self.allLogs,
            self.projectLogs,
            self.downloadLogs,
            self.videoLogs,
            self.whisperLogs,
            self.aiLogs,
            self.ffmpegLogs,
        )

    def __onClearLogClicked(self):
        """清空所有日志"""
        box = MessageBox(
            self.tr("清空所有日志"),
            self.tr("确定要清空所有日志文件吗？此操作不可恢复。"),
            self.window(),
        )
        box.yesButton.setText(self.tr("确定"))
        box.cancelButton.setText(self.tr("取消"))
        if not box.exec():
            return

        from ..common.logger import LOG_FOLDER

        deleted = 0
        if LOG_FOLDER.exists():
            for log_file in LOG_FOLDER.glob("*.log"):
                try:
                    log_file.unlink()
                    deleted += 1
                except Exception:
                    pass

        # 清空内存中的日志
        self.__initLog()
        try:
            self.logWindow.setLog("", "", "", "", "", "", "")
        except Exception:
            pass

        event_bus.notification_service.show_success(
            self.tr("清空成功"), self.tr(f"已清空 {deleted} 个日志文件")
        )

    def __onResetClicked(self):
        """重置所有设置并重启"""
        box = MessageBox(
            self.tr("重置所有设置"),
            self.tr("确定要重置软件所有设置吗？软件将会重启，此操作不可恢复。"),
            self.window(),
        )
        box.yesButton.setText(self.tr("确定"))
        box.cancelButton.setText(self.tr("取消"))
        if not box.exec():
            return

        # 删除配置文件
        try:
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
        except Exception as e:
            event_bus.notification_service.show_error(self.tr("重置失败"), str(e))
            return

        self.__restartApplication()

    def __restartApplication(self):
        """重启应用程序"""
        from PySide6.QtWidgets import QApplication

        # 标记主窗口真正退出，避免最小化到托盘
        main_window = self.window()
        if main_window is not None and hasattr(main_window, "_really_quit"):
            main_window._really_quit = True
        if main_window is not None and hasattr(main_window, "system_tray"):
            try:
                main_window.system_tray.hide()
            except Exception:
                pass

        # 在应用退出后启动新实例，避免单例共享内存冲突
        QApplication.instance().aboutToQuit.connect(self.__spawnNewInstance)
        QApplication.instance().exit(0)

    def __spawnNewInstance(self):
        """启动新的应用实例"""
        program = sys.executable
        if getattr(sys, "frozen", False):
            # 打包后的可执行文件
            args = sys.argv[1:]
        else:
            # 脚本运行
            args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
        QProcess.startDetached(program, args)

    def appendLog(self, log_name, message):
        """追加日志到日志窗口"""
        self.allLogs += message
        if log_name == "project":
            self.projectLogs += message
        elif log_name == "download":
            self.downloadLogs += message
        elif log_name == "videocr":
            self.videoLogs += message
        elif log_name == "whisper":
            self.whisperLogs += message
        elif log_name == "ai":
            self.aiLogs += message
        elif log_name == "ffmpeg":
            self.ffmpegLogs += message

        try:
            self.logWindow.setLog(
                self.allLogs,
                self.projectLogs,
                self.downloadLogs,
                self.videoLogs,
                self.whisperLogs,
                self.aiLogs,
                self.ffmpegLogs,
            )
        except Exception:
            pass

    def setVersion(self, version: str):
        text = version or "1.0.0"
        self.versionWidget.valueLabel.setText(text)
        self.versionWidget.valueLabel.setTextColor(
            QColor(0, 0, 0), QColor(255, 255, 255)
        )
