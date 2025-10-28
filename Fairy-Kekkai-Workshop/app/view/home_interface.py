# coding:utf-8
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QVBoxLayout, QWidget
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

        self._connectSignalToSlot()

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
            icon=QIcon(":/app/images/controls/setting.svg"),
            title="软件设置",
            content=self.tr("设置软件的各项参数"),
            routeKey="settingInterface",
            index=4,
        )
        self.vBoxLayout.addWidget(basicInputView)

    def _connectSignalToSlot(self):
        # 检查更新
        self.fairyKekkaiWorkshopInfoCard.updateButton.clicked.connect(
            event_bus.checkUpdateSig
        )
