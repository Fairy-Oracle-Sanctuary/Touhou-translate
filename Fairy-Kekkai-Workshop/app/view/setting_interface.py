# coding:utf-8
# from ..common.signal_bus import signalBus
# from ..common.icon import Logo
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPainter
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBoxSettingCard,
    Dialog,
    ExpandLayout,
    IconWidget,
    PrimaryPushSettingCard,
    PushButton,
    PushSettingCard,
    RangeSettingCard,
    ScrollArea,
    SwitchSettingCard,
    TitleLabel,
    isDarkTheme,
    setFont,
    setTheme,
    setThemeColor,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCardGroup as CardGroup
from qframelesswindow.utils import getSystemAccentColor

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import EXE_SUFFIX, TEAM, VERSION, YEAR


class DetectionCard(QFrame):
    def __init__(self, icon, title, content, parent=None):
        super().__init__(parent)
        self.iconWidget = IconWidget(icon)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.openButton = PushButton("检测", self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(73)
        self.iconWidget.setFixedSize(16, 16)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.openButton.setFixedWidth(130)

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
        self.hBoxLayout.addSpacing(5)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class SettingCardGroup(CardGroup):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        setFont(self.titleLabel, 14, QFont.Weight.DemiBold)


class SettingInterface(ScrollArea):
    """Setting interface"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = TitleLabel(self.tr("设置"), self)

        # 个性化
        self.personalGroup = SettingCardGroup(self.tr("个性化"), self.scrollWidget)
        self.themeCard = ComboBoxSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr("应用主题"),
            self.tr("调整应用的外观"),
            texts=[self.tr("浅色"), self.tr("深色"), self.tr("跟随系统设置")],
            parent=self.personalGroup,
        )
        self.accentColorCard = ComboBoxSettingCard(
            cfg.accentColor,
            FIF.PALETTE,
            self.tr("主题色"),
            self.tr("调整应用的主题颜色"),
            texts=[self.tr("海沫绿"), self.tr("跟随系统设置")],
            parent=self.personalGroup,
        )
        self.zoomCard = ComboBoxSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("界面缩放"),
            self.tr("调整组件和字体的大小"),
            texts=["100%", "125%", "150%", "175%", "200%", self.tr("跟随系统设置")],
            parent=self.personalGroup,
        )
        self.showBackgroundCard = SwitchSettingCard(
            FIF.BACKGROUND_FILL,
            self.tr("背景图片"),
            self.tr("启用或禁用应用背景图片"),
            configItem=cfg.showBackground,
            parent=self.personalGroup,
        )
        self.backgroundPathCard = PushSettingCard(
            self.tr("选择文件"),
            FIF.PHOTO,
            "选择背景图片",
            cfg.get(cfg.backgroundPath),
            self.personalGroup,
        )
        self.backgroundRectCard = RangeSettingCard(
            cfg.backgroundRect,
            FIF.TRANSPARENT,
            title="背景透明度",
            content="调整背景图片的透明度",
        )

        # project
        self.projectGroup = SettingCardGroup(self.tr("项目"), self.scrollWidget)
        self.detailProjectItemNumCard = RangeSettingCard(
            cfg.detailProjectItemNum,
            FIF.DOCUMENT,
            title=self.tr("项目详情页数量"),
            content=self.tr("调整项目详情页项目数量"),
            parent=self.projectGroup,
        )

        # download
        self.downloadGroup = SettingCardGroup(self.tr("下载"), self.scrollWidget)
        self.ytdlpPathCard = PushSettingCard(
            self.tr("选择文件"),
            ":/app/images/logo/ytdlp.svg",
            "yt-dlp",
            cfg.get(cfg.ytdlpPath),
            self.downloadGroup,
        )
        self.ffmpegPathCard = PushSettingCard(
            self.tr("选择文件"),
            ":/app/images/logo/FFmpeg.svg",
            "FFmpeg",
            cfg.get(cfg.ffmpegPath),
            self.downloadGroup,
        )
        self.detectionCard = DetectionCard(
            FIF.SEARCH, "检测程序", "自动检测并更新程序路径"
        )

        # 关于
        self.aboutGroup = SettingCardGroup(self.tr("关于"), self.scrollWidget)
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("检查更新"),
            ":/app/images/logo.png",
            self.tr("关于"),
            "🄯 "
            + self.tr("Copyleft")
            + f" {YEAR}, {TEAM}. "
            + self.tr("当前版本")
            + " v"
            + VERSION,
            self.aboutGroup,
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 90, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        # initialize style sheet
        setFont(self.settingLabel, 23, QFont.Weight.DemiBold)
        self.enableTransparentBackground()

        # initialize layout
        self.__initLayout()
        self._connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 40)

        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.accentColorCard)
        self.personalGroup.addSettingCard(self.showBackgroundCard)
        self.personalGroup.addSettingCard(self.backgroundPathCard)
        self.personalGroup.addSettingCard(self.backgroundRectCard)

        self.projectGroup.addSettingCard(self.detailProjectItemNumCard)

        self.downloadGroup.addSettingCard(self.ytdlpPathCard)
        self.downloadGroup.addSettingCard(self.ffmpegPathCard)
        self.downloadGroup.addSettingCard(self.detectionCard)

        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(26)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.projectGroup)
        self.expandLayout.addWidget(self.downloadGroup)
        self.expandLayout.addWidget(self.aboutGroup)

        # adjust icon size
        # for card in self.findChildren(SettingCard):
        #     card.setIconSize(18, 18)

    def _showRestartTooltip(self):
        """show restart tooltip"""
        event_bus.notification_service.show_success("更新成功", "配置在重启软件后生效")

    def _backgroundPathCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("选择背景图片"))

        if not path or cfg.get(cfg.backgroundPath) == path:
            return

        cfg.set(cfg.backgroundPath, path)
        self.backgroundPathCard.setContent(path)

    def _onYTDLPPathCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("选择ytdlp文件"))

        if not path or cfg.get(cfg.ytdlpPath) == path:
            return

        cfg.set(cfg.ytdlpPath, path)
        self.ytdlpPathCard.setContent(path)

    def _onFFmpegPathCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("选择ffmpeg文件"))

        if not path or cfg.get(cfg.ffmpegPath) == path:
            return

        cfg.set(cfg.ffmpegPath, path)
        self.ffmpegPathCard.setContent(path)

    def _detectExe(self, exe_name, url, cfg_item, path_card):
        exe_path = Path(f"tools/{exe_name}{EXE_SUFFIX}").absolute()
        if not exe_path.exists():
            exe_path = shutil.which(exe_name)
        exe_path = str(exe_path)
        if exe_path:
            cfg.set(cfg_item, exe_path)
            event_bus.notification_service.show_success(
                "检测成功", f"{exe_name}路径已设置为" + exe_path
            )
            path_card.setContent(exe_path)
        else:
            dialog = Dialog("检测失败", f"未检测到{exe_name}程序，是否要下载", self)
            dialog.yesButton.setText("前往下载")
            dialog.cancelButton.setText("取消")
            if dialog.exec():
                QDesktopServices.openUrl(QUrl(url))

    def _onDectectionCardClicked(self):
        # ffmpeg
        self._detectExe(
            "ffmpeg",
            "https://ffmpeg.org/download.html",
            cfg.ffmpegPath,
            self.ffmpegPathCard,
        )

        # ytdlp
        self._detectExe(
            "yt-dlp",
            "https://github.com/yt-dlp/yt-dlp/releases",
            cfg.ytdlpPath,
            self.ytdlpPathCard,
        )

    def _onAccentColorChanged(self):
        color = cfg.get(cfg.accentColor)
        if color != "Auto":
            setThemeColor(color, save=False)
        else:
            sysColor = getSystemAccentColor()
            if sysColor.isValid():
                setThemeColor(sysColor, save=False)
            else:
                setThemeColor(color, save=False)

    def _connectSignalToSlot(self):
        """绑定信号"""
        cfg.appRestartSig.connect(self._showRestartTooltip)

        # 个性化
        cfg.themeChanged.connect(setTheme)
        cfg.accentColor.valueChanged.connect(self._onAccentColorChanged)
        self.backgroundPathCard.clicked.connect(self._backgroundPathCardClicked)

        # 下载
        self.ytdlpPathCard.clicked.connect(self._onYTDLPPathCardClicked)
        self.ffmpegPathCard.clicked.connect(self._onFFmpegPathCardClicked)
        self.detectionCard.openButton.clicked.connect(self._onDectectionCardClicked)

        # 检查更新
        self.aboutCard.clicked.connect(event_bus.checkUpdateSig)
