# coding:utf-8
from qfluentwidgets import (ScrollArea, CardWidget, IconWidget, BodyLabel, CaptionLabel, 
                           PushButton, PrimaryPushButton, HyperlinkButton, FluentIcon,
                           StrongBodyLabel, TitleLabel, SubtitleLabel, ProgressRing,
                           ImageLabel, SimpleCardWidget, HorizontalSeparator, InfoBar)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPainterPath, QLinearGradient
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class HomeInterface(ScrollArea):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__initWidget()
        # self.loadSamples()

    def __initWidget(self):
        self.setObjectName('homeInterface')
        self.enableTransparentBackground()
