# coding: utf-8
import sys

from PySide6.QtCore import QUrl, QSize, Qt, QLocale, Signal, QSettings
from PySide6.QtGui import QIcon, QColor, QGuiApplication, QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout, QSystemTrayIcon
from PySide6.QtSql import QSqlDatabase

from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen, MessageBox, InfoBarIcon, SubtitleLabel, setFont, InfoBarPosition
from qfluentwidgets import FluentIcon as FIF

from ..service.event_bus import event_bus
from ..service.infobar import NotificationService
from ..components.system_tray import SystemTray

from .home_interface import HomeInterface
from .project_interface import ProjectInterface
from .download_interface import DownloadInterface  # 假设你有一个播放列表界面

from ..resource import resource_rc

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        # 初始化通知服务
        self.notification_service = NotificationService(self)
        
        # 可以自定义配置（可选）
        self.notification_service.set_default_duration(3000)
        self.notification_service.set_position(InfoBarPosition.BOTTOM_RIGHT)
        event_bus.notification_service = self.notification_service

        # 读取设置
        self.settings = QSettings("Fairy-Kekkai-Workshop", "Settings")

        self.initWindow()

        # 创建页面
        # self.homeInterface = HomeInterface(self.notification_service, self)
        self.projectInterface = ProjectInterface(self)
        self.downloadInterface = DownloadInterface(self)  

        # 连接信号
        # self.projectInterface.topButtonCard.newFromPlaylistButton.clicked.connect(self.switch_to_download_interface)

        self.initNavigation()

        # 初始化系统托盘
        self.system_tray = SystemTray(self)
        
        # 设置应用程序不在最后一个窗口关闭时退出
        QApplication.setQuitOnLastWindowClosed(False)
        
        # 连接托盘信号
        self.system_tray.messageClicked.connect(self.on_tray_message_clicked)

        # 初始化完毕 取消启动界面
        self.splashScreen.finish()

        # 恢复窗口状态
        self.restore_window_state()

    def initNavigation(self):
        # self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.projectInterface, FIF.FOLDER, '项目')
        self.addSubInterface(self.downloadInterface, FIF.DOWNLOAD, '下载')

        # 添加自定义导航组件
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        # self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(1000, 700)
        self.setWindowIcon(QIcon(':/app/images/logo.png'))
        self.setWindowTitle('Fairy-Kekkai-Workshop')

        #创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        screen = QApplication.primaryScreen()
        desktop = screen.availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def switch_to_download_interface(self):
        """切换到播放列表界面"""
        # 设置导航栏当前项为播放列表界面
        # self.navigationInterface.setCurrentItem(self.playlistInterface.objectName())
        # 切换到播放列表界面
        self.stackedWidget.setCurrentWidget(self.downloadInterface)

    def showMessageBox(self):
        w = MessageBox(
            '支持项目',
            '现在团队人手紧缺，如果感兴趣的话请加入我们',
            self
        )
        w.yesButton.setText('访问仓库')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate"))

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
        if hasattr(self, '_really_quit') and self._really_quit:
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
                QSystemTrayIcon.Information,
                3000
            )
    
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