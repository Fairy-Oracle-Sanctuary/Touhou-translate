# coding: utf-8
import sys

from PySide6.QtCore import QUrl, QSize, Qt, QLocale, Signal
from PySide6.QtGui import QIcon, QColor, QGuiApplication, QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QFrame, QHBoxLayout
from PySide6.QtSql import QSqlDatabase

from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen, MessageBox, InfoBarIcon, SubtitleLabel, setFont
from qfluentwidgets import FluentIcon as FIF

from .home_interface import HomeInterface
from .project_interface import ProjectInterface
from .download_interface import DownloadInterface  # 假设你有一个播放列表界面

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

        self.initWindow()

        # 创建页面
        # self.homeInterface = HomeInterface(self)
        self.projectInterface = ProjectInterface(self)
        self.downloadInterface = DownloadInterface(self)  

        # 连接信号
        # self.projectInterface.topButtonCard.newFromPlaylistButton.clicked.connect(self.switch_to_download_interface)

        self.initNavigation()

        # 初始化完毕 取消启动界面
        self.splashScreen.finish()

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
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
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