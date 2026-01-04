# coding:utf-8
from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    HyperlinkLabel,
    ImageLabel,
    PrimaryPushButton,
    SimpleCardWidget,
    TitleLabel,
    TransparentToolButton,
    VerticalSeparator,
)

from ..common.setting import GITHUB_URL, PADDLEOCR_VERSION, UPDATE_TIME, VERSION
from ..resource import resource_rc  # noqa: F401
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
        self.paddleocrWidget = StatisticsWidget(
            self.tr("PaddleOCR"), PADDLEOCR_VERSION, self
        )

        self.descriptionLabel = BodyLabel(
            self.tr("仙 · 结界工坊"),
            self,
        )

        self.githubButton = TransparentToolButton(FluentIcon.GITHUB, self)
        self.githubButton.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL))
        )

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()

        self.__initWidgets()

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
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.paddleocrWidget)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # button
        self.vBoxLayout.addSpacing(12)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.buttonLayout)
        # self.buttonLayout.addWidget(self.tagButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.githubButton, 0, Qt.AlignRight)

    def setVersion(self, version: str):
        text = version or "1.0.0"
        self.versionWidget.valueLabel.setText(text)
        self.versionWidget.valueLabel.setTextColor(
            QColor(0, 0, 0), QColor(255, 255, 255)
        )
