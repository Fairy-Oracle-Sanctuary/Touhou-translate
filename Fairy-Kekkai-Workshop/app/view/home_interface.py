# coding:utf-8
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ScrollArea

from ..common.event_bus import event_bus
from ..components.info_card import FairyKekkaiWorkshopInfoCard
from ..components.sample_card import SampleCardView


class HomeInterface(ScrollArea):
    """Home interface"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.loadProgressInfoBar = None
        self.installProgressInfoBar = None

        self.fairyKekkaiWorkshopInfoCard = FairyKekkaiWorkshopInfoCard(self.view)

        self.vBoxLayout = QVBoxLayout(self.view)

        self._initWidget()
        self.loadSamples()
        self._connectSignalToSlot()

    def _initWidget(self):
        self.setWidget(self.view)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 10, 10)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(
            self.fairyKekkaiWorkshopInfoCard, 0, Qt.AlignmentFlag.AlignTop
        )

        self.resize(780, 800)
        self.setObjectName("HomeInterface")
        self.enableTransparentBackground()

    def loadSamples(self):
        """load samples"""
        # basic input samples
        basicInputView = SampleCardView(self.tr("功能一览"), self.view)
        basicInputView.addSampleCard(
            icon=QIcon(":/app/images/controls/project.svg"),
            title="项目管理",
            content=self.tr("查看您的烤肉项目"),
            routeKey="ProjectStackedInterface",
            index=1,
        )
        basicInputView.addSampleCard(
            icon=QIcon(":/app/images/controls/download.svg"),
            title="视频下载",
            content=self.tr("从Youtube下载您相中的系列"),
            routeKey="VideocrStackedInterfaces",
            index=2,
        )
        basicInputView.addSampleCard(
            icon=QIcon(":/app/images/controls/subtitle.svg"),
            title="字幕提取",
            content=self.tr("使用最新的PaddleOCR引擎提取字幕"),
            routeKey="DownloadStackedInterfaces",
            index=3,
        )
        basicInputView.addSampleCard(
            icon=QIcon(":/app/images/controls/translate.svg"),
            title="翻译字幕",
            content=self.tr("翻译提取出的字幕文件"),
            routeKey="TranslationStackedInterface",
            index=4,
        )
        basicInputView.addSampleCard(
            icon=QIcon(":/app/images/controls/video.svg"),
            title="视频压制",
            content=self.tr("压制烤制好的视频"),
            routeKey="FFmpegStackedInterface",
            index=5,
        )
        basicInputView.addSampleCard(
            icon=QIcon(":/app/images/controls/setting.svg"),
            title="软件设置",
            content=self.tr("设置软件的各项参数"),
            routeKey="settingInterface",
            index=-1,
        )

        # url sameples
        urlSamepleView = SampleCardView(self.tr("必要资源"), self.view)
        urlSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/logo/FFmpeg.svg"),
            title="FFmpeg (已内置)",
            content="FFmpeg下载地址，下载后可在设置里设定路径",
            url="https://ffmpeg.org/download.html",
        )
        urlSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/logo/ytdlp.svg"),
            title="yt-dlp (已内置)",
            content="yt-dlp下载地址，下载后可在设置里设定路径",
            url="https://github.com/yt-dlp/yt-dlp/releases/latest",
        )
        urlSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/logo/Paddle.svg"),
            title="PaddleOCR (已内置)",
            content="PaddleOCR下载地址，根据您的硬件下载\n对应版本后设置其路径",
            url="https://github.com/timminator/PaddleOCR-Standalone/releases/latest",
        )

        urlSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/logo/Paddle.svg"),
            title="PaddleOCRv5.support.files (已内置)",
            content="PaddleOCR支持文件下载地址\n下载后设置其路径",
            url="https://github.com/timminator/PaddleOCR-Standalone/releases/download/v1.4.0/PaddleOCR.PP-OCRv5.support.files.VideOCR.7z",
        )

        """
        AI_model_dict = {
        "腾讯混元": "hunyuan-turbos-latest",
        "Deepseek": "deepseek",
        "Gemini 3 Flash": "gemini-3-flash-preview",
        "书生": "intern-latest",
        "GLM-4.5-FLASH": "glm-4.5-flash",
        "Spark-Lite": "spark-lite",
        "百度ERNIE-Speed-128K": "ernie-speed-128k",}
        """
        apiSamepleView = SampleCardView(self.tr("API平台"), self.view)
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/hunyuan-turbos-latest.svg"),
            title="腾讯混元",
            content="腾讯混元(hunyuan-lite)API服务\n⭐⭐⭐⭐⭐",
            url="https://console.cloud.tencent.com/hunyuan-turbos",
        )
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/deepseek.svg"),
            title="Deepseek",
            content="深度求索API服务\n⭐⭐⭐⭐⭐",
            url="https://platform.deepseek.com/",
        )
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/gemini-3-flash-preview.svg"),
            title="Google Gemini",
            content="Gemini 3 Flash API服务\n⭐⭐⭐⭐⭐⭐",
            url="https://aistudio.google.com/app/api-keys",
        )
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/intern-latest.svg"),
            title="书生",
            content="书生API服务\n⭐⭐⭐⭐",
            url="https://internlm.intern-ai.org.cn/api",
        )
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/glm-4.5-flash.svg"),
            title="智谱 AI",
            content="GLM-4.5-FLASH API服务\n⭐⭐⭐",
            url="https://www.bigmodel.cn/",
        )
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/spark-lite.svg"),
            title="讯飞星火",
            content="Spark-Lite API服务\n⭐⭐",
            url="https://www.xfyun.cn/",
        )
        apiSamepleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/ernie-speed-128k.svg"),
            title="百度千帆",
            content="ERNIE-Speed-128K API服务\n⭐",
            url="https://cloud.baidu.com/",
        )

        webSampleView = SampleCardView(self.tr("常用网站"), self.view)
        webSampleView.addOpenUrlCard(
            icon=QIcon(":/app/images/logo/bilibili.svg"),
            title="Bilibili",
            content="哔哩哔哩视频平台",
            url="https://www.bilibili.com/",
        )
        webSampleView.addOpenUrlCard(
            icon=QIcon(":/app/images/logo/youtube.svg"),
            title="YouTube",
            content="油管视频平台",
            url="https://www.youtube.com/",
        )
        webSampleView.addOpenUrlCard(
            icon=QIcon(":/app/images/icons/deepseek.svg"),
            title="Deepseek",
            content="深度求索",
            url="https://www.deepseek.com/",
        )
        webSampleView.addOpenUrlCard(
            icon=FIF.GITHUB,
            title="GitHub",
            content="GitHub代码仓库",
            url="https://www.github.com/",
        )

        self.vBoxLayout.addWidget(basicInputView)
        self.vBoxLayout.addWidget(urlSamepleView)
        self.vBoxLayout.addWidget(apiSamepleView)
        self.vBoxLayout.addWidget(webSampleView)

    def _connectSignalToSlot(self):
        # 检查更新
        self.fairyKekkaiWorkshopInfoCard.updateButton.clicked.connect(
            event_bus.checkUpdateSig
        )
