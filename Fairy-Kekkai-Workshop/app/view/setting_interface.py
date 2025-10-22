# coding:utf-8
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog, QWidget
from qfluentwidgets import (
    ComboBoxSettingCard,
    ExpandLayout,
    PrimaryPushSettingCard,
    PushSettingCard,
    RangeSettingCard,
    ScrollArea,
    SwitchSettingCard,
    TitleLabel,
    setFont,
    setTheme,
    setThemeColor,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCardGroup as CardGroup
from qframelesswindow.utils import getSystemAccentColor

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import AUTHOR, VERSION, YEAR

# from ..common.signal_bus import signalBus
# from ..common.icon import Logo


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

        # 关于
        self.aboutGroup = SettingCardGroup(self.tr("关于"), self.scrollWidget)
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("检查更新"),
            ":/app/images/logo.png",
            self.tr("关于"),
            "© "
            + self.tr("Copyright")
            + f" {YEAR}, {AUTHOR}. "
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

        # 检查更新
        self.aboutCard.clicked.connect(event_bus.checkUpdateSig)
