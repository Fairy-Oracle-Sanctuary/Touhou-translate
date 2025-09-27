# coding:utf-8
from qfluentwidgets import (SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, isDarkTheme, setFont)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCardGroup as CardGroup
from qfluentwidgets import InfoBar, TitleLabel, SettingCard
from qframelesswindow.utils import getSystemAccentColor

from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import QWidget, QLabel, QFileDialog

from ..service.config import cfg, isWin11
# from ..service.setting import HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
# from ..common.signal_bus import signalBus
# from ..common.icon import Logo


class SettingCardGroup(CardGroup):

   def __init__(self, title: str, parent=None):
       super().__init__(title, parent)
       setFont(self.titleLabel, 14, QFont.Weight.DemiBold)



class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = TitleLabel(self.tr("设置"), self)

        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('个性化'), self.scrollWidget)
        self.themeCard = ComboBoxSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('应用主题'),
            self.tr("调整应用的外观"),
            texts=[
                self.tr('浅色'), self.tr('深色'),
                self.tr('跟随系统设置')
            ],
            parent=self.personalGroup
        )
        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 90, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        setFont(self.settingLabel, 23, QFont.Weight.DemiBold)
        self.enableTransparentBackground()

        # initialize layout
        self.__initLayout()
        self._connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 40)

        self.personalGroup.addSettingCard(self.themeCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(26)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.personalGroup)

        # adjust icon size
        # for card in self.findChildren(SettingCard):
        #     card.setIconSize(18, 18)

    def _showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def _onM3U8DLPathCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose N_m3u8DL-RE"))

        if not path or cfg.get(cfg.m3u8dlPath) == path:
            return

        cfg.set(cfg.m3u8dlPath, path)
        self.m3u8dlPathCard.setContent(path)

    def _onFFmpegPathCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose ffmpeg"))

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
        """ connect signal to slot """
        # personalization
        cfg.themeChanged.connect(setTheme)
        cfg.accentColor.valueChanged.connect(self._onAccentColorChanged)

