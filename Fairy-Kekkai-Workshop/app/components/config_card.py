# coding:utf-8
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog, QWidget
from qfluentwidgets import (
    ComboBoxSettingCard,
    ExpandLayout,
    LineEdit,
    PushSettingCard,
    RangeSettingCard,
    ScrollArea,
    SettingCard,
    SwitchSettingCard,
    TitleLabel,
    setFont,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SettingCardGroup as CardGroup

from ..common.config import cfg


class SettingCardGroup(CardGroup):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        setFont(self.titleLabel, 14, QFont.Weight.DemiBold)


class LineEditSettingCard(SettingCard):
    """自定义文本输入设置卡片"""

    def __init__(
        self, configItem, icon, title, content=None, placeholderText="", parent=None
    ):
        super().__init__(icon, title, content, parent)
        self.configItem = configItem

        self.lineEdit = LineEdit(self)
        self.lineEdit.setPlaceholderText(placeholderText)
        self.lineEdit.setText(self.configItem.value)
        self.lineEdit.textChanged.connect(lambda v: cfg.set(configItem, v))

        self.hBoxLayout.addWidget(self.lineEdit, 1)
        self.hBoxLayout.addSpacing(16)


class YTDLPSettingInterface(ScrollArea):
    """YT-DLP 设置界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = TitleLabel(self.tr("YT-DLP 下载设置"), self)

        # ytdlp路径
        self.ytdlpPathGroup = SettingCardGroup(
            self.tr("YT-DLP 路径"), self.scrollWidget
        )
        self.ytdlpPathCard = PushSettingCard(
            self.tr("选择文件"),
            ":/app/images/logo/ytdlp.svg",
            "yt-dlp",
            cfg.get(cfg.ytdlpPath),
            self.ytdlpPathGroup,
        )

        # 下载格式与质量
        self.formatGroup = SettingCardGroup(
            self.tr("下载格式与质量"), self.scrollWidget
        )
        self.downloadFormatCard = ComboBoxSettingCard(
            cfg.downloadFormat,
            FIF.VIDEO,
            self.tr("下载格式"),
            self.tr("选择视频下载格式"),
            texts=[
                self.tr("MP4格式"),
                self.tr("最佳质量"),
                self.tr("最差质量"),
                self.tr("最佳视频"),
                self.tr("最佳音频"),
            ],
            parent=self.formatGroup,
        )
        self.downloadQualityCard = ComboBoxSettingCard(
            cfg.downloadQuality,
            FIF.CAMERA,
            self.tr("视频质量"),
            self.tr("选择视频分辨率"),
            texts=[
                self.tr("4K (2160p)"),
                self.tr("2K (1440p)"),
                self.tr("全高清 (1080p)"),
                self.tr("高清 (720p)"),
                self.tr("标清 (480p)"),
                self.tr("流畅 (360p)"),
                self.tr("最佳质量"),
                self.tr("最差质量"),
            ],
            parent=self.formatGroup,
        )
        self.videoCodecCard = ComboBoxSettingCard(
            cfg.videoCodec,
            FIF.DEVELOPER_TOOLS,
            self.tr("视频编码器"),
            self.tr("选择视频编码格式"),
            texts=["H.264", "H.265", "VP9", "AV1", "MP4V"],
            parent=self.formatGroup,
        )
        self.audioCodecCard = ComboBoxSettingCard(
            cfg.audioCodec,
            FIF.MUSIC,
            self.tr("音频编码器"),
            self.tr("选择音频编码格式"),
            texts=["AAC", "FLAC", "MP3", "Opus", "Vorbis"],
            parent=self.formatGroup,
        )

        # 代理设置
        self.proxyGroup = SettingCardGroup(self.tr("代理设置"), self.scrollWidget)
        self.systemProxyCard = SwitchSettingCard(
            FIF.WIFI,
            self.tr("系统代理"),
            self.tr("是否启用系统默认代理"),
            configItem=cfg.systemProxy,
            parent=self.proxyGroup,
        )
        self.proxyUrlCard = LineEditSettingCard(
            cfg.proxyUrl,
            FIF.GLOBE,
            self.tr("自定义代理"),
            self.tr("设置自定义的代理地址"),
            placeholderText=cfg.get(cfg.proxyUrl),
            parent=self.proxyGroup,
        )

        # 字幕设置
        self.subtitleGroup = SettingCardGroup(self.tr("字幕设置"), self.scrollWidget)
        self.downloadSubtitlesCard = SwitchSettingCard(
            FIF.LANGUAGE,
            self.tr("下载字幕"),
            self.tr("自动下载视频字幕"),
            configItem=cfg.downloadSubtitles,
            parent=self.subtitleGroup,
        )
        self.subtitleLanguagesCard = LineEditSettingCard(
            cfg.subtitleLanguages,
            FIF.FONT,
            self.tr("字幕语言"),
            self.tr("设置字幕语言，多个语言用逗号分隔"),
            placeholderText="en,zh,ja",
            parent=self.subtitleGroup,
        )
        self.embedSubtitlesCard = SwitchSettingCard(
            FIF.CHAT,
            self.tr("内嵌字幕"),
            self.tr("将字幕嵌入视频文件中"),
            configItem=cfg.embedSubtitles,
            parent=self.subtitleGroup,
        )

        # 元数据与缩略图
        self.metadataGroup = SettingCardGroup(
            self.tr("元数据与缩略图"), self.scrollWidget
        )
        self.downloadThumbnailCard = SwitchSettingCard(
            FIF.PHOTO,
            self.tr("下载缩略图"),
            self.tr("下载视频缩略图"),
            configItem=cfg.downloadThumbnail,
            parent=self.metadataGroup,
        )
        self.embedThumbnailCard = SwitchSettingCard(
            FIF.PHOTO,
            self.tr("内嵌缩略图"),
            self.tr("将缩略图嵌入视频文件中"),
            configItem=cfg.embedThumbnail,
            parent=self.metadataGroup,
        )
        self.downloadMetadataCard = SwitchSettingCard(
            FIF.INFO,
            self.tr("下载元数据"),
            self.tr("下载视频元数据信息"),
            configItem=cfg.downloadMetadata,
            parent=self.metadataGroup,
        )
        self.writeDescriptionCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("写入描述"),
            self.tr("将视频描述写入单独文件"),
            configItem=cfg.writeDescription,
            parent=self.metadataGroup,
        )
        self.writeInfoJsonCard = SwitchSettingCard(
            FIF.CODE,
            self.tr("写入信息JSON"),
            self.tr("将视频信息写入JSON文件"),
            configItem=cfg.writeInfoJson,
            parent=self.metadataGroup,
        )
        self.writeAnnotationsCard = SwitchSettingCard(
            FIF.EDIT,
            self.tr("写入注释"),
            self.tr("写入视频注释信息"),
            configItem=cfg.writeAnnotations,
            parent=self.metadataGroup,
        )

        # 下载控制
        self.downloadControlGroup = SettingCardGroup(
            self.tr("下载控制"), self.scrollWidget
        )
        self.concurrentDownloadsCard = RangeSettingCard(
            cfg.concurrentDownloads,
            FIF.SPEED_HIGH,
            title=self.tr("并发下载数量"),
            content=self.tr("同时下载的最大视频数量"),
            parent=self.downloadControlGroup,
        )
        self.retryAttemptsCard = RangeSettingCard(
            cfg.retryAttempts,
            FIF.SYNC,
            title=self.tr("重试次数"),
            content=self.tr("下载失败时的重试次数"),
            parent=self.downloadControlGroup,
        )
        self.downloadTimeoutCard = RangeSettingCard(
            cfg.downloadTimeout,
            FIF.ROTATE,
            title=self.tr("下载超时(秒)"),
            content=self.tr("下载超时时间设置"),
            parent=self.downloadControlGroup,
        )
        self.limitDownloadRateCard = SwitchSettingCard(
            FIF.PAGE_LEFT,
            self.tr("限速下载"),
            self.tr("启用下载速率限制"),
            configItem=cfg.limitDownloadRate,
            parent=self.downloadControlGroup,
        )
        self.maxDownloadRateCard = LineEditSettingCard(
            cfg.maxDownloadRate,
            FIF.PAGE_RIGHT,
            self.tr("最大下载速率"),
            self.tr("设置最大下载速率 (如: 10M, 1K)"),
            placeholderText="10M",
            parent=self.downloadControlGroup,
        )
        self.skipExistingFilesCard = SwitchSettingCard(
            FIF.ACCEPT,
            self.tr("跳过已存在文件"),
            self.tr("避免重复下载已存在的文件"),
            configItem=cfg.skipExistingFiles,
            parent=self.downloadControlGroup,
        )

        # 播放列表设置
        # self.playlistGroup = SettingCardGroup(
        #     self.tr("播放列表设置"), self.scrollWidget
        # )
        # self.playlistStartCard = RangeSettingCard(
        #     cfg.playlistStart,
        #     FIF.NUMBER_SYMBOL,
        #     title=self.tr("起始位置"),
        #     content=self.tr("播放列表下载起始位置"),
        #     parent=self.playlistGroup,
        # )
        # self.playlistEndCard = RangeSettingCard(
        #     cfg.playlistEnd,
        #     FIF.NUMBER_SYMBOL,
        #     title=self.tr("结束位置"),
        #     content=self.tr("播放列表下载结束位置 (0表示无限制)"),
        #     parent=self.playlistGroup,
        # )
        # self.extractAudioCard = SwitchSettingCard(
        #     FIF.AUDIO,
        #     self.tr("提取音频"),
        #     self.tr("只下载音频不下载视频"),
        #     configItem=cfg.extractAudio,
        #     parent=self.playlistGroup,
        # )
        # self.keepVideoCard = SwitchSettingCard(
        #     FIF.VIDEO,
        #     self.tr("保留视频"),
        #     self.tr("提取音频时保留原始视频文件"),
        #     configItem=cfg.keepVideo,
        #     parent=self.playlistGroup,
        # )

        # 高级设置
        self.advancedGroup = SettingCardGroup(self.tr("高级设置"), self.scrollWidget)
        self.outputTemplateCard = LineEditSettingCard(
            cfg.outputTemplate,
            FIF.SAVE,
            self.tr("输出模板"),
            self.tr("设置输出文件名模板"),
            placeholderText="%(title)s.%(ext)s",
            parent=self.advancedGroup,
        )
        self.useCookiesCard = SwitchSettingCard(
            FIF.CERTIFICATE,
            self.tr("使用Cookies"),
            self.tr("使用cookies文件进行下载"),
            configItem=cfg.useCookies,
            parent=self.advancedGroup,
        )
        self.cookiesFileCard = PushSettingCard(
            self.tr("选择文件"),
            FIF.DOCUMENT,
            "Cookies文件",
            cfg.get(cfg.cookiesFile),
            self.advancedGroup,
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 90, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("ytdlpSettingInterface")

        # initialize style sheet
        setFont(self.settingLabel, 23, QFont.Weight.DemiBold)
        self.enableTransparentBackground()

        # initialize layout
        self.__initLayout()
        self._connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 40)

        # ytdlp路径
        self.ytdlpPathGroup.addSettingCard(self.ytdlpPathCard)

        # 下载格式与质量
        self.formatGroup.addSettingCard(self.downloadFormatCard)
        self.formatGroup.addSettingCard(self.downloadQualityCard)
        self.formatGroup.addSettingCard(self.videoCodecCard)
        self.formatGroup.addSettingCard(self.audioCodecCard)

        # 代理设置
        self.proxyGroup.addSettingCard(self.systemProxyCard)
        self.proxyGroup.addSettingCard(self.proxyUrlCard)

        # 字幕设置
        self.subtitleGroup.addSettingCard(self.downloadSubtitlesCard)
        self.subtitleGroup.addSettingCard(self.subtitleLanguagesCard)
        self.subtitleGroup.addSettingCard(self.embedSubtitlesCard)

        # 元数据与缩略图
        self.metadataGroup.addSettingCard(self.downloadThumbnailCard)
        self.metadataGroup.addSettingCard(self.embedThumbnailCard)
        self.metadataGroup.addSettingCard(self.downloadMetadataCard)
        self.metadataGroup.addSettingCard(self.writeDescriptionCard)
        self.metadataGroup.addSettingCard(self.writeInfoJsonCard)
        self.metadataGroup.addSettingCard(self.writeAnnotationsCard)

        # 下载控制
        self.downloadControlGroup.addSettingCard(self.concurrentDownloadsCard)
        self.downloadControlGroup.addSettingCard(self.retryAttemptsCard)
        self.downloadControlGroup.addSettingCard(self.downloadTimeoutCard)
        self.downloadControlGroup.addSettingCard(self.limitDownloadRateCard)
        self.downloadControlGroup.addSettingCard(self.maxDownloadRateCard)
        self.downloadControlGroup.addSettingCard(self.skipExistingFilesCard)

        # 播放列表设置
        # self.playlistGroup.addSettingCard(self.playlistStartCard)
        # self.playlistGroup.addSettingCard(self.playlistEndCard)
        # self.playlistGroup.addSettingCard(self.extractAudioCard)
        # self.playlistGroup.addSettingCard(self.keepVideoCard)

        # 高级设置
        self.advancedGroup.addSettingCard(self.outputTemplateCard)
        self.advancedGroup.addSettingCard(self.useCookiesCard)
        self.advancedGroup.addSettingCard(self.cookiesFileCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(26)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.ytdlpPathGroup)
        self.expandLayout.addWidget(self.formatGroup)
        self.expandLayout.addWidget(self.proxyGroup)
        self.expandLayout.addWidget(self.subtitleGroup)
        self.expandLayout.addWidget(self.metadataGroup)
        self.expandLayout.addWidget(self.downloadControlGroup)
        # self.expandLayout.addWidget(self.playlistGroup)
        self.expandLayout.addWidget(self.advancedGroup)

    def _onYTDLPPathCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("选择ytdlp文件"))

        if not path or cfg.get(cfg.ytdlpPath) == path:
            return

        cfg.set(cfg.ytdlpPath, path)
        self.ytdlpPathCard.setContent(path)

    def _onCookiesFileCardClicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("选择Cookies文件"),
            "",
            self.tr("Text Files (*.txt);;All Files (*)"),
        )

        if not path or cfg.get(cfg.cookiesFile) == path:
            return

        cfg.set(cfg.cookiesFile, path)
        self.cookiesFileCard.setContent(path)

    def _connectSignalToSlot(self):
        """绑定信号"""
        # ytdlp路径
        self.ytdlpPathCard.clicked.connect(self._onYTDLPPathCardClicked)

        # 高级设置
        self.cookiesFileCard.clicked.connect(self._onCookiesFileCardClicked)
