# coding: utf-8
import sys
from pathlib import Path

from PySide6.QtCore import QRect, QSettings, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    InfoBarPosition,
    MessageBox,
    MSFluentWindow,
    NavigationItemPosition,
    SplashScreen,
)

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import GITHUB_URL, RELEASE_URL
from ..components.infobar import NotificationService
from ..components.system_tray import SystemTray
from ..service.version_service import VersionService
from .download_interface import DownloadStackedInterface
from .home_interface import HomeInterface
from .project_interface import ProjectStackedInterface
from .setting_interface import SettingInterface
from .translate_interface import TranslateStackedInterfaces
from .videocr_interface import VideocrStackedInterfaces


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()

        # 初始化版本服务
        self.versionManager = VersionService()

        # 初始化通知服务
        self.notification_service = NotificationService(self)

        # 可以自定义配置（可选）
        self.notification_service.set_default_duration(3000)
        self.notification_service.set_position(InfoBarPosition.BOTTOM_RIGHT)
        event_bus.notification_service = self.notification_service

        # 读取设置
        self.settings = QSettings("Fairy-Kekkai-Workshop", "Settings")

        # 背景图片
        self.isShowBackground = False
        if cfg.get(cfg.showBackground):
            if Path(cfg.get(cfg.backgroundPath)).exists():
                self.isShowBackground = True
                self.backgroundPixmap = QPixmap(cfg.get(cfg.backgroundPath))
            else:
                event_bus.notification_service.show_error(
                    "背景图片错误", "请检查图片是否存在"
                )

        # 创建页面
        self.homeInterface = HomeInterface(self)
        self.projectInterface = ProjectStackedInterface(self)
        self.downloadInterface = DownloadStackedInterface(self)
        self.videoCRInterface = VideocrStackedInterfaces(self)
        self.translateInterface = TranslateStackedInterfaces(self)
        self.settingInterface = SettingInterface(self)

        self.interface = [
            self.homeInterface,
            self.projectInterface,
            self.downloadInterface,
            self.videoCRInterface,
            self.translateInterface,
            self.settingInterface,
        ]
        # 连接信号
        # self.projectInterface.topButtonCard.newFromPlaylistButton.clicked.connect(self.switch_to_download_interface)

        self.initNavigation()

        # 初始化系统托盘
        self.system_tray = SystemTray(self)

        # 设置应用程序不在最后一个窗口关闭时退出
        QApplication.setQuitOnLastWindowClosed(False)

        # 连接信号
        self.system_tray.messageClicked.connect(self.on_tray_message_clicked)
        event_bus.checkUpdateSig.connect(self.checkUpdate)
        event_bus.switchToSampleCard.connect(self.switchToSample)
        event_bus.openUrl.connect(self.openUrl)
        event_bus.download_finished_signal.connect(
            self.show_system_tray_message_download_finished
        )
        event_bus.ocr_finished_signal.connect(
            self.show_system_tray_message_videocr_finished
        )
        event_bus.translate_finished_signal.connect(
            self.show_system_tray_message_translate_finished
        )

        # 初始化完毕 取消启动界面
        self.splashScreen.finish()

        # 恢复窗口状态
        self.restore_window_state()

    def paintEvent(self, event):
        """重绘事件，绘制背景图片"""
        if self.isShowBackground:
            painter = QPainter(self)
            painter.setRenderHints(
                QPainter.RenderHint.SmoothPixmapTransform
                | QPainter.RenderHint.Antialiasing
            )

            if not self.backgroundPixmap.isNull():
                # 缩放图片以适应窗口大小，同时保持比例
                scaledPixmap = self.backgroundPixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # 计算居中位置
                x = (scaledPixmap.width() - self.width()) // 2
                y = (scaledPixmap.height() - self.height()) // 2

                # 绘制背景图片
                painter.drawPixmap(
                    0, 0, scaledPixmap, x, y, self.width(), self.height()
                )

                # 添加半透明黑色遮罩，让前景内容更清晰
                painter.fillRect(
                    self.rect(), QColor(0, 0, 0, cfg.get(cfg.backgroundRect))
                )

                # 为导航栏和标题栏添加更深的遮罩，确保内容清晰
                if self.navigationInterface.isVisible():
                    nav_rect = self.navigationInterface.geometry()
                    painter.fillRect(nav_rect, QColor(0, 0, 0, 0))

                if self.titleBar.isVisible():
                    title_bar_rect = self.titleBar.geometry()
                    painter.fillRect(title_bar_rect, QColor(0, 0, 0, 0))

                # 为标题栏按钮区域添加完全不透明的背景
                if self.titleBar.isVisible():
                    title_bar_rect = self.titleBar.geometry()

                    # 获取最小化、最大化、关闭按钮的位置
                    # 这些按钮通常在标题栏的右侧
                    button_width = 46  # 标准按钮宽度
                    button_height = title_bar_rect.height() - 15

                    # 计算按钮区域
                    close_button_rect = QRect(
                        title_bar_rect.right() - button_width,
                        title_bar_rect.top(),
                        button_width,
                        button_height,
                    )

                    maximize_button_rect = QRect(
                        close_button_rect.left() - button_width,
                        title_bar_rect.top(),
                        button_width,
                        button_height,
                    )

                    minimize_button_rect = QRect(
                        maximize_button_rect.left() - button_width,
                        title_bar_rect.top(),
                        button_width,
                        button_height,
                    )

                    # 绘制不透明背景
                    button_color = QColor(45, 45, 45)  # 深灰色背景
                    painter.fillRect(minimize_button_rect, button_color)
                    painter.fillRect(maximize_button_rect, button_color)
                    painter.fillRect(close_button_rect, button_color)
            # 调用父类的绘制事件，确保其他内容正常显示
            super().paintEvent(event)

    def setBackgroundImage(self, imagePath):
        """设置背景图片路径"""
        self.backgroundPixmap = QPixmap(imagePath)
        self.update()  # 触发重绘

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, "主页")
        self.addSubInterface(self.projectInterface, FIF.FOLDER, "项目")
        self.addSubInterface(self.downloadInterface, FIF.DOWNLOAD, "下载")
        self.addSubInterface(self.videoCRInterface, FIF.VIDEO, "字幕")
        self.addSubInterface(
            self.translateInterface, QIcon(":/app/images/icons/deepseek.svg"), "翻译"
        )

        # 添加自定义导航组件
        self.navigationInterface.addItem(
            routeKey="Help",
            icon=FIF.HELP,
            text="帮助",
            onClick=self.showHelpBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.settingInterface,
            FIF.SETTING,
            "设置",
            FIF.SETTING,
            NavigationItemPosition.BOTTOM,
        )

        # self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(960, 754 if sys.platform == "win32" else 773)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(":/app/images/logo.png"))
        self.setWindowTitle("Fairy Kekkai Workshop")

        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        screen = QApplication.primaryScreen()
        desktop = screen.availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def showHelpBox(self):
        w = MessageBox(
            self.tr("支持项目"),
            self.tr("现在团队人手紧缺，如果感兴趣的话请加入我们"),
            self,
        )
        w.yesButton.setText(self.tr("访问仓库"))
        w.cancelButton.setText(self.tr("下次一定"))

        if w.exec():
            QDesktopServices.openUrl(QUrl(GITHUB_URL))

    def restore_window_state(self):
        """恢复窗口状态"""
        # 恢复窗口大小和位置
        size = self.settings.value("window/size", self.size())
        position = self.settings.value("window/position", self.pos())

        self.resize(size)
        self.move(position)

        # 恢复窗口最大化状态
        if self.settings.value("window/maximized", False, type=bool):
            self.showMaximized()

    def save_window_state(self):
        """保存窗口状态"""
        # 如果窗口是最大化的，保存正常状态的大小
        if self.isMaximized():
            self.settings.setValue("window/maximized", True)
            self.showNormal()  # 临时恢复正常状态以获取大小
            self.settings.setValue("window/size", self.size())
            self.showMaximized()  # 恢复最大化
        else:
            self.settings.setValue("window/maximized", False)
            self.settings.setValue("window/size", self.size())
            self.settings.setValue("window/position", self.pos())

    def closeEvent(self, event):
        """重写关闭事件"""
        # 检查是否真的需要退出（例如通过托盘菜单的退出选项）
        if hasattr(self, "_really_quit") and self._really_quit:
            # 保存窗口状态
            self.save_window_state()
            # 执行真正的退出
            super().closeEvent(event)
        else:
            # 最小化到托盘
            event.ignore()
            self.hide()

            # 显示通知
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                "程序已最小化到系统托盘\n右键点击托盘图标可显示菜单",
                QIcon(":/app/images/logo.png"),
                3000,
            )

    def checkUpdate(self):
        if self.versionManager.hasNewVersion():
            self.showMessageBox(
                self.tr("检测到新版本"),
                self.tr("新版本")
                + f" {self.versionManager.lastestVersion} "
                + self.tr("可用，你是否要下载新版本？"),
                True,
                lambda: QDesktopServices.openUrl(QUrl(RELEASE_URL)),
            )
        else:
            self.showMessageBox(
                self.tr("没有新版本"),
                self.tr("Fairy Kekkai Workshop 已是最新版本"),
            )

    def showMessageBox(
        self, title: str, content: str, showYesButton=False, yesSlot=None
    ):
        """show message box"""
        w = MessageBox(title, content, self)
        w.yesButton.setText(self.tr("确定"))
        w.cancelButton.setText(self.tr("关闭"))
        if not showYesButton:
            w.cancelButton.setText(self.tr("关闭"))
            w.yesButton.hide()
            w.buttonLayout.insertStretch(0, 1)

        if w.exec() and yesSlot is not None:
            yesSlot()

    def on_tray_message_clicked(self):
        """托盘消息被点击时的处理"""
        self.show_main_window_from_tray()

    def show_main_window_from_tray(self):
        """从托盘显示主窗口"""
        self.show()
        self.activateWindow()
        self.raise_()

    def really_quit(self):
        """真正退出应用程序"""
        self._really_quit = True
        self.system_tray.hide()
        # self.close()

    def switchToSample(self, routeKey, index):
        """切换界面"""
        self.switchTo(self.interface[index])

    def openUrl(self, url):
        """打开指定 URL"""
        QDesktopServices.openUrl(QUrl(url))

    def show_system_tray_message_download_finished(self, success, message):
        """通过系统托盘显示下载完成消息"""
        if success:
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                f"下载完成 -{message}-",
                QIcon(":/app/images/logo.png"),
                3000,
            )
        else:
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                f"下载失败 -{message}-",
                QIcon(":/app/images/logo.png"),
                3000,
            )

    def show_system_tray_message_videocr_finished(self, success, message):
        """通过系统托盘显示视频字幕识别完成消息"""
        if success:
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                f"视频字幕识别完成 -{message}-",
                QIcon(":/app/images/logo.png"),
                3000,
            )
        else:
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                f"视频字幕识别失败 -{message}-",
                QIcon(":/app/images/logo.png"),
                3000,
            )

    def show_system_tray_message_translate_finished(self, success, message):
        """通过系统托盘显示翻译完成消息"""
        if success:
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                f"翻译完成 -{message[-1]}-",
                QIcon(":/app/images/logo.png"),
                3000,
            )
        else:
            self.system_tray.showMessage(
                "Fairy-Kekkai-Workshop",
                f"翻译失败 -{message}-",
                QIcon(":/app/images/logo.png"),
                3000,
            )
